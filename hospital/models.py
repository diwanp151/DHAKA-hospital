from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

departments=[('Cardiologist','Cardiologist'),
('Dermatologists','Dermatologists'),
('Emergency Medicine Specialists','Emergency Medicine Specialists'),
('Allergists/Immunologists','Allergists/Immunologists'),
('Anesthesiologists','Anesthesiologists'),
('Colon and Rectal Surgeons','Colon and Rectal Surgeons')
]

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/DoctorProfilePic/', null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=True)
    department = models.CharField(max_length=50, choices=departments, default='Cardiologist')
    status = models.BooleanField(default=False)
    consultation_fee = models.IntegerField(default=500)
    
    # Doctor qualifications and experience
    qualification = models.CharField(max_length=120, default='MBBS')
    experience_years = models.PositiveIntegerField(default=0)
    
    # ✅ NEW FIELD FOR ADMIN DASHBOARD: Duty Time
    duty_time = models.CharField(max_length=50, null=True, blank=True, default='9:00 AM - 5:00 PM')
    
    # Rating system
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    rating_count = models.PositiveIntegerField(default=0)
    
    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name
    
    @property
    def get_id(self):
        return self.user.id
    
    @property
    def experience(self):
        """For backward compatibility with admin dashboard"""
        return f"{self.experience_years} years" if self.experience_years else "N/A"
    
    def refresh_rating(self):
        agg = self.feedback_set.aggregate(avg=Avg('rating'))
        avg = agg['avg'] or 0
        self.rating_avg = round(float(avg), 2)
        self.rating_count = self.feedback_set.count()
        self.save(update_fields=['rating_avg', 'rating_count'])
    
    def __str__(self):
        return "{} ({})".format(self.user.first_name, self.department)


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pic/PatientProfilePic/', null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=False)
    admitDate = models.DateField(auto_now=True)
    status = models.BooleanField(default=False)
    assigned_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    
    # ✅ NEW FIELDS FOR ADMIN DASHBOARD
    age = models.PositiveIntegerField(null=True, blank=True, default=0)
    gender = models.CharField(max_length=10, null=True, blank=True, 
                              choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], 
                              default='Male')
    blood_group = models.CharField(max_length=5, null=True, blank=True, 
                                   choices=[('A+', 'A+'), ('A-', 'A-'), 
                                           ('B+', 'B+'), ('B-', 'B-'),
                                           ('O+', 'O+'), ('O-', 'O-'),
                                           ('AB+', 'AB+'), ('AB-', 'AB-')],
                                   default='O+')
    
    @property
    def get_name(self):
        return self.user.first_name + " " + self.user.last_name
    
    @property
    def get_id(self):
        return self.user.id
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),  # ✅ ADDED
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    date = models.DateTimeField(null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    payment_status = models.BooleanField(default=False)
    payment_amount = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ✅ PROPERTIES FOR ADMIN DASHBOARD COMPATIBILITY
    @property
    def appointmentDate(self):
        """For backward compatibility"""
        return self.date.date() if self.date else None
    
    @property
    def appointmentTime(self):
        """For backward compatibility"""
        return self.date.time() if self.date else None
    
    @property
    def patientName(self):
        """For backward compatibility"""
        return self.patient.get_name if self.patient else "N/A"
    
    @property
    def doctorName(self):
        """For backward compatibility"""
        return f"Dr. {self.doctor.get_name}" if self.doctor else "N/A"
    
    @property
    def feedback(self):
        try:
            return self.feedback_set.get()
        except Feedback.DoesNotExist:
            return None
    
    def __str__(self):
        return f"{self.patient.get_name if self.patient else 'Unknown'} with {self.doctor.get_name if self.doctor else 'Unknown'}"


class Feedback(models.Model):
    """
    One feedback per (patient, appointment). Rating 1..5
    """
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # keep doctor aggregates in sync
        self.doctor.refresh_rating()
    
    def __str__(self):
        return f"Feedback for {self.doctor.get_name} by {self.patient.get_name}"


class PatientDischargeDetails(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.SET_NULL, null=True, blank=True)
    doctor = models.ForeignKey('Doctor', on_delete=models.SET_NULL, null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=True)
    symptoms = models.CharField(max_length=100, null=True)

    admitDate = models.DateField()
    releaseDate = models.DateField()
    daySpent = models.PositiveIntegerField()

    roomCharge = models.PositiveIntegerField()
    medicineCost = models.PositiveIntegerField()
    doctorFee = models.PositiveIntegerField()
    OtherCharge = models.PositiveIntegerField()
    total = models.PositiveIntegerField()

    def __str__(self):
        return f"Discharge: {self.patient} by {self.doctor}"


class MedicalReport(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    report_file = models.FileField(upload_to='medical_reports/')
    uploaded_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.patient.get_name()}"
    
    class Meta:
        ordering = ['-uploaded_date']


# ============================================================================
# MIGRATION INSTRUCTIONS
# ============================================================================
# After updating this models.py file, run:
#
# python manage.py makemigrations
# python manage.py migrate
#
# Django will ask you to provide default values for existing records.
# You can:
# 1. Press 1 to provide a default value now
# 2. Press 2 to quit and add default values in the model (already done above)
#
# All new fields have default values, so migration should work smoothly!
# ============================================================================