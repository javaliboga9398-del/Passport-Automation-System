import io
import csv
from datetime import datetime, date, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, Response, jsonify
from backend.database.db import db
from backend.models.models import (
    User, Applicant, Application, Document,
    AppointmentSlot, Appointment, VerificationRecord,
    ApplicationStatusHistory, Notification
)
from backend.utils.decorators import login_required, role_required
from backend.services.app_service import ApplicationService
from backend.services.notification_service import NotificationService

officer_bp = Blueprint('officer', __name__, url_prefix='/admin')

@officer_bp.route('/dashboard')
@login_required
@role_required('officer', 'admin')
def dashboard():
    total_applicants = Applicant.query.count()
    total_applications = Application.query.filter(Application.status != 'Draft').count()
    pending_verification = Application.query.filter(Application.status.in_(['Submitted', 'Under Verification'])).count()
    approved_count = Application.query.filter_by(status='Approved').count()
    rejected_count = Application.query.filter_by(status='Rejected').count()
    dispatched_count = Application.query.filter_by(status='Dispatched').count()

    today = date.today()
    today_appointments = Appointment.query.filter_by(appointment_date=today).count()

    # Recent pending applications requiring attention
    urgent_applications = Application.query.filter(
        Application.status.in_(['Submitted', 'Under Verification'])
    ).order_by(Application.submitted_at.asc()).limit(6).all()

    # Upcoming appointments
    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date >= today
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).limit(6).all()

    # Status distribution dictionary for visual bars/charts
    status_counts = {
        'Submitted': Application.query.filter_by(status='Submitted').count(),
        'Under Verification': Application.query.filter_by(status='Under Verification').count(),
        'Approved': approved_count,
        'Printed': Application.query.filter_by(status='Printed').count(),
        'Dispatched': dispatched_count,
        'Returned for Correction': Application.query.filter_by(status='Returned for Correction').count(),
        'Rejected': rejected_count
    }

    return render_template(
        'admin/dashboard.html',
        total_applicants=total_applicants,
        total_applications=total_applications,
        pending_verification=pending_verification,
        approved_count=approved_count,
        rejected_count=rejected_count,
        dispatched_count=dispatched_count,
        today_appointments=today_appointments,
        urgent_applications=urgent_applications,
        upcoming_appointments=upcoming_appointments,
        status_counts=status_counts
    )

@officer_bp.route('/applications')
@login_required
@role_required('officer', 'admin')
def applications():
    status_filter = request.args.get('status', '')
    query_text = request.args.get('q', '').strip()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = Application.query

    if status_filter:
        query = query.filter(Application.status == status_filter)
    
    if query_text:
        query = query.filter(
            db.or_(
                Application.application_number.ilike(f'%{query_text}%'),
                Application.full_name.ilike(f'%{query_text}%'),
                Application.email.ilike(f'%{query_text}%'),
                Application.mobile_number.ilike(f'%{query_text}%')
            )
        )

    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Application.created_at >= d_from)
        except ValueError:
            pass

    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Application.created_at <= d_to)
        except ValueError:
            pass

    applications_list = query.order_by(Application.created_at.desc()).all()

    return render_template(
        'admin/applications.html',
        applications=applications_list,
        status_filter=status_filter,
        query_text=query_text,
        date_from=date_from,
        date_to=date_to
    )

@officer_bp.route('/applications/<int:app_id>')
@login_required
@role_required('officer', 'admin')
def application_details(app_id):
    application = Application.query.get_or_404(app_id)
    documents = Document.query.filter_by(application_id=application.id).all()
    appointment = Appointment.query.filter_by(application_id=application.id).first()
    history = ApplicationStatusHistory.query.filter_by(application_id=application.id).order_by(ApplicationStatusHistory.created_at.desc()).all()
    verification_records = VerificationRecord.query.filter_by(application_id=application.id).order_by(VerificationRecord.action_date.desc()).all()

    return render_template(
        'admin/application_details.html',
        app=application,
        documents=documents,
        appointment=appointment,
        history=history,
        verification_records=verification_records
    )

@officer_bp.route('/applications/<int:app_id>/verify')
@login_required
@role_required('officer', 'admin')
def verification(app_id):
    application = Application.query.get_or_404(app_id)
    documents = Document.query.filter_by(application_id=application.id).all()
    appointment = Appointment.query.filter_by(application_id=application.id).first()
    history = ApplicationStatusHistory.query.filter_by(application_id=application.id).order_by(ApplicationStatusHistory.created_at.desc()).all()

    return render_template(
        'admin/verification.html',
        app=application,
        documents=documents,
        appointment=appointment,
        history=history
    )

@officer_bp.route('/applications/<int:app_id>/verify-document', methods=['POST'])
@login_required
@role_required('officer', 'admin')
def verify_document(app_id):
    doc_id = request.form.get('doc_id')
    status = request.form.get('status')  # 'Verified' or 'Rejected'
    reason = request.form.get('reason')

    success, msg = ApplicationService.verify_document(
        document_id=int(doc_id),
        officer_id=session['user_id'],
        status=status,
        rejection_reason=reason
    )

    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    return redirect(url_for('officer.verification', app_id=app_id))

@officer_bp.route('/applications/<int:app_id>/action', methods=['POST'])
@login_required
@role_required('officer', 'admin')
def application_action(app_id):
    application = Application.query.get_or_404(app_id)
    action = request.form.get('action')  # 'Approve', 'Reject', 'Return'
    remarks = request.form.get('remarks', '').strip()
    reason = request.form.get('reason', '').strip()

    officer_id = session['user_id']

    if action == 'Approve':
        # Enforce requirement: check that mandatory documents are verified
        if not application.has_all_mandatory_docs_verified:
            flash('Cannot approve application: All required documents (Identity Proof, Address Proof, Photograph) must be verified before approval.', 'danger')
            return redirect(url_for('officer.verification', app_id=app_id))

        new_status = 'Approved'
        v_record = VerificationRecord(
            application_id=application.id,
            officer_id=officer_id,
            action='Approved',
            remarks=remarks or 'Application verified and approved by officer.',
            reason=None
        )
        db.session.add(v_record)
        ApplicationService.change_status(
            application=application,
            new_status=new_status,
            updated_by_user_id=officer_id,
            remarks=remarks or 'Application approved.'
        )
        flash(f'Application {application.application_number} has been APPROVED successfully.', 'success')

    elif action == 'Reject':
        if not reason:
            flash('A specific reason is mandatory when rejecting an application.', 'danger')
            return redirect(url_for('officer.verification', app_id=app_id))

        new_status = 'Rejected'
        v_record = VerificationRecord(
            application_id=application.id,
            officer_id=officer_id,
            action='Rejected',
            remarks=remarks,
            reason=reason
        )
        db.session.add(v_record)
        ApplicationService.change_status(
            application=application,
            new_status=new_status,
            updated_by_user_id=officer_id,
            remarks=f"Rejected: {reason}. {remarks}".strip()
        )
        flash(f'Application {application.application_number} has been REJECTED.', 'warning')

    elif action == 'Return':
        if not reason:
            flash('A specific reason is mandatory when returning an application for correction.', 'danger')
            return redirect(url_for('officer.verification', app_id=app_id))

        new_status = 'Returned for Correction'
        v_record = VerificationRecord(
            application_id=application.id,
            officer_id=officer_id,
            action='Returned for Correction',
            remarks=remarks,
            reason=reason
        )
        db.session.add(v_record)
        ApplicationService.change_status(
            application=application,
            new_status=new_status,
            updated_by_user_id=officer_id,
            remarks=f"Returned for correction: {reason}. {remarks}".strip()
        )
        flash(f'Application {application.application_number} has been RETURNED FOR CORRECTION.', 'info')

    return redirect(url_for('officer.applications'))

@officer_bp.route('/appointments')
@login_required
@role_required('officer', 'admin')
def appointments():
    date_filter = request.args.get('date', '')
    status_filter = request.args.get('status', '')

    query = Appointment.query

    if date_filter:
        try:
            d_val = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(appointment_date=d_val)
        except ValueError:
            pass

    if status_filter:
        query = query.filter_by(status=status_filter)

    appointments_list = query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    return render_template(
        'admin/appointments.html',
        appointments=appointments_list,
        date_filter=date_filter,
        status_filter=status_filter
    )

@officer_bp.route('/slots', methods=['GET', 'POST'])
@login_required
@role_required('officer', 'admin')
def slots():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'toggle_status':
            slot_id = request.form.get('slot_id')
            slot = AppointmentSlot.query.get_or_404(slot_id)
            slot.is_active = not slot.is_active
            db.session.commit()
            status_text = 'activated' if slot.is_active else 'disabled'
            flash(f'Appointment slot on {slot.slot_date} ({slot.formatted_time}) {status_text}.', 'info')
            return redirect(url_for('officer.slots'))

        elif action == 'create':
            slot_date_str = request.form.get('slot_date')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            capacity = request.form.get('max_capacity', 5)
            location = request.form.get('location', 'Passport Seva Kendra - Central Branch')

            try:
                s_date = datetime.strptime(slot_date_str, '%Y-%m-%d').date()
                s_time = datetime.strptime(start_time_str, '%H:%M').time()
                e_time = datetime.strptime(end_time_str, '%H:%M').time()

                # Check unique slot constraint
                existing = AppointmentSlot.query.filter_by(
                    slot_date=s_date,
                    start_time=s_time,
                    end_time=e_time
                ).first()

                if existing:
                    flash('A slot already exists for this exact date and time.', 'warning')
                else:
                    new_slot = AppointmentSlot(
                        slot_date=s_date,
                        start_time=s_time,
                        end_time=e_time,
                        max_capacity=int(capacity),
                        booked_count=0,
                        location=location.strip(),
                        is_active=True
                    )
                    db.session.add(new_slot)
                    db.session.commit()
                    flash('New appointment slot created successfully.', 'success')

            except Exception as e:
                db.session.rollback()
                flash(f'Error creating slot: {str(e)}', 'danger')

            return redirect(url_for('officer.slots'))

    # List all slots ordered by date
    all_slots = AppointmentSlot.query.order_by(AppointmentSlot.slot_date.asc(), AppointmentSlot.start_time.asc()).all()
    return render_template('admin/slots.html', slots=all_slots)

@officer_bp.route('/applicants')
@login_required
@role_required('officer', 'admin')
def applicants():
    q = request.args.get('q', '').strip()
    query = Applicant.query.join(User)

    if q:
        query = query.filter(
            db.or_(
                User.full_name.ilike(f'%{q}%'),
                User.email.ilike(f'%{q}%'),
                User.mobile_number.ilike(f'%{q}%'),
                Applicant.city.ilike(f'%{q}%')
            )
        )

    applicants_list = query.all()
    return render_template('admin/applicants.html', applicants=applicants_list, q=q)

@officer_bp.route('/status-management', methods=['GET', 'POST'])
@login_required
@role_required('officer', 'admin')
def status_management():
    if request.method == 'POST':
        app_id = request.form.get('application_id')
        new_status = request.form.get('new_status')
        remarks = request.form.get('remarks', '').strip()

        application = Application.query.get_or_404(app_id)
        if application.status == 'Draft':
            flash('Cannot update status of a Draft application.', 'danger')
            return redirect(url_for('officer.status_management'))

        ApplicationService.change_status(
            application=application,
            new_status=new_status,
            updated_by_user_id=session['user_id'],
            remarks=remarks or f'Status updated to {new_status} by officer.'
        )
        flash(f'Application {application.application_number} status updated to {new_status}.', 'success')
        return redirect(url_for('officer.status_management'))

    # Load submitted & active applications
    applications_list = Application.query.filter(Application.status != 'Draft').order_by(Application.updated_at.desc()).all()
    all_statuses = ['Submitted', 'Under Verification', 'Approved', 'Printed', 'Dispatched', 'Returned for Correction', 'Rejected']

    return render_template('admin/status_management.html', applications=applications_list, statuses=all_statuses)

@officer_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
@role_required('officer', 'admin')
def notifications_mgmt():
    if request.method == 'POST':
        recipient_type = request.form.get('recipient_type')  # 'all' or specific user_id
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        notif_type = request.form.get('type', 'info')

        if not title or not message:
            flash('Title and message are required.', 'danger')
            return redirect(url_for('officer.notifications_mgmt'))

        if recipient_type == 'all':
            # Broadcast to all applicants
            applicant_users = User.query.filter_by(role='applicant').all()
            for u in applicant_users:
                NotificationService.send(u.id, title, message, notif_type)
            flash(f'Broadcast notification sent to {len(applicant_users)} applicants.', 'success')
        else:
            try:
                u_id = int(recipient_type)
                NotificationService.send(u_id, title, message, notif_type)
                flash('Notification sent to selected user.', 'success')
            except ValueError:
                flash('Invalid recipient selected.', 'danger')

        return redirect(url_for('officer.notifications_mgmt'))

    recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(20).all()
    applicant_users = User.query.filter_by(role='applicant').all()
    return render_template('admin/notifications_mgmt.html', notifications=recent_notifications, applicants=applicant_users)

@officer_bp.route('/reports')
@login_required
@role_required('officer', 'admin')
def reports():
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = Application.query.filter(Application.status != 'Draft')

    if date_from:
        try:
            d_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Application.created_at >= d_from)
        except ValueError:
            pass

    if date_to:
        try:
            d_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Application.created_at <= d_to)
        except ValueError:
            pass

    applications_list = query.all()

    # Aggregate counts
    status_summary = {
        'Submitted': sum(1 for a in applications_list if a.status == 'Submitted'),
        'Under Verification': sum(1 for a in applications_list if a.status == 'Under Verification'),
        'Approved': sum(1 for a in applications_list if a.status == 'Approved'),
        'Printed': sum(1 for a in applications_list if a.status == 'Printed'),
        'Dispatched': sum(1 for a in applications_list if a.status == 'Dispatched'),
        'Returned for Correction': sum(1 for a in applications_list if a.status == 'Returned for Correction'),
        'Rejected': sum(1 for a in applications_list if a.status == 'Rejected')
    }

    type_summary = {
        'Normal': sum(1 for a in applications_list if a.application_type == 'Normal'),
        'Tatkaal': sum(1 for a in applications_list if a.application_type == 'Tatkaal')
    }

    service_summary = {
        'Fresh': sum(1 for a in applications_list if a.service_type == 'Fresh'),
        'Renewal': sum(1 for a in applications_list if a.service_type == 'Renewal')
    }

    total_appointments = Appointment.query.count()
    completed_appointments = Appointment.query.filter_by(status='Completed').count()

    return render_template(
        'admin/reports.html',
        applications=applications_list,
        total_count=len(applications_list),
        status_summary=status_summary,
        type_summary=type_summary,
        service_summary=service_summary,
        total_appointments=total_appointments,
        completed_appointments=completed_appointments,
        date_from=date_from,
        date_to=date_to
    )

@officer_bp.route('/reports/export-csv')
@login_required
@role_required('officer', 'admin')
def export_csv():
    applications_list = Application.query.filter(Application.status != 'Draft').order_by(Application.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Application Number', 'Applicant Name', 'Email', 'Mobile',
        'Application Type', 'Service Type', 'Booklet Type',
        'Status', 'Submission Date', 'Appointment Date', 'Location'
    ])

    for a in applications_list:
        apt_date = a.appointment.appointment_date.strftime('%Y-%m-%d') if a.appointment else 'Not Scheduled'
        apt_loc = a.appointment.location if a.appointment else 'N/A'
        sub_date = a.submitted_at.strftime('%Y-%m-%d %H:%M') if a.submitted_at else 'N/A'

        writer.writerow([
            a.application_number,
            a.full_name,
            a.email,
            a.mobile_number,
            a.application_type,
            a.service_type,
            a.booklet_type,
            a.status,
            sub_date,
            apt_date,
            apt_loc
        ])

    output.seek(0)
    filename = f"passport_applications_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@officer_bp.route('/profile')
@login_required
@role_required('officer', 'admin')
def profile():
    user = User.query.get(session['user_id'])
    return render_template('admin/profile.html', user=user)
