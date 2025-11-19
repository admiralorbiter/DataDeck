from django.shortcuts import get_object_or_404, redirect, render
from .models import Student, StudentMediaInteraction, Comment, Media, Session, Observer, CustomAdmin, District
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CommentForm
from django.db.models import Count, Sum, F, Case, When, IntegerField, Q
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .decorators import user_or_observer_required
import json


@user_or_observer_required
def post(request, id):
    media = get_object_or_404(Media, id=id)
    
    # Check observer district permission
    if 'observer_id' in request.session:
        observer = Observer.objects.get(id=request.session['observer_id'])
        if not observer.can_view_session(media.session):
            messages.error(request, "You don't have permission to view this content")
            return redirect('observer_dashboard')
    
    # Add poster information
    if media.student:
        avatar_path = media.student.avatar_image_path
        if avatar_path and not avatar_path.startswith('/static/'):
            media.poster_avatar = f'/static/{avatar_path}'
        else:
            media.poster_avatar = avatar_path
        media.poster_name = media.student.name
    elif media.posted_by_admin:
        media.poster_avatar = media.posted_by_admin.profile_picture
        if media.poster_avatar and not media.poster_avatar.startswith('/static/'):
            media.poster_avatar = f'/static/{media.poster_avatar}'
        media.poster_name = f"Admin: {media.posted_by_admin.username}"
    else:
        media.poster_avatar = None
        media.poster_name = "Unknown"

    comments = media.comments.filter(parent__isnull=True)
    new_comment = None
    student = None

    if 'student_id' in request.session:
        student = Student.objects.filter(id=request.session['student_id']).first()

    # Only show comment form for authenticated users or students, not observers
    show_comment_form = request.user.is_authenticated or 'student_id' in request.session
    comment_form = CommentForm() if show_comment_form else None

    if request.method == 'POST' and show_comment_form:
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.media = media

            if student:
                new_comment.name = student.name
                new_comment.is_admin = False
                new_comment.student = student
            elif request.user.is_staff or request.user.is_superuser:
                new_comment.name = f"Admin: {request.user.username}"
                new_comment.is_admin = True
                new_comment.admin_avatar = request.user.profile_picture
            else:
                messages.error(request, 'You do not have permission to comment on this media.')
                return redirect('post', id=media.id)

            parent_id = request.POST.get('parent_id')
            if parent_id:
                new_comment.parent = Comment.objects.get(id=parent_id)
            
            new_comment.save()
            
            if student:
                interaction, _ = StudentMediaInteraction.objects.get_or_create(student=student, media=media)
                interaction.comment_count += 1
                interaction.save()

            messages.success(request, 'Your comment has been added successfully.')
            return redirect('post', id=media.id)
        else:
            messages.error(request, 'There was an error with your comment. Please try again.')

    if student:
        interaction = StudentMediaInteraction.objects.filter(student=student, media=media).first()
        media.user_liked_graph = interaction.liked_graph if interaction else False
        media.user_liked_eye = interaction.liked_eye if interaction else False
        media.user_liked_read = interaction.liked_read if interaction else False
    
    # Serialize the images list to JSON
    project_images_json = json.dumps(media.get_all_images())

    context = {
        'media': media,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'student': student,
        'is_observer': 'observer_id' in request.session,
        'show_comment_form': show_comment_form,
        'project_images_json': project_images_json,
    }

    return render(request, 'video_app/post.html', context)


# Add this function to update comment count
def update_comment_count(student, media):
    interaction, created = StudentMediaInteraction.objects.get_or_create(
        student=student,
        media=media
    )
    interaction.comment_count += 1
    interaction.save()


def index(request):
    student = None
    if 'student_id' in request.session:
        student = Student.objects.filter(id=request.session['student_id']).first()
    
    context = {
        'student': student,
        # ... other context variables ...
    }
    return render(request, 'video_app/index.html', context)

@login_required
def teacher_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get all sessions for this teacher
    sessions = Session.objects.filter(created_by=request.user).order_by('-created_at')
    
    # Get all students for this teacher with their interactions, but only from non-archived sessions
    # Only count interactions where at least one like flag is set (not just comment-only interactions)
    students = Student.objects.filter(
        admin=request.user,
        section__is_archived=False  # Only get students from non-archived sessions
    ).select_related(
        'section'
    ).annotate(
        total_votes=Count(
            'media_interactions',
            filter=Q(media_interactions__liked_graph=True) | 
                   Q(media_interactions__liked_eye=True) | 
                   Q(media_interactions__liked_read=True),
            distinct=True
        ),
        total_comments=Count('comments')
    ).order_by('section__section', 'name')
    
    context = {
        'teacher': request.user,
        'districts': District.objects.filter(is_active=True),
        'sessions': sessions,
        'students': students,
        'media_leaderboard': Media.objects.filter(
            session__created_by=request.user,
            session__is_archived=False  # Only show media from non-archived sessions
        ).annotate(
            # Only count interactions where at least one like flag is set (not just comment-only interactions)
            total_votes=Count(
                'student_interactions',
                filter=Q(student_interactions__liked_graph=True) | 
                       Q(student_interactions__liked_eye=True) | 
                       Q(student_interactions__liked_read=True),
                distinct=True
            ),
            total_comments=Count('comments')
        ).order_by('-total_votes', '-total_comments')[:10]
    }
    
    return render(request, 'video_app/teacher_view.html', context)

def filter_media(request, session_pk):
    tags = request.GET.getlist('tags')
    
    # Construct the URL with the selected tags
    url = reverse('session', kwargs={'session_pk': session_pk})
    if tags:
        url += '?' + '&'.join([f'tags={tag}' for tag in tags])
    
    return redirect(url)

@login_required
def set_media_password(request):
    if request.method == 'POST':
        media_password = request.POST.get('media_password')
        if media_password:
            request.user.media_password = media_password
            request.user.save()
            messages.success(request, 'Media password set successfully.')
        else:
            messages.error(request, 'Please provide a valid media password.')
    return redirect('teacher_view')

@user_passes_test(lambda u: u.is_staff)
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    media_id = comment.media.id
    if request.method == 'POST':
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('post', id=media_id)

def nav_sessions(request):
    if request.user.is_authenticated and request.user.is_staff:
        if request.user.is_superuser:
            sessions = Session.objects.all().select_related('created_by')
        else:
            sessions = Session.objects.filter(created_by=request.user)
        return {'nav_sessions': sessions}
    return {'nav_sessions': []}

@require_POST
def like_media(request, media_id, like_type):
    media = get_object_or_404(Media, id=media_id)
    student = None
    if 'student_id' in request.session:
        student = Student.objects.filter(id=request.session['student_id']).first()
    
    if not student:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
    
    interaction, created = StudentMediaInteraction.objects.get_or_create(student=student, media=media)
    
    # Update the like status
    if like_type == 'graph':
        interaction.liked_graph = not interaction.liked_graph
    elif like_type == 'eye':
        interaction.liked_eye = not interaction.liked_eye
    elif like_type == 'read':
        interaction.liked_read = not interaction.liked_read
    else:
        return JsonResponse({'success': False, 'error': 'Invalid like type'}, status=400)
    
    interaction.save()
    
    # Update the media like counts
    media.graph_likes = media.student_interactions.filter(liked_graph=True).count()
    media.eye_likes = media.student_interactions.filter(liked_eye=True).count()
    media.read_likes = media.student_interactions.filter(liked_read=True).count()
    media.save()
    
    return JsonResponse({
        'success': True,
        'graph_likes': media.graph_likes,
        'eye_likes': media.eye_likes,
        'read_likes': media.read_likes,
        'user_like': like_type if getattr(interaction, f'liked_{like_type}') else None
    })

@login_required
def observer_dashboard(request):
    observer = request.user
    if not hasattr(observer, 'district'):
        messages.error(request, "No district assigned")
        return redirect('login')
    
    # Get all teachers in the observer's district
    teachers = CustomAdmin.objects.filter(district=observer.district)
    
    # Get all sessions from teachers in this district
    sessions = Session.objects.filter(created_by__in=teachers)
    
    # Get recent media submissions
    media_items = Media.objects.filter(
        session__in=sessions
    ).select_related('session', 'session__created_by').order_by('-uploaded_at')[:50]
    
    context = {
        'teachers': teachers,
        'sessions': sessions,
        'media_items': media_items,
        'district': observer.district
    }
    return render(request, 'video_app/observer_dashboard.html', context)

@login_required
def archive_session(request, session_pk):
    session = get_object_or_404(Session, pk=session_pk)
    if session.is_archived:
        session.unarchive()
        messages.success(request, f"Hour {session.section} has been unarchived.")
    else:
        session.archive()
        messages.success(request, f"Hour {session.section} has been archived.")
    return redirect('teacher_view')
