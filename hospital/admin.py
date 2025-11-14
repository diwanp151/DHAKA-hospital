from django.contrib import admin
from .models import Doctor, Patient, Appointment, PatientDischargeDetails

# Doctor admin registration
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'mobile', 'status']
    list_filter = ['department', 'status']
    search_fields = ['user__first_name', 'user__last_name', 'mobile']
    list_editable = ['status']

admin.site.register(Doctor, DoctorAdmin)

# Patient admin registration
class PatientAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'mobile', 'admitDate', 'status']
    list_filter = ['status']
    search_fields = ['user__first_name', 'user__last_name', 'mobile']

    def get_name(self, obj):
        return obj.user.get_full_name()
    get_name.short_description = 'Name'

admin.site.register(Patient, PatientAdmin)

# Appointment admin registration
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['get_patient_name', 'get_doctor_name', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['patient__user__first_name', 'doctor__user__first_name']

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name()
    get_patient_name.short_description = 'Patient Name'

    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name()
    get_doctor_name.short_description = 'Doctor Name'
admin.site.register(Appointment, AppointmentAdmin)

# PatientDischargeDetails admin registration
class PatientDischargeDetailsAdmin(admin.ModelAdmin):
    list_display = [
        'get_patient_name', 
        'get_doctor_name', 
        'address', 
        'mobile', 
        'admitDate', 
        'releaseDate', 
        'total'
    ]

    def get_patient_name(self, obj):
        if hasattr(obj, "patient") and obj.patient:
            return obj.patient.user.get_full_name()
        elif hasattr(obj, "patientName"):
            return obj.patientName
        return "-"
    get_patient_name.short_description = 'Patient Name'

    def get_doctor_name(self, obj):
        if hasattr(obj, "doctor") and obj.doctor:
            return obj.doctor.user.get_full_name()
        elif hasattr(obj, "assigned_doctorName"):
            return obj.assigned_doctorName
        return "-"
    get_doctor_name.short_description = 'Doctor Name'

admin.site.register(PatientDischargeDetails, PatientDischargeDetailsAdmin)
