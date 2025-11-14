"""

Developed By : diwan

"""




from django.contrib import admin
from django.urls import path, include
from hospital import views
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings  # ✅ Added
from django.conf.urls.static import static  # ✅ Added


#-------------FOR ADMIN RELATED URLS
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.home_view, name='home'),
    path('', include('hospital.urls')),

    path('aboutus', views.aboutus_view, name='aboutus'),
    path('contactus', views.contactus_view, name='contactus'),

    path('adminclick', views.adminclick_view, name='adminclick'),
    path('doctorclick', views.doctorclick_view, name='doctorclick'),
    path('patientclick', views.patientclick_view, name='patientclick'),

    path('adminsignup', views.admin_signup_view, name='adminsignup'),
    path('doctorsignup', views.doctor_signup_view, name='doctorsignup'),
    path('patientsignup', views.patient_signup_view, name='patientsignup'),
    
    # LOGIN URLS - FIXED: Added 'name' parameter to all
    path('adminlogin', LoginView.as_view(template_name='hospital/adminlogin.html'), name='adminlogin'),
    path('doctorlogin', views.doctor_login_view, name='doctorlogin'),
    path('patientlogin', views.patient_login_view, name='patientlogin'),

    path('afterlogin', views.afterlogin_view, name='afterlogin'),
    path('logout', LogoutView.as_view(template_name='hospital/index.html'), name='logout'),

    # ADMIN DASHBOARD
    path('admin-dashboard', views.admin_dashboard_view, name='admin-dashboard'),

    # ADMIN - DOCTOR MANAGEMENT
    path('admin-doctor', views.admin_doctor_view, name='admin-doctor'),
    path('admin-view-doctor-json/', views.admin_view_doctor_json, name='admin-view-doctor-json'),
    path('delete-doctor-from-hospital/<int:pk>', views.delete_doctor_from_hospital_view, name='delete-doctor-from-hospital'),
    path('update-doctor/<int:pk>', views.update_doctor_view, name='update-doctor'),
    path('admin-add-doctor', views.admin_add_doctor_view, name='admin-add-doctor'),
   # path('admin-approve-doctor', views.admin_approve_doctor_view, name='admin-approve-doctor'),
   # path('approve-doctor/<int:pk>', views.approve_doctor_view, name='approve-doctor'),
   # path('reject-doctor/<int:pk>', views.reject_doctor_view, name='reject-doctor'),
    path('admin-view-doctor-specialisation', views.admin_view_doctor_specialisation_view, name='admin-view-doctor-specialisation'),

    # ADMIN - PATIENT MANAGEMENT
    path('admin-patient', views.admin_patient_view, name='admin-patient'),
    path('admin-view-patient', views.admin_view_patient_view, name='admin-view-patient'),
    path('delete-patient-from-hospital/<int:pk>', views.delete_patient_from_hospital_view, name='delete-patient-from-hospital'),
    path('update-patient/<int:pk>', views.update_patient_view, name='update-patient'),
    path('admin-add-patient', views.admin_add_patient_view, name='admin-add-patient'),
    path('admin-approve-patient', views.admin_approve_patient_view, name='admin-approve-patient'),
    path('approve-patient/<int:pk>', views.approve_patient_view, name='approve-patient'),
    path('reject-patient/<int:pk>', views.reject_patient_view, name='reject-patient'),
    path('admin-discharge-patient', views.admin_discharge_patient_view, name='admin-discharge-patient'),
    path('discharge-patient/<int:pk>', views.discharge_patient_view, name='discharge-patient'),
    path('download-pdf/<int:pk>', views.download_pdf_view, name='download-pdf'),

    # ADMIN - APPOINTMENT MANAGEMENT
    path('admin-appointment', views.admin_appointment_view, name='admin-appointment'),
    path('admin-view-appointment', views.admin_view_appointment_view, name='admin-view-appointment'),
    path('admin-add-appointment', views.admin_add_appointment_view, name='admin-add-appointment'),
    path('admin-approve-appointment', views.admin_approve_appointment_view, name='admin-approve-appointment'),
    path('approve-appointment/<int:pk>', views.approve_appointment_view, name='approve-appointment'),
    path('reject-appointment/<int:pk>', views.reject_appointment_view, name='reject-appointment'),
]

#---------FOR DOCTOR RELATED URLS-------------------------------------
urlpatterns += [
    # DOCTOR DASHBOARD
    path('doctor-dashboard', views.doctor_dashboard_view, name='doctor-dashboard'),
    
    # DOCTOR - APPOINTMENT MANAGEMENT
    path('doctor-appointment', views.doctor_appointment_view, name='doctor-appointment'),
    path('doctor-view-appointment', views.doctor_view_appointment_view, name='doctor-view-appointment'),
    path('doctor-delete-appointment', views.doctor_delete_appointment_view, name='doctor-delete-appointment'),
    path('delete-appointment/<int:pk>', views.delete_appointment_view, name='delete-appointment'),
    path('doctor-appointment-confirm/<int:appointment_id>/', views.confirm_appointment, name='confirm-appointment'),
    path('doctor-appointment-cancel/<int:appointment_id>/', views.cancel_appointment_api, name='cancel-appointment'),
    path('doctor-appointment-complete/<int:appointment_id>/', views.complete_appointment, name='complete-appointment'),
    
    # DOCTOR - PATIENT MANAGEMENT
    path('doctor-patient', views.doctor_patient_view, name='doctor-patient'),
    path('doctor-view-patient', views.doctor_view_patient_view, name='doctor-view-patient'),
    path('doctor-view-discharge-patient', views.doctor_view_discharge_patient_view, name='doctor-view-discharge-patient'),
    
    # DOCTOR - REPORTS & SEARCH
    path('upload-report/', views.upload_report, name='upload-report'),

    path('search', views.search_view, name='search'),
]


#---------FOR PATIENT RELATED URLS-------------------------------------
urlpatterns += [
    # PATIENT DASHBOARD
    path('patient-dashboard', views.patient_dashboard_view, name='patient-dashboard'),
    
    # PATIENT - APPOINTMENT MANAGEMENT
    path('patient-appointment', views.patient_appointment_view, name='patient-appointment'),
    path('patient-book-appointment/<int:doctor_id>/', views.patient_book_appointment_view, name='patient-book-appointment'),
    path('patient-view-appointment', views.patient_view_appointment_view, name='patient-view-appointment'),
    
    # PATIENT - DOCTOR & DISCHARGE
    path('patient-view-doctor', views.patient_view_doctor_view, name='patient-view-doctor'),
    path('searchdoctor', views.search_doctor_view, name='searchdoctor'),
    path('patient-discharge', views.patient_discharge_view, name='patient-discharge'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)