from django.shortcuts import render, redirect
from django.contrib import messages
from functools import wraps
from .models import Session, Observer, CustomAdmin, Media

def observer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        observer_id = request.session.get('observer_id')
        if not observer_id:
            messages.error(request, "Please log in as an observer")
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@observer_required
def observer_dashboard(request):
    try:
        observer = Observer.objects.get(id=request.session['observer_id'])
        
        # Get all teachers in the observer's district
        teachers = CustomAdmin.objects.filter(
            district=observer.district
        ).prefetch_related('session_set')
        
        # Get recent media submissions from this district
        media_items = Media.objects.filter(
            session__created_by__district=observer.district
        ).select_related(
            'session', 
            'session__created_by'
        ).order_by('-uploaded_at')[:50]
        
        context = {
            'district': observer.district,
            'teachers': teachers,
            'media_items': media_items
        }
        
        # Refresh the session
        request.session.modified = True
        
        return render(request, 'video_app/observer_dashboard.html', context)
    except Observer.DoesNotExist:
        # Clear the invalid session
        request.session.flush()
        messages.error(request, "Observer not found")
        return redirect('admin_login')

def observer_logout(request):
    if 'observer_id' in request.session:
        request.session.flush()  # This clears all session data
    messages.success(request, "Successfully logged out")
    return redirect('admin_login')