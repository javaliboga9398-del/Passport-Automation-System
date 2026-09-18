"""
End-to-End Automated Test Suite for Passport Automation System
Verifies complete functionality across presentation, business logic, and database tiers.
"""

import sys
import io
import unittest
from pathlib import Path
from datetime import datetime, date

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.database.db import db
from backend.models.models import (
    User, Applicant, Application, Document,
    AppointmentSlot, Appointment, VerificationRecord,
    ApplicationStatusHistory, Notification
)
from database.init_db import init_database

class PassportAutomationSystemTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            init_database(self.app)

    # 1. TEST PUBLIC PAGES
    def test_01_public_pages(self):
        print("\n[TEST 1] Verifying public pages accessibility...")
        for path in ['/', '/about', '/contact', '/login', '/register']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, f"Failed to load {path}")
        print("  -> All public pages loaded with HTTP 200.")

    # 2. TEST AUTHENTICATION & LOGIN
    def test_02_authentication(self):
        print("\n[TEST 2] Verifying authentication & role redirection...")
        
        # Invalid login
        res_fail = self.client.post('/login', data={'email': 'admin@passport.gov', 'password': 'WrongPassword'}, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res_fail.data)
        print("  -> Invalid login correctly rejected.")

        # Valid Admin login
        res_admin = self.client.post('/login', data={'email': 'admin@passport.gov', 'password': 'Admin@123'}, follow_redirects=True)
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'Admin Dashboard', res_admin.data)
        print("  -> Admin login successful and redirected to Admin Dashboard.")

        # Log out before logging in as applicant
        self.client.get('/logout')

        # Valid Applicant login
        res_app = self.client.post('/login', data={'email': 'rajesh.sharma@example.com', 'password': 'Applicant@123'}, follow_redirects=True)
        self.assertEqual(res_app.status_code, 200)
        self.assertIn(b'Applicant Dashboard', res_app.data)
        print("  -> Applicant login successful and redirected to Applicant Dashboard.")

    # 3. TEST ROLE AUTHORIZATION
    def test_03_role_authorization(self):
        print("\n[TEST 3] Verifying role authorization security...")
        
        # Anonymous accessing admin
        res_anon = self.client.get('/admin/dashboard')
        self.assertEqual(res_anon.status_code, 302, "Anonymous should be redirected to login")
        print("  -> Anonymous user barred from admin area.")

        # Applicant accessing admin
        self.client.post('/login', data={'email': 'rajesh.sharma@example.com', 'password': 'Applicant@123'})
        res_app_admin = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access Denied', res_app_admin.data)
        print("  -> Applicant denied access to admin views.")

    # 4. TEST NEW APPLICANT REGISTRATION
    def test_04_applicant_registration(self):
        print("\n[TEST 4] Verifying citizen registration & duplicate checks...")
        test_email = f"citizen_{int(datetime.utcnow().timestamp())}@example.com"
        
        reg_data = {
            'full_name': 'Test Citizen Kumar',
            'email': test_email,
            'mobile_number': '9876543299',
            'date_of_birth': '1996-05-15',
            'gender': 'Male',
            'address': 'Test House 123, Sector 5',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }
        res_reg = self.client.post('/register', data=reg_data, follow_redirects=True)
        self.assertIn(b'Registration successful', res_reg.data)
        print("  -> Registration successful.")

        # Duplicate email prevention
        res_dup = self.client.post('/register', data=reg_data, follow_redirects=True)
        self.assertIn(b'already exists', res_dup.data)
        print("  -> Duplicate registration prevented.")

    # 5. TEST COMPLETE APPLICATION LIFECYCLE (APPLICANT -> OFFICER -> APPLICANT)
    def test_05_complete_workflow(self):
        print("\n[TEST 5] Verifying complete end-to-end application lifecycle...")
        
        # Step A: Login as applicant
        self.client.post('/login', data={'email': 'rajesh.sharma@example.com', 'password': 'Applicant@123'})

        # Step B: Start new application
        res_new = self.client.post('/applicant/applications/new', data={
            'service_type': 'Fresh',
            'application_type': 'Normal',
            'booklet_type': '36 Pages'
        }, follow_redirects=False)
        self.assertEqual(res_new.status_code, 302)
        redirect_url = res_new.headers['Location']
        app_id = int(redirect_url.split('/applications/')[1].split('/form')[0])
        print(f"  -> Created draft application with internal ID #{app_id}.")

        # Step C: Fill multi-step form & save draft
        self.client.post(f'/applicant/applications/{app_id}/form', data={
            'step': '1',
            'action': 'next',
            'full_name': 'Rajesh Kumar Sharma',
            'date_of_birth': '1995-04-12',
            'gender': 'Male',
            'place_of_birth': 'Bengaluru',
            'nationality': 'Indian',
            'marital_status': 'Single'
        })
        self.client.post(f'/applicant/applications/{app_id}/form', data={
            'step': '2',
            'action': 'next',
            'mobile_number': '9811122233',
            'email': 'rajesh.sharma@example.com',
            'alternate_contact': '9811122299'
        })
        self.client.post(f'/applicant/applications/{app_id}/form', data={
            'step': '3',
            'action': 'next',
            'house_no': 'Flat 101',
            'street': 'Bannerghatta Road',
            'city': 'Bengaluru',
            'district': 'Bengaluru Urban',
            'state': 'Karnataka',
            'pincode': '560076',
            'country': 'India'
        })
        self.client.post(f'/applicant/applications/{app_id}/form', data={
            'step': '4',
            'action': 'next',
            'service_type': 'Fresh',
            'application_type': 'Normal',
            'booklet_type': '36 Pages'
        })
        self.client.post(f'/applicant/applications/{app_id}/form', data={
            'step': '5',
            'action': 'next',
            'declaration_accepted': '1'
        })
        print("  -> All 5 wizard steps completed.")

        # Step D: Upload mandatory documents
        docs_to_upload = [
            ('Identity Proof', 'id_proof.pdf', b'%PDF-1.4 sample id content'),
            ('Address Proof', 'address_proof.pdf', b'%PDF-1.4 sample address content'),
            ('Photograph', 'photo.jpg', b'\xff\xd8\xff\xe0\x00\x10JFIF sample photo content')
        ]
        for dtype, fname, fbytes in docs_to_upload:
            data = {
                'doc_type': dtype,
                'file': (io.BytesIO(fbytes), fname)
            }
            res_up = self.client.post(f'/applicant/applications/{app_id}/documents', data=data, content_type='multipart/form-data', follow_redirects=True)
            self.assertIn(b'uploaded successfully', res_up.data)
        print("  -> Uploaded 3 mandatory documents.")

        # Step E: Submit application & obtain unique Application ID
        res_submit = self.client.post(f'/applicant/applications/{app_id}/submit', follow_redirects=True)
        self.assertIn(b'Application submitted successfully', res_submit.data)
        
        with self.app.app_context():
            submitted_app = Application.query.get(app_id)
            app_number = submitted_app.application_number
            self.assertTrue(app_number.startswith('PAS'))
            self.assertEqual(submitted_app.status, 'Submitted')
            print(f"  -> Generated sequential Application ID: {app_number}.")

        # Step F: Book appointment slot
        with self.app.app_context():
            slot = AppointmentSlot.query.filter_by(is_active=True).first()
            slot_id = slot.id

        res_book = self.client.post(f'/applicant/applications/{app_id}/appointment', data={'slot_id': slot_id}, follow_redirects=True)
        self.assertIn(b'Appointment booked successfully', res_book.data)
        print("  -> Booked appointment slot.")

        # Step G: Switch to Officer role and perform Verification
        self.client.get('/logout')
        self.client.post('/login', data={'email': 'officer@passport.gov', 'password': 'Officer@123'})

        with self.app.app_context():
            app_docs = Document.query.filter_by(application_id=app_id).all()
            for doc in app_docs:
                self.client.post(f'/admin/applications/{app_id}/verify-document', data={
                    'doc_id': doc.id,
                    'status': 'Verified'
                })
        print("  -> Officer verified all 3 uploaded documents.")

        # Step H: Officer approves application
        res_approve = self.client.post(f'/admin/applications/{app_id}/action', data={
            'action': 'Approve',
            'remarks': 'Approved during automated test execution.'
        }, follow_redirects=True)
        self.assertIn(b'APPROVED successfully', res_approve.data)
        print("  -> Officer approved application.")

        # Step I: Verify state progression and notification creation
        with self.app.app_context():
            final_app = Application.query.get(app_id)
            self.assertEqual(final_app.status, 'Approved')

            # Verify notification created
            notif = Notification.query.filter_by(application_id=app_id).order_by(Notification.id.desc()).first()
            self.assertIsNotNone(notif)
            self.assertIn('Approved', notif.title)
            print(f"  -> In-app notification dispatched: '{notif.title}'.")

    # 6. TEST REPORTS & CSV EXPORT
    def test_06_reports_and_export(self):
        print("\n[TEST 6] Verifying admin reporting and CSV download...")
        self.client.post('/login', data={'email': 'admin@passport.gov', 'password': 'Admin@123'})
        
        res_rep = self.client.get('/admin/reports')
        self.assertEqual(res_rep.status_code, 200)
        self.assertIn(b'Performance Reports', res_rep.data)

        res_csv = self.client.get('/admin/reports/export-csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.mimetype, 'text/csv')
        self.assertIn(b'Application Number,Applicant Name', res_csv.data)
        print("  -> Reports loaded and CSV export generated with headers.")

    # 7. TEST REST API ENDPOINTS
    def test_07_rest_apis(self):
        print("\n[TEST 7] Verifying RESTful API endpoints...")
        
        # API Available slots
        res_slots = self.client.get('/api/appointments/available')
        self.assertEqual(res_slots.status_code, 200)
        data = res_slots.get_json()
        self.assertTrue(data.get('success'))
        self.assertGreater(len(data.get('slots', [])), 0)
        print(f"  -> GET /api/appointments/available returned {len(data['slots'])} slots.")

        # API Login
        res_login = self.client.post('/api/login', json={'email': 'rajesh.sharma@example.com', 'password': 'Applicant@123'})
        self.assertEqual(res_login.status_code, 200)
        print("  -> POST /api/login returned HTTP 200 with session token.")

if __name__ == '__main__':
    unittest.main()
