# utils.py
# utils.py (place this in the same app as your views.py)

import random
from django.core.mail import send_mail
from django.conf import settings
def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    """
    Sends the OTP to the provided email.
    Returns True if sent successfully, False otherwise.
    """
    try:
        send_mail(
            subject="Your Email OTP",
            message=f"Your OTP for hospital registration is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )
        return True
    except Exception as e:
        print("Email send error:", e)
        return False
