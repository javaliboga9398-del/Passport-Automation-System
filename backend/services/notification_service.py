from backend.database.db import db
from backend.models.models import Notification

class NotificationService:
    @staticmethod
    def send(user_id, title, message, notif_type='info', application_id=None):
        """Creates and commits a new notification for a specific user."""
        try:
            notif = Notification(
                user_id=user_id,
                application_id=application_id,
                title=title,
                message=message,
                type=notif_type,
                is_read=False
            )
            db.session.add(notif)
            db.session.commit()
            return notif
        except Exception as e:
            db.session.rollback()
            print(f"[Notification Error] Failed to send notification to user {user_id}: {e}")
            return None

    @classmethod
    def notify_submission(cls, application):
        user_id = application.applicant.user_id
        return cls.send(
            user_id=user_id,
            title='Application Submitted Successfully',
            message=f'Your Passport Application {application.application_number} has been submitted. Please schedule an appointment.',
            notif_type='success',
            application_id=application.id
        )

    @classmethod
    def notify_appointment(cls, appointment):
        user_id = appointment.application.applicant.user_id
        return cls.send(
            user_id=user_id,
            title='Appointment Confirmed',
            message=f'Your appointment (Ref: {appointment.appointment_number}) for {appointment.application.application_number} is confirmed on {appointment.appointment_date} ({appointment.appointment_time}) at {appointment.location}.',
            notif_type='info',
            application_id=appointment.application_id
        )

    @classmethod
    def notify_status_update(cls, application, previous_status, new_status, remarks=None):
        user_id = application.applicant.user_id
        type_map = {
            'Under Verification': 'info',
            'Approved': 'success',
            'Printed': 'info',
            'Dispatched': 'success',
            'Rejected': 'danger',
            'Returned for Correction': 'warning'
        }
        notif_type = type_map.get(new_status, 'info')
        
        detail_msg = f" Remarks: {remarks}" if remarks else ""
        message = f"Your Application {application.application_number} status has been updated from '{previous_status}' to '{new_status}'.{detail_msg}"
        
        return cls.send(
            user_id=user_id,
            title=f"Application Status: {new_status}",
            message=message,
            notif_type=notif_type,
            application_id=application.id
        )
