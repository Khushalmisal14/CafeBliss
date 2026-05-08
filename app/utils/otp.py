import random
import string
from flask_mail import Message
from app import mail
from flask import current_app


def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


def send_email_otp(email, otp):
    """Send OTP to user's email with fallback to console."""
    try:
        msg = Message(
            subject    = '☕ CafeBliss — Your OTP Verification Code',
            recipients = [email]
        )
        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px;
                    margin: auto; padding: 30px;
                    border: 1px solid #e0d0b0; border-radius: 10px;">
            <h2 style="color: #2c1810;">☕ CafeBliss</h2>
            <p>Hello! Thanks for signing up.</p>
            <p>Your OTP verification code is:</p>
            <div style="font-size: 36px; font-weight: bold;
                        letter-spacing: 10px; color: #c8860a;
                        text-align: center; padding: 20px;
                        background: #fdf6ec; border-radius: 8px;
                        margin: 20px 0;">
                {otp}
            </div>
            <p style="color: #666;">
                This code is valid for <strong>10 minutes</strong>.<br>
                Do not share this code with anyone.
            </p>
            <hr style="border-color: #e0d0b0;">
            <p style="color: #999; font-size: 12px;">
                CafeBliss — Crafted with love & Python ☕
            </p>
        </div>
        """
        mail.send(msg)
        print(f'✅ OTP sent to {email}')
        return True

    except Exception as e:
        # Fallback — print OTP to terminal for testing
        print(f'⚠️  Email sending failed: {e}')
        print(f'🔑 OTP for {email}: {otp}')
        return False