from datetime import datetime
from backend.database.db import db
from backend.models.models import (
    Application, Document, AppointmentSlot, Appointment,
    VerificationRecord, ApplicationStatusHistory
)
from backend.services.notification_service import NotificationService
from backend.utils.helpers import generate_appointment_number

class ApplicationService:
    @staticmethod
    def change_status(application, new_status, updated_by_user_id=None, remarks=None):
        """
        Transitions an application to a new status, records an audit log in
        application_status_history, and dispatches an in-app notification.
        """
        prev_status = application.status
        application.status = new_status
        application.updated_at = datetime.utcnow()

        history_entry = ApplicationStatusHistory(
            application_id=application.id,
            previous_status=prev_status,
            new_status=new_status,
            updated_by=updated_by_user_id,
            remarks=remarks
        )
        db.session.add(history_entry)
        db.session.commit()

        # Send notification to applicant
        NotificationService.notify_status_update(
            application=application,
            previous_status=prev_status,
            new_status=new_status,
            remarks=remarks
        )
        return True

    @staticmethod
    def book_appointment(application_id, slot_id):
        """
        Safely books an appointment slot for an application.
        Prevents double-booking and enforces slot capacity limits.
        """
        application = Application.query.get(application_id)
        if not application:
            return False, "Application not found.", None

        if application.status == 'Draft':
            return False, "Cannot book appointment for a draft application. Please submit the application first.", None

        # Check if already booked
        existing_apt = Appointment.query.filter_by(application_id=application_id).first()
        if existing_apt and existing_apt.status == 'Scheduled':
            return False, f"You already have a scheduled appointment (Ref: {existing_apt.appointment_number}).", existing_apt

        slot = AppointmentSlot.query.get(slot_id)
        if not slot or not slot.is_active:
            return False, "Selected appointment slot is no longer active.", None

        # Concurrency/Capacity check
        if slot.booked_count >= slot.max_capacity:
            return False, "This appointment slot is full. Please select a different time slot or date.", None

        try:
            slot.booked_count += 1
            apt_number = generate_appointment_number()
            
            appointment = Appointment(
                application_id=application.id,
                slot_id=slot.id,
                appointment_number=apt_number,
                appointment_date=slot.slot_date,
                appointment_time=slot.formatted_time,
                location=slot.location,
                status='Scheduled'
            )
            db.session.add(appointment)
            db.session.commit()

            NotificationService.notify_appointment(appointment)
            return True, "Appointment booked successfully!", appointment

        except Exception as e:
            db.session.rollback()
            return False, f"Booking failed due to an internal error: {str(e)}", None

    @staticmethod
    def verify_document(document_id, officer_id, status, rejection_reason=None):
        """Officer verifies or rejects an uploaded document."""
        doc = Document.query.get(document_id)
        if not doc:
            return False, "Document not found."

        if status not in ['Verified', 'Rejected']:
            return False, "Invalid verification status."

        if status == 'Rejected' and not (rejection_reason and rejection_reason.strip()):
            return False, "A rejection reason is required when rejecting a document."

        doc.verification_status = status
        doc.rejection_reason = rejection_reason.strip() if status == 'Rejected' else None
        db.session.commit()
        return True, f"Document marked as {status}."
