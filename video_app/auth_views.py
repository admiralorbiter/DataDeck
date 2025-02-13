from django.contrib.auth import views, authenticate
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from .models import Session, Student, Observer, CustomAdmin
from django.contrib.auth.hashers import check_password
from django import forms

def student_login(request):
    User = get_user_model()
    if request.user.is_staff:
        if request.user.is_superuser:
            sessions = Session.objects.all()
        else:
            sessions = Session.objects.filter(created_by=request.user)
    else:
        sessions = []
    
    if request.method == 'POST':
        student_password = request.POST.get('student_password')
        session_code = request.POST.get('session_code')
        
        if session_code:
            try:
                session_instance = Session.objects.get(session_code=session_code)
                request.session['current_session_id'] = session_instance.id
                request.session['current_session_name'] = session_instance.name
                return redirect('session', session_pk=session_instance.pk)
            except Session.DoesNotExist:
                return render(request, 'video_app/student_login.html', {'error': 'Invalid session code', 'sessions': sessions})
        
        elif student_password:
            try:
                student = Student.objects.get(password=student_password)
                session_instance = student.section
                
                # Create a user account for the student if it doesn't exist
                username = f"student_{student.id}"
                user, created = User.objects.get_or_create(username=username)
                if created:
                    user.set_password(student_password)
                    user.is_staff = False
                    user.is_superuser = False
                    user.save()
                
                # Log in the student
                login(request, user)
                
                request.session['current_session_id'] = session_instance.id
                request.session['current_session_name'] = session_instance.name
                request.session['student_id'] = student.id
                return redirect('session', session_pk=session_instance.pk)
            except Student.DoesNotExist:
                return render(request, 'video_app/student_login.html', {'error': 'Invalid student password', 'sessions': sessions})
    
    context = {
        'sessions': sessions,
    }
    return render(request, 'video_app/student_login.html', context)

def student_logout(request):
    logout(request)
    return redirect('home')  # or any other appropriate page after logout

class CustomLoginForm(forms.Form):
    username = forms.CharField(label='Email/Username')
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def get_user(self):
        return self.user_cache

class AdminLoginView(views.LoginView):
    template_name = 'video_app/login.html'
    redirect_authenticated_user = True
    form_class = CustomLoginForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        # Try to authenticate as observer FIRST
        try:
            observer = Observer.objects.get(email=username)
            # The password in DB is already hashed with pbkdf2_sha256
            if check_password(password, observer.password):
                if not observer.is_active:
                    messages.error(self.request, "This observer account is inactive")
                    return self.form_invalid(form)
                
                # Store observer info in session
                self.request.session['observer_id'] = observer.id
                self.request.session['observer_name'] = observer.name
                self.request.session['observer_district'] = observer.district.id
                self.request.session.save()
                
                messages.success(self.request, f"Welcome, {observer.name}!")
                return redirect('observer_dashboard')
            else:
                messages.error(self.request, "Invalid password for observer account")
                return self.form_invalid(form)
                
        except Observer.DoesNotExist:
            # If not an observer, try admin authentication
            user = authenticate(username=username, password=password)
            if user and isinstance(user, CustomAdmin):
                login(self.request, user)
                messages.success(self.request, f"Welcome, {user.get_full_name()}!")
                return redirect('home')
            else:
                messages.error(self.request, "Invalid login credentials")
                return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid login credentials")
        return super().form_invalid(form)

    def get_success_url(self):
        if 'observer_id' in self.request.session:
            return reverse_lazy('observer_dashboard')
        return reverse_lazy('home')
    
@login_required
def update_teacher_info(request):
    if request.method == 'POST':
        teacher = request.user
        teacher.district = request.POST.get('district')
        teacher.school = request.POST.get('school')
        teacher.first_name = request.POST.get('first_name')
        teacher.last_name = request.POST.get('last_name')
        
        # Handle password update
        new_password = request.POST.get('new_password')
        if new_password:
            teacher.set_password(new_password)
        
        teacher.save()
        messages.success(request, 'Teacher information updated successfully.')
        
        # If password was changed, update the session to prevent logout
        if new_password:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, teacher)
    
    return redirect('teacher_view')
