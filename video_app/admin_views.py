from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from video_app.models import Observer, CustomAdmin, District
from django.contrib.auth.hashers import make_password

@login_required
def admin_dashboard(request):
    if not isinstance(request.user, CustomAdmin):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')

    context = {
        'observers': Observer.objects.all(),
        'districts': District.objects.all(),
        'teachers': CustomAdmin.objects.all(),
    }
    return render(request, 'video_app/admin_dashboard.html', context)

@login_required
def create_district(request):
    if request.method == 'POST':
        name = request.POST.get('district_name')
        if name:
            try:
                code = name.upper().replace(' ', '_')[:20]
                District.objects.create(
                    name=name,
                    code=code,
                    is_active=True
                )
                messages.success(request, f"District '{name}' created successfully!")
            except Exception as e:
                messages.error(request, f"Error creating district: {str(e)}")
    return redirect('admin_dashboard')

@login_required
def edit_district(request, district_id):
    district = get_object_or_404(District, id=district_id)
    if request.method == 'POST':
        name = request.POST.get('district_name')
        if name:
            try:
                district.name = name
                district.code = name.upper().replace(' ', '_')[:20]
                district.save()
                messages.success(request, f"District updated successfully!")
            except Exception as e:
                messages.error(request, f"Error updating district: {str(e)}")
    return redirect('admin_dashboard')

@login_required
def delete_district(request, district_id):
    district = get_object_or_404(District, id=district_id)
    if request.method == 'POST':
        try:
            # Check if district has any associated teachers or observers
            if district.customadmin_set.exists() or district.observer_set.exists():
                messages.error(request, "Cannot delete district with associated teachers or observers")
            else:
                district.delete()
                messages.success(request, "District deleted successfully!")
        except Exception as e:
            messages.error(request, f"Error deleting district: {str(e)}")
    return redirect('admin_dashboard')

@login_required
def toggle_district(request, district_id):
    district = get_object_or_404(District, id=district_id)
    if request.method == 'POST':
        try:
            district.is_active = not district.is_active
            district.save()
            status = "activated" if district.is_active else "deactivated"
            messages.success(request, f"District {status} successfully!")
        except Exception as e:
            messages.error(request, f"Error toggling district: {str(e)}")
    return redirect('admin_dashboard')

@login_required
def create_observer(request):
    if request.method == 'POST':
        try:
            district = District.objects.get(id=request.POST.get('district'))
            observer = Observer.objects.create(
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                district=district,
                password=make_password(request.POST.get('password')),
                created_by=request.user
            )
            messages.success(request, f"Observer {observer.name} created successfully!")
        except Exception as e:
            messages.error(request, f"Error creating observer: {str(e)}")
    
    return redirect('admin_dashboard')

@login_required
def update_teacher_district(request, teacher_id):
    if not isinstance(request.user, CustomAdmin):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')

    if request.method == 'POST':
        try:
            teacher = CustomAdmin.objects.get(id=teacher_id)
            district = District.objects.get(id=request.POST.get('district'))
            teacher.district = district
            teacher.save()
            messages.success(request, f"Updated district for {teacher.get_full_name()}")
        except CustomAdmin.DoesNotExist:
            messages.error(request, "Teacher not found.")
        except District.DoesNotExist:
            messages.error(request, "District not found.")
        except Exception as e:
            messages.error(request, f"Error updating teacher district: {str(e)}")
    
    return redirect('admin_dashboard')

@login_required
def deactivate_observer(request, observer_id):
    if not isinstance(request.user, CustomAdmin):
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')

    try:
        observer = Observer.objects.get(id=observer_id, created_by=request.user)
        observer.is_active = not observer.is_active
        observer.save()
        status = "activated" if observer.is_active else "deactivated"
        messages.success(request, f"Observer {observer.name} has been {status}.")
    except Observer.DoesNotExist:
        messages.error(request, "Observer not found.")
    
    return redirect('admin_dashboard')
