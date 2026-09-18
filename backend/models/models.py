from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database.db import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='applicant', index=True)  # applicant, officer, admin
    full_name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applicant = db.relationship('Applicant', back_populates='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='user', cascade='all, delete-orphan')
    verification_records = db.relationship('VerificationRecord', back_populates='officer')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'mobile_number': self.mobile_number,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Applicant(db.Model):
    __tablename__ = 'applicants'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # Male, Female, Other
    address_line = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    country = db.Column(db.String(50), default='India')

    # Relationships
    user = db.relationship('User', back_populates='applicant')
    applications = db.relationship('Application', back_populates='applicant', cascade='all, delete-orphan')


class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    application_number = db.Column(db.String(30), unique=True, nullable=True, index=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicants.id', ondelete='CASCADE'), nullable=False)
    
    # Status: Draft, Submitted, Under Verification, Approved, Printed, Dispatched, Rejected, Returned for Correction
    status = db.Column(db.String(30), default='Draft', nullable=False, index=True)
    
    # Application Config
    application_type = db.Column(db.String(20), default='Normal', nullable=False)  # Normal, Tatkaal
    service_type = db.Column(db.String(20), default='Fresh', nullable=False)        # Fresh, Renewal
    booklet_type = db.Column(db.String(20), default='36 Pages', nullable=False)     # 36 Pages, 60 Pages
    previous_passport_number = db.Column(db.String(20), nullable=True)

    # Step 1: Personal Details
    full_name = db.Column(db.String(100), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    place_of_birth = db.Column(db.String(100), nullable=True)
    nationality = db.Column(db.String(50), default='Indian')
    marital_status = db.Column(db.String(30), nullable=True)

    # Step 2: Contact Details
    mobile_number = db.Column(db.String(15), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    alternate_contact = db.Column(db.String(15), nullable=True)

    # Step 3: Address Details
    house_no = db.Column(db.String(50), nullable=True)
    street = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    country = db.Column(db.String(50), default='India')

    # Step 5: Declaration
    declaration_accepted = db.Column(db.Boolean, default=False)
    current_step = db.Column(db.Integer, default=1)  # 1 to 5

    submitted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applicant = db.relationship('Applicant', back_populates='applications')
    documents = db.relationship('Document', back_populates='application', cascade='all, delete-orphan')
    appointment = db.relationship('Appointment', back_populates='application', uselist=False, cascade='all, delete-orphan')
    verification_records = db.relationship('VerificationRecord', back_populates='application', cascade='all, delete-orphan', order_by='VerificationRecord.action_date.desc()')
    status_history = db.relationship('ApplicationStatusHistory', back_populates='application', cascade='all, delete-orphan', order_by='ApplicationStatusHistory.created_at.desc()')
    notifications = db.relationship('Notification', back_populates='application')

    @property
    def is_draft(self):
        return self.status == 'Draft'

    @property
    def has_all_mandatory_docs_verified(self):
        """Mandatory categories: Identity Proof, Address Proof, Photograph"""
        verified_types = {d.doc_type for d in self.documents if d.verification_status == 'Verified'}
        required = {'Identity Proof', 'Address Proof', 'Photograph'}
        return required.issubset(verified_types)


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False, index=True)
    doc_type = db.Column(db.String(50), nullable=False)  # Identity Proof, Address Proof, DOB Proof, Photograph, Signature, Other
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    verification_status = db.Column(db.String(20), default='Pending', nullable=False)  # Pending, Verified, Rejected
    rejection_reason = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship('Application', back_populates='documents')

    @property
    def is_image(self):
        return self.mime_type.startswith('image/')

    @property
    def formatted_size(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class AppointmentSlot(db.Model):
    __tablename__ = 'appointment_slots'

    id = db.Column(db.Integer, primary_key=True)
    slot_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_capacity = db.Column(db.Integer, default=5, nullable=False)
    booked_count = db.Column(db.Integer, default=0, nullable=False)
    location = db.Column(db.String(150), default='Passport Seva Kendra - Central Branch', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', back_populates='slot')

    @property
    def is_full(self):
        return self.booked_count >= self.max_capacity

    @property
    def available_seats(self):
        return max(0, self.max_capacity - self.booked_count)

    @property
    def formatted_time(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id', ondelete='CASCADE'), unique=True, nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('appointment_slots.id'), nullable=False)
    appointment_number = db.Column(db.String(30), unique=True, nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(20), default='Scheduled', nullable=False)  # Scheduled, Completed, Cancelled
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship('Application', back_populates='appointment')
    slot = db.relationship('AppointmentSlot', back_populates='appointments')


class VerificationRecord(db.Model):
    __tablename__ = 'verification_records'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(30), nullable=False)  # Verified, Approved, Rejected, Returned for Correction
    remarks = db.Column(db.Text, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    action_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship('Application', back_populates='verification_records')
    officer = db.relationship('User', back_populates='verification_records')


class ApplicationStatusHistory(db.Model):
    __tablename__ = 'application_status_history'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id', ondelete='CASCADE'), nullable=False)
    previous_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    application = db.relationship('Application', back_populates='status_history')
    updater = db.relationship('User')


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info', nullable=False)  # info, success, warning, danger
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='notifications')
    application = db.relationship('Application', back_populates='notifications')
