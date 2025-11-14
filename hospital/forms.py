from django import forms
from django.contrib.auth.models import User
from . import models
from django.contrib.auth.forms import UserCreationForm



#for admin signup
class AdminSigupForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }


# ------------------------
# Doctor signup user form
# ------------------------
class DoctorUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password1', 'password2']
        # Django handles password hashing, validation, and uniqueness for you automatically


# ------------------------
# Doctor profile form
# ------------------------
class DoctorForm(forms.ModelForm):
    class Meta:
        model = models.Doctor
        fields = ['address', 'mobile', 'department', 'status', 'profile_pic', 'qualification',
            'experience_years',]
        widgets = {
            'experience_years': forms.NumberInput(attrs={'min': 0})
        }
#for patient related form
class PatientUserForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }
    
class PatientForm(forms.ModelForm):
    class Meta:
        model = models.Patient
        fields = ['address', 'mobile', 'profile_pic']



class AppointmentForm(forms.ModelForm):
    doctorId=forms.ModelChoiceField(queryset=models.Doctor.objects.all().filter(status=True),empty_label="Doctor Name and Department", to_field_name="user_id")
    patientId=forms.ModelChoiceField(queryset=models.Patient.objects.all().filter(status=True),empty_label="Patient Name and Symptoms", to_field_name="user_id")
    class Meta:
        model=models.Appointment
        fields=['description','status']


class PatientAppointmentForm(forms.ModelForm):
    doctorId=forms.ModelChoiceField(queryset=models.Doctor.objects.all().filter(status=True),empty_label="Doctor Name and Department", to_field_name="user_id")
    class Meta:
        model=models.Appointment
        fields=['description','status']


#for contact us page
class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))
class MedicalReportForm(forms.ModelForm):
    class Meta:
        model = models.MedicalReport
        fields = ['patient', 'title', 'description', 'report_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Report Title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Report Description',
                'rows': 4
            }),
            'patient': forms.Select(attrs={
                'class': 'form-control'
            }),
            'report_file': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, doctor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show patients assigned to this doctor
        self.fields['patient'].queryset = models.Patient.objects.filter(
            assigned_doctor=doctor,
            status=True
        )
        self.fields['patient'].label_from_instance = lambda obj: f"{obj.get_name()} - {obj.mobile}"