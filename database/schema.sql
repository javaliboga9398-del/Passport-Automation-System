-- ==========================================================
-- PASSPORT AUTOMATION SYSTEM - DATABASE SCHEMA
-- Target Database: MySQL 8.0+
-- Compatible with SQLAlchemy and standard MySQL imports
-- ==========================================================

CREATE DATABASE IF NOT EXISTS `passport_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `passport_db`;

-- Drop tables if existing (in reverse dependency order)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `application_status_history`;
DROP TABLE IF EXISTS `verification_records`;
DROP TABLE IF EXISTS `appointments`;
DROP TABLE IF EXISTS `appointment_slots`;
DROP TABLE IF EXISTS `documents`;
DROP TABLE IF EXISTS `applications`;
DROP TABLE IF EXISTS `applicants`;
DROP TABLE IF EXISTS `users`;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. USERS TABLE
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('applicant', 'officer', 'admin') NOT NULL DEFAULT 'applicant',
    `full_name` VARCHAR(100) NOT NULL,
    `mobile_number` VARCHAR(15) NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`),
    INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. APPLICANTS TABLE (Profile details linked to User)
CREATE TABLE `applicants` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `date_of_birth` DATE NULL,
    `gender` ENUM('Male', 'Female', 'Other') NULL,
    `address_line` VARCHAR(255) NULL,
    `city` VARCHAR(100) NULL,
    `district` VARCHAR(100) NULL,
    `state` VARCHAR(100) NULL,
    `pincode` VARCHAR(10) NULL,
    `country` VARCHAR(50) DEFAULT 'India',
    CONSTRAINT `fk_applicants_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. APPLICATIONS TABLE
CREATE TABLE `applications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `application_number` VARCHAR(30) UNIQUE NULL,
    `applicant_id` INT NOT NULL,
    `status` ENUM('Draft', 'Submitted', 'Under Verification', 'Approved', 'Printed', 'Dispatched', 'Rejected', 'Returned for Correction') NOT NULL DEFAULT 'Draft',
    `application_type` ENUM('Normal', 'Tatkaal') NOT NULL DEFAULT 'Normal',
    `service_type` ENUM('Fresh', 'Renewal') NOT NULL DEFAULT 'Fresh',
    `booklet_type` ENUM('36 Pages', '60 Pages') NOT NULL DEFAULT '36 Pages',
    `previous_passport_number` VARCHAR(20) NULL,
    `full_name` VARCHAR(100) NULL,
    `date_of_birth` DATE NULL,
    `gender` VARCHAR(20) NULL,
    `place_of_birth` VARCHAR(100) NULL,
    `nationality` VARCHAR(50) DEFAULT 'Indian',
    `marital_status` VARCHAR(30) NULL,
    `mobile_number` VARCHAR(15) NULL,
    `email` VARCHAR(120) NULL,
    `alternate_contact` VARCHAR(15) NULL,
    `house_no` VARCHAR(50) NULL,
    `street` VARCHAR(100) NULL,
    `city` VARCHAR(100) NULL,
    `district` VARCHAR(100) NULL,
    `state` VARCHAR(100) NULL,
    `pincode` VARCHAR(10) NULL,
    `country` VARCHAR(50) DEFAULT 'India',
    `declaration_accepted` BOOLEAN DEFAULT FALSE,
    `current_step` INT DEFAULT 1,
    `submitted_at` DATETIME NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_app_status` (`status`),
    INDEX `idx_app_number` (`application_number`),
    CONSTRAINT `fk_applications_applicant` FOREIGN KEY (`applicant_id`) REFERENCES `applicants`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. DOCUMENTS TABLE
CREATE TABLE `documents` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `application_id` INT NOT NULL,
    `doc_type` VARCHAR(50) NOT NULL,
    `original_filename` VARCHAR(255) NOT NULL,
    `stored_filename` VARCHAR(255) NOT NULL,
    `file_path` VARCHAR(255) NOT NULL,
    `file_size` INT NOT NULL,
    `mime_type` VARCHAR(100) NOT NULL,
    `verification_status` ENUM('Pending', 'Verified', 'Rejected') NOT NULL DEFAULT 'Pending',
    `rejection_reason` TEXT NULL,
    `uploaded_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_docs_app` (`application_id`),
    CONSTRAINT `fk_documents_application` FOREIGN KEY (`application_id`) REFERENCES `applications`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. APPOINTMENT SLOTS TABLE
CREATE TABLE `appointment_slots` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `slot_date` DATE NOT NULL,
    `start_time` TIME NOT NULL,
    `end_time` TIME NOT NULL,
    `max_capacity` INT NOT NULL DEFAULT 5,
    `booked_count` INT NOT NULL DEFAULT 0,
    `location` VARCHAR(150) NOT NULL DEFAULT 'Passport Seva Kendra - Central Branch',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_slot_date_time` (`slot_date`, `start_time`, `end_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. APPOINTMENTS TABLE
CREATE TABLE `appointments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `application_id` INT NOT NULL UNIQUE,
    `slot_id` INT NOT NULL,
    `appointment_number` VARCHAR(30) NOT NULL UNIQUE,
    `appointment_date` DATE NOT NULL,
    `appointment_time` VARCHAR(30) NOT NULL,
    `location` VARCHAR(150) NOT NULL,
    `status` ENUM('Scheduled', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Scheduled',
    `booked_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_appointments_app` FOREIGN KEY (`application_id`) REFERENCES `applications`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_appointments_slot` FOREIGN KEY (`slot_id`) REFERENCES `appointment_slots`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. VERIFICATION RECORDS TABLE
CREATE TABLE `verification_records` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `application_id` INT NOT NULL,
    `officer_id` INT NOT NULL,
    `action` ENUM('Verified', 'Approved', 'Rejected', 'Returned for Correction') NOT NULL,
    `remarks` TEXT NULL,
    `reason` TEXT NULL,
    `action_date` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_verif_app` FOREIGN KEY (`application_id`) REFERENCES `applications`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_verif_officer` FOREIGN KEY (`officer_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. APPLICATION STATUS HISTORY TABLE
CREATE TABLE `application_status_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `application_id` INT NOT NULL,
    `previous_status` VARCHAR(50) NULL,
    `new_status` VARCHAR(50) NOT NULL,
    `updated_by` INT NULL,
    `remarks` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_history_app` FOREIGN KEY (`application_id`) REFERENCES `applications`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_history_user` FOREIGN KEY (`updated_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. NOTIFICATIONS TABLE
CREATE TABLE `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `application_id` INT NULL,
    `title` VARCHAR(150) NOT NULL,
    `message` TEXT NOT NULL,
    `type` ENUM('info', 'success', 'warning', 'danger') NOT NULL DEFAULT 'info',
    `is_read` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_notif_user` (`user_id`, `is_read`),
    CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_notif_app` FOREIGN KEY (`application_id`) REFERENCES `applications`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
