from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.database.db import db
from backend.models.models import User, Applicant
from backend.utils.validators import validate_email, validate_mobile, validate_password
from backend.utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('public/index.html')

@auth_bp.route('/about')
def about():
    return render_template('public/about.html')

@auth_bp.route('/contact')
def contact():
    return render_template('public/contact.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('role')
        if role in ['officer', 'admin']:
            return redirect(url_for('officer.dashboard'))
        return redirect(url_for('applicant.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        if not email or not password:
            flash('Please provide both email and password.', 'warning')
            return render_template('public/login.html', email=email)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please verify your credentials.', 'danger')
            return render_template('public/login.html', email=email)

        # Establish secure session
        session.clear()
        session['user_id'] = user.id
        session['email'] = user.email
        session['role'] = user.role
        session['full_name'] = user.full_name
        session.permanent = bool(remember)

        flash(f'Welcome back, {user.full_name}!', 'success')
        
        # Redirection based on role
        if user.role in ['officer', 'admin']:
            return redirect(url_for('officer.dashboard'))
        else:
            return redirect(url_for('applicant.dashboard'))

    return render_template('public/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('applicant.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        mobile = request.form.get('mobile_number', '').strip()
        dob_str = request.form.get('date_of_birth', '').strip()
        gender = request.form.get('gender', '').strip()
        address = request.form.get('address', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not full_name:
            flash('Full Name is required.', 'danger')
            return render_template('public/register.html', **request.form)

        valid_email, email_err = validate_email(email)
        if not valid_email:
            flash(email_err, 'danger')
            return render_template('public/register.html', **request.form)

        valid_mobile, mobile_val = validate_mobile(mobile)
        if not valid_mobile:
            flash(mobile_val, 'danger')
            return render_template('public/register.html', **request.form)

        valid_pwd, pwd_err = validate_password(password)
        if not valid_pwd:
            flash(pwd_err, 'danger')
            return render_template('public/register.html', **request.form)

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'danger')
            return render_template('public/register.html', **request.form)

        # Check existing user
        if User.query.filter_by(email=email).first():
            flash('An account with this email address already exists. Please login.', 'warning')
            return redirect(url_for('auth.login'))

        try:
            from datetime import datetime
            dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None

            # Create User record
            user = User(
                email=email,
                role='applicant',
                full_name=full_name,
                mobile_number=mobile_val
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # Create Applicant record
            applicant = Applicant(
                user_id=user.id,
                date_of_birth=dob_date,
                gender=gender or None,
                address_line=address or None
            )
            db.session.add(applicant)
            db.session.commit()

            flash('Registration successful! Please log in with your credentials.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')
            return render_template('public/register.html', **request.form)

    return render_template('public/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('applicant/change_password.html')

        valid_pwd, pwd_err = validate_password(new_password)
        if not valid_pwd:
            flash(pwd_err, 'danger')
            return render_template('applicant/change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('applicant/change_password.html')

        user.set_password(new_password)
        db.session.commit()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('applicant.dashboard') if user.role == 'applicant' else url_for('officer.dashboard'))

    return render_template('applicant/change_password.html', user=user)
