import csv
import os
from random import shuffle
import random
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Count, Exists, OuterRef, Value, BooleanField, ExpressionWrapper
from datadeck import settings
from .forms import StartSessionForm
from .models import CustomAdmin, Session, Media, Student, Comment, StudentMediaInteraction, District
from django.core.paginator import Paginator
import json
from django.db.models import Prefetch
from django.http import JsonResponse
from .utils import get_available_character_sets
import logging
from django.http import HttpResponse
from django.utils import timezone
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

def check_section_availability(request):
    section = request.GET.get('section')
    user = request.user
    custom_admin = CustomAdmin.objects.get(id=user.id)
    is_available = not Session.objects.filter(
        section=section, 
        created_by=custom_admin,
        is_archived=False  # Only check non-archived sessions
    ).exists()
    return JsonResponse({'is_available': is_available})

@transaction.atomic
def start_session(request):
    User = get_user_model()
    user = User.objects.get(username=request.user.username)
    custom_admin, created = CustomAdmin.objects.get_or_create(id=user.id)

    if request.method == 'POST':
        form = StartSessionForm(request.POST)
        if form.is_valid():
            try:
                # Get or create the district
                district_name = form.cleaned_data['district']
                district, created = District.objects.get_or_create(
                    name=district_name,
                    defaults={
                        'code': district_name.upper().replace(' ', '_')[:20],
                        'is_active': True
                    }
                )
                
                # Update teacher information
                custom_admin.district = district
                custom_admin.school = form.cleaned_data['school']
                custom_admin.first_name = form.cleaned_data['first_name']
                custom_admin.last_name = form.cleaned_data['last_name']
                custom_admin.save()
                
                # Check for active (non-archived) sessions with the same section
                existing_active_session = Session.objects.filter(
                    section=form.cleaned_data['section'],
                    created_by=custom_admin,
                    is_archived=False  # Only check non-archived sessions
                ).first()
                
                if existing_active_session:
                    messages.error(request, f"An active session for Hour {form.cleaned_data['section']} already exists. Please archive the existing session first.")
                    return render(request, 'video_app/start_session.html', {'form': form})
                
                # Create the session
                title = f"{custom_admin.last_name}'s Data Deck Fall 2024"
                new_session = Session.objects.create(
                    name=title,
                    section=form.cleaned_data['section'],
                    created_by=custom_admin,
                    module=form.cleaned_data['module']
                )
                
                # Generate students
                generate_users_for_section(new_session, form.cleaned_data['num_students'], custom_admin)
                
                messages.success(request, f"Session '{title}' created successfully!")
                return redirect('session', session_pk=new_session.id)
                
            except Exception as e:
                messages.error(request, f"Error creating session: {str(e)}")
                return render(request, 'video_app/start_session.html', {'form': form})
        else:
            logger.warning("Form is invalid")
            logger.warning(f"Form errors: {form.errors}")
    else:
        initial_data = {
            'district': custom_admin.district.name if custom_admin.district else '',
            'school': custom_admin.school,
            'first_name': custom_admin.first_name,
            'last_name': custom_admin.last_name,
            'module': '4'
        }
        form = StartSessionForm(initial=initial_data)
    
    return render(request, 'video_app/start_session.html', {'form': form})

def session(request, session_pk):
    session_instance = get_object_or_404(Session, pk=session_pk)
    medias = Media.objects.filter(session=session_instance).select_related('student', 'posted_by_admin')

    # Get filter parameters
    graph_tag = request.GET.get('graph_tag')
    variable_tag = request.GET.get('variable_tag')

    # Apply filters if they exist
    if graph_tag:
        medias = medias.filter(graph_tag=graph_tag)
    if variable_tag:
        medias = medias.filter(variable_tag=variable_tag)

    # Get the current student from the session
    student = None
    if 'student_id' in request.session:
        student = Student.objects.filter(id=request.session['student_id']).first()

    # Annotate each media item with user interactions, comments, and poster info
    for media in medias:
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

        # Add interaction information
        interaction = media.student_interactions.filter(student=student).first()
        media.user_liked_graph = interaction.liked_graph if interaction else False
        media.user_liked_eye = interaction.liked_eye if interaction else False
        media.user_liked_read = interaction.liked_read if interaction else False
        media.has_user_comment = Comment.objects.filter(media=media, student=student).exists()

    # Pagination
    paginator = Paginator(medias, 12)  # Show 12 media items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get choices from Media model
    graph_choices = Media.GRAPH_TAG_CHOICES
    variable_choices = Media.VARIABLE_TAG_CHOICES

    # Add archived status to context
    context = {
        'session_instance': session_instance,
        'page_obj': page_obj,
        'student': student,
        'graph_choices': graph_choices,
        'variable_choices': variable_choices,
        'selected_graph_tag': graph_tag,
        'selected_variable_tag': variable_tag,
        'filter_params': f"&graph_tag={graph_tag if graph_tag else ''}&variable_tag={variable_tag if variable_tag else ''}",
        'is_archived': session_instance.is_archived,
        'archived_at': session_instance.archived_at,
    }
    
    # If the session is archived, show a banner or message
    if session_instance.is_archived:
        messages.info(request, "This is an archived session. Some features may be limited.")
    
    return render(request, 'video_app/session.html', context)

@login_required
def delete_session(request, session_pk):
    session = get_object_or_404(Session, pk=session_pk)
    session.delete()
    return redirect('teacher_view')

def pause_session(request, session_pk):
    session = get_object_or_404(Session, id=session_pk)
    session.is_paused = not(session.is_paused)
    session.save()
    return redirect('student_login')

@login_required
def archive_session(request, session_pk):
    session = get_object_or_404(Session, pk=session_pk)
    
    try:
        # Toggle archive status
        if session.is_archived:
            session.unarchive()
            messages.success(request, f"Session '{session.name}' has been unarchived.")
        else:
            session.archive()
            messages.success(request, f"Session '{session.name}' has been archived.")
    except ValidationError as e:
        # Handle the validation error
        error_message = str(e.message if hasattr(e, 'message') else e.messages[0])
        messages.error(request, error_message)
    
    return redirect('teacher_view')

@transaction.atomic
def generate_users_for_section(section, num_students, admin):
    """Generates students with unique character names and details for a given section, saving them to the database."""
    all_character_sets = get_available_character_sets()
    all_characters = []
    
    for character_set in all_character_sets:
        _, characters = load_character_set(character_set)
        all_characters.extend(characters)
    
    # Get existing character names and passcodes for this section
    existing_names = set(Student.objects.filter(section=section).values_list('name', flat=True))
    existing_passcodes = set(Student.objects.filter(section=section).values_list('password', flat=True))
    
    generated_students = []
    
    for _ in range(num_students):
        # Try to find a unique character
        attempts = 0
        max_attempts = len(all_characters)
        
        while attempts < max_attempts:
            character = random.choice(all_characters)
            if character['name'] not in existing_names:
                break
            attempts += 1
        
        if attempts == max_attempts:
            raise ValueError("Not enough unique characters available for this section.")
        
        # Generate a unique 5-digit passcode
        while True:
            passcode = generate_passcode()
            if passcode not in existing_passcodes:
                break
        
        # Construct the correct avatar image path
        avatar_image_path = f'video_app/images/characters/{character["character_set"]}/{character["filename"]}'
        
        # Save the student to the database
        student = Student.objects.create(
            name=character['name'],
            password=passcode,
            section=section,
            admin=admin,
            character_description=character['description'],
            avatar_image_path=avatar_image_path
        )
        
        generated_students.append(student)
        existing_names.add(character['name'])
        existing_passcodes.add(passcode)
    
    return generated_students


# Paths to your files
NAMES_FILE_PATH = os.path.join(settings.BASE_DIR, 'video_app', 'static', 'video_app', 'names.txt')
WORDS_FILE_PATH = os.path.join(settings.BASE_DIR, 'video_app', 'static', 'video_app', 'words.txt')

def load_names():
    """Load names from the names.txt file."""
    with open(NAMES_FILE_PATH, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f]

def load_words():
    """Load words from the words.txt file."""
    with open(WORDS_FILE_PATH, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f]

def generate_passcode():
    """Generates a unique 5-digit passcode."""
    return f"{random.randint(10000, 99999):05d}"

def load_marvel_characters():
    """Load Marvel characters from the CSV file."""
    characters = []
    csv_path = os.path.join(settings.BASE_DIR, 'video_app', 'static', 'video_app', 'characters/marvel.csv')
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            characters.append(row)
    return characters

def load_character_set(character_set):
    """Load characters from the specified CSV file."""
    characters = []
    csv_path = os.path.join(settings.BASE_DIR, 'video_app', 'static', 'video_app', 'characters', f'{character_set}.csv')
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['character_set'] = character_set  # Add the character_set to each character
            characters.append(row)
    return character_set, characters

def get_available_character_sets():
    """Get a list of available character set names."""
    character_dir = os.path.join(settings.BASE_DIR, 'video_app', 'static', 'video_app', 'characters')
    return [os.path.splitext(f)[0] for f in os.listdir(character_dir) if f.endswith('.csv')]

@login_required
@transaction.atomic
def generate_new_students(request):
    if request.method == 'POST':
        num_students = int(request.POST.get('num_students', 0))
        section_id = request.POST.get('section')
        
        if num_students > 0 and section_id:
            try:
                session = Session.objects.get(id=section_id)
                
                # Check if session is archived
                if session.is_archived:
                    messages.error(request, "Cannot add students to an archived session.")
                    return redirect('teacher_view')
                
                admin = CustomAdmin.objects.get(id=request.user.id)
                
                # Get existing student names for this session
                existing_names = set(Student.objects.filter(
                    section=session,
                    section__is_archived=False  # Only check against active sessions
                ).values_list('name', flat=True))
                
                generated_students = []
                attempts = 0
                max_attempts = num_students * 3  # Limit attempts to avoid infinite loop
                
                while len(generated_students) < num_students and attempts < max_attempts:
                    new_student = generate_user_for_section(session, admin, existing_names)
                    if new_student:
                        generated_students.append(new_student)
                        existing_names.add(new_student.name)
                    attempts += 1
                
                if len(generated_students) < num_students:
                    messages.warning(request, f"Only {len(generated_students)} new unique students could be generated. Consider using a different character set.")
                elif len(generated_students) > 0:
                    messages.success(request, f"{len(generated_students)} new students generated for Hour {session.section}")
                else:
                    messages.error(request, "No students were generated. Please try again.")
            
            except Session.DoesNotExist:
                messages.error(request, "Invalid session selected. Please try again.")
            except CustomAdmin.DoesNotExist:
                messages.error(request, "User is not a CustomAdmin. Please log in with the correct account.")
            except Exception as e:
                messages.error(request, f"Error generating students: {str(e)}")
                print(f"Error in generate_new_students: {str(e)}")  # For debugging
        else:
            messages.error(request, "Invalid input. Please try again.")
    
    return redirect('teacher_view')

def generate_user_for_section(session, admin, existing_names):
    """Generates a single student with a unique character name and details for a given section."""
    try:
        all_character_sets = get_available_character_sets()
        all_characters = []
        
        for character_set in all_character_sets:
            _, characters = load_character_set(character_set)
            all_characters.extend(characters)
        
        # Add debug logging
        print(f"Found {len(all_characters)} total characters")
        print(f"Existing names: {existing_names}")
        
        # Filter out characters that already exist in the session
        available_characters = [char for char in all_characters if char['name'] not in existing_names]
        print(f"Found {len(available_characters)} available characters")
        
        if not available_characters:
            print("No unique characters available.")
            return None
        
        character = random.choice(available_characters)
        print(f"Selected character: {character['name']}")
        
        # Generate a unique 5-digit passcode
        existing_passcodes = set(Student.objects.filter(section=session).values_list('password', flat=True))
        while True:
            passcode = generate_passcode()
            if passcode not in existing_passcodes:
                break
        
        avatar_image_path = f'video_app/images/characters/{character["character_set"]}/{character["filename"]}'
        
        student = Student.objects.create(
            name=character['name'],
            password=passcode,
            section=session,
            admin=admin,
            character_description=character['description'],
            avatar_image_path=avatar_image_path
        )
        
        print(f"Successfully created student: {student.name}")
        return student
    except Exception as e:
        print(f"Error generating user: {str(e)}")
        return None

