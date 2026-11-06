"""
LabTrace - Automated Database Seeding Script
Populates the 12-table MySQL database with realistic university laboratory data.
Generates 120+ equipment items and rich relational records.
"""

import sys
import random
from datetime import datetime, timedelta
import pymysql
from pymysql.cursors import DictCursor
from config import Config
from db import get_db_connection, execute_sql_file

def initialize_database_if_needed():
    """Ensure labtrace_db exists and tables are created from schema.sql."""
    # Check if database exists
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE %s", (Config.MYSQL_DB,))
            exists = cursor.fetchone()
            if not exists:
                print(f"[LabTrace] Database '{Config.MYSQL_DB}' not found. Initializing schema...")
                execute_sql_file("schema.sql")
                print(f"[LabTrace] Database and tables created successfully.")
            else:
                cursor.execute(f"USE `{Config.MYSQL_DB}`")
                cursor.execute("SHOW TABLES LIKE 'equipment'")
                if not cursor.fetchone():
                    print(f"[LabTrace] Tables not found. Initializing schema...")
                    execute_sql_file("schema.sql")
    finally:
        conn.close()

def seed_database(force=False):
    """
    Checks if the equipment table is empty.
    If empty (or force=True), populates all 12 tables with realistic data including 100+ equipment items.
    """
    initialize_database_if_needed()
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM equipment")
            eq_count = cursor.fetchone()["total"]

            if eq_count > 0 and not force:
                print(f"[LabTrace] Equipment table already contains {eq_count} records. Seeding skipped.")
                return eq_count

            print(f"[LabTrace] Equipment table is empty (count={eq_count}). Starting automated seeding...")

            # Clean existing tables if force is used
            if force:
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                for table in [
                    "purchase_orders", "transactions", "maintenance", "borrowings",
                    "consumables", "equipment", "suppliers", "equipment_categories",
                    "laboratories", "users", "departments", "roles"
                ]:
                    cursor.execute(f"TRUNCATE TABLE `{table}`")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                print("[LabTrace] All tables truncated for fresh seed.")

            # -------------------------------------------------------------
            # 1. ROLES
            # -------------------------------------------------------------
            roles_data = [
                ("Admin", "Full administrative control over all laboratories, assets, and users"),
                ("Lab Technician", "Responsible for inventory maintenance, calibration, checkouts, and testing"),
                ("Faculty", "Principal investigators and teaching faculty supervising research projects"),
                ("Student", "Undergraduate and graduate researchers accessing labs for authorized coursework"),
                ("Lab Assistant", "Assists with daily logistics, consumable stock management, and basic equipment returns")
            ]
            cursor.executemany(
                "INSERT INTO roles (role_name, description) VALUES (%s, %s)",
                roles_data
            )
            print("[✓] Seeded roles (5 entries)")

            # -------------------------------------------------------------
            # 2. DEPARTMENTS
            # -------------------------------------------------------------
            dept_data = [
                ("Computer Science & Engineering", "CSE", "Turing Computing Complex"),
                ("Electrical & Electronics Engineering", "EEE", "Tesla Science Wing"),
                ("Mechanical & Aerospace Engineering", "MECH", "Faraday Applied Labs"),
                ("Biotechnology & Biomedical Engineering", "BIO", "Franklin Life Sciences Tower"),
                ("Chemistry & Materials Science", "CHEM", "Curie Analytical Facility"),
                ("Physics & Quantum Dynamics", "PHYS", "Einstein Research Center")
            ]
            cursor.executemany(
                "INSERT INTO departments (department_name, code, building) VALUES (%s, %s, %s)",
                dept_data
            )
            print("[✓] Seeded departments (6 entries)")

            # -------------------------------------------------------------
            # 3. USERS
            # -------------------------------------------------------------
            # Mapping: roles (1:Admin, 2:Tech, 3:Faculty, 4:Student, 5:Assistant)
            users_data = [
                (1, 1, "Dr. Alexander", "Wright", "a.wright@university.edu", "+1-555-0101", "Active"),
                (2, 1, "Marcus", "Vance", "m.vance@university.edu", "+1-555-0102", "Active"),
                (2, 2, "Sarah", "Jenkins", "s.jenkins@university.edu", "+1-555-0103", "Active"),
                (2, 3, "Raj", "Patel", "r.patel@university.edu", "+1-555-0104", "Active"),
                (2, 4, "Elena", "Rostova", "e.rostova@university.edu", "+1-555-0105", "Active"),
                (2, 5, "David", "Kowalski", "d.kowalski@university.edu", "+1-555-0106", "Active"),
                (3, 1, "Prof. Evelyn", "Holloway", "e.holloway@university.edu", "+1-555-0201", "Active"),
                (3, 2, "Prof. Jonathan", "Reid", "j.reid@university.edu", "+1-555-0202", "Active"),
                (3, 3, "Prof. Vikram", "Shenoy", "v.shenoy@university.edu", "+1-555-0203", "Active"),
                (3, 4, "Dr. Clara", "Mendez", "c.mendez@university.edu", "+1-555-0204", "Active"),
                (3, 5, "Dr. Arthur", "Pendleton", "a.pendleton@university.edu", "+1-555-0205", "Active"),
                (4, 1, "Liam", "Chen", "l.chen@student.university.edu", "+1-555-0301", "Active"),
                (4, 1, "Maya", "Rodriguez", "m.rodriguez@student.university.edu", "+1-555-0302", "Active"),
                (4, 2, "Noah", "Kim", "n.kim@student.university.edu", "+1-555-0303", "Active"),
                (4, 2, "Olivia", "Taylor", "o.taylor@student.university.edu", "+1-555-0304", "Active"),
                (4, 3, "Lucas", "Bennett", "l.bennett@student.university.edu", "+1-555-0305", "Active"),
                (4, 4, "Sophia", "Alvarez", "s.alvarez@student.university.edu", "+1-555-0306", "Active"),
                (4, 5, "Ethan", "Miller", "e.miller@student.university.edu", "+1-555-0307", "Active"),
                (5, 1, "Chloe", "Davis", "c.davis@university.edu", "+1-555-0401", "Active"),
                (5, 2, "Jordan", "Lee", "j.lee@university.edu", "+1-555-0402", "Active")
            ]
            cursor.executemany(
                """INSERT INTO users (role_id, department_id, first_name, last_name, email, phone, status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                users_data
            )
            print(f"[✓] Seeded users ({len(users_data)} entries)")

            # -------------------------------------------------------------
            # 4. LABORATORIES
            # -------------------------------------------------------------
            labs_data = [
                (1, "Robotics & Autonomous Systems Lab", "Room 302", "Turing Computing Complex", 32, 2),
                (1, "AI, Cloud & High Performance Computing Lab", "Room 410", "Turing Computing Complex", 40, 2),
                (2, "Power Electronics & Energy Systems Lab", "Room 105", "Tesla Science Wing", 28, 3),
                (2, "VLSI Design & Embedded Hardware Lab", "Room 214", "Tesla Science Wing", 35, 3),
                (3, "Thermal Dynamics & Fluidics Lab", "Room 101", "Faraday Applied Labs", 25, 4),
                (3, "CNC Machining & Prototyping Workshop", "Room B12", "Faraday Applied Labs", 20, 4),
                (4, "Molecular Biology & Genomics Lab", "Room 204", "Franklin Life Sciences Tower", 24, 5),
                (4, "Biochemical Spectroscopy & Cell Culture Lab", "Room 310", "Franklin Life Sciences Tower", 22, 5),
                (5, "Analytical Chemistry & Mass Spec Lab", "Room 118", "Curie Analytical Facility", 26, 6),
                (6, "Quantum Optics & Nanophotonics Facility", "Room 108", "Einstein Research Center", 18, 6)
            ]
            cursor.executemany(
                """INSERT INTO laboratories (department_id, lab_name, room_number, building, capacity, in_charge_user_id) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                labs_data
            )
            print(f"[✓] Seeded laboratories ({len(labs_data)} entries)")

            # -------------------------------------------------------------
            # 5. EQUIPMENT CATEGORIES
            # -------------------------------------------------------------
            categories_data = [
                ("Electronic Test & Measurement", "Oscilloscopes, digital multimeters, spectrum analyzers, logic analyzers"),
                ("Analytical & Spectroscopic Instruments", "Spectrophotometers, chromatography, mass spectrometers, fluorometers"),
                ("Computing, Servers & Hardware Dev", "GPU compute servers, FPGA dev boards, embedded kits, logic workstations"),
                ("Microscopy & Optical Imaging", "Electron microscopes, confocal microscopes, stereo inspection optics"),
                ("Precision Fabrication & Machining", "3D printers, CNC mills, reflow ovens, PCB prototyping, laser cutters"),
                ("Thermal & Environmental Chambers", "Autoclaves, ultra-low freezers (-80C), incubators, climate chambers"),
                ("Signal Generation & Power Sources", "RF signal generators, programmable DC power supplies, function generators")
            ]
            cursor.executemany(
                "INSERT INTO equipment_categories (category_name, description) VALUES (%s, %s)",
                categories_data
            )
            print(f"[✓] Seeded equipment_categories ({len(categories_data)} entries)")

            # -------------------------------------------------------------
            # 6. SUPPLIERS
            # -------------------------------------------------------------
            suppliers_data = [
                ("Keysight Technologies", "Robert Miller", "orders@keysight-supply.com", "+1-800-539-7444", "1400 Fountaingrove Pkwy, Santa Rosa, CA"),
                ("Thermo Fisher Scientific", "Amanda Clark", "procurement@thermofisher.com", "+1-800-678-5599", "168 Third Avenue, Waltham, MA"),
                ("Tektronix & Keithley Instruments", "David Zhang", "sales@tektronix.com", "+1-800-833-9200", "14150 SW Karl Braun Dr, Beaverton, OR"),
                ("Agilent Technologies", "Melissa Ross", "orders@agilent.com", "+1-877-424-4536", "5301 Stevens Creek Blvd, Santa Clara, CA"),
                ("Dell Technologies Enterprise OEM", "Jason Vance", "direct@dellenterprise.com", "+1-800-456-3355", "One Dell Way, Round Rock, TX"),
                ("Leica Microsystems", "Helmut Weiss", "info@leica-microsystems.com", "+1-800-248-0123", "Ernst-Leitz-Strasse 17-37, Wetzlar, Germany"),
                ("Eppendorf AG North America", "Karen Lindqvist", "custserv@eppendorf.com", "+1-800-645-3050", "175 Freshwater Blvd, Enfield, CT"),
                ("Shimadzu Scientific Instruments", "Kenji Sato", "weborders@shimadzu.com", "+1-800-477-1227", "7102 Riverwood Dr, Columbia, MD"),
                ("Fluke Corporation", "Brian O'Connor", "orders@fluke.com", "+1-800-443-5853", "6920 Seaway Blvd, Everett, WA"),
                ("Formlabs Prototyping Systems", "Chloe Dubois", "enterprise@formlabs.com", "+1-617-702-8476", "35 Medford St, Somerville, MA")
            ]
            cursor.executemany(
                """INSERT INTO suppliers (supplier_name, contact_person, email, phone, address) 
                   VALUES (%s, %s, %s, %s, %s)""",
                suppliers_data
            )
            print(f"[✓] Seeded suppliers ({len(suppliers_data)} entries)")

            # -------------------------------------------------------------
            # 7. EQUIPMENT (120+ realistic records generated via loop)
            # -------------------------------------------------------------
            # Templates for realistic equipment generation
            equipment_templates = [
                # (Category_id, Base Name, Model Prefix, Supplier_id, Min Cost, Max Cost)
                (1, "InfiniiVision Digital Storage Oscilloscope 200MHz", "DSO-X-3024T", 1, 3200, 5800),
                (1, "Mixed Domain Digital Oscilloscope 1GHz 4-Channel", "MDO34-4-BW", 3, 7500, 11200),
                (1, "Truevolt 6.5 Digit Precision Digital Multimeter", "34465A", 1, 1400, 2100),
                (1, "Fluke 87V Industrial True-RMS Multimeter", "87V-MAX", 9, 450, 750),
                (1, "Keysight FieldFox Handheld RF Spectrum Analyzer", "N9918B", 1, 12500, 19500),
                (1, "Keithley 2450 SourceMeter High-Precision SMU", "2450-SMU", 3, 6200, 8900),
                (1, "Rigol 4-Channel Digital Phosphor Oscilloscope", "DS1054Z-PRO", 1, 650, 1100),
                
                (2, "NanoDrop One Microvolume UV-Vis Spectrophotometer", "ND-ONE-W", 2, 9800, 14500),
                (2, "Shimadzu UV-1900i Double-Beam UV-Vis Spectrophotometer", "UV-1900i", 8, 8500, 13000),
                (2, "Agilent 1260 Infinity II Quaternary HPLC System", "1260-LC", 4, 24000, 38000),
                (2, "Thermo Scientific Sorvall Legend X1 Centrifuge", "SL-X1R", 2, 7200, 11500),
                (2, "Eppendorf Mastercycler X50 High-Speed PCR Thermal Cycler", "X50a-PCR", 7, 6800, 9500),
                (2, "Eppendorf 5424 R Microcentrifuge with Refrigeration", "5424R-STD", 7, 4200, 6100),
                (2, "Varian Cary 60 UV-Vis Spectrophotometer Station", "CARY-60", 4, 7900, 10800),
                
                (3, "Dell Precision 7920 Dual Intel Xeon GPU Workstation", "T7920-AI", 5, 5400, 8800),
                (3, "NVIDIA RTX 6000 Ada Deep Learning Training Server", "DGX-SVR-4U", 5, 14000, 22000),
                (3, "Xilinx UltraScale+ ZCU102 FPGA Evaluation Board", "ZCU102-EK", 1, 2800, 4200),
                (3, "Raspberry Pi 5 Embedded Edge Cluster Bench (8-Node)", "RPI5-CLUST", 5, 1200, 1800),
                (3, "National Instruments CompactRIO Controller System", "cRIO-9045", 3, 4900, 7100),
                (3, "Altera Cyclone V GX FPGA Development Platform", "CYC5-DK", 1, 1600, 2500),
                
                (4, "Leica DM750 Advanced Biological Binocular Microscope", "DM750-LED", 6, 2600, 4100),
                (4, "Olympus CX23 Upright Phase Contrast Microscope", "CX23-PH", 6, 1800, 2900),
                (4, "FLIR E8-XT High Resolution Thermal Imaging Camera", "E8-XT-MSX", 9, 3200, 4500),
                (4, "Leica S9D High Resolution Stereo Zoom Microscope", "S9D-CMOS", 6, 4100, 6300),
                (4, "Zeiss Stemi 508 Greenough Stereo Microscope", "STEMI-508", 6, 3800, 5200),
                
                (5, "Formlabs Form 3+ Stereolithography (SLA) 3D Printer", "FORM-3P", 10, 3750, 4900),
                (5, "UltiMaker S5 Dual Extrusion 3D Production Printer", "UMS5-PRO", 10, 5900, 7200),
                (5, "Tormach PCNC 440 Desktop CNC Milling Machine", "PCNC440-S3", 10, 9500, 14000),
                (5, "Pace MBT 350 Dual Channel Digital Solder & Rework Station", "MBT-350", 9, 1400, 2200),
                (5, "LPKF ProtoMat S64 High-Precision PCB Prototyping Mill", "S64-PCB", 10, 18500, 26000),
                (5, "Glowforge Pro Laser Cutter and Engraver 45W CO2", "GF-PRO-45W", 10, 4800, 6200),
                
                (6, "Thermo Fisher Heracell 150i CO2 Incubator", "HERA-150i", 2, 7400, 9800),
                (6, "Thermo Scientific Forma 88000 Ultra-Low -80C Freezer", "F88400A", 2, 11500, 16500),
                (6, "Tuttnauer 3870EL Automated Autoclave Sterilizer", "3870EL-CL", 2, 8900, 12800),
                (6, "Labconco Purifier Logic+ Class II Biosafety Cabinet", "LOGIC-A2-4", 2, 9200, 13400),
                (6, "Binder ED 115 Natural Convection Drying Oven 300C", "ED115-230V", 8, 2600, 3900),
                
                (7, "Keysight E36313A Triple Output Programmable DC Supply", "E36313A", 1, 2100, 3100),
                (7, "Tektronix AFG31022 Dual Channel Arbitrary Function Generator", "AFG-31022", 3, 3800, 5400),
                (7, "Rigol DG4162 Waveform & Function Generator 160MHz", "DG4162-GEN", 1, 1100, 1800),
                (7, "Rohde & Schwarz HMC8043 3-Channel Power Supply 100W", "HMC-8043", 1, 1650, 2450)
            ]

            statuses = ["Available", "Available", "Available", "Available", "In Use", "In Use", "Under Maintenance", "Reserved"]
            conditions = ["New", "Excellent", "Good", "Good", "Good", "Fair"]

            equipment_rows = []
            random.seed(42)  # Deterministic seed for reproducible testing

            total_items_to_seed = 125
            for i in range(1, total_items_to_seed + 1):
                tmpl = equipment_templates[(i - 1) % len(equipment_templates)]
                cat_id = tmpl[0]
                base_name = tmpl[1]
                model_prefix = tmpl[2]
                supp_id = tmpl[3]
                min_cost = tmpl[4]
                max_cost = tmpl[5]

                # Distribute equipment across the 10 labs matching their field
                if cat_id in (1, 7): # Electronics / Measurement
                    lab_id = random.choice([1, 2, 3, 4])
                elif cat_id == 2: # Analytical / Spectroscopic
                    lab_id = random.choice([7, 8, 9])
                elif cat_id == 3: # Computing / Hardware
                    lab_id = random.choice([1, 2, 4, 10])
                elif cat_id == 4: # Microscopy
                    lab_id = random.choice([7, 8, 9, 10])
                elif cat_id == 5: # Fabrication
                    lab_id = random.choice([1, 4, 5, 6])
                else: # Environmental / Thermal
                    lab_id = random.choice([5, 7, 8, 9])

                asset_tag = f"EQ-2024-{i:04d}"
                unit_number = ((i - 1) // len(equipment_templates)) + 1
                name = f"{base_name} (Unit #{unit_number})"
                model = f"{model_prefix}-V{unit_number}"
                serial_num = f"SN-{supp_id:02d}{cat_id:02d}-{100000 + i * 37}"
                
                # Purchase date between 2021 and 2024
                days_ago = random.randint(30, 1100)
                purch_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                cost = round(random.uniform(min_cost, max_cost), 2)
                status = random.choice(statuses)
                condition = "Needs Repair" if status == "Under Maintenance" else random.choice(conditions)

                equipment_rows.append((
                    cat_id, lab_id, supp_id, asset_tag, name, model, serial_num, purch_date, cost, status, condition
                ))

            cursor.executemany(
                """INSERT INTO equipment 
                   (category_id, lab_id, supplier_id, asset_tag, name, model, serial_number, purchase_date, cost, status, condition_state)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                equipment_rows
            )
            print(f"[✓] Seeded equipment ({len(equipment_rows)} entries generated - exceeding 100+ requirement)")

            # -------------------------------------------------------------
            # 8. CONSUMABLES
            # -------------------------------------------------------------
            consumables_data = [
                (1, "ESD Anti-Static Wrist Strap Kits", "CONS-ESD-01", 45, "Sets", 15, "Adequate", "2024-08-10"),
                (1, "Lead-Free Solder Wire Sn99.3Cu0.7 (500g)", "CONS-SLD-02", 12, "Spools", 5, "Adequate", "2024-09-01"),
                (2, "Cat6A Shielded Ethernet Cable 2m", "CONS-NET-03", 85, "Pieces", 20, "Adequate", "2024-07-15"),
                (3, "High-Voltage Banana Plug Test Leads Set", "CONS-TST-04", 6, "Sets", 10, "Low Stock", "2024-05-12"),
                (3, "Fast-Blow Ceramic Fuses 10A 600V", "CONS-FUS-05", 3, "Packs", 10, "Low Stock", "2024-04-20"),
                (4, "Breadboard Jumper Wire Ribbons (120pcs)", "CONS-JMP-06", 30, "Packs", 8, "Adequate", "2024-09-20"),
                (4, "Conductive Copper Foil Shielding Tape", "CONS-CPR-07", 0, "Rolls", 4, "Out of Stock", "2024-03-10"),
                (5, "High-Temperature Thermal Interface Paste 50g", "CONS-THM-08", 8, "Tubes", 5, "Adequate", "2024-08-14"),
                (6, "PLA 3D Printing Filament Spool 1.75mm White", "CONS-PLA-09", 22, "Spools", 8, "Adequate", "2024-09-18"),
                (6, "Tough Resin 1L Cartridge for Form 3+", "CONS-RSN-10", 4, "Cartridges", 6, "Low Stock", "2024-07-29"),
                (6, "Carbide End Mill CNC Bits Set 1/8 inch", "CONS-CNC-11", 14, "Sets", 5, "Adequate", "2024-08-25"),
                (7, "Nitrile Exam Gloves Powder-Free Medium (100pk)", "CONS-GLV-12", 28, "Boxes", 10, "Adequate", "2024-09-30"),
                (7, "Sterile Filter Pipette Tips 200uL (960pk)", "CONS-PIP-13", 18, "Racks", 8, "Adequate", "2024-09-12"),
                (7, "PCR Tubes 0.2mL Thin-Wall Strips (120pk)", "CONS-PCR-14", 5, "Packs", 10, "Low Stock", "2024-06-18"),
                (8, "Ethanol 70% Molecular Grade Solvent 4L", "CONS-ETH-15", 9, "Bottles", 4, "Adequate", "2024-08-30"),
                (8, "Disposable Quartz UV Cuvettes 10mm Path", "CONS-CUV-16", 2, "Boxes", 5, "Low Stock", "2024-05-19"),
                (9, "HPLC Grade Acetonitrile 99.9% 4L", "CONS-ACN-17", 12, "Bottles", 6, "Adequate", "2024-09-05"),
                (9, "Chromatography Autosampler Vials 2mL (100pk)", "CONS-VIA-18", 34, "Packs", 12, "Adequate", "2024-08-22"),
                (10, "Optics Cleaning Lens Tissue Paper (500 sheets)", "CONS-LNS-19", 15, "Booklets", 5, "Adequate", "2024-09-10"),
                (10, "Argon Gas Cylinder Research Grade 99.999%", "CONS-ARG-20", 1, "Cylinders", 2, "Low Stock", "2024-06-01")
            ]
            cursor.executemany(
                """INSERT INTO consumables (lab_id, item_name, sku, quantity, unit, min_stock_level, reorder_status, last_restocked)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                consumables_data
            )
            print(f"[✓] Seeded consumables ({len(consumables_data)} entries)")

            # -------------------------------------------------------------
            # 9. BORROWINGS
            # -------------------------------------------------------------
            # Find equipment that is "In Use" or previously borrowed
            borrowing_records = []
            now = datetime.now()
            
            # Create a set of 30 borrowings across students and faculty
            for b_idx in range(1, 35):
                eq_id = (b_idx * 3) % total_items_to_seed + 1
                user_id = random.choice([7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18])
                
                if b_idx <= 12:
                    # Currently active / In Use
                    borrow_dt = now - timedelta(days=random.randint(2, 10))
                    expected_dt = now + timedelta(days=random.randint(3, 14))
                    actual_dt = None
                    status = "Issued"
                elif b_idx <= 16:
                    # Overdue
                    borrow_dt = now - timedelta(days=random.randint(18, 30))
                    expected_dt = now - timedelta(days=random.randint(2, 7))
                    actual_dt = None
                    status = "Overdue"
                else:
                    # Completed / Returned
                    borrow_dt = now - timedelta(days=random.randint(30, 90))
                    expected_dt = borrow_dt + timedelta(days=14)
                    actual_dt = borrow_dt + timedelta(days=random.randint(5, 13))
                    status = "Returned"

                purposes = [
                    "Senior Capstone Research Project",
                    "ECE 480 Embedded Systems Laboratory Assignment",
                    "Independent Master Thesis Experimentation",
                    "Faculty Supervised NSF Research Grant Measurements",
                    "Robotics Club Autonomous Rover Prototyping",
                    "Bioinformatics Sample Assay Preparation",
                    "Quantum Optics Interferometry Testing"
                ]

                borrowing_records.append((
                    eq_id, user_id, 
                    borrow_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    expected_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    actual_dt.strftime("%Y-%m-%d %H:%M:%S") if actual_dt else None,
                    status,
                    random.choice(purposes),
                    "Checked out in good condition" if status != "Overdue" else "Notice sent to user regarding overdue return"
                ))

            cursor.executemany(
                """INSERT INTO borrowings (equipment_id, user_id, borrow_date, expected_return_date, actual_return_date, status, purpose, remarks)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                borrowing_records
            )
            print(f"[✓] Seeded borrowings ({len(borrowing_records)} entries)")

            # -------------------------------------------------------------
            # 10. MAINTENANCE
            # -------------------------------------------------------------
            maint_records = []
            maint_types = ["Routine Inspection", "Calibration", "Repair", "Software Update", "Preventive"]
            maint_statuses = ["Completed", "Completed", "Scheduled", "In Progress"]
            technicians = [2, 3, 4, 5, 6]

            for m_idx in range(1, 30):
                eq_id = (m_idx * 4) % total_items_to_seed + 1
                tech_id = random.choice(technicians)
                m_type = random.choice(maint_types)
                m_stat = random.choice(maint_statuses)
                svc_date = (now - timedelta(days=random.randint(5, 200))).strftime("%Y-%m-%d")
                next_date = (now + timedelta(days=random.randint(60, 240))).strftime("%Y-%m-%d")
                cost = round(random.uniform(50.0, 750.0), 2)
                desc = f"{m_type} conducted per ISO/IEC 17025 standards. All test points verified within operational tolerances."

                maint_records.append((
                    eq_id, tech_id, svc_date, m_type, desc, cost, next_date, m_stat
                ))

            cursor.executemany(
                """INSERT INTO maintenance (equipment_id, technician_id, service_date, maintenance_type, description, cost, next_scheduled_date, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                maint_records
            )
            print(f"[✓] Seeded maintenance ({len(maint_records)} entries)")

            # -------------------------------------------------------------
            # 11. TRANSACTIONS
            # -------------------------------------------------------------
            txn_records = []
            txn_types = ["Transfer", "Relocation", "Initial Setup", "Return From Repair"]
            reasons = [
                "Reallocated for cross-departmental grant project",
                "Moved to higher capacity laboratory room",
                "Initial lab commissioning and asset placement",
                "Reinstalled after vendor certified calibration"
            ]

            for t_idx in range(1, 30):
                eq_id = (t_idx * 3) % total_items_to_seed + 1
                from_lab = random.randint(1, 5) if t_idx % 4 != 0 else None
                to_lab = random.randint(6, 10) if from_lab else random.randint(1, 10)
                by_user = random.choice([2, 3, 4, 5, 6])
                t_date = (now - timedelta(days=random.randint(10, 300))).strftime("%Y-%m-%d %H:%M:%S")
                t_type = "Initial Setup" if from_lab is None else random.choice(txn_types)
                reason = random.choice(reasons)

                txn_records.append((
                    eq_id, from_lab, to_lab, by_user, t_date, t_type, reason
                ))

            cursor.executemany(
                """INSERT INTO transactions (equipment_id, from_lab_id, to_lab_id, transferred_by_user_id, transaction_date, transaction_type, reason)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                txn_records
            )
            print(f"[✓] Seeded transactions ({len(txn_records)} entries)")

            # -------------------------------------------------------------
            # 12. PURCHASE ORDERS
            # -------------------------------------------------------------
            po_records = []
            po_statuses = ["Received", "Received", "Approved", "Shipped", "Pending"]
            for p_idx in range(1, 16):
                po_num = f"PO-2024-{p_idx:04d}"
                supp_id = (p_idx % 10) + 1
                ord_by = random.choice([1, 7, 8, 9, 10, 11])
                ord_date = (now - timedelta(days=random.randint(20, 180))).strftime("%Y-%m-%d")
                del_date = (now - timedelta(days=random.randint(1, 15))).strftime("%Y-%m-%d") if p_idx % 2 == 0 else None
                amount = round(random.uniform(2500.0, 48000.0), 2)
                p_stat = random.choice(po_statuses)
                notes = f"Annual departmental procurement package #{p_idx} funded under University Academic Research Fund."

                po_records.append((
                    po_num, supp_id, ord_by, ord_date, del_date, amount, p_stat, notes
                ))

            cursor.executemany(
                """INSERT INTO purchase_orders (po_number, supplier_id, ordered_by_user_id, order_date, delivery_date, total_amount, status, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                po_records
            )
            print(f"[✓] Seeded purchase_orders ({len(po_records)} entries)")

            conn.commit()
            print("\n=======================================================")
            print("  LabTrace Automated Seeding Completed Successfully! ")
            print(f"  Total Equipment Entries: {len(equipment_rows)}")
            print("  All 12 Relational Tables Populated and Linked.")
            print("=======================================================")
            return len(equipment_rows)

    finally:
        conn.close()

if __name__ == "__main__":
    force_seed = "--force" in sys.argv
    seed_database(force=force_seed)
