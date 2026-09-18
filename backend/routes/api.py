from datetime import datetime, date
from flask import Blueprint, request, jsonify, session, current_app
from backend.database.db import db
from backend.models.models import (
    User, Applicant, Application, Document,
    AppointmentSlot, Appointment, VerificationRecord,
    ApplicationStatusHistory, Notification
)
from backend.utils.decorators import login_required, role_required
from backend.utils.validators import validate_email, validate_mobile, validate_password
from backend.utils.helpers import generate_application_number, save_uploaded_file, allowed_file
from backend.services.app_service import ApplicationService
from backend.services.notification_service import NotificationService

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- AUTH APIS ---
@api_bp.route('/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    mobile = data.get('mobile_number', '').strip()

    valid_email, email_err = validate_email(email)
    if not valid_email:
        return jsonify({'success': False, 'error': email_err}), 400

    valid_mobile, mob_val = validate_mobile(mobile)
    if not valid_mobile:
        return jsonify({'success': False, 'error': mob_val}), 400

    valid_pwd, pwd_err = validate_password(password)
    if not valid_pwd:
        return jsonify({'success': False, 'error': pwd_err}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already registered.'}), 409

    try:
        user = User(email=email, role='applicant', full_name=full_name, mobile_number=mob_val)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        applicant = Applicant(user_id=user.id)
        db.session.add(applicant)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Registration successful. Please login.', 'user_id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'error': 'Invalid email or password.'}), 401

    session.clear()
    session['user_id'] = user.id
    session['email'] = user.email
    session['role'] = user.role
    session['full_name'] = user.full_name

    return jsonify({
        'success': True,
        'message': 'Login successful.',
        'user': user.to_dict()
    }), 200

@api_bp.route('/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'}), 200

# --- APPLICANT APPLICATION APIS ---
@api_bp.route('/applications', methods=['GET'])
@login_required
def api_get_applications():
    user = User.query.get(session['user_id'])
    if user.role == 'applicant':
        applicant = Applicant.query.filter_by(user_id=user.id).first()
        apps = Application.query.filter_by(applicant_id=applicant.id).all()
    else:
        apps = Application.query.all()

    result = [{
        'id': a.id,
        'application_number': a.application_number,
        'full_name': a.full_name,
        'status': a.status,
        'service_type': a.service_type,
        'application_type': a.application_type,
        'created_at': a.created_at.strftime('%Y-%m-%d %H:%M:%S') if a.created_at else None
    } for a in apps]

    return jsonify({'success': True, 'applications': result})

@api_bp.route('/applications', methods=['POST'])
@login_required
@role_required('applicant')
def api_create_application():
    data = request.get_json() or {}
    applicant = Applicant.query.filter_by(user_id=session['user_id']).first()

    app = Application(
        applicant_id=applicant.id,
        status='Draft',
        application_type=data.get('application_type', 'Normal'),
        service_type=data.get('service_type', 'Fresh'),
        booklet_type=data.get('booklet_type', '36 Pages'),
        full_name=data.get('full_name', applicant.user.full_name),
        mobile_number=data.get('mobile_number', applicant.user.mobile_number),
        email=data.get('email', applicant.user.email)
    )
    db.session.add(app)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Draft application created.', 'application_id': app.id}), 201

@api_bp.route('/applications/<int:app_id>', methods=['GET'])
@login_required
def api_get_application(app_id):
    application = Application.query.get_or_404(app_id)
    return jsonify({
        'success': True,
        'application': {
            'id': application.id,
            'application_number': application.application_number,
            'status': application.status,
            'full_name': application.full_name,
            'email': application.email,
            'mobile_number': application.mobile_number,
            'date_of_birth': application.date_of_birth.strftime('%Y-%m-%d') if application.date_of_birth else None,
            'gender': application.gender,
            'place_of_birth': application.place_of_birth,
            'city': application.city,
            'state': application.state,
            'pincode': application.pincode,
            'documents': [{'id': d.id, 'type': d.doc_type, 'status': d.verification_status} for d in application.documents]
        }
    })

@api_bp.route('/applications/<int:app_id>', methods=['PUT'])
@login_required
@role_required('applicant')
def api_update_application(app_id):
    applicant = Applicant.query.filter_by(user_id=session['user_id']).first()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()

    if application.status not in ['Draft', 'Returned for Correction']:
        return jsonify({'success': False, 'error': 'Application cannot be edited after submission.'}), 400

    data = request.get_json() or {}
    for key, val in data.items():
        if hasattr(application, key) and key not in ['id', 'application_number', 'applicant_id', 'status']:
            setattr(application, key, val)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Application updated successfully.'})

@api_bp.route('/applications/<int:app_id>/submit', methods=['POST'])
@login_required
@role_required('applicant')
def api_submit_application(app_id):
    applicant = Applicant.query.filter_by(user_id=session['user_id']).first()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()

    if application.status not in ['Draft', 'Returned for Correction']:
        return jsonify({'success': False, 'error': 'Application has already been submitted.'}), 400

    if not application.application_number:
        application.application_number = generate_application_number()

    prev_status = application.status
    application.status = 'Submitted'
    application.submitted_at = datetime.utcnow()

    history = ApplicationStatusHistory(
        application_id=application.id,
        previous_status=prev_status,
        new_status='Submitted',
        updated_by=session['user_id'],
        remarks='Application submitted via API.'
    )
    db.session.add(history)
    db.session.commit()

    NotificationService.notify_submission(application)

    return jsonify({
        'success': True,
        'message': 'Application submitted successfully.',
        'application_number': application.application_number
    })

# --- APPOINTMENT APIS ---
@api_bp.route('/appointments/available', methods=['GET'])
def api_available_appointments():
    date_param = request.args.get('date')
    query = AppointmentSlot.query.filter(AppointmentSlot.is_active == True)
    
    if date_param:
        try:
            d_val = datetime.strptime(date_param, '%Y-%m-%d').date()
            query = query.filter(AppointmentSlot.slot_date == d_val)
        except ValueError:
            pass
    else:
        query = query.filter(AppointmentSlot.slot_date >= date.today())

    slots = query.order_by(AppointmentSlot.slot_date.asc(), AppointmentSlot.start_time.asc()).all()
    result = [{
        'id': s.id,
        'date': s.slot_date.strftime('%Y-%m-%d'),
        'time': s.formatted_time,
        'max_capacity': s.max_capacity,
        'booked_count': s.booked_count,
        'available': s.available_seats,
        'location': s.location
    } for s in slots]

    return jsonify({'success': True, 'slots': result})

@api_bp.route('/appointments/book', methods=['POST'])
@login_required
@role_required('applicant')
def api_book_appointment():
    data = request.get_json() or {}
    app_id = data.get('application_id')
    slot_id = data.get('slot_id')

    if not app_id or not slot_id:
        return jsonify({'success': False, 'error': 'application_id and slot_id are required.'}), 400

    success, msg, apt = ApplicationService.book_appointment(int(app_id), int(slot_id))
    if not success:
        return jsonify({'success': False, 'error': msg}), 400

    return jsonify({
        'success': True,
        'message': msg,
        'appointment_number': apt.appointment_number,
        'date': apt.appointment_date.strftime('%Y-%m-%d'),
        'time': apt.appointment_time
    }), 201

# --- NOTIFICATIONS APIS ---
@api_bp.route('/notifications', methods=['GET'])
@login_required
def api_get_notifications():
    notifs = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    return jsonify({
        'success': True,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'is_read': n.is_read,
            'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for n in notifs]
    })

@api_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def api_read_notification(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=session['user_id']).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'Notification marked as read.'})

# --- OFFICER APIS ---
@api_bp.route('/admin/applications/<int:app_id>/approve', methods=['POST'])
@login_required
@role_required('officer', 'admin')
def api_approve_application(app_id):
    application = Application.query.get_or_404(app_id)
    if not application.has_all_mandatory_docs_verified:
        return jsonify({'success': False, 'error': 'Mandatory documents (Identity, Address, Photo) must be verified before approval.'}), 400

    ApplicationService.change_status(application, 'Approved', session['user_id'], 'Approved via API.')
    return jsonify({'success': True, 'message': f'Application {application.application_number} approved.'})

@api_bp.route('/admin/applications/<int:app_id>/reject', methods=['POST'])
@login_required
@role_required('officer', 'admin')
def api_reject_application(app_id):
    data = request.get_json() or {}
    reason = data.get('reason', '').strip()
    if not reason:
        return jsonify({'success': False, 'error': 'Reason is mandatory when rejecting.'}), 400

    application = Application.query.get_or_404(app_id)
    ApplicationService.change_status(application, 'Rejected', session['user_id'], f'Rejected: {reason}')
    return jsonify({'success': True, 'message': f'Application {application.application_number} rejected.'})
