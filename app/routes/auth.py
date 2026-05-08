from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.utils.otp import generate_otp, send_email_otp
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)


# ---------- SIGNUP ----------
@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('customer.home'))

    if request.method == 'POST':
        name     = request.form.get('name').strip()
        email    = request.form.get('email').strip().lower()
        mobile   = request.form.get('mobile').strip()
        password = request.form.get('password')
        confirm  = request.form.get('confirm_password')

        # Basic validation
        if not all([name, email, mobile, password, confirm]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.signup'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.signup'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('auth.signup'))

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('auth.login'))

        if User.query.filter_by(mobile=mobile).first():
            flash('Mobile number already registered.', 'warning')
            return redirect(url_for('auth.signup'))

        # Generate OTP
        otp = generate_otp()
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)

        # Save user temporarily in session until OTP verified
        session['pending_user'] = {
            'name'    : name,
            'email'   : email,
            'mobile'  : mobile,
            'password': password,
            'otp'     : otp,
            'expiry'  : otp_expiry.isoformat()
        }

        # Send OTP email
        send_email_otp(email, otp)

        flash(f'OTP sent to {email}. Please verify.', 'info')
        return redirect(url_for('auth.verify_otp'))

    return render_template('auth/signup.html')


# ---------- VERIFY OTP ----------
@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    pending = session.get('pending_user')
    if not pending:
        flash('Session expired. Please signup again.', 'danger')
        return redirect(url_for('auth.signup'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp').strip()
        expiry      = datetime.fromisoformat(pending['expiry'])

        if datetime.utcnow() > expiry:
            session.pop('pending_user', None)
            flash('OTP expired. Please signup again.', 'danger')
            return redirect(url_for('auth.signup'))

        if entered_otp != pending['otp']:
            flash('Invalid OTP. Please try again.', 'danger')
            return render_template('auth/verify_otp.html', email=pending['email'])

        # OTP correct — create the user
        user = User(
            name       = pending['name'],
            email      = pending['email'],
            mobile     = pending['mobile'],
            is_verified= True
        )
        user.set_password(pending['password'])
        db.session.add(user)
        db.session.commit()

        session.pop('pending_user', None)
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/verify_otp.html', email=pending['email'])


# ---------- LOGIN ----------
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('customer.home'))

    if request.method == 'POST':
        email    = request.form.get('email').strip().lower()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_verified:
            flash('Please verify your email first.', 'warning')
            return redirect(url_for('auth.login'))

        login_user(user)
        flash(f'Welcome back, {user.name}!', 'success')

        # Redirect based on role
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('customer.home'))

    return render_template('auth/login.html')


# ---------- LOGOUT ----------
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))