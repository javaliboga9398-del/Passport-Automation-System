import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from backend.models.models import Application, Appointment
from backend.utils.validators import allowed_file

def generate_application_number():
    """Generates unique formatted ID: PAS202600001"""
    year = datetime.now().year
    prefix = f"PAS{year}"
    
    last_app = Application.query.filter(
        Application.application_number.like(f"{prefix}%")
    ).order_by(Application.id.desc()).first()
    
    if last_app and last_app.application_number:
        try:
            seq_str = last_app.application_number.replace(prefix, "")
            seq_num = int(seq_str) + 1
        except ValueError:
            seq_num = Application.query.count() + 1
    else:
        seq_num = 1
        
    return f"{prefix}{seq_num:05d}"

def generate_appointment_number():
    """Generates unique formatted ID: APT202600001"""
    year = datetime.now().year
    prefix = f"APT{year}"
    
    last_apt = Appointment.query.filter(
        Appointment.appointment_number.like(f"{prefix}%")
    ).order_by(Appointment.id.desc()).first()
    
    if last_apt and last_apt.appointment_number:
        try:
            seq_str = last_apt.appointment_number.replace(prefix, "")
            seq_num = int(seq_str) + 1
        except ValueError:
            seq_num = Appointment.query.count() + 1
    else:
        seq_num = 1
        
    return f"{prefix}{seq_num:05d}"

def save_uploaded_file(file_storage, upload_folder):
    """
    Saves uploaded file with secure unique UUID filename to prevent collisions and directory traversal.
    Returns: (stored_filename, file_path, file_size, mime_type)
    """
    os.makedirs(upload_folder, exist_ok=True)
    orig_name = secure_filename(file_storage.filename)
    ext = orig_name.rsplit('.', 1)[1].lower() if '.' in orig_name else 'bin'
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    dest_path = os.path.join(upload_folder, stored_name)
    
    file_storage.save(dest_path)
    file_size = os.path.getsize(dest_path)
    mime_type = file_storage.mimetype or 'application/octet-stream'
    
    # Store relative path for portability
    rel_path = f"uploads/documents/{stored_name}"
    return stored_name, rel_path, file_size, mime_type

def get_status_badge(status):
    """Returns CSS class and icon for application status."""
    mapping = {
        'Draft': {'class': 'badge-draft', 'icon': 'fa-pencil-alt', 'color': '#64748b'},
        'Submitted': {'class': 'badge-info', 'icon': 'fa-paper-plane', 'color': '#2563eb'},
        'Under Verification': {'class': 'badge-warning', 'icon': 'fa-search', 'color': '#d97706'},
        'Approved': {'class': 'badge-success', 'icon': 'fa-check-circle', 'color': '#059669'},
        'Printed': {'class': 'badge-primary', 'icon': 'fa-print', 'color': '#4f46e5'},
        'Dispatched': {'class': 'badge-dark', 'icon': 'fa-truck', 'color': '#0284c7'},
        'Rejected': {'class': 'badge-danger', 'icon': 'fa-times-circle', 'color': '#dc2626'},
        'Returned for Correction': {'class': 'badge-warning', 'icon': 'fa-undo', 'color': '#ea580c'}
    }
    return mapping.get(status, {'class': 'badge-secondary', 'icon': 'fa-circle', 'color': '#64748b'})
