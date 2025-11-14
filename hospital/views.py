from django.shortcuts import render,redirect,reverse, get_object_or_404
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required,user_passes_test
from datetime import datetime,timedelta,date
from django.conf import settings
from django.db.models import Q,Count
from django.http import JsonResponse
from .utils import generate_otp, send_otp_email
from django.contrib.auth import authenticate,login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from .models import Appointment, Feedback
from hospital.models import Doctor
import json

# views.py

def home_view(request):
    return render(request, 'hospital/index.html')

# Showing signup/login button for admin
def adminclick_view(request):
    return render(request, 'hospital/adminclick.html')

# Showing signup/login button for doctor
def doctorclick_view(request):
    return render(request, 'hospital/doctorclick.html')

# Showing signup/login button for patient
def patientclick_view(request):
    return render(request, 'hospital/patientclick.html')


# Admin Signup with OTP
ADMIN_ALLOWED_EMAIL = 'diwanp151@gmail.com'  # Change this to your admin email

def admin_signup_view(request):
    if request.method == 'POST':
        # Check if it's OTP send request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            email = request.POST.get('email', '').strip().lower()
            
            # Check if email is allowed
            if email != ADMIN_ALLOWED_EMAIL.lower():
                return JsonResponse({'msg': 'unauthorized'}, status=403)
            
            otp = generate_otp()
            request.session['admin_otp'] = str(otp)
            request.session['admin_email'] = email
            
            result = send_otp_email(email, otp)
            if result:
                return JsonResponse({'msg': 'sent'})
            else:
                return JsonResponse({'msg': 'email_error'}, status=500)
        
        # Handle form submission
        form = forms.AdminSigupForm(request.POST)
        otp_input = request.POST.get('otp', '').strip()
        otp_session = request.session.get('admin_otp', '').strip()
        email_session = request.session.get('admin_email', '').strip().lower()
        
        if form.is_valid():
            user_email = form.cleaned_data['email'].strip().lower()
            
            # Verify email and OTP
            if user_email == email_session == ADMIN_ALLOWED_EMAIL.lower() and otp_input == otp_session:
                user = form.save()
                user.set_password(user.password)
                user.save()
                
                my_admin_group, _ = Group.objects.get_or_create(name='ADMIN')
                my_admin_group.user_set.add(user)
                
                # Clear session
                del request.session['admin_otp']
                del request.session['admin_email']
                
                # Auto-login
                login(request, user)
                messages.success(request, '✅ Admin account created successfully!')
                return redirect('admin-dashboard')
            else:
                messages.error(request, '❌ Invalid OTP or unauthorized email!')
        else:
            messages.error(request, '❌ Please fix the form errors.')
    else:
        form = forms.AdminSigupForm()
    
    return render(request, 'hospital/adminsignup.html', {'form': form, 'admin_email': ADMIN_ALLOWED_EMAIL})
def doctor_signup_view(request):
    if request.method == 'POST':
        userForm = forms.DoctorUserForm(request.POST)
        doctorForm = forms.DoctorForm(request.POST, request.FILES)
        
        if userForm.is_valid() and doctorForm.is_valid():
            user = userForm.save()  # Handles password hashing + validation
            
            doctor = doctorForm.save(commit=False)
            doctor.user = user
            doctor.save()

            # Assign to DOCTOR group
            group, created = Group.objects.get_or_create(name='DOCTOR')
            group.user_set.add(user)

            # Auto-login after signup
            raw_password = userForm.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            if user:
                login(request, user)
                return redirect('doctor-dashboard')

            return redirect('doctorlogin')

        # invalid form
        return render(request, 'hospital/doctorsignup.html', {
            'userForm': userForm,
            'doctorForm': doctorForm,
        })

    # GET request
    return render(request, 'hospital/doctorsignup.html', {
        'userForm': forms.DoctorUserForm(),
        'doctorForm': forms.DoctorForm(),
    })

def doctor_login_view(request):
    form = AuthenticationForm()
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # ✅ Check if user is actually a doctor
                if is_doctor(user):
                    login(request, user)
                    return redirect('doctor-dashboard')
                else:
                    messages.error(request, 'You are not registered as a doctor!')
            else:
                messages.error(request, 'Invalid username or password')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'hospital/doctorlogin.html', {'form': form})
def patient_signup_view(request):
    userForm = forms.PatientUserForm()
    patientForm = forms.PatientForm()
    
    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            email = request.POST.get('email')
            otp = generate_otp()
            request.session['email_otp'] = str(otp)
            request.session['email_for_otp'] = email.strip().lower()
            print(f"✓ OTP SENT: {otp} to {email}")
            result = send_otp_email(email, otp)
            if result:
                return JsonResponse({'msg': 'sent'})
            else:
                return JsonResponse({'msg': 'email_error'}, status=500)
        
        userForm = forms.PatientUserForm(request.POST)
        patientForm = forms.PatientForm(request.POST, request.FILES)
        
        otp_input = request.POST.get('otp', '').strip()
        email_for_otp = request.session.get('email_for_otp', '').strip().lower()
        otp_session = request.session.get('email_otp', '').strip()
        
        error_messages = []
        
        if userForm.is_valid() and patientForm.is_valid():
            user_email = userForm.cleaned_data['email'].strip().lower()
            
            if otp_input and otp_session and otp_input == otp_session and user_email == email_for_otp:
                user = userForm.save(commit=False)
                user.is_active = True
                user.set_password(user.password)
                user.save()
                
                patient = patientForm.save(commit=False)
                patient.user = user
                patient.status = True  # <-- Auto-approve patient!
                patient.save()
                
                my_patient_group = Group.objects.get_or_create(name='PATIENT')
                my_patient_group[0].user_set.add(user)
                
                del request.session['email_otp']
                del request.session['email_for_otp']
                
                login(request, user)
                
                print("✓ REGISTRATION SUCCESSFUL! User logged in and auto-approved.")
                return redirect('patient-dashboard')
            else:
                error_messages.append("Incorrect OTP or email mismatch.")
        else:
            if not userForm.is_valid():
                for field, errors in userForm.errors.items():
                    for error in errors:
                        error_messages.append(f"{field.title()}: {error}")
            if not patientForm.is_valid():
                for field, errors in patientForm.errors.items():
                    for error in errors:
                        error_messages.append(f"{field.title()}: {error}")
        
        mydict = {'userForm': userForm, 'patientForm': patientForm, 'error_messages': error_messages}
        return render(request, 'hospital/patientsignup.html', context=mydict)
    
    mydict = {'userForm': userForm, 'patientForm': patientForm}
    return render(request, 'hospital/patientsignup.html', context=mydict)

def patient_login_view(request):
    form = AuthenticationForm()
    error_messages = None

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect based on role or simply to the patient dashboard
            return redirect('afterlogin')  # Or use 'patient-dashboard' if you want to skip role check
        else:
            # Collect Django's standard error messages for failed login
            error_messages = form.non_field_errors()

    return render(request, 'hospital/patientlogin.html', {
        'form': form,
        'error_messages': error_messages
    })

#-----------for checking user is doctor , patient or admin(by diwan)
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()
def is_doctor(user):
    return user.groups.filter(name='DOCTOR').exists()
def is_patient(user):
    return user.groups.filter(name='PATIENT').exists()


#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,DOCTOR OR PATIENT
@login_required(login_url='login')
def afterlogin_view(request):
    user = request.user

    # Check group membership
    if user.groups.filter(name='ADMIN').exists():
        return redirect('admin-dashboard')

    elif user.groups.filter(name='DOCTOR').exists():
        # Ensure doctor exists
        from .models import Doctor
        try:
            doctor = Doctor.objects.get(user=user)
            if doctor.status:  # approved
                return redirect('doctor-dashboard')
            else:
                return redirect('doctor-dashboard')
        except Doctor.DoesNotExist:
            return redirect('doctorlogin')

    elif user.groups.filter(name='PATIENT').exists():
        from .models import Patient
        try:
            patient = Patient.objects.get(user=user)
            if patient.status:  # approved
                return redirect('patient-dashboard')
            else:
                return redirect('patient-pending')  # optional page
        except Patient.DoesNotExist:
            return redirect('patientlogin')

    # Fallback if user has no group
    return redirect('home')






#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    # Get all data
    doctors = models.Doctor.objects.select_related('user').all().order_by('-id')
    patients = models.Patient.objects.select_related('user').all().order_by('-id')
    appointments = models.Appointment.objects.select_related('doctor__user', 'patient__user').all().order_by('-id')[:20]
    
    # Stats
    stats = {
        'total_doctors': doctors.count(),
        'approved_doctors': doctors.filter(status=True).count(),
        'pending_doctors': doctors.filter(status=False).count(),
        'total_patients': patients.count(),
        'approved_patients': patients.filter(status=True).count(),
        'pending_patients': patients.filter(status=False).count(),
        'total_appointments': appointments.count(),
        'pending_appointments': models.Appointment.objects.filter(status='pending').count(),
        'confirmed_appointments': models.Appointment.objects.filter(status='confirmed').count(),
        'completed_appointments': models.Appointment.objects.filter(status='completed').count(),
    }
    
    context = {
        'doctors': doctors[:10],  # Recent 10
        'patients': patients[:10],  # Recent 10
        'appointments': appointments,
        'stats': stats,
    }
    return render(request, 'hospital/admin_dashboard.html', context)



# this view for sidebar click on admin page
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_view(request):
    return render(request,'hospital/admin_doctor.html')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_appointments(request, doctor_id):
    doctor = get_object_or_404(models.Doctor, id=doctor_id)
    appointments = models.Appointment.objects.filter(doctor=doctor).select_related('patient__user').order_by('-id')
    
    context = {
        'doctor': doctor,
        'appointments': appointments,
    }
    return render(request, 'hospital/admin_doctor_appointments.html', context)
#########new################

# Doctor Detail API
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_detail_api(request, doctor_id):
    """Get single doctor details"""
    try:
        doctor = models.Doctor.objects.select_related('user').get(id=doctor_id)
        data = {
            'id': doctor.id,
            'name': f"{doctor.user.first_name} {doctor.user.last_name}",
            'department': doctor.department,
            'mobile': doctor.mobile or '',
            'qualification': doctor.qualification or 'MBBS',
            'experience': doctor.experience_years if hasattr(doctor, 'experience_years') else (doctor.experience if hasattr(doctor, 'experience') else '0 years'),
            'duty_timings': doctor.duty_time if hasattr(doctor, 'duty_time') else (doctor.duty_timings if hasattr(doctor, 'duty_timings') else '9:00 AM - 5:00 PM'),
            'consultation_fee': doctor.consultation_fee if hasattr(doctor, 'consultation_fee') else 500,
        }
        return JsonResponse({'success': True, **data})
    except models.Doctor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Doctor not found'}, status=404)


# Update Doctor API
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@require_POST
def admin_update_doctor_api(request, doctor_id):
    """Update doctor profile"""
    try:
        doctor = models.Doctor.objects.get(id=doctor_id)
        
        # Parse JSON body
        data = json.loads(request.body)
        
        # Update fields
        if 'qualification' in data:
            doctor.qualification = data['qualification']
        if 'experience' in data:
            if hasattr(doctor, 'experience_years'):
                doctor.experience_years = data['experience']
            elif hasattr(doctor, 'experience'):
                doctor.experience = data['experience']
        if 'duty_time' in data or 'duty_timings' in data:
            duty = data.get('duty_time') or data.get('duty_timings')
            if hasattr(doctor, 'duty_time'):
                doctor.duty_time = duty
            elif hasattr(doctor, 'duty_timings'):
                doctor.duty_timings = duty
        
        doctor.save()
        return JsonResponse({'success': True, 'message': 'Doctor updated successfully'})
    except models.Doctor.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Doctor not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# Delete Doctor API
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@require_POST
def admin_delete_doctor_api(request, doctor_id):
    """Delete doctor"""
    try:
        doctor = models.Doctor.objects.get(id=doctor_id)
        user = doctor.user
        
        # Delete doctor and associated user
        doctor.delete()
        user.delete()
        
        return JsonResponse({'success': True, 'message': 'Doctor deleted successfully'})
    except models.Doctor.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Doctor not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# Doctor Appointments API
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_doctor_appointments_api(request, doctor_id):
    """Get all appointments for a doctor"""
    try:
        doctor = models.Doctor.objects.get(id=doctor_id)
        appointments = models.Appointment.objects.filter(
            doctor=doctor
        ).select_related('patient__user').order_by('-date')
        
        appointments_list = [{
            'id': a.id,
            'patient_name': f"{a.patient.user.first_name} {a.patient.user.last_name}",
            'date': str(a.date.date()) if a.date else 'N/A',
            'time': str(a.date.time().strftime('%I:%M %p')) if a.date else 'N/A',
            'status': a.status,
            'reason': a.description or '',
            'description': a.description or '',
        } for a in appointments]
        
        return JsonResponse({'success': True, 'appointments': appointments_list})
    except models.Doctor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Doctor not found'}, status=404)


# Patient Detail API
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_detail_api(request, patient_id):
    """Get patient details and appointments"""
    try:
        patient = models.Patient.objects.select_related('user').get(id=patient_id)
        
        # Patient data
        patient_data = {
            'id': patient.id,
            'name': f"{patient.user.first_name} {patient.user.last_name}",
            'age': patient.age if hasattr(patient, 'age') else 0,
            'gender': patient.gender if hasattr(patient, 'gender') else 'N/A',
            'blood_group': patient.blood_group if hasattr(patient, 'blood_group') else '',
            'phone': patient.mobile if hasattr(patient, 'mobile') else '',
            'email': patient.user.email,
            'mobile': patient.mobile if hasattr(patient, 'mobile') else '',
            'address': patient.address if hasattr(patient, 'address') else '',
            'joined': str(patient.user.date_joined.date()) if patient.user.date_joined else 'N/A',
        }
        
        # Patient's appointments
        appointments = models.Appointment.objects.filter(
            patient=patient
        ).select_related('doctor__user').order_by('-date')
        
        appointments_list = [{
            'id': a.id,
            'doctor_name': f"Dr. {a.doctor.user.first_name} {a.doctor.user.last_name}",
            'date': str(a.date.date()) if a.date else 'N/A',
            'time': str(a.date.time().strftime('%I:%M %p')) if a.date else 'N/A',
            'status': a.status,
            'reason': a.description or '',
            'description': a.description or '',
        } for a in appointments]
        
        return JsonResponse({
            'success': True,
            'patient': patient_data,
            'appointments': appointments_list
        })
    except models.Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'}, status=404)


# Delete Patient API
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@require_POST
def admin_delete_patient_api(request, patient_id):
    """Delete patient"""
    try:
        patient = models.Patient.objects.get(id=patient_id)
        user = patient.user
        
        # Delete patient and associated user
        patient.delete()
        user.delete()
        
        return JsonResponse({'success': True, 'message': 'Patient deleted successfully'})
    except models.Patient.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Patient not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# Cancel Appointment API
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
@require_POST
def admin_cancel_appointment_api(request, appointment_id):
    """Cancel an appointment"""
    try:
        appointment = models.Appointment.objects.get(id=appointment_id)
        appointment.status = 'cancelled'
        appointment.save()
        
        return JsonResponse({'success': True, 'message': 'Appointment cancelled successfully'})
    except models.Appointment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Appointment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor.html',{'doctors':doctors})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(models.Appointment, id=appointment_id)
    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, f'✅ Appointment cancelled successfully!')
    return redirect(request.META.get('HTTP_REFERER', 'admin-dashboard'))




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_doctor_from_hospital_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)
    user.delete()
    doctor.delete()
    return redirect('admin-view-doctor')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_doctor_view(request,pk):
    doctor=models.Doctor.objects.get(id=pk)
    user=models.User.objects.get(id=doctor.user_id)

    userForm=forms.DoctorUserForm(instance=user)
    doctorForm=forms.DoctorForm(request.FILES,instance=doctor)
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST,instance=user)
        doctorForm=forms.DoctorForm(request.POST,request.FILES,instance=doctor)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            doctor=doctorForm.save(commit=False)
            doctor.status=True
            doctor.save()
            return redirect('admin-view-doctor')
    return render(request,'hospital/admin_update_doctor.html',context=mydict)




@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_doctor_view(request):
    userForm=forms.DoctorUserForm()
    doctorForm=forms.DoctorForm()
    mydict={'userForm':userForm,'doctorForm':doctorForm}
    if request.method=='POST':
        userForm=forms.DoctorUserForm(request.POST)
        doctorForm=forms.DoctorForm(request.POST, request.FILES)
        if userForm.is_valid() and doctorForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            doctor=doctorForm.save(commit=False)
            doctor.user=user
            doctor.status=True
            doctor.save()

            my_doctor_group = Group.objects.get_or_create(name='DOCTOR')
            my_doctor_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-doctor')
    return render(request,'hospital/admin_add_doctor.html',context=mydict)

# Patient Management Views
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_appointments(request, patient_id):
    patient = get_object_or_404(models.Patient, id=patient_id)
    appointments = models.Appointment.objects.filter(patient=patient).select_related('doctor__user').order_by('-id')
    
    context = {
        'patient': patient,
        'appointments': appointments,
    }
    return render(request, 'hospital/admin_patient_appointments.html', context)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_specialisation_view(request):
    doctors=models.Doctor.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_doctor_specialisation.html',{'doctors':doctors})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_doctor_json(request):
    """JSON API for doctor data"""
    try:
        # Get all doctors with selected fields
        doctors = Doctor.objects.all().values(
            'id', 
            'user__first_name',
            'user__last_name', 
            'department', 
            'mobile', 
            'status'
        )
        doctors_list = list(doctors)
        return JsonResponse(doctors_list, safe=False)
    except Exception as e:
        # Return error if something goes wrong
        return JsonResponse({'error': str(e)}, status=500)
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_patient_view(request):
    return render(request,'hospital/admin_patient.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_patient_from_hospital_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-view-patient')

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def get_patient_info_api(request, patient_id):
    try:
        patient = models.Patient.objects.get(id=patient_id)
        patient_data = {
            'id': patient.id,
            'name': patient.get_name,
            'mobile': patient.mobile,
            'address': patient.address,
            'symptoms': patient.symptoms,
            # Add other fields as needed
        }
        return JsonResponse({'success': True, 'patient': patient_data})
    except models.Patient.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient not found'})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)

    userForm=forms.PatientUserForm(instance=user)
    patientForm=forms.PatientForm(request.FILES,instance=patient)
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST,instance=user)
        patientForm=forms.PatientForm(request.POST,request.FILES,instance=patient)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            patient=patientForm.save(commit=False)
            patient.status=True
            patient.assigned_doctorId=request.POST.get('assigned_doctorId')
            patient.save()
            return redirect('admin-view-patient')
    return render(request,'hospital/admin_update_patient.html',context=mydict)





@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_patient_view(request):
    userForm=forms.PatientUserForm()
    patientForm=forms.PatientForm()
    mydict={'userForm':userForm,'patientForm':patientForm}
    if request.method=='POST':
        userForm=forms.PatientUserForm(request.POST)
        patientForm=forms.PatientForm(request.POST,request.FILES)
        if userForm.is_valid() and patientForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()

            patient=patientForm.save(commit=False)
            patient.user=user
            patient.status=True
            patient.assigned_doctorId=request.POST.get('assigned_doctorId')
            patient.save()

            my_patient_group = Group.objects.get_or_create(name='PATIENT')
            my_patient_group[0].user_set.add(user)

        return HttpResponseRedirect('admin-view-patient')
    return render(request,'hospital/admin_add_patient.html',context=mydict)



#------------------FOR APPROVING PATIENT BY ADMIN----------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_patient_view(request):
    #those whose approval are needed
    patients=models.Patient.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    patient.status=True
    patient.save()
    return redirect(reverse('admin-approve-patient'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    user=models.User.objects.get(id=patient.user_id)
    user.delete()
    patient.delete()
    return redirect('admin-approve-patient')



#--------------------- FOR DISCHARGING PATIENT BY ADMIN START-------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_discharge_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True)
    return render(request,'hospital/admin_discharge_patient.html',{'patients':patients})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def discharge_patient_view(request,pk):
    patient=models.Patient.objects.get(id=pk)
    days=(date.today()-patient.admitDate) #2 days, 0:00:00
    assigned_doctor=models.User.objects.all().filter(id=patient.assigned_doctorId)
    d=days.days # only how many day that is 2
    patientDict={
        'patientId':pk,
        'name':patient.get_name,
        'mobile':patient.mobile,
        'address':patient.address,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'todayDate':date.today(),
        'day':d,
        'assigned_doctorName':assigned_doctor[0].first_name,
    }
    if request.method == 'POST':
        feeDict ={
            'roomCharge':int(request.POST['roomCharge'])*int(d),
            'doctorFee':request.POST['doctorFee'],
            'medicineCost' : request.POST['medicineCost'],
            'OtherCharge' : request.POST['OtherCharge'],
            'total':(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        }
        patientDict.update(feeDict)
        #for updating to database patientDischargeDetails (pDD)
        pDD=models.PatientDischargeDetails()
        pDD.patientId=pk
        pDD.patientName=patient.get_name
        pDD.assigned_doctorName=assigned_doctor[0].first_name
        pDD.address=patient.address
        pDD.mobile=patient.mobile
        pDD.symptoms=patient.symptoms
        pDD.admitDate=patient.admitDate
        pDD.releaseDate=date.today()
        pDD.daySpent=int(d)
        pDD.medicineCost=int(request.POST['medicineCost'])
        pDD.roomCharge=int(request.POST['roomCharge'])*int(d)
        pDD.doctorFee=int(request.POST['doctorFee'])
        pDD.OtherCharge=int(request.POST['OtherCharge'])
        pDD.total=(int(request.POST['roomCharge'])*int(d))+int(request.POST['doctorFee'])+int(request.POST['medicineCost'])+int(request.POST['OtherCharge'])
        pDD.save()
        return render(request,'hospital/patient_final_bill.html',context=patientDict)
    return render(request,'hospital/patient_generate_bill.html',context=patientDict)

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def get_stats_data(request):
    """Get dashboard statistics"""
    doctors = models.Doctor.objects.all()
    patients = models.Patient.objects.all()
    appointments = models.Appointment.objects.all()
    
    stats = {
        'total_doctors': doctors.count(),
        'approved_doctors': doctors.filter(status=True).count(),
        'pending_doctors': doctors.filter(status=False).count(),
        'total_patients': patients.count(),
        'approved_patients': patients.filter(status=True).count(),
        'pending_patients': patients.filter(status=False).count(),
        'total_appointments': appointments.count(),
        'pending_appointments': appointments.filter(status='pending').count(),
        'confirmed_appointments': appointments.filter(status='confirmed').count(),
        'completed_appointments': appointments.filter(status='completed').count(),
    }
    
    return JsonResponse(stats)
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def get_doctors_data(request):
    """Get all doctors data"""
    doctors = models.Doctor.objects.select_related('user').all().order_by('-id')
    
    doctors_list = []
    for doctor in doctors:
        # Count appointments for this doctor
        appointment_count = models.Appointment.objects.filter(doctor=doctor).count()
        
        doctors_list.append({
            'id': doctor.id,
            'name': f"{doctor.user.first_name} {doctor.user.last_name}",
            'department': doctor.department,
            'status': doctor.status,
            'qualification': doctor.qualification,
            'experience': f"{doctor.experience_years} years",
            'duty_time': doctor.duty_time or 'Not Set',
            'appointment_count': appointment_count,
        })
    
    return JsonResponse({'doctors': doctors_list})
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def get_patients_data(request):
    """Get all patients data"""
    patients = models.Patient.objects.select_related('user').all().order_by('-id')
    
    patients_list = []
    for patient in patients:
        # Count appointments for this patient
        appointment_count = models.Appointment.objects.filter(patient=patient).count()
        
        patients_list.append({
            'id': patient.id,
            'name': f"{patient.user.first_name} {patient.user.last_name}",
            'age': patient.age if hasattr(patient, 'age') else 0,
            'gender': patient.gender if hasattr(patient, 'gender') else 'N/A',
            'blood_group': patient.blood_group if hasattr(patient, 'blood_group') else '',
            'phone': patient.mobile if hasattr(patient, 'mobile') else '',
            'email': patient.user.email,
            'appointment_count': appointment_count,
        })
    
    return JsonResponse({'patients': patients_list})

@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def get_appointments_data(request):
    """Get all appointments data"""
    appointments = models.Appointment.objects.select_related(
        'doctor__user', 'patient__user'
    ).all().order_by('-id')
    
    appointments_list = []
    for apt in appointments:
        appointments_list.append({
            'id': apt.id,
            'doctor_name': f"Dr. {apt.doctor.user.first_name} {apt.doctor.user.last_name}",
            'patient_name': f"{apt.patient.user.first_name} {apt.patient.user.last_name}",
            'date': str(apt.appointmentDate),
            'time': str(apt.appointmentTime) if hasattr(apt, 'appointmentTime') else 'N/A',
            'status': apt.status if hasattr(apt, 'status') else 'pending',
            'reason': apt.description if hasattr(apt, 'description') else '',
            'description': apt.description if hasattr(apt, 'description') else '',
        })
    
    return JsonResponse({'appointments': appointments_list})

#--------------for discharge patient bill (pdf) download and printing
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse


def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return



def download_pdf_view(request,pk):
    dischargeDetails=models.PatientDischargeDetails.objects.all().filter(patientId=pk).order_by('-id')[:1]
    dict={
        'patientName':dischargeDetails[0].patientName,
        'assigned_doctorName':dischargeDetails[0].assigned_doctorName,
        'address':dischargeDetails[0].address,
        'mobile':dischargeDetails[0].mobile,
        'symptoms':dischargeDetails[0].symptoms,
        'admitDate':dischargeDetails[0].admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
    }
    return render_to_pdf('hospital/download_bill.html',dict)



#-----------------APPOINTMENT START--------------------------------------------------------------------
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_appointment_view(request):
    return render(request,'hospital/admin_appointment.html')



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_appointment_view(request):
    appointments=models.Appointment.objects.all().filter(status=True)
    return render(request,'hospital/admin_view_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_appointment_view(request):
    appointmentForm=forms.AppointmentForm()
    mydict={'appointmentForm':appointmentForm,}
    if request.method=='POST':
        appointmentForm=forms.AppointmentForm(request.POST)
        if appointmentForm.is_valid():
            appointment=appointmentForm.save(commit=False)
            appointment.doctorId=request.POST.get('doctorId')
            appointment.patientId=request.POST.get('patientId')
            appointment.doctorName=models.User.objects.get(id=request.POST.get('doctorId')).first_name
            appointment.patientName=models.User.objects.get(id=request.POST.get('patientId')).first_name
            appointment.status=True
            appointment.save()
        return HttpResponseRedirect('admin-view-appointment')
    return render(request,'hospital/admin_add_appointment.html',context=mydict)



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_appointment_view(request):
    #those whose approval are needed
    appointments=models.Appointment.objects.all().filter(status=False)
    return render(request,'hospital/admin_approve_appointment.html',{'appointments':appointments})



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.status=True
    appointment.save()
    return redirect(reverse('admin-approve-appointment'))



@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def reject_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    return redirect('admin-approve-appointment')
#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_dashboard_view(request):
    doctor = models.Doctor.objects.get(user=request.user)

    # Appointments QuerySet (define FIRST!)
    appointments = models.Appointment.objects.filter(doctor=doctor).order_by('-id')

    # Now filter the status
    pending_appointments = appointments.filter(status='pending')
    completed_appointments = appointments.filter(status='completed')
    cancelled_appointments = appointments.filter(status='cancelled')

    # Stats for dashboard cards
    patientcount = models.Patient.objects.filter(status=True, assigned_doctor=doctor).count()
    appointmentcount = appointments.count()
    patientdischarged = models.PatientDischargeDetails.objects.filter(patient__assigned_doctor=doctor).count()

    # Other dashboard info
    recent_reports = models.MedicalReport.objects.filter(doctor=doctor).order_by('-uploaded_date')[:8]
    patients = models.Patient.objects.filter(status=True, assigned_doctor=doctor)
    upload_form = forms.MedicalReportForm(doctor)
    mydict = {
        'patientcount': patientcount,
        'appointmentcount': appointmentcount,
        'patientdischarged': patientdischarged,
        'appointments': appointments,
        'doctor': doctor,
        'recent_reports': recent_reports,
        'patients': patients,
        'pending_appointments': pending_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'upload_form': upload_form,
    }
    return render(request, 'hospital/doctor_dashboard.html', context=mydict)


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_patient_view(request):
    mydict={
    'doctor':models.Doctor.objects.get(user_id=request.user.id), #for profile picture of doctor in sidebar
    }
    return render(request,'hospital/doctor_patient.html',context=mydict)





@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_patient_view(request):
    patients=models.Patient.objects.all().filter(status=True,assigned_doctor=request.user.id)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def search_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    # whatever user write in search box we get in query
    query = request.GET['query']
    patients=models.Patient.objects.all().filter(status=True,assigned_doctorId=request.user.id).filter(Q(symptoms__icontains=query)|Q(user__first_name__icontains=query))
    return render(request,'hospital/doctor_view_patient.html',{'patients':patients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_discharge_patient_view(request):
    dischargedpatients=models.PatientDischargeDetails.objects.all().distinct().filter(assigned_doctorName=request.user.first_name)
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_view_discharge_patient.html',{'dischargedpatients':dischargedpatients,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    return render(request,'hospital/doctor_appointment.html',{'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_view_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_view_appointment.html',{'appointments':appointments,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def doctor_delete_appointment_view(request):
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})



@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def delete_appointment_view(request,pk):
    appointment=models.Appointment.objects.get(id=pk)
    appointment.delete()
    doctor=models.Doctor.objects.get(user_id=request.user.id) #for profile picture of doctor in sidebar
    appointments=models.Appointment.objects.all().filter(status=True,doctorId=request.user.id)
    patientid=[]
    for a in appointments:
        patientid.append(a.patientId)
    patients=models.Patient.objects.all().filter(status=True,user_id__in=patientid)
    appointments=zip(appointments,patients)
    return render(request,'hospital/doctor_delete_appointment.html',{'appointments':appointments,'doctor':doctor})

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(models.Appointment, id=appointment_id, doctor__user=request.user)
    appointment.status = 'confirmed'
    appointment.save()
    messages.success(request, f'Appointment with {appointment.patient.get_name} confirmed!')
    return redirect('doctor-dashboard')

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def cancel_appointment_api(request, appointment_id):
    appointment = get_object_or_404(models.Appointment, id=appointment_id, doctor__user=request.user)
    appointment.status = 'cancelled'
    appointment.save()
    messages.warning(request, f'Appointment with {appointment.patient.get_name} cancelled.')
    return redirect('doctor-dashboard')

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def complete_appointment(request, appointment_id):
    appointment = get_object_or_404(models.Appointment, id=appointment_id, doctor__user=request.user)
    appointment.status = 'completed'
    appointment.save()
    messages.success(request, f'Appointment with {appointment.patient.get_name} marked as completed!')
    return redirect('doctor-dashboard')

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def upload_report(request):
    doctor = models.Doctor.objects.get(user=request.user)

    if request.method == 'POST':
        form = forms.MedicalReportForm(doctor, request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.doctor = doctor
            # patient comes from the form (already filtered to doctor's patients)
            report.save()
            messages.success(request, 'Medical report uploaded successfully!')
            return redirect('doctor-dashboard')
        messages.error(request, 'Error uploading report. Please check the form.')
    else:
        form = forms.MedicalReportForm(doctor)

    return render(request, 'hospital/upload_report.html', {'form': form, 'doctor': doctor})
#---------------------------------------------------------------------------------
#------------------------ DOCTOR RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------






#---------------------------------------------------------------------------------
#------------------------ PATIENT RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_dashboard_view(request):
    print("Messages:", list(messages.get_messages(request)))

    # Current patient (with related auth user for efficiency)
    patient = models.Patient.objects.select_related('user').get(user=request.user)

    # All specializations (departments) shown as chips/filters
    # If you don't want any gating, remove status filter entirely.
    specializations = (
        models.Doctor.objects
        .values_list('department', flat=True)
        .distinct()
        .order_by('department')
    )

    # 🔹 Show ALL doctors (no approval filter)
    doctors = (
        models.Doctor.objects
        .select_related('user')
        .order_by('department', 'user__first_name', 'user__last_name')
    )

    # Patient’s appointments (newest first)
    # If your model doesn’t have created_at, sort by date/time fields you have.
    appointments = (
    models.Appointment.objects
    .filter(patient=patient)
    .select_related('doctor__user')
    .order_by('-date', '-created_at')  # <-- use existing fields
)

    # Patient’s medical reports
    medical_reports = (
        models.MedicalReport.objects
        .filter(patient=patient)
        .select_related('doctor__user')
        .order_by('-uploaded_date')
    )

    # Stats (provide both key styles to match older/newer templates)
    total_appointments = appointments.count()
    pending_appointments = appointments.filter(status='pending').count()
    completed_appointments = appointments.filter(status='completed').count()

    context = {
        'patient': patient,
        'specializations': specializations,
        'doctors': doctors,
        'appointments': appointments,
        'medical_reports': medical_reports,

        # old keys you used
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
        'completed_appointments': completed_appointments,

        # also provide these keys in case templates expect them
        'appointments_total': total_appointments,
        'appointments_pending': pending_appointments,
        'appointments_completed': completed_appointments,
        'reports_uploaded': medical_reports.count(),
    }

    return render(request, 'hospital/patient_dashboard.html', context)
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_view_doctor_view(request):
    """
    Simple page that lists all doctors for the patient to browse.
    """
    doctors = (
        models.Doctor.objects
        .select_related('user')
        .order_by('department', 'user__first_name', 'user__last_name')
    )
    return render(request, 'hospital/patient_view_doctor.html', {'doctors': doctors})
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    return render(request,'hospital/patient_appointment.html',{'patient':patient})



# Book Appointment View

@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_book_appointment_view(request, doctor_id):
    doctor = get_object_or_404(models.Doctor, pk=doctor_id)
    patient = get_object_or_404(models.Patient, user=request.user)

    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        description = (request.POST.get('description') or '').strip()

        if not appointment_date or not appointment_time:
            messages.warning(request, '⚠️ Please select both date and time.')
            return render(request, 'hospital/patient_book_appointment.html', {
                'doctor': doctor,
                'patient': patient,
                'today': date.today(),
            })

        # Combine date + time into one datetime field
        try:
            combined_datetime = datetime.strptime(
                f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M"
            )
            combined_datetime = timezone.make_aware(combined_datetime)  # ✅ for timezone support
        except ValueError:
            messages.error(request, '❌ Invalid date or time format.')
            return render(request, 'hospital/patient_book_appointment.html', {
                'doctor': doctor,
                'patient': patient,
                'today': date.today(),
            })

        # Prevent booking past appointments
        if combined_datetime.date() < date.today():
            messages.error(request, '⚠️ Please choose today or a future date.')
            return render(request, 'hospital/patient_book_appointment.html', {
                'doctor': doctor,
                'patient': patient,
                'today': date.today(),
            })

        # Create appointment
        models.Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=combined_datetime,  # ✅ Your model expects a single DateTimeField
            description=description,
            status='pending',
            payment_status=True,  # mock payment success
            payment_amount=getattr(doctor, 'consultation_fee', 0) or 0,
        )

        messages.success(
            request,
            f'✅ Appointment booked successfully with Dr. {doctor.get_name} on {combined_datetime.strftime("%d %b %Y, %I:%M %p")}.'
        )
        return redirect('patient-dashboard')

    return render(request, 'hospital/patient_book_appointment.html', {
        'doctor': doctor,
        'patient': patient,
        'today': date.today(),
    })
@user_passes_test(is_patient)
def patient_view_appointment_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    appointments=models.Appointment.objects.all().filter(patientId=request.user.id)
    return render(request,'hospital/patient_view_appointment.html',{'appointments':appointments,'patient':patient})
@login_required
@user_passes_test(is_doctor)
@require_POST
def doctor_update_appointment_status(request, appointment_id, action):
    """
    Doctor can confirm, complete, or cancel an appointment.
    """
    appt = get_object_or_404(models.Appointment, pk=appointment_id, doctor__user=request.user)

    ACTIONS = {
        'confirm': 'pending',     # if you later add a 'confirmed' status, change this
        'complete': 'completed',
        'cancel': 'cancelled',
    }

    if action not in ACTIONS:
        messages.error(request, "❌ Invalid action.")
        return redirect('doctor-view-appointment')

    appt.status = ACTIONS[action]
    appt.save(update_fields=['status'])

    verb = {
        'confirm': 'confirmed',
        'complete': 'marked as completed',
        'cancel': 'cancelled'
    }[action]
    messages.success(request, f"✅ Appointment with {appt.patient.get_name} has been {verb}.")
    return redirect('doctor-view-appointment')


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def patient_discharge_view(request):
    patient=models.Patient.objects.get(user_id=request.user.id) #for profile picture of patient in sidebar
    dischargeDetails=models.PatientDischargeDetails.objects.all().filter(patientId=patient.id).order_by('-id')[:1]
    patientDict=None
    if dischargeDetails:
        patientDict ={
        'is_discharged':True,
        'patient':patient,
        'patientId':patient.id,
        'patientName':patient.get_name,
        'assigned_doctorName':dischargeDetails[0].assigned_doctorName,
        'address':patient.address,
        'mobile':patient.mobile,
        'symptoms':patient.symptoms,
        'admitDate':patient.admitDate,
        'releaseDate':dischargeDetails[0].releaseDate,
        'daySpent':dischargeDetails[0].daySpent,
        'medicineCost':dischargeDetails[0].medicineCost,
        'roomCharge':dischargeDetails[0].roomCharge,
        'doctorFee':dischargeDetails[0].doctorFee,
        'OtherCharge':dischargeDetails[0].OtherCharge,
        'total':dischargeDetails[0].total,
        }
        print(patientDict)
    else:
        patientDict={
            'is_discharged':False,
            'patient':patient,
            'patientId':request.user.id,
        }
    return render(request,'hospital/patient_discharge.html',context=patientDict)
@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def search_doctor_view(request):
    """Basic search by department or doctor name."""
    q = request.GET.get('q', '').strip()
    doctors = models.Doctor.objects.select_related('user')

    if q:
        from django.db.models import Q
        doctors = doctors.filter(
            Q(department__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)
        )

    doctors = doctors.order_by('department', 'user__first_name')
    return render(request, 'hospital/patient_view_doctor.html', {'doctors': doctors, 'q': q})

@login_required(login_url='patientlogin')
def submit_feedback(request, appointment_id):
    appt = get_object_or_404(Appointment, pk=appointment_id, patient__user=request.user)
    if appt.status != 'completed':
        messages.error(request, "You can only rate completed appointments.")
        return redirect('patient-dashboard')

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '').strip()
        if rating not in (1,2,3,4,5):
            messages.error(request, "Please choose a rating from 1 to 5.")
            return redirect('submit-feedback', appointment_id=appointment_id)

        Feedback.objects.update_or_create(
            appointment=appt,
            defaults={
                'doctor': appt.doctor,
                'patient': appt.patient,
                'rating': rating,
                'comment': comment,
            }
        )
        messages.success(request, "Thanks for your feedback!")
        return redirect('patient-dashboard')

    return render(request, 'hospital/feedback_form.html', {'appointment': appt})

#------------------------ PATIENT RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------








#---------------------------------------------------------------------------------
#------------------------ ABOUT US AND CONTACT US VIEWS START ------------------------------
#---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request,'hospital/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message,settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'hospital/contactussuccess.html')
    return render(request, 'hospital/contactus.html', {'form':sub})


#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS END ------------------------------
#---------------------------------------------------------------------------------
# ============================================================================
# REAL-TIME UPDATE APIs FOR DOCTOR & PATIENT DASHBOARDS
# ============================================================================

@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def get_doctor_profile_api(request):
    """Get current doctor's profile data"""
    try:
        doctor = models.Doctor.objects.select_related('user').get(user=request.user)
        
        data = {
            'id': doctor.id,
            'name': doctor.get_name,
            'department': doctor.department,
            'qualification': doctor.qualification,
            'experience_years': doctor.experience_years,
            'duty_time': doctor.duty_time or 'Not Set',
            'consultation_fee': doctor.consultation_fee,
            'rating_avg': float(doctor.rating_avg),
            'rating_count': doctor.rating_count,
        }
        return JsonResponse({'success': True, 'doctor': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='doctorlogin')
@user_passes_test(is_doctor)
def get_doctor_appointments_realtime(request):
    """Get doctor's appointments for real-time updates"""
    try:
        doctor = models.Doctor.objects.get(user=request.user)
        appointments = models.Appointment.objects.filter(
            doctor=doctor
        ).select_related('patient__user').order_by('-date')[:20]
        
        appointments_list = [{
            'id': a.id,
            'patient_name': a.patient.get_name,
            'date': str(a.date.date()) if a.date else 'N/A',
            'time': str(a.date.time().strftime('%I:%M %p')) if a.date else 'N/A',
            'status': a.status,
            'description': a.description or '',
            'payment_status': a.payment_status,
        } for a in appointments]
        
        # Counts
        counts = {
            'total': appointments.count(),
            'pending': models.Appointment.objects.filter(doctor=doctor, status='pending').count(),
            'confirmed': models.Appointment.objects.filter(doctor=doctor, status='confirmed').count(),
            'completed': models.Appointment.objects.filter(doctor=doctor, status='completed').count(),
            'cancelled': models.Appointment.objects.filter(doctor=doctor, status='cancelled').count(),
        }
        
        return JsonResponse({
            'success': True,
            'appointments': appointments_list,
            'counts': counts
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def get_patient_profile_api(request):
    """Get current patient's profile data"""
    try:
        patient = models.Patient.objects.select_related('user').get(user=request.user)
        
        data = {
            'id': patient.id,
            'name': patient.get_name,
            'age': patient.age or 0,
            'gender': patient.gender or 'N/A',
            'blood_group': patient.blood_group or 'N/A',
            'mobile': patient.mobile,
            'address': patient.address,
            'email': patient.user.email,
        }
        return JsonResponse({'success': True, 'patient': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='patientlogin')
@user_passes_test(is_patient)
def get_patient_appointments_realtime(request):
    """Get patient's appointments for real-time updates"""
    try:
        patient = models.Patient.objects.get(user=request.user)
        appointments = models.Appointment.objects.filter(
            patient=patient
        ).select_related('doctor__user').order_by('-date')[:20]
        
        appointments_list = [{
            'id': a.id,
            'doctor_name': f"Dr. {a.doctor.get_name}",
            'doctor_department': a.doctor.department,
            'date': str(a.date.date()) if a.date else 'N/A',
            'time': str(a.date.time().strftime('%I:%M %p')) if a.date else 'N/A',
            'status': a.status,
            'description': a.description or '',
            'payment_status': a.payment_status,
            'payment_amount': a.payment_amount,
        } for a in appointments]
        
        # Counts
        counts = {
            'total': appointments.count(),
            'pending': models.Appointment.objects.filter(patient=patient, status='pending').count(),
            'confirmed': models.Appointment.objects.filter(patient=patient, status='confirmed').count(),
            'completed': models.Appointment.objects.filter(patient=patient, status='completed').count(),
        }
        
        return JsonResponse({
            'success': True,
            'appointments': appointments_list,
            'counts': counts
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

