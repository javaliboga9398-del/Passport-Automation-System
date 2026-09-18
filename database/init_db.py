import os
import sys
from pathlib import Path
from datetime import datetime, date, time, timedelta

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import Config
from backend.database.db import db
from backend.models.models import (
    User, Applicant, Application, Document,
    AppointmentSlot, Appointment, VerificationRecord,
    ApplicationStatusHistory, Notification
)
from flask import Flask

def create_sample_files(upload_dir):
    """Create lightweight dummy files for pre-seeded demo documents."""
    os.makedirs(upload_dir, exist_ok=True)
    
    sample_files = {
        'demo_aadhaar_01.pdf': b'%PDF-1.4 demo identity proof content (Aadhaar Card)',
        'demo_bill_01.pdf': b'%PDF-1.4 demo address proof content (Utility Bill)',
        'demo_photo_01.jpg': b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x10\x00\x10\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9',
        'demo_pan_02.pdf': b'%PDF-1.4 demo identity proof content (PAN Card)',
        'demo_voter_02.pdf': b'%PDF-1.4 demo address proof content (Voter ID)',
        'demo_aadhaar_03.pdf': b'%PDF-1.4 demo identity proof content (Aadhaar Card)',
        'demo_statement_03.pdf': b'%PDF-1.4 demo address proof content (Bank Statement)',
        'demo_rent_05.pdf': b'%PDF-1.4 demo address proof content (Expired Rent Agreement)'
    }
    
    for filename, content in sample_files.items():
        filepath = Path(upload_dir) / filename
        if not filepath.exists():
            with open(filepath, 'wb') as f:
                f.write(content)

def init_database(app):
    with app.app_context():
        # Create all tables defined in models
        print("[Init DB] Creating database tables...")
        db.create_all()

        # Check if users already seeded
        if User.query.first():
            print("[Init DB] Database already contains records. Skipping seed.")
            return

        print("[Init DB] Seeding initial users and demonstration records...")
        
        # 1. Users
        admin = User(
            email='admin@passport.gov',
            role='admin',
            full_name='System Administrator',
            mobile_number='9876543210'
        )
        admin.set_password('Admin@123')

        officer = User(
            email='officer@passport.gov',
            role='officer',
            full_name='Senior Verification Officer',
            mobile_number='9876543211'
        )
        officer.set_password('Officer@123')

        applicant_1 = User(
            email='rajesh.sharma@example.com',
            role='applicant',
            full_name='Rajesh Sharma',
            mobile_number='9811122233'
        )
        applicant_1.set_password('Applicant@123')

        applicant_2 = User(
            email='priya.patel@example.com',
            role='applicant',
            full_name='Priya Patel',
            mobile_number='9822233344'
        )
        applicant_2.set_password('Applicant@123')

        applicant_3 = User(
            email='arun.kumar@example.com',
            role='applicant',
            full_name='Arun Kumar',
            mobile_number='9833344455'
        )
        applicant_3.set_password('Applicant@123')

        db.session.add_all([admin, officer, applicant_1, applicant_2, applicant_3])
        db.session.commit()

        # 2. Applicant Profiles
        app_profile_1 = Applicant(
            user_id=applicant_1.id,
            date_of_birth=date(1995, 4, 12),
            gender='Male',
            address_line='Flat 402, Greenfield Apartments, M.G. Road',
            city='Bengaluru',
            district='Bengaluru Urban',
            state='Karnataka',
            pincode='560001',
            country='India'
        )

        app_profile_2 = Applicant(
            user_id=applicant_2.id,
            date_of_birth=date(1998, 8, 25),
            gender='Female',
            address_line='Plot 15, Vasant Vihar Phase 2',
            city='Ahmedabad',
            district='Ahmedabad',
            state='Gujarat',
            pincode='380015',
            country='India'
        )

        app_profile_3 = Applicant(
            user_id=applicant_3.id,
            date_of_birth=date(1992, 11, 3),
            gender='Male',
            address_line='House 78, Sector 14',
            city='Gurugram',
            district='Gurugram',
            state='Haryana',
            pincode='122001',
            country='India'
        )

        db.session.add_all([app_profile_1, app_profile_2, app_profile_3])
        db.session.commit()

        # 3. Appointment Slots (today and next 7 days)
        today = date.today()
        slots_list = []
        for d_offset in range(1, 8):
            slot_date = today + timedelta(days=d_offset)
            # Skip Sunday (6)
            if slot_date.weekday() == 6:
                continue
            
            times = [
                (time(9, 0), time(10, 0)),
                (time(10, 30), time(11, 30)),
                (time(12, 0), time(13, 0)),
                (time(14, 0), time(15, 0)),
                (time(15, 30), time(16, 30)),
            ]
            for st, et in times:
                s = AppointmentSlot(
                    slot_date=slot_date,
                    start_time=st,
                    end_time=et,
                    max_capacity=5,
                    booked_count=0,
                    location='Passport Seva Kendra - Central City Branch',
                    is_active=True
                )
                slots_list.append(s)

        db.session.add_all(slots_list)
        db.session.commit()

        # 4. Sample Applications across different statuses
        app1 = Application(
            application_number='PAS202600001',
            applicant_id=app_profile_1.id,
            status='Approved',
            application_type='Normal',
            service_type='Fresh',
            booklet_type='36 Pages',
            full_name='Rajesh Sharma',
            date_of_birth=date(1995, 4, 12),
            gender='Male',
            place_of_birth='Bengaluru',
            nationality='Indian',
            marital_status='Single',
            mobile_number='9811122233',
            email='rajesh.sharma@example.com',
            house_no='Flat 402',
            street='Greenfield Apartments, M.G. Road',
            city='Bengaluru',
            district='Bengaluru Urban',
            state='Karnataka',
            pincode='560001',
            country='India',
            declaration_accepted=True,
            current_step=5,
            submitted_at=datetime.utcnow() - timedelta(days=5),
            created_at=datetime.utcnow() - timedelta(days=6)
        )

        app2 = Application(
            application_number='PAS202600002',
            applicant_id=app_profile_2.id,
            status='Submitted',
            application_type='Tatkaal',
            service_type='Fresh',
            booklet_type='36 Pages',
            full_name='Priya Patel',
            date_of_birth=date(1998, 8, 25),
            gender='Female',
            place_of_birth='Ahmedabad',
            nationality='Indian',
            marital_status='Single',
            mobile_number='9822233344',
            email='priya.patel@example.com',
            house_no='Plot 15',
            street='Vasant Vihar Phase 2',
            city='Ahmedabad',
            district='Ahmedabad',
            state='Gujarat',
            pincode='380015',
            country='India',
            declaration_accepted=True,
            current_step=5,
            submitted_at=datetime.utcnow() - timedelta(days=2),
            created_at=datetime.utcnow() - timedelta(days=3)
        )

        app3 = Application(
            application_number='PAS202600003',
            applicant_id=app_profile_3.id,
            status='Under Verification',
            application_type='Normal',
            service_type='Renewal',
            booklet_type='60 Pages',
            previous_passport_number='Z1098273',
            full_name='Arun Kumar',
            date_of_birth=date(1992, 11, 3),
            gender='Male',
            place_of_birth='Gurugram',
            nationality='Indian',
            marital_status='Married',
            mobile_number='9833344455',
            email='arun.kumar@example.com',
            house_no='House 78',
            street='Sector 14',
            city='Gurugram',
            district='Gurugram',
            state='Haryana',
            pincode='122001',
            country='India',
            declaration_accepted=True,
            current_step=5,
            submitted_at=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow() - timedelta(days=2)
        )

        app4 = Application(
            application_number='PAS202600004',
            applicant_id=app_profile_1.id,
            status='Dispatched',
            application_type='Normal',
            service_type='Renewal',
            booklet_type='36 Pages',
            previous_passport_number='K8827164',
            full_name='Rajesh Sharma',
            date_of_birth=date(1995, 4, 12),
            gender='Male',
            place_of_birth='Bengaluru',
            nationality='Indian',
            marital_status='Single',
            mobile_number='9811122233',
            email='rajesh.sharma@example.com',
            house_no='Flat 402',
            street='Greenfield Apartments, M.G. Road',
            city='Bengaluru',
            district='Bengaluru Urban',
            state='Karnataka',
            pincode='560001',
            country='India',
            declaration_accepted=True,
            current_step=5,
            submitted_at=datetime.utcnow() - timedelta(days=15),
            created_at=datetime.utcnow() - timedelta(days=16)
        )

        app5 = Application(
            application_number='PAS202600005',
            applicant_id=app_profile_2.id,
            status='Returned for Correction',
            application_type='Normal',
            service_type='Fresh',
            booklet_type='36 Pages',
            full_name='Priya Patel',
            date_of_birth=date(1998, 8, 25),
            gender='Female',
            place_of_birth='Ahmedabad',
            nationality='Indian',
            marital_status='Single',
            mobile_number='9822233344',
            email='priya.patel@example.com',
            house_no='Plot 15',
            street='Vasant Vihar Phase 2',
            city='Ahmedabad',
            district='Ahmedabad',
            state='Gujarat',
            pincode='380015',
            country='India',
            declaration_accepted=True,
            current_step=5,
            submitted_at=datetime.utcnow() - timedelta(days=4),
            created_at=datetime.utcnow() - timedelta(days=5)
        )

        app6 = Application(
            application_number=None,
            applicant_id=app_profile_3.id,
            status='Draft',
            application_type='Normal',
            service_type='Fresh',
            booklet_type='36 Pages',
            full_name='Arun Kumar',
            date_of_birth=date(1992, 11, 3),
            gender='Male',
            place_of_birth='Gurugram',
            nationality='Indian',
            marital_status='Married',
            mobile_number='9833344455',
            email='arun.kumar@example.com',
            house_no='House 78',
            street='Sector 14',
            city='Gurugram',
            district='Gurugram',
            state='Haryana',
            pincode='122001',
            country='India',
            declaration_accepted=False,
            current_step=3,
            submitted_at=None,
            created_at=datetime.utcnow()
        )

        db.session.add_all([app1, app2, app3, app4, app5, app6])
        db.session.commit()

        # 5. Documents for seeded applications
        doc1 = Document(
            application_id=app1.id,
            doc_type='Identity Proof',
            original_filename='aadhaar_card.pdf',
            stored_filename='demo_aadhaar_01.pdf',
            file_path='uploads/documents/demo_aadhaar_01.pdf',
            file_size=245120,
            mime_type='application/pdf',
            verification_status='Verified'
        )
        doc2 = Document(
            application_id=app1.id,
            doc_type='Address Proof',
            original_filename='utility_bill.pdf',
            stored_filename='demo_bill_01.pdf',
            file_path='uploads/documents/demo_bill_01.pdf',
            file_size=189400,
            mime_type='application/pdf',
            verification_status='Verified'
        )
        doc3 = Document(
            application_id=app1.id,
            doc_type='Photograph',
            original_filename='passport_photo.jpg',
            stored_filename='demo_photo_01.jpg',
            file_path='uploads/documents/demo_photo_01.jpg',
            file_size=84200,
            mime_type='image/jpeg',
            verification_status='Verified'
        )
        doc4 = Document(
            application_id=app2.id,
            doc_type='Identity Proof',
            original_filename='pan_card.pdf',
            stored_filename='demo_pan_02.pdf',
            file_path='uploads/documents/demo_pan_02.pdf',
            file_size=154000,
            mime_type='application/pdf',
            verification_status='Pending'
        )
        doc5 = Document(
            application_id=app2.id,
            doc_type='Address Proof',
            original_filename='voter_id.pdf',
            stored_filename='demo_voter_02.pdf',
            file_path='uploads/documents/demo_voter_02.pdf',
            file_size=210000,
            mime_type='application/pdf',
            verification_status='Pending'
        )
        doc6 = Document(
            application_id=app3.id,
            doc_type='Identity Proof',
            original_filename='aadhaar_card.pdf',
            stored_filename='demo_aadhaar_03.pdf',
            file_path='uploads/documents/demo_aadhaar_03.pdf',
            file_size=230000,
            mime_type='application/pdf',
            verification_status='Verified'
        )
        doc7 = Document(
            application_id=app3.id,
            doc_type='Address Proof',
            original_filename='bank_statement.pdf',
            stored_filename='demo_statement_03.pdf',
            file_path='uploads/documents/demo_statement_03.pdf',
            file_size=310000,
            mime_type='application/pdf',
            verification_status='Pending'
        )
        doc8 = Document(
            application_id=app5.id,
            doc_type='Address Proof',
            original_filename='rent_agreement.pdf',
            stored_filename='demo_rent_05.pdf',
            file_path='uploads/documents/demo_rent_05.pdf',
            file_size=420000,
            mime_type='application/pdf',
            verification_status='Rejected',
            rejection_reason='Document expired. Please upload an active utility bill or registered rent agreement.'
        )

        db.session.add_all([doc1, doc2, doc3, doc4, doc5, doc6, doc7, doc8])
        db.session.commit()

        # 6. Book an appointment for app1 and app2
        first_slot = AppointmentSlot.query.first()
        if first_slot:
            first_slot.booked_count = 2
            apt1 = Appointment(
                application_id=app1.id,
                slot_id=first_slot.id,
                appointment_number='APT202600001',
                appointment_date=first_slot.slot_date,
                appointment_time=first_slot.formatted_time,
                location=first_slot.location,
                status='Completed'
            )
            apt2 = Appointment(
                application_id=app2.id,
                slot_id=first_slot.id,
                appointment_number='APT202600002',
                appointment_date=first_slot.slot_date,
                appointment_time=first_slot.formatted_time,
                location=first_slot.location,
                status='Scheduled'
            )
            db.session.add_all([apt1, apt2])
            db.session.commit()

        # 7. Verification Records & Status History
        vr1 = VerificationRecord(
            application_id=app1.id,
            officer_id=officer.id,
            action='Verified',
            remarks='All physical and digital documents matched successfully.'
        )
        vr2 = VerificationRecord(
            application_id=app1.id,
            officer_id=officer.id,
            action='Approved',
            remarks='Passport application approved by Senior Officer.'
        )
        vr3 = VerificationRecord(
            application_id=app5.id,
            officer_id=officer.id,
            action='Returned for Correction',
            remarks='Address proof expired. Need updated utility bill.',
            reason='Expired document provided for address verification.'
        )
        db.session.add_all([vr1, vr2, vr3])

        sh1 = ApplicationStatusHistory(
            application_id=app1.id,
            previous_status='Draft',
            new_status='Submitted',
            updated_by=applicant_1.id,
            remarks='Application submitted by applicant.'
        )
        sh2 = ApplicationStatusHistory(
            application_id=app1.id,
            previous_status='Submitted',
            new_status='Under Verification',
            updated_by=officer.id,
            remarks='Officer initiated document review.'
        )
        sh3 = ApplicationStatusHistory(
            application_id=app1.id,
            previous_status='Under Verification',
            new_status='Approved',
            updated_by=officer.id,
            remarks='Application approved.'
        )
        sh4 = ApplicationStatusHistory(
            application_id=app4.id,
            previous_status='Approved',
            new_status='Printed',
            updated_by=admin.id,
            remarks='Passport booklet printed.'
        )
        sh5 = ApplicationStatusHistory(
            application_id=app4.id,
            previous_status='Printed',
            new_status='Dispatched',
            updated_by=admin.id,
            remarks='Dispatched via Speed Post Track #SP9928172IN.'
        )
        sh6 = ApplicationStatusHistory(
            application_id=app5.id,
            previous_status='Submitted',
            new_status='Returned for Correction',
            updated_by=officer.id,
            remarks='Document re-upload requested.'
        )
        db.session.add_all([sh1, sh2, sh3, sh4, sh5, sh6])

        # 8. Notifications
        n1 = Notification(
            user_id=applicant_1.id,
            application_id=app1.id,
            title='Application Approved',
            message='Congratulations! Your Passport Application PAS202600001 has been approved by the Passport Office.',
            type='success',
            is_read=False
        )
        n2 = Notification(
            user_id=applicant_2.id,
            application_id=app2.id,
            title='Appointment Confirmed',
            message=f'Your appointment for PAS202600002 is confirmed for {first_slot.slot_date} ({first_slot.formatted_time}).',
            type='info',
            is_read=False
        )
        n3 = Notification(
            user_id=applicant_2.id,
            application_id=app5.id,
            title='Application Returned for Correction',
            message='Your application PAS202600005 requires correction. Reason: Expired address proof document.',
            type='warning',
            is_read=False
        )
        db.session.add_all([n1, n2, n3])
        db.session.commit()

        # Create sample files in upload directory
        create_sample_files(Config.UPLOAD_FOLDER)

        print("[Init DB] Initialization & demo seeding completed successfully!")

if __name__ == '__main__':
    from backend.app import create_app
    app = create_app()
    init_database(app)
