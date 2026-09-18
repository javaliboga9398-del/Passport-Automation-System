-- ==========================================================
-- PASSPORT AUTOMATION SYSTEM - SEED / DEMO DATA
-- Password for Admin: Admin@123
-- Password for Officer: Officer@123
-- Password for Applicants: Applicant@123
-- ==========================================================

USE `passport_db`;

-- 1. SEED USERS
INSERT INTO `users` (`id`, `email`, `password_hash`, `role`, `full_name`, `mobile_number`, `created_at`) VALUES
(1, 'admin@passport.gov', 'scrypt:32768:8:1$EkFTh65Fe2WAuB86$a7a2826f1dc197891cc4f35b6123dc154a4395850d57f23c5a54d7e4aa62ed232c0271757c2414a85d08127df8a9e5da0a9869836f859bfc865704fd1d3542da', 'admin', 'System Administrator', '9876543210', '2026-01-01 10:00:00'),
(2, 'officer@passport.gov', 'scrypt:32768:8:1$0NqpjPhbt32atimB$2e3b3f3833e36babe0c3c9c3c92c1a5cb3924105e6ed1561012acea150e28973b5fce7ce00b553cf025c0dafee6506009f2c29a6e6bc2b52ad4ed59276f2de95', 'officer', 'Senior Verification Officer', '9876543211', '2026-01-01 10:30:00'),
(3, 'rajesh.sharma@example.com', 'scrypt:32768:8:1$Us430OryhaH3BXb6$34d4638c0181c8e1be16be7b8c8d963de54171d0ac653d673aef44e40c60f3f0272e3ceaa75308c7b0ae167511ae3e87d54c082535bb213ed5e93a02f94ff209', 'applicant', 'Rajesh Sharma', '9811122233', '2026-02-01 09:15:00'),
(4, 'priya.patel@example.com', 'scrypt:32768:8:1$Us430OryhaH3BXb6$34d4638c0181c8e1be16be7b8c8d963de54171d0ac653d673aef44e40c60f3f0272e3ceaa75308c7b0ae167511ae3e87d54c082535bb213ed5e93a02f94ff209', 'applicant', 'Priya Patel', '9822233344', '2026-02-05 11:45:00'),
(5, 'arun.kumar@example.com', 'scrypt:32768:8:1$Us430OryhaH3BXb6$34d4638c0181c8e1be16be7b8c8d963de54171d0ac653d673aef44e40c60f3f0272e3ceaa75308c7b0ae167511ae3e87d54c082535bb213ed5e93a02f94ff209', 'applicant', 'Arun Kumar', '9833344455', '2026-02-10 14:20:00');

-- 2. SEED APPLICANT PROFILES
INSERT INTO `applicants` (`id`, `user_id`, `date_of_birth`, `gender`, `address_line`, `city`, `district`, `state`, `pincode`, `country`) VALUES
(1, 3, '1995-04-12', 'Male', 'Flat 402, Greenfield Apartments, M.G. Road', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', '560001', 'India'),
(2, 4, '1998-08-25', 'Female', 'Plot 15, Vasant Vihar Phase 2', 'Ahmedabad', 'Ahmedabad', 'Gujarat', '380015', 'India'),
(3, 5, '1992-11-03', 'Male', 'House 78, Sector 14', 'Gurugram', 'Gurugram', 'Haryana', '122001', 'India');

-- 3. SEED APPOINTMENT SLOTS (for today and upcoming days)
INSERT INTO `appointment_slots` (`id`, `slot_date`, `start_time`, `end_time`, `max_capacity`, `booked_count`, `location`, `is_active`) VALUES
(1, '2026-09-18', '09:00:00', '10:00:00', 5, 2, 'Passport Seva Kendra - Central City Branch', 1),
(2, '2026-09-18', '10:30:00', '11:30:00', 5, 1, 'Passport Seva Kendra - Central City Branch', 1),
(3, '2026-09-18', '12:00:00', '13:00:00', 5, 0, 'Passport Seva Kendra - Central City Branch', 1),
(4, '2026-09-18', '14:00:00', '15:00:00', 5, 0, 'Passport Seva Kendra - Central City Branch', 1),
(5, '2026-09-19', '09:00:00', '10:00:00', 5, 0, 'Passport Seva Kendra - Central City Branch', 1),
(6, '2026-09-19', '10:30:00', '11:30:00', 5, 0, 'Passport Seva Kendra - Central City Branch', 1),
(7, '2026-09-20', '09:00:00', '10:00:00', 5, 0, 'Passport Seva Kendra - Central City Branch', 1),
(8, '2026-09-20', '11:00:00', '12:00:00', 5, 0, 'Passport Seva Kendra - Central City Branch', 1);

-- 4. SEED APPLICATIONS (covering multiple statuses)
INSERT INTO `applications` (
    `id`, `application_number`, `applicant_id`, `status`, `application_type`, `service_type`, `booklet_type`,
    `full_name`, `date_of_birth`, `gender`, `place_of_birth`, `nationality`, `marital_status`,
    `mobile_number`, `email`, `house_no`, `street`, `city`, `district`, `state`, `pincode`, `country`,
    `declaration_accepted`, `current_step`, `submitted_at`, `created_at`
) VALUES
(
    1, 'PAS202600001', 1, 'Approved', 'Normal', 'Fresh', '36 Pages',
    'Rajesh Sharma', '1995-04-12', 'Male', 'Bengaluru', 'Indian', 'Single',
    '9811122233', 'rajesh.sharma@example.com', 'Flat 402', 'Greenfield Apartments, M.G. Road', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', '560001', 'India',
    1, 5, '2026-09-01 11:30:00', '2026-09-01 10:00:00'
),
(
    2, 'PAS202600002', 2, 'Submitted', 'Tatkaal', 'Fresh', '36 Pages',
    'Priya Patel', '1998-08-25', 'Female', 'Ahmedabad', 'Indian', 'Single',
    '9822233344', 'priya.patel@example.com', 'Plot 15', 'Vasant Vihar Phase 2', 'Ahmedabad', 'Ahmedabad', 'Gujarat', '380015', 'India',
    1, 5, '2026-09-10 14:15:00', '2026-09-10 13:00:00'
),
(
    3, 'PAS202600003', 3, 'Under Verification', 'Normal', 'Renewal', '60 Pages',
    'Arun Kumar', '1992-11-03', 'Male', 'Gurugram', 'Indian', 'Married',
    '9833344455', 'arun.kumar@example.com', 'House 78', 'Sector 14', 'Gurugram', 'Gurugram', 'Haryana', '122001', 'India',
    1, 5, '2026-09-12 16:40:00', '2026-09-12 15:30:00'
),
(
    4, 'PAS202600004', 1, 'Dispatched', 'Normal', 'Renewal', '36 Pages',
    'Rajesh Sharma', '1995-04-12', 'Male', 'Bengaluru', 'Indian', 'Single',
    '9811122233', 'rajesh.sharma@example.com', 'Flat 402', 'Greenfield Apartments, M.G. Road', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', '560001', 'India',
    1, 5, '2026-08-15 10:00:00', '2026-08-15 09:00:00'
),
(
    5, 'PAS202600005', 2, 'Returned for Correction', 'Normal', 'Fresh', '36 Pages',
    'Priya Patel', '1998-08-25', 'Female', 'Ahmedabad', 'Indian', 'Single',
    '9822233344', 'priya.patel@example.com', 'Plot 15', 'Vasant Vihar Phase 2', 'Ahmedabad', 'Ahmedabad', 'Gujarat', '380015', 'India',
    1, 5, '2026-09-14 12:00:00', '2026-09-14 11:00:00'
),
(
    6, NULL, 3, 'Draft', 'Normal', 'Fresh', '36 Pages',
    'Arun Kumar', '1992-11-03', 'Male', 'Gurugram', 'Indian', 'Married',
    '9833344455', 'arun.kumar@example.com', 'House 78', 'Sector 14', 'Gurugram', 'Gurugram', 'Haryana', '122001', 'India',
    0, 3, NULL, '2026-09-16 10:00:00'
);

-- 5. SEED DOCUMENTS
INSERT INTO `documents` (`id`, `application_id`, `doc_type`, `original_filename`, `stored_filename`, `file_path`, `file_size`, `mime_type`, `verification_status`, `rejection_reason`) VALUES
(1, 1, 'Identity Proof', 'aadhaar_card.pdf', 'demo_aadhaar_01.pdf', 'uploads/documents/demo_aadhaar_01.pdf', 245120, 'application/pdf', 'Verified', NULL),
(2, 1, 'Address Proof', 'utility_bill.pdf', 'demo_bill_01.pdf', 'uploads/documents/demo_bill_01.pdf', 189400, 'application/pdf', 'Verified', NULL),
(3, 1, 'Photograph', 'passport_photo.jpg', 'demo_photo_01.jpg', 'uploads/documents/demo_photo_01.jpg', 84200, 'image/jpeg', 'Verified', NULL),
(4, 2, 'Identity Proof', 'pan_card.pdf', 'demo_pan_02.pdf', 'uploads/documents/demo_pan_02.pdf', 154000, 'application/pdf', 'Pending', NULL),
(5, 2, 'Address Proof', 'voter_id.pdf', 'demo_voter_02.pdf', 'uploads/documents/demo_voter_02.pdf', 210000, 'application/pdf', 'Pending', NULL),
(6, 3, 'Identity Proof', 'aadhaar_card.pdf', 'demo_aadhaar_03.pdf', 'uploads/documents/demo_aadhaar_03.pdf', 230000, 'application/pdf', 'Verified', NULL),
(7, 3, 'Address Proof', 'bank_statement.pdf', 'demo_statement_03.pdf', 'uploads/documents/demo_statement_03.pdf', 310000, 'application/pdf', 'Pending', NULL),
(8, 5, 'Address Proof', 'rent_agreement.pdf', 'demo_rent_05.pdf', 'uploads/documents/demo_rent_05.pdf', 420000, 'application/pdf', 'Rejected', 'Document expired. Please upload an active utility bill or valid agreement.');

-- 6. SEED APPOINTMENTS
INSERT INTO `appointments` (`id`, `application_id`, `slot_id`, `appointment_number`, `appointment_date`, `appointment_time`, `location`, `status`, `booked_at`) VALUES
(1, 1, 1, 'APT202600001', '2026-09-18', '09:00 AM - 10:00 AM', 'Passport Seva Kendra - Central City Branch', 'Completed', '2026-09-02 10:00:00'),
(2, 2, 1, 'APT202600002', '2026-09-18', '09:00 AM - 10:00 AM', 'Passport Seva Kendra - Central City Branch', 'Scheduled', '2026-09-11 11:00:00'),
(3, 3, 2, 'APT202600003', '2026-09-18', '10:30 AM - 11:30 AM', 'Passport Seva Kendra - Central City Branch', 'Scheduled', '2026-09-13 14:30:00');

-- 7. SEED VERIFICATION RECORDS
INSERT INTO `verification_records` (`id`, `application_id`, `officer_id`, `action`, `remarks`, `reason`, `action_date`) VALUES
(1, 1, 2, 'Verified', 'All documents examined and verified with original physical copies.', NULL, '2026-09-03 14:00:00'),
(2, 1, 2, 'Approved', 'Application cleared by Senior Verification Officer.', NULL, '2026-09-04 11:00:00'),
(3, 5, 2, 'Returned for Correction', 'Address proof is expired.', 'Invalid address proof document provided.', '2026-09-15 15:30:00');

-- 8. SEED APPLICATION STATUS HISTORY
INSERT INTO `application_status_history` (`id`, `application_id`, `previous_status`, `new_status`, `updated_by`, `remarks`, `created_at`) VALUES
(1, 1, 'Draft', 'Submitted', 3, 'Application submitted by applicant.', '2026-09-01 11:30:00'),
(2, 1, 'Submitted', 'Under Verification', 2, 'Application taken up for document verification.', '2026-09-03 09:30:00'),
(3, 1, 'Under Verification', 'Approved', 2, 'Application approved after successful verification.', '2026-09-04 11:00:00'),
(4, 2, 'Draft', 'Submitted', 4, 'Application submitted by applicant.', '2026-09-10 14:15:00'),
(5, 3, 'Draft', 'Submitted', 5, 'Application submitted by applicant.', '2026-09-12 16:40:00'),
(6, 3, 'Submitted', 'Under Verification', 2, 'Verification in progress.', '2026-09-13 10:00:00'),
(7, 4, 'Approved', 'Printed', 1, 'Passport booklet sent for printing.', '2026-08-20 10:00:00'),
(8, 4, 'Printed', 'Dispatched', 1, 'Passport dispatched via Speed Post Tracking #SP9928172IN.', '2026-08-22 15:00:00'),
(9, 5, 'Submitted', 'Returned for Correction', 2, 'Address document expired. Re-upload requested.', '2026-09-15 15:30:00');

-- 9. SEED NOTIFICATIONS
INSERT INTO `notifications` (`id`, `user_id`, `application_id`, `title`, `message`, `type`, `is_read`, `created_at`) VALUES
(1, 3, 1, 'Application Approved', 'Congratulations! Your Passport Application PAS202600001 has been approved by the Passport Officer.', 'success', 0, '2026-09-04 11:00:00'),
(2, 4, 2, 'Appointment Scheduled', 'Your appointment for PAS202600002 is confirmed for 2026-09-18 at 09:00 AM - 10:00 AM.', 'info', 0, '2026-09-11 11:00:00'),
(3, 5, 3, 'Application Under Verification', 'Your Passport Application PAS202600003 is currently undergoing document verification.', 'info', 1, '2026-09-13 10:00:00'),
(4, 4, 5, 'Action Required: Application Returned', 'Your Application PAS202600005 has been returned for correction. Reason: Invalid/expired address proof document.', 'warning', 0, '2026-09-15 15:30:00');
