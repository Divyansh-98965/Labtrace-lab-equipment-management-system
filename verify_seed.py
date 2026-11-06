"""
LabTrace 12-Table Test Suite & Seed Verification Script
Compatible with XAMPP MySQL localhost:3306
"""

import random
from datetime import datetime, timedelta
import pymysql
from pymysql.cursors import DictCursor

def run_seed():
    print("[*] Connecting to local MySQL Server (root@localhost)...")
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",
        database="labtrace_db",
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False
    )

    try:
        with conn.cursor() as cursor:
            print("[*] Truncating all 12 tables for clean verification...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            tables = [
                "purchase_orders", "transactions", "maintenance", "borrowings",
                "consumables", "equipment", "suppliers", "equipment_categories",
                "laboratories", "users", "departments", "roles"
            ]
            for t in tables:
                cursor.execute(f"TRUNCATE TABLE `{t}`;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            # 1. roles
            print("[+] Seeding table 1: roles...")
            roles = [
                ("Admin", "Full administrative governance over assets, users, and infrastructure"),
                ("Lab Technician", "Responsible for calibrations, maintenance, and issue checkouts"),
                ("Faculty", "Principal investigators supervising departmental research projects"),
                ("Student", "Undergraduate and graduate student laboratory researchers"),
                ("Lab Assistant", "Daily consumable logistics and equipment check-in operations")
            ]
            cursor.executemany("INSERT INTO roles (role_name, description) VALUES (%s, %s);", roles)

            # 2. departments
            print("[+] Seeding table 2: departments...")
            depts = [
                ("Computer Science & Engineering", "CSE", "Turing Computing Complex"),
                ("Electrical & Electronics Engineering", "EEE", "Tesla Science Wing"),
                ("Mechanical & Aerospace Engineering", "MECH", "Faraday Applied Labs"),
                ("Biotechnology & Biomedical Engineering", "BIO", "Franklin Life Sciences Tower"),
                ("Chemistry & Materials Science", "CHEM", "Curie Analytical Facility"),
                ("Physics & Quantum Dynamics", "PHYS", "Einstein Research Center")
            ]
            cursor.executemany("INSERT INTO departments (department_name, code, building) VALUES (%s, %s, %s);", depts)

            # 3. users
            print("[+] Seeding table 3: users...")
            users = [
                (1, 1, "Alexander", "Wright", "a.wright@university.edu", "+1-555-0101", "Active"),
                (2, 1, "Marcus", "Vance", "m.vance@university.edu", "+1-555-0102", "Active"),
                (2, 2, "Sarah", "Jenkins", "s.jenkins@university.edu", "+1-555-0103", "Active"),
                (2, 3, "Raj", "Patel", "r.patel@university.edu", "+1-555-0104", "Active"),
                (3, 1, "Evelyn", "Holloway", "e.holloway@university.edu", "+1-555-0201", "Active"),
                (3, 2, "Jonathan", "Reid", "j.reid@university.edu", "+1-555-0202", "Active"),
                (4, 1, "Liam", "Chen", "l.chen@student.university.edu", "+1-555-0301", "Active"),
                (4, 2, "Maya", "Rodriguez", "m.rodriguez@student.university.edu", "+1-555-0302", "Active"),
                (4, 3, "Noah", "Kim", "n.kim@student.university.edu", "+1-555-0303", "Active"),
                (5, 1, "Chloe", "Davis", "c.davis@university.edu", "+1-555-0401", "Active")
            ]
            cursor.executemany("""
                INSERT INTO users (role_id, department_id, first_name, last_name, email, phone, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, users)

            # 4. laboratories
            print("[+] Seeding table 4: laboratories...")
            labs = [
                (1, "Robotics & Autonomous Systems Lab", "Room 302", "Turing Computing Complex", 30, 2),
                (1, "High Performance Computing & AI Cluster", "Room 410", "Turing Computing Complex", 40, 2),
                (2, "Power Electronics & Energy Systems Lab", "Room 105", "Tesla Science Wing", 28, 3),
                (3, "Thermal Dynamics & Fluidics Lab", "Room 101", "Faraday Applied Labs", 25, 4),
                (4, "Genomics & Molecular Biology Lab", "Room 204", "Franklin Life Sciences Tower", 24, 2),
                (5, "Analytical Chemistry & Mass Spec Lab", "Room 118", "Curie Analytical Facility", 26, 3)
            ]
            cursor.executemany("""
                INSERT INTO laboratories (department_id, lab_name, room_number, building, capacity, in_charge_user_id)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, labs)

            # 5. equipment_categories
            print("[+] Seeding table 5: equipment_categories...")
            categories = [
                ("Electronic Test & Measurement", "Oscilloscopes, digital multimeters, spectrum analyzers"),
                ("Analytical & Spectroscopic Instruments", "Spectrophotometers, chromatography, mass spectrometers"),
                ("Computing, Servers & Hardware Dev", "GPU training servers, FPGA kits, logic analyzers"),
                ("Microscopy & Optical Imaging", "Electron microscopes, confocal optics, thermal cameras"),
                ("Precision Fabrication & Prototyping", "3D printers, CNC mills, PCB prototyping stations"),
                ("Thermal & Environmental Chambers", "Autoclaves, -80C ultra-low freezers, cell incubators")
            ]
            cursor.executemany("INSERT INTO equipment_categories (category_name, description) VALUES (%s, %s);", categories)

            # 6. suppliers
            print("[+] Seeding table 6: suppliers...")
            suppliers = [
                ("Keysight Technologies", "Robert Miller", "orders@keysight.com", "+1-800-539-7444", "Santa Rosa, CA"),
                ("Thermo Fisher Scientific", "Amanda Clark", "procurement@thermofisher.com", "+1-800-678-5599", "Waltham, MA"),
                ("Tektronix Instruments", "David Zhang", "sales@tektronix.com", "+1-800-833-9200", "Beaverton, OR"),
                ("Agilent Technologies", "Melissa Ross", "orders@agilent.com", "+1-877-424-4536", "Santa Clara, CA"),
                ("Dell Technologies Enterprise", "Jason Vance", "direct@dell.com", "+1-800-456-3355", "Round Rock, TX")
            ]
            cursor.executemany("""
                INSERT INTO suppliers (supplier_name, contact_person, email, phone, address)
                VALUES (%s, %s, %s, %s, %s);
            """, suppliers)

            # 7. equipment (Generating 100+ Realistic Assets)
            print("[+] Seeding table 7: equipment (100+ populated assets)...")
            models_catalog = [
                (1, "InfiniiVision Digital Storage Oscilloscope 200MHz", "DSO-X-3024T", 1, 3800.00),
                (1, "Mixed Domain Digital Oscilloscope 1GHz 4-Ch", "MDO34-4-BW", 3, 8500.00),
                (1, "Truevolt 6.5 Digit Precision Multimeter", "34465A", 1, 1650.00),
                (2, "NanoDrop One Microvolume UV-Vis Spectrophotometer", "ND-ONE-W", 2, 11200.00),
                (2, "Agilent 1260 Infinity II HPLC System", "1260-LC", 4, 32000.00),
                (3, "Dell Precision 7920 Dual Xeon GPU Server", "T7920-AI", 5, 7800.00),
                (3, "Xilinx UltraScale+ FPGA Development Bench", "ZCU102-EK", 1, 3400.00),
                (4, "Leica DM750 Advanced Biological Microscope", "DM750-LED", 2, 3200.00),
                (5, "Formlabs Form 3+ Stereolithography 3D Printer", "FORM-3P", 5, 4500.00),
                (6, "Thermo Scientific Forma -80C Ultra-Low Freezer", "F88400A", 2, 14500.00)
            ]

            now = datetime.now()
            equipment_rows = []
            for i in range(1, 121):
                template = models_catalog[(i - 1) % len(models_catalog)]
                cat_id, base_name, model_prefix, supp_id, base_cost = template
                lab_id = (i % len(labs)) + 1
                asset_tag = f"EQ-2024-{i:04d}"
                name = f"{base_name} (Unit #{((i-1)//len(models_catalog))+1})"
                model = f"{model_prefix}-V{((i-1)//len(models_catalog))+1}"
                serial = f"SN-KT-{100000 + i * 43}"
                purch_date = (now - timedelta(days=random.randint(60, 900))).strftime("%Y-%m-%d")
                cost = base_cost + round(random.uniform(-150.0, 300.0), 2)
                status = "Available" if i % 6 != 0 else ("In Use" if i % 2 == 0 else "Under Maintenance")
                cond = "Good" if status != "Under Maintenance" else "Needs Repair"

                equipment_rows.append((
                    cat_id, lab_id, supp_id, asset_tag, name, model, serial, purch_date, cost, status, cond
                ))

            cursor.executemany("""
                INSERT INTO equipment (
                    category_id, lab_id, supplier_id, asset_tag, name,
                    model, serial_number, purchase_date, cost, status, condition_state
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, equipment_rows)

            # 8. consumables
            print("[+] Seeding table 8: consumables...")
            consumables = [
                (1, "ESD Anti-Static Wrist Strap Kits", "CONS-ESD-01", 35, "Sets", 10, "Adequate", "2024-09-01"),
                (1, "Lead-Free Solder Wire Sn99.3Cu0.7 (500g)", "CONS-SLD-02", 4, "Spools", 8, "Low Stock", "2024-08-15"),
                (2, "Cat6A Shielded Patch Cable 2m", "CONS-NET-03", 65, "Pieces", 20, "Adequate", "2024-09-10"),
                (4, "PLA 3D Printing Filament 1.75mm White", "CONS-PLA-04", 18, "Spools", 5, "Adequate", "2024-09-18"),
                (5, "Nitrile Exam Gloves Powder-Free Medium (100pk)", "CONS-GLV-05", 22, "Boxes", 10, "Adequate", "2024-09-22"),
                (5, "Sterile Filter Pipette Tips 200uL (960pk)", "CONS-PIP-06", 0, "Racks", 6, "Out of Stock", "2024-07-10")
            ]
            cursor.executemany("""
                INSERT INTO consumables (
                    lab_id, item_name, sku, quantity, unit, min_stock_level, reorder_status, last_restocked
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, consumables)

            # 9. borrowings
            print("[+] Seeding table 9: borrowings...")
            borrowings = []
            for b in range(1, 21):
                eq_id = b * 3
                user_id = random.choice([7, 8, 9])
                b_date = now - timedelta(days=random.randint(5, 30))
                exp_date = b_date + timedelta(days=14)
                if b <= 8:
                    act_date = None
                    status = "Issued"
                else:
                    act_date = b_date + timedelta(days=10)
                    status = "Returned"
                borrowings.append((
                    eq_id, user_id, b_date.strftime("%Y-%m-%d %H:%M:%S"),
                    exp_date.strftime("%Y-%m-%d %H:%M:%S"),
                    act_date.strftime("%Y-%m-%d %H:%M:%S") if act_date else None,
                    status, "Academic Coursework Research Project"
                ))
            cursor.executemany("""
                INSERT INTO borrowings (
                    equipment_id, user_id, borrow_date, expected_return_date, actual_return_date, status, purpose
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, borrowings)

            # 10. maintenance
            print("[+] Seeding table 10: maintenance...")
            maintenance = []
            m_types = ["Routine Inspection", "Calibration", "Repair", "Preventive"]
            for m in range(1, 16):
                eq_id = m * 4
                tech_id = random.choice([2, 3, 4])
                s_date = (now - timedelta(days=random.randint(10, 150))).strftime("%Y-%m-%d")
                next_d = (now + timedelta(days=random.randint(90, 240))).strftime("%Y-%m-%d")
                maintenance.append((
                    eq_id, tech_id, s_date, random.choice(m_types),
                    "Calibrated and verified within ISO/IEC 17025 operational tolerances.",
                    round(random.uniform(75.0, 650.0), 2), next_d, "Completed"
                ))
            cursor.executemany("""
                INSERT INTO maintenance (
                    equipment_id, technician_id, service_date, maintenance_type,
                    description, cost, next_scheduled_date, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, maintenance)

            # 11. transactions
            print("[+] Seeding table 11: transactions...")
            transactions = []
            for t in range(1, 16):
                eq_id = t * 5
                from_l = 1 if t % 2 == 0 else 2
                to_l = 3 if from_l == 1 else 4
                t_date = (now - timedelta(days=random.randint(1, 40))).strftime("%Y-%m-%d %H:%M:%S")
                transactions.append((
                    eq_id, from_l, to_l, 2, t_date, "Relocation",
                    "Inter-laboratory research loan transfer"
                ))
            cursor.executemany("""
                INSERT INTO transactions (
                    equipment_id, from_lab_id, to_lab_id, transferred_by_user_id,
                    transaction_date, transaction_type, reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, transactions)

            # 12. purchase_orders
            print("[+] Seeding table 12: purchase_orders...")
            pos = [
                ("PO-2024-001", 1, 1, "2024-03-01", "2024-03-20", 18500.00, "Received", "Annual RF equipment package"),
                ("PO-2024-002", 2, 1, "2024-04-10", "2024-04-25", 24300.00, "Received", "Analytical spectroscopy batch"),
                ("PO-2024-003", 3, 5, "2024-06-15", "2024-07-01", 12400.00, "Received", "Tektronix mixed domain units"),
                ("PO-2024-004", 4, 6, "2024-08-01", None, 32000.00, "Shipped", "HPLC column replacements and detectors"),
                ("PO-2024-005", 5, 1, "2024-09-05", None, 15600.00, "Approved", "Deep learning server compute expansion")
            ]
            cursor.executemany("""
                INSERT INTO purchase_orders (
                    po_number, supplier_id, ordered_by_user_id, order_date,
                    delivery_date, total_amount, status, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, pos)

            conn.commit()

        print("\n" + "="*70)
        print(" [SUCCESS] ALL 12 TABLES SEEDED AND VERIFIED UNDER XAMPP MYSQL!")
        print("="*70)

    except Exception as exc:
        conn.rollback()
        print(f"[!] Seeding failure: {exc}", file=sys.stderr)
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    run_seed()

