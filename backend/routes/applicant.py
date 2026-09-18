import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_from_directory, jsonify
from backend.database.db import db
from backend.models.models import (
    User, Applicant, Application, Document,
    AppointmentSlot, Appointment, ApplicationStatusHistory, Notification
)
from backend.utils.decorators import login_required, role_required
from backend.utils.helpers import (
    generate_application_number, save_uploaded_file, allowed_file, get_status_badge
)
from backend.utils.validators import validate_dob, validate_mobile, validate_email, validate_pincode
from backend.services.app_service import ApplicationService
from backend.services.notification_service import NotificationService

applicant_bp = Blueprint('applicant', __name__, url_prefix='/applicant')

def get_current_applicant():
    user_id = session.get('user_id')
    return Applicant.query.filter_by(user_id=user_id).first()

@applicant_bp.route('/dashboard')
@login_required
@role_required('applicant')
def dashboard():
    applicant = get_current_applicant()
    if not applicant:
        flash('Applicant profile not found.', 'danger')
        return redirect(url_for('auth.logout'))

    applications = Application.query.filter_by(applicant_id=applicant.id).order_by(Application.created_at.desc()).all()
    
    # Compute counts
    draft_count = sum(1 for a in applications if a.status == 'Draft')
    submitted_count = sum(1 for a in applications if a.status == 'Submitted')
    pending_verif_count = sum(1 for a in applications if a.status == 'Under Verification')
    
    # Check scheduled appointments
    app_ids = [a.id for a in applications]
    appointments = Appointment.query.filter(
        Appointment.application_id.in_(app_ids),
        Appointment.status == 'Scheduled'
    ).order_by(Appointment.appointment_date.asc()).all() if app_ids else []
    
    appointment_count = len(appointments)
    upcoming_appointment = appointments[0] if appointments else None

    # Recent notifications
    recent_notifications = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        'applicant/dashboard.html',
        applicant=applicant,
        applications=applications[:5],
        all_applications=applications,
        draft_count=draft_count,
        submitted_count=submitted_count,
        pending_verif_count=pending_verif_count,
        appointment_count=appointment_count,
        upcoming_appointment=upcoming_appointment,
        notifications=recent_notifications
    )

@applicant_bp.route('/applications/new', methods=['GET', 'POST'])
@login_required
@role_required('applicant')
def new_application():
    applicant = get_current_applicant()
    
    if request.method == 'POST':
        app_type = request.form.get('application_type', 'Normal')
        service_type = request.form.get('service_type', 'Fresh')
        booklet_type = request.form.get('booklet_type', '36 Pages')
        prev_passport = request.form.get('previous_passport_number', '').strip()

        # Create initial Draft application
        app = Application(
            applicant_id=applicant.id,
            status='Draft',
            application_type=app_type,
            service_type=service_type,
            booklet_type=booklet_type,
            previous_passport_number=prev_passport if service_type == 'Renewal' else None,
            full_name=applicant.user.full_name,
            mobile_number=applicant.user.mobile_number,
            email=applicant.user.email,
            date_of_birth=applicant.date_of_birth,
            gender=applicant.gender,
            city=applicant.city,
            district=applicant.district,
            state=applicant.state,
            pincode=applicant.pincode,
            country=applicant.country or 'India',
            current_step=1
        )
        db.session.add(app)
        db.session.commit()

        flash('New passport application initiated. Please fill in your details.', 'info')
        return redirect(url_for('applicant.form_wizard', app_id=app.id, step=1))

    return render_template('applicant/new_application.html')

@applicant_bp.route('/applications/<int:app_id>/form', methods=['GET', 'POST'])
@login_required
@role_required('applicant')
def form_wizard(app_id):
    applicant = get_current_applicant()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()

    if application.status not in ['Draft', 'Returned for Correction']:
        flash('This application has already been submitted and cannot be modified.', 'warning')
        return redirect(url_for('applicant.application_details', app_id=app_id))

    current_step = int(request.args.get('step', application.current_step or 1))

    if request.method == 'POST':
        action = request.form.get('action', 'next')  # 'save_draft', 'next', 'prev'
        step_posted = int(request.form.get('step', current_step))

        # Update fields based on step_posted
        if step_posted == 1:
            application.full_name = request.form.get('full_name', '').strip()
            dob_str = request.form.get('date_of_birth', '').strip()
            if dob_str:
                valid_dob, dob_msg, dob_val = validate_dob(dob_str)
                if not valid_dob and action != 'save_draft':
                    flash(dob_msg, 'danger')
                    return render_template('applicant/form_wizard.html', app=application, step=1)
                application.date_of_birth = dob_val
            application.gender = request.form.get('gender')
            application.place_of_birth = request.form.get('place_of_birth', '').strip()
            application.nationality = request.form.get('nationality', 'Indian').strip()
            application.marital_status = request.form.get('marital_status')

        elif step_posted == 2:
            application.mobile_number = request.form.get('mobile_number', '').strip()
            application.email = request.form.get('email', '').strip()
            application.alternate_contact = request.form.get('alternate_contact', '').strip()

        elif step_posted == 3:
            application.house_no = request.form.get('house_no', '').strip()
            application.street = request.form.get('street', '').strip()
            application.city = request.form.get('city', '').strip()
            application.district = request.form.get('district', '').strip()
            application.state = request.form.get('state', '').strip()
            application.pincode = request.form.get('pincode', '').strip()
            application.country = request.form.get('country', 'India').strip()

        elif step_posted == 4:
            application.application_type = request.form.get('application_type', 'Normal')
            application.service_type = request.form.get('service_type', 'Fresh')
            application.booklet_type = request.form.get('booklet_type', '36 Pages')
            application.previous_passport_number = request.form.get('previous_passport_number', '').strip() or None

        elif step_posted == 5:
            application.declaration_accepted = bool(request.form.get('declaration_accepted'))

        # Handle navigation / draft save
        if action == 'save_draft':
            application.current_step = step_posted
            db.session.commit()
            flash('Application draft saved successfully. You can return anytime to continue.', 'success')
            return redirect(url_for('applicant.form_wizard', app_id=app_id, step=step_posted))

        elif action == 'prev':
            prev_step = max(1, step_posted - 1)
            application.current_step = prev_step
            db.session.commit()
            return redirect(url_for('applicant.form_wizard', app_id=app_id, step=prev_step))

        elif action == 'next':
            # Validation for moving forward
            if step_posted == 1 and (not application.full_name or not application.gender or not application.place_of_birth):
                flash('Please complete all required personal details before continuing.', 'danger')
                return render_template('applicant/form_wizard.html', app=application, step=1)
            
            if step_posted == 2 and not application.mobile_number:
                flash('Please complete contact details.', 'danger')
                return render_template('applicant/form_wizard.html', app=application, step=2)

            if step_posted == 3 and (not application.city or not application.pincode or not application.state):
                flash('Please complete address details.', 'danger')
                return render_template('applicant/form_wizard.html', app=application, step=3)

            if step_posted == 5:
                if not application.declaration_accepted:
                    flash('You must accept the self-declaration to proceed to document upload.', 'danger')
                    return render_template('applicant/form_wizard.html', app=application, step=5)
                application.current_step = 5
                db.session.commit()
                return redirect(url_for('applicant.document_upload', app_id=app_id))

            next_step = min(5, step_posted + 1)
            application.current_step = next_step
            db.session.commit()
            return redirect(url_for('applicant.form_wizard', app_id=app_id, step=next_step))

    return render_template('applicant/form_wizard.html', app=application, step=current_step)

@applicant_bp.route('/applications/<int:app_id>/documents', methods=['GET', 'POST'])
@login_required
@role_required('applicant')
def document_upload(app_id):
    applicant = get_current_applicant()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()

    if application.status not in ['Draft', 'Returned for Correction']:
        flash('Documents cannot be modified after application submission.', 'warning')
        return redirect(url_for('applicant.application_details', app_id=app_id))

    if request.method == 'POST':
        doc_type = request.form.get('doc_type')
        file = request.files.get('file')

        if not doc_type:
            flash('Please select a document category.', 'danger')
            return redirect(url_for('applicant.document_upload', app_id=app_id))

        if not file or file.filename == '':
            flash('Please choose a valid file to upload.', 'danger')
            return redirect(url_for('applicant.document_upload', app_id=app_id))

        if not allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            flash('Invalid file format. Only PDF, JPG, JPEG, and PNG files are allowed.', 'danger')
            return redirect(url_for('applicant.document_upload', app_id=app_id))

        try:
            stored_name, rel_path, file_size, mime_type = save_uploaded_file(
                file, current_app.config['UPLOAD_FOLDER']
            )

            # Check if document for this type already exists; replace it if so
            existing_doc = Document.query.filter_by(application_id=application.id, doc_type=doc_type).first()
            if existing_doc:
                existing_doc.original_filename = file.filename
                existing_doc.stored_filename = stored_name
                existing_doc.file_path = rel_path
                existing_doc.file_size = file_size
                existing_doc.mime_type = mime_type
                existing_doc.verification_status = 'Pending'
                existing_doc.rejection_reason = None
                existing_doc.uploaded_at = datetime.utcnow()
                flash(f'Document "{doc_type}" replaced successfully.', 'success')
            else:
                doc = Document(
                    application_id=application.id,
                    doc_type=doc_type,
                    original_filename=file.filename,
                    stored_filename=stored_name,
                    file_path=rel_path,
                    file_size=file_size,
                    mime_type=mime_type,
                    verification_status='Pending'
                )
                db.session.add(doc)
                flash(f'Document "{doc_type}" uploaded successfully.', 'success')

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f'Upload failed: {str(e)}', 'danger')

        return redirect(url_for('applicant.document_upload', app_id=app_id))

    uploaded_docs = Document.query.filter_by(application_id=application.id).all()
    categories = [
        'Identity Proof',
        'Address Proof',
        'Date of Birth Proof',
        'Photograph',
        'Signature',
        'Other Supporting Document'
    ]

    return render_template(
        'applicant/document_upload.html',
        app=application,
        documents=uploaded_docs,
        categories=categories
    )

@applicant_bp.route('/documents/<int:doc_id>/delete', methods=['POST'])
@login_required
@role_required('applicant')
def delete_document(doc_id):
    applicant = get_current_applicant()
    doc = Document.query.get_or_404(doc_id)
    app = Application.query.filter_by(id=doc.application_id, applicant_id=applicant.id).first_or_404()

    if app.status not in ['Draft', 'Returned for Correction']:
        flash('Cannot delete documents after submission.', 'danger')
        return redirect(url_for('applicant.application_details', app_id=app.id))

    try:
        # Remove physical file if present
        full_path = os.path.join(current_app.root_path, '..', doc.file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except OSError:
                pass
        
        db.session.delete(doc)
        db.session.commit()
        flash('Document deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting document: {str(e)}', 'danger')

    return redirect(url_for('applicant.document_upload', app_id=app.id))

@applicant_bp.route('/applications/<int:app_id>/review')
@login_required
@role_required('applicant')
def application_review(app_id):
    applicant = get_current_applicant()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()
    documents = Document.query.filter_by(application_id=application.id).all()

    return render_template('applicant/application_review.html', app=application, documents=documents)

@applicant_bp.route('/applications/<int:app_id>/submit', methods=['POST'])
@login_required
@role_required('applicant')
def submit_application(app_id):
    applicant = get_current_applicant()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()

    if application.status not in ['Draft', 'Returned for Correction']:
        flash('Application has already been submitted.', 'warning')
        return redirect(url_for('applicant.application_details', app_id=app_id))

    # Verification: Ensure mandatory documents uploaded
    doc_types = {d.doc_type for d in application.documents}
    if 'Identity Proof' not in doc_types or 'Address Proof' not in doc_types or 'Photograph' not in doc_types:
        flash('Please upload all mandatory documents (Identity Proof, Address Proof, Photograph) before submission.', 'danger')
        return redirect(url_for('applicant.document_upload', app_id=app_id))

    # Generate Unique Application ID
    if not application.application_number:
        application.application_number = generate_application_number()

    is_resubmission = (application.status == 'Returned for Correction')
    new_status = 'Submitted'
    application.status = new_status
    application.submitted_at = datetime.utcnow()

    # Record History
    history_entry = ApplicationStatusHistory(
        application_id=application.id,
        previous_status='Returned for Correction' if is_resubmission else 'Draft',
        new_status=new_status,
        updated_by=session['user_id'],
        remarks='Application resubmitted by applicant.' if is_resubmission else 'Application submitted by applicant.'
    )
    db.session.add(history_entry)
    db.session.commit()

    # Send Notification
    NotificationService.notify_submission(application)

    flash(f'Application submitted successfully! Your Application ID is {application.application_number}. Please schedule your appointment.', 'success')
    return redirect(url_for('applicant.appointment_schedule', app_id=application.id))

@applicant_bp.route('/applications/<int:app_id>/appointment', methods=['GET', 'POST'])
@login_required
@role_required('applicant')
def appointment_schedule(app_id):
    applicant = get_current_applicant()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()

    if application.status == 'Draft':
        flash('Please submit your application before scheduling an appointment.', 'warning')
        return redirect(url_for('applicant.form_wizard', app_id=app_id, step=1))

    existing_apt = Appointment.query.filter_by(application_id=application.id).first()

    if request.method == 'POST':
        slot_id = request.form.get('slot_id')
        if not slot_id:
            flash('Please select an appointment time slot.', 'danger')
            return redirect(url_for('applicant.appointment_schedule', app_id=app_id))

        success, msg, apt = ApplicationService.book_appointment(application.id, int(slot_id))
        if success:
            flash(msg, 'success')
            return redirect(url_for('applicant.appointment_confirmation', app_id=app_id))
        else:
            flash(msg, 'danger')
            return redirect(url_for('applicant.appointment_schedule', app_id=app_id))

    # Fetch available slots (today and future dates)
    from datetime import date
    available_slots = AppointmentSlot.query.filter(
        AppointmentSlot.slot_date >= date.today(),
        AppointmentSlot.is_active == True
    ).order_by(AppointmentSlot.slot_date.asc(), AppointmentSlot.start_time.asc()).all()

    # Group by date for clear UI calendar
    slots_by_date = {}
    for s in available_slots:
        d_str = s.slot_date.strftime('%Y-%m-%d')
        if d_str not in slots_by_date:
            slots_by_date[d_str] = []
        slots_by_date[d_str].append(s)

    return render_template(
        'applicant/appointment_schedule.html',
        app=application,
        existing_apt=existing_apt,
        slots_by_date=slots_by_date
    )

@applicant_bp.route('/applications/<int:app_id>/appointment/confirmation')
@login_required
@role_required('applicant')
def appointment_confirmation(app_id):
    applicant = get_current_applicant()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()
    appointment = Appointment.query.filter_by(application_id=application.id).first_or_404()

    return render_template('applicant/appointment_confirm.html', app=application, appointment=appointment)

@applicant_bp.route('/applications/<int:app_id>/track')
@login_required
@role_required('applicant')
def status_tracking(app_id):
    applicant = get_current_applicant()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()
    history = ApplicationStatusHistory.query.filter_by(application_id=application.id).order_by(ApplicationStatusHistory.created_at.desc()).all()
    latest_verification = application.verification_records[0] if application.verification_records else None

    # Status stages for timeline
    stages = [
        {'id': 'Submitted', 'label': 'Submitted'},
        {'id': 'Under Verification', 'label': 'Under Verification'},
        {'id': 'Approved', 'label': 'Approved'},
        {'id': 'Printed', 'label': 'Printed'},
        {'id': 'Dispatched', 'label': 'Dispatched'}
    ]

    return render_template(
        'applicant/status_tracking.html',
        app=application,
        stages=stages,
        history=history,
        latest_verification=latest_verification
    )

@applicant_bp.route('/my-applications')
@login_required
@role_required('applicant')
def my_applications():
    applicant = get_current_applicant()
    applications = Application.query.filter_by(applicant_id=applicant.id).order_by(Application.created_at.desc()).all()
    return render_template('applicant/my_applications.html', applications=applications)

@applicant_bp.route('/applications/<int:app_id>/details')
@login_required
@role_required('applicant')
def application_details(app_id):
    applicant = get_current_applicant()
    application = Application.query.filter_by(id=app_id, applicant_id=applicant.id).first_or_404()
    documents = Document.query.filter_by(application_id=application.id).all()
    appointment = Appointment.query.filter_by(application_id=application.id).first()
    history = ApplicationStatusHistory.query.filter_by(application_id=application.id).order_by(ApplicationStatusHistory.created_at.desc()).all()

    return render_template(
        'applicant/application_details.html',
        app=application,
        documents=documents,
        appointment=appointment,
        history=history
    )

@applicant_bp.route('/notifications')
@login_required
@role_required('applicant')
def notifications():
    user_notifications = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).all()
    # Mark as read
    for n in user_notifications:
        if not n.is_read:
            n.is_read = True
    db.session.commit()
    return render_template('applicant/notifications.html', notifications=user_notifications)

@applicant_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('applicant')
def profile():
    applicant = get_current_applicant()
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.full_name = request.form.get('full_name', '').strip()
        user.mobile_number = request.form.get('mobile_number', '').strip()
        
        dob_str = request.form.get('date_of_birth', '').strip()
        if dob_str:
            v, m, parsed_dob = validate_dob(dob_str)
            if v:
                applicant.date_of_birth = parsed_dob
        
        applicant.gender = request.form.get('gender')
        applicant.address_line = request.form.get('address_line', '').strip()
        applicant.city = request.form.get('city', '').strip()
        applicant.district = request.form.get('district', '').strip()
        applicant.state = request.form.get('state', '').strip()
        applicant.pincode = request.form.get('pincode', '').strip()

        db.session.commit()
        session['full_name'] = user.full_name
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('applicant.profile'))

    return render_template('applicant/profile.html', user=user, applicant=applicant)
