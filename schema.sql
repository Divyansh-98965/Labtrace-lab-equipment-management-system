-- =============================================================================
-- LabTrace - Relational Database Management System Schema
-- Compatible with MySQL 5.7+ / 8.0+ and XAMPP phpMyAdmin
-- Database: labtrace_db
-- Tables: 12 interconnected relational tables with strict foreign keys
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `labtrace_db` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `labtrace_db`;

-- Disable foreign key checks during schema creation
SET FOREIGN_KEY_CHECKS = 0;

-- -----------------------------------------------------------------------------
-- 1. roles: User permissions and access roles (e.g., Admin, Student, Technician)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles` (
    `role_id` INT AUTO_INCREMENT PRIMARY KEY,
    `role_name` VARCHAR(50) NOT NULL UNIQUE,
    `description` VARCHAR(255) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. departments: University departments
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `departments`;
CREATE TABLE `departments` (
    `department_id` INT AUTO_INCREMENT PRIMARY KEY,
    `department_name` VARCHAR(100) NOT NULL UNIQUE,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `building` VARCHAR(100) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. users: Students, faculty, technicians, administrators
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `role_id` INT NOT NULL,
    `department_id` INT NOT NULL,
    `first_name` VARCHAR(50) NOT NULL,
    `last_name` VARCHAR(50) NOT NULL,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `phone` VARCHAR(30) NULL,
    `status` ENUM('Active', 'Inactive', 'Suspended') NOT NULL DEFAULT 'Active',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) 
        REFERENCES `roles` (`role_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_users_department` FOREIGN KEY (`department_id`) 
        REFERENCES `departments` (`department_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. laboratories: Labs, buildings, and physical locations
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `laboratories`;
CREATE TABLE `laboratories` (
    `lab_id` INT AUTO_INCREMENT PRIMARY KEY,
    `department_id` INT NOT NULL,
    `lab_name` VARCHAR(100) NOT NULL,
    `room_number` VARCHAR(50) NOT NULL,
    `building` VARCHAR(100) NOT NULL,
    `capacity` INT NOT NULL DEFAULT 30,
    `in_charge_user_id` INT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_labs_department` FOREIGN KEY (`department_id`) 
        REFERENCES `departments` (`department_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_labs_in_charge` FOREIGN KEY (`in_charge_user_id`) 
        REFERENCES `users` (`user_id`) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. equipment_categories: Equipment classification
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `equipment_categories`;
CREATE TABLE `equipment_categories` (
    `category_id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_name` VARCHAR(100) NOT NULL UNIQUE,
    `description` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. suppliers: Supplier information and vendors
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers` (
    `supplier_id` INT AUTO_INCREMENT PRIMARY KEY,
    `supplier_name` VARCHAR(150) NOT NULL,
    `contact_person` VARCHAR(100) NULL,
    `email` VARCHAR(100) NULL,
    `phone` VARCHAR(50) NULL,
    `address` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 7. equipment: Individual equipment assets
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `equipment`;
CREATE TABLE `equipment` (
    `equipment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_id` INT NOT NULL,
    `lab_id` INT NOT NULL,
    `supplier_id` INT NULL,
    `asset_tag` VARCHAR(50) NOT NULL UNIQUE,
    `name` VARCHAR(150) NOT NULL,
    `model` VARCHAR(100) NULL,
    `serial_number` VARCHAR(100) UNIQUE NULL,
    `purchase_date` DATE NULL,
    `cost` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `status` ENUM('Available', 'In Use', 'Under Maintenance', 'Decommissioned', 'Reserved') NOT NULL DEFAULT 'Available',
    `condition_state` ENUM('New', 'Excellent', 'Good', 'Fair', 'Needs Repair') NOT NULL DEFAULT 'Good',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_equipment_category` FOREIGN KEY (`category_id`) 
        REFERENCES `equipment_categories` (`category_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_equipment_lab` FOREIGN KEY (`lab_id`) 
        REFERENCES `laboratories` (`lab_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_equipment_supplier` FOREIGN KEY (`supplier_id`) 
        REFERENCES `suppliers` (`supplier_id`) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 8. consumables: Laboratory supplies and stock levels
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `consumables`;
CREATE TABLE `consumables` (
    `consumable_id` INT AUTO_INCREMENT PRIMARY KEY,
    `lab_id` INT NOT NULL,
    `item_name` VARCHAR(150) NOT NULL,
    `sku` VARCHAR(50) NOT NULL UNIQUE,
    `quantity` INT NOT NULL DEFAULT 0,
    `unit` VARCHAR(30) NOT NULL DEFAULT 'Units',
    `min_stock_level` INT NOT NULL DEFAULT 10,
    `reorder_status` ENUM('Adequate', 'Low Stock', 'Out of Stock') NOT NULL DEFAULT 'Adequate',
    `last_restocked` DATE NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_consumables_lab` FOREIGN KEY (`lab_id`) 
        REFERENCES `laboratories` (`lab_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 9. borrowings: Equipment issue, checkout, and return logs
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `borrowings`;
CREATE TABLE `borrowings` (
    `borrowing_id` INT AUTO_INCREMENT PRIMARY KEY,
    `equipment_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `borrow_date` DATETIME NOT NULL,
    `expected_return_date` DATETIME NOT NULL,
    `actual_return_date` DATETIME NULL,
    `status` ENUM('Requested', 'Issued', 'Returned', 'Overdue') NOT NULL DEFAULT 'Issued',
    `purpose` VARCHAR(255) NULL,
    `remarks` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_borrowings_equipment` FOREIGN KEY (`equipment_id`) 
        REFERENCES `equipment` (`equipment_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_borrowings_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 10. maintenance: Repairs and calibration history
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `maintenance`;
CREATE TABLE `maintenance` (
    `maintenance_id` INT AUTO_INCREMENT PRIMARY KEY,
    `equipment_id` INT NOT NULL,
    `technician_id` INT NULL,
    `service_date` DATE NOT NULL,
    `maintenance_type` ENUM('Routine Inspection', 'Calibration', 'Repair', 'Software Update', 'Preventive') NOT NULL,
    `description` TEXT NULL,
    `cost` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `next_scheduled_date` DATE NULL,
    `status` ENUM('Scheduled', 'In Progress', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Completed',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_maintenance_equipment` FOREIGN KEY (`equipment_id`) 
        REFERENCES `equipment` (`equipment_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_maintenance_technician` FOREIGN KEY (`technician_id`) 
        REFERENCES `users` (`user_id`) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 11. transactions: Equipment transfers and inventory stock movements
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `transactions`;
CREATE TABLE `transactions` (
    `transaction_id` INT AUTO_INCREMENT PRIMARY KEY,
    `equipment_id` INT NOT NULL,
    `from_lab_id` INT NULL,
    `to_lab_id` INT NOT NULL,
    `transferred_by_user_id` INT NULL,
    `transaction_date` DATETIME NOT NULL,
    `transaction_type` ENUM('Transfer', 'Relocation', 'Disposal', 'Initial Setup', 'Return From Repair') NOT NULL,
    `reason` VARCHAR(255) NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_transactions_equipment` FOREIGN KEY (`equipment_id`) 
        REFERENCES `equipment` (`equipment_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_transactions_from_lab` FOREIGN KEY (`from_lab_id`) 
        REFERENCES `laboratories` (`lab_id`) 
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT `fk_transactions_to_lab` FOREIGN KEY (`to_lab_id`) 
        REFERENCES `laboratories` (`lab_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_transactions_transferred_by` FOREIGN KEY (`transferred_by_user_id`) 
        REFERENCES `users` (`user_id`) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 12. purchase_orders: Procurement records
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS `purchase_orders`;
CREATE TABLE `purchase_orders` (
    `po_id` INT AUTO_INCREMENT PRIMARY KEY,
    `po_number` VARCHAR(50) NOT NULL UNIQUE,
    `supplier_id` INT NOT NULL,
    `ordered_by_user_id` INT NULL,
    `order_date` DATE NOT NULL,
    `delivery_date` DATE NULL,
    `total_amount` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `status` ENUM('Pending', 'Approved', 'Shipped', 'Received', 'Cancelled') NOT NULL DEFAULT 'Pending',
    `notes` TEXT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_po_supplier` FOREIGN KEY (`supplier_id`) 
        REFERENCES `suppliers` (`supplier_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_po_ordered_by` FOREIGN KEY (`ordered_by_user_id`) 
        REFERENCES `users` (`user_id`) 
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

