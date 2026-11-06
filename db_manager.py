"""
LabTrace Database Connection & Operations Manager
Connects to local XAMPP MySQL/MariaDB server and handles atomic transactions.
"""

import sys
from typing import Any, Dict, List, Optional
import pymysql
from pymysql.cursors import DictCursor

class DatabaseManager:
    """Manages transactional database connections and parameterized queries."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "labtrace_db"
    ):
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
            "autocommit": False  # Enforces manual transaction control
        }

    def get_connection(self) -> pymysql.Connection:
        """Establishes and returns an active MySQL connection."""
        try:
            return pymysql.connect(**self.config)
        except pymysql.MySQLError as err:
            print(f"[ERROR] Failed connecting to XAMPP MySQL: {err}", file=sys.stderr)
            raise

    # -------------------------------------------------------------------------
    # Core CRUD Functions
    # -------------------------------------------------------------------------

    def create_equipment(
        self,
        category_id: int,
        lab_id: int,
        asset_tag: str,
        name: str,
        cost: float,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        supplier_id: Optional[int] = None,
        purchase_date: Optional[str] = None,
        condition_state: str = "Good"
    ) -> int:
        """
        Creates a new equipment record and atomically logs its initial setup
        transaction in a single ACID transaction.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. Insert Equipment Record
                sql_insert_eq = """
                    INSERT INTO equipment (
                        category_id, lab_id, supplier_id, asset_tag, name,
                        model, serial_number, purchase_date, cost, status, condition_state
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Available', %s);
                """
                cursor.execute(sql_insert_eq, (
                    category_id, lab_id, supplier_id, asset_tag, name,
                    model, serial_number, purchase_date, cost, condition_state
                ))
                new_equipment_id = cursor.lastrowid

                # 2. Insert Commissioning Transaction
                sql_insert_txn = """
                    INSERT INTO transactions (
                        equipment_id, from_lab_id, to_lab_id, transferred_by_user_id,
                        transaction_date, transaction_type, reason
                    ) VALUES (%s, NULL, %s, 1, NOW(), 'Initial Setup', 'Commissioning intake into lab');
                """
                cursor.execute(sql_insert_txn, (new_equipment_id, lab_id))

            conn.commit()
            return new_equipment_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_equipment_by_id(self, equipment_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves an equipment asset with resolved relational foreign keys."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT 
                        e.equipment_id, e.asset_tag, e.name, e.model, e.serial_number,
                        e.purchase_date, e.cost, e.status, e.condition_state,
                        c.category_name,
                        l.lab_name, l.room_number, l.building,
                        s.supplier_name, s.contact_person AS supplier_contact
                    FROM equipment e
                    JOIN equipment_categories c ON e.category_id = c.category_id
                    JOIN laboratories l ON e.lab_id = l.lab_id
                    LEFT JOIN suppliers s ON e.supplier_id = s.supplier_id
                    WHERE e.equipment_id = %s;
                """
                cursor.execute(sql, (equipment_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    def relocate_equipment(
        self,
        equipment_id: int,
        target_lab_id: int,
        acting_user_id: int,
        reason: str
    ) -> bool:
        """
        Relocates an asset to a new laboratory and records the movement audit log.
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT lab_id FROM equipment WHERE equipment_id = %s FOR UPDATE;", (equipment_id,))
                row = cursor.fetchone()
                if not row:
                    raise ValueError(f"Equipment with ID {equipment_id} not found.")

                source_lab_id = row["lab_id"]
                if source_lab_id == target_lab_id:
                    return False

                cursor.execute(
                    "UPDATE equipment SET lab_id = %s WHERE equipment_id = %s;",
                    (target_lab_id, equipment_id)
                )

                cursor.execute("""
                    INSERT INTO transactions (
                        equipment_id, from_lab_id, to_lab_id, transferred_by_user_id,
                        transaction_date, transaction_type, reason
                    ) VALUES (%s, %s, %s, %s, NOW(), 'Relocation', %s);
                """, (equipment_id, source_lab_id, target_lab_id, acting_user_id, reason))

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def issue_borrowing(
        self,
        equipment_id: int,
        user_id: int,
        expected_return_date: str,
        purpose: str
    ) -> int:
        """Issues an available piece of equipment to an authorized user."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT status FROM equipment WHERE equipment_id = %s FOR UPDATE;",
                    (equipment_id,)
                )
                eq = cursor.fetchone()
                if not eq:
                    raise ValueError("Asset not found.")
                if eq["status"] != "Available":
                    raise ValueError(f"Asset is currently '{eq['status']}' and cannot be issued.")

                cursor.execute("""
                    INSERT INTO borrowings (
                        equipment_id, user_id, borrow_date, expected_return_date,
                        status, purpose
                    ) VALUES (%s, %s, NOW(), %s, 'Issued', %s);
                """, (equipment_id, user_id, expected_return_date, purpose))
                borrowing_id = cursor.lastrowid

                cursor.execute(
                    "UPDATE equipment SET status = 'In Use' WHERE equipment_id = %s;",
                    (equipment_id,)
                )

            conn.commit()
            return borrowing_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def return_borrowing(self, borrowing_id: int) -> bool:
        """Records return of an asset and restores Available status."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT equipment_id, status FROM borrowings WHERE borrowing_id = %s FOR UPDATE;",
                    (borrowing_id,)
                )
                b = cursor.fetchone()
                if not b or b["status"] == "Returned":
                    return False

                cursor.execute("""
                    UPDATE borrowings 
                    SET status = 'Returned', actual_return_date = NOW() 
                    WHERE borrowing_id = %s;
                """, (borrowing_id,))

                cursor.execute(
                    "UPDATE equipment SET status = 'Available' WHERE equipment_id = %s;",
                    (b["equipment_id"],)
                )

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def restock_consumable(self, consumable_id: int, added_quantity: int) -> int:
        """Restocks a consumable supply and updates reorder status dynamically."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT quantity, min_stock_level FROM consumables WHERE consumable_id = %s FOR UPDATE;",
                    (consumable_id,)
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Consumable not found.")

                new_quantity = row["quantity"] + added_quantity
                min_threshold = row["min_stock_level"]

                if new_quantity == 0:
                    status = "Out of Stock"
                elif new_quantity <= min_threshold:
                    status = "Low Stock"
                else:
                    status = "Adequate"

                cursor.execute("""
                    UPDATE consumables 
                    SET quantity = %s, reorder_status = %s, last_restocked = CURDATE()
                    WHERE consumable_id = %s;
                """, (new_quantity, status, consumable_id))

            conn.commit()
            return new_quantity
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

