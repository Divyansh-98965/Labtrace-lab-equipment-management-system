"""
LabTrace - Laboratory Equipment & Inventory Management System
Flask Backend Application connected to MySQL (localhost, root, no password, labtrace_db)
Compatible with XAMPP phpMyAdmin and 12-table relational schema.
"""

import csv
import io
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify, Response, session
)
import pymysql
from pymysql.cursors import DictCursor
from config import Config
from db import get_db_connection
from seed import seed_database
from blueprints.analysis import analysis_bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(analysis_bp)

# Hardcoded Authentication Credentials
DEMO_USERNAME = "admin@Labtrace"
DEMO_PASSWORD = "password"

@app.before_request
def require_login():
    """
    Enforces authentication across all routes except login, logout, and static assets.
    """
    # Allow login, static files, and error handling without session
    if request.endpoint in ("login", "logout", "static") or (request.endpoint and request.endpoint.startswith("static")) or request.path.startswith("/static"):
        return None
    
    # Require login for all operational and analysis routes
    if not session.get("logged_in"):
        return redirect(url_for("login", next=request.path))

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Single-user login endpoint.
    Accepts hardcoded demo credentials: admin@Labtrace / password.
    """
    if session.get("logged_in"):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Support case-insensitive email match while requiring exact password
        if username.lower() == DEMO_USERNAME.lower() and password == DEMO_PASSWORD:
            session["logged_in"] = True
            session["user"] = DEMO_USERNAME
            flash("Welcome to LabTrace! Successfully authenticated as Administrator.", "success")
            
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password. Please use the demo credentials provided below.", "danger")
            return render_template("login.html", username=username)

    return render_template("login.html")

@app.route("/logout")
def logout():
    """
    Clears the session and redirects to login.
    """
    session.clear()
    flash("You have been signed out of LabTrace.", "info")
    return redirect(url_for("login"))

# Ensure database and seeds are ready on launch
try:
    seed_database(force=False)
except Exception as e:
    print(f"[Warning] Startup database check encountered an issue: {e}")

# Helper function to get lookup options (categories, labs, suppliers, users)
def get_form_lookups():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT category_id, category_name FROM equipment_categories ORDER BY category_name ASC")
            categories = cursor.fetchall()

            cursor.execute("""
                SELECT l.lab_id, l.lab_name, l.room_number, l.building, d.code AS dept_code
                FROM laboratories l
                JOIN departments d ON l.department_id = d.department_id
                ORDER BY l.lab_name ASC
            """)
            labs = cursor.fetchall()

            cursor.execute("SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_name ASC")
            suppliers = cursor.fetchall()

            cursor.execute("""
                SELECT u.user_id, CONCAT(u.first_name, ' ', u.last_name) AS full_name, r.role_name
                FROM users u
                JOIN roles r ON u.role_id = r.role_id
                ORDER BY u.first_name ASC
            """)
            users = cursor.fetchall()

            return {
                "categories": categories,
                "labs": labs,
                "suppliers": suppliers,
                "users": users
            }
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 1. Main Dashboard & Equipment Inventory
# -----------------------------------------------------------------------------
@app.route("/")
@app.route("/dashboard")
def index():
    """
    Main dashboard: Displays KPIs and the equipment inventory data table
    with search, filter, and pagination support.
    """
    search_query = request.args.get("q", "").strip()
    category_id = request.args.get("category", "").strip()
    lab_id = request.args.get("lab", "").strip()
    status_filter = request.args.get("status", "").strip()
    condition_filter = request.args.get("condition", "").strip()
    
    # Pagination
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    
    per_page_param = request.args.get("per_page", "25")
    if per_page_param == "all":
        per_page = 500
    else:
        try:
            per_page = max(5, int(per_page_param))
        except ValueError:
            per_page = 25

    offset = (page - 1) * per_page

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Dashboard Metrics (KPIs)
            cursor.execute("""
                SELECT 
                    COUNT(*) AS total_equipment,
                    SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) AS total_available,
                    SUM(CASE WHEN status = 'In Use' THEN 1 ELSE 0 END) AS total_in_use,
                    SUM(CASE WHEN status = 'Under Maintenance' THEN 1 ELSE 0 END) AS total_maintenance,
                    SUM(cost) AS total_valuation
                FROM equipment
            """)
            stats = cursor.fetchone() or {}

            cursor.execute("SELECT COUNT(*) AS total_labs FROM laboratories")
            stats["total_labs"] = cursor.fetchone()["total_labs"]

            cursor.execute("SELECT COUNT(*) AS low_stock FROM consumables WHERE reorder_status IN ('Low Stock', 'Out of Stock')")
            stats["low_stock_consumables"] = cursor.fetchone()["low_stock"]

            cursor.execute("SELECT COUNT(*) AS active_borrowings FROM borrowings WHERE status IN ('Issued', 'Overdue')")
            stats["active_borrowings"] = cursor.fetchone()["active_borrowings"]

            # 2. Build Query with Filters
            where_clauses = ["1=1"]
            params = []

            if search_query:
                where_clauses.append("""
                    (e.asset_tag LIKE %s 
                     OR e.name LIKE %s 
                     OR e.model LIKE %s 
                     OR e.serial_number LIKE %s 
                     OR s.supplier_name LIKE %s
                     OR c.category_name LIKE %s)
                """)
                search_term = f"%{search_query}%"
                params.extend([search_term, search_term, search_term, search_term, search_term, search_term])

            if category_id:
                where_clauses.append("e.category_id = %s")
                params.append(category_id)

            if lab_id:
                where_clauses.append("e.lab_id = %s")
                params.append(lab_id)

            if status_filter:
                where_clauses.append("e.status = %s")
                params.append(status_filter)

            if condition_filter:
                where_clauses.append("e.condition_state = %s")
                params.append(condition_filter)

            where_sql = " AND ".join(where_clauses)

            # Count total matching records for pagination
            count_sql = f"""
                SELECT COUNT(*) AS filtered_count
                FROM equipment e
                JOIN equipment_categories c ON e.category_id = c.category_id
                JOIN laboratories l ON e.lab_id = l.lab_id
                LEFT JOIN suppliers s ON e.supplier_id = s.supplier_id
                WHERE {where_sql}
            """
            cursor.execute(count_sql, tuple(params))
            total_records = cursor.fetchone()["filtered_count"]

            # Query the page of equipment
            query_sql = f"""
                SELECT 
                    e.equipment_id,
                    e.asset_tag,
                    e.name,
                    e.model,
                    e.serial_number,
                    e.purchase_date,
                    e.cost,
                    e.status,
                    e.condition_state,
                    e.category_id,
                    e.lab_id,
                    e.supplier_id,
                    c.category_name,
                    l.lab_name,
                    l.room_number,
                    l.building,
                    s.supplier_name
                FROM equipment e
                JOIN equipment_categories c ON e.category_id = c.category_id
                JOIN laboratories l ON e.lab_id = l.lab_id
                LEFT JOIN suppliers s ON e.supplier_id = s.supplier_id
                WHERE {where_sql}
                ORDER BY e.equipment_id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query_sql, tuple(params + [per_page, offset]))
            equipment_list = cursor.fetchall()

            # Lookup data for dropdowns in modals & filters
            lookups = get_form_lookups()

            total_pages = max(1, (total_records + per_page - 1) // per_page)

            return render_template(
                "index.html",
                equipment_list=equipment_list,
                stats=stats,
                lookups=lookups,
                search_query=search_query,
                selected_category=category_id,
                selected_lab=lab_id,
                selected_status=status_filter,
                selected_condition=condition_filter,
                page=page,
                total_pages=total_pages,
                per_page=per_page_param,
                total_records=total_records
            )
    finally:
        conn.close()

# -----------------------------------------------------------------------------
# 2. Equipment CRUD Routes
# -----------------------------------------------------------------------------
@app.route("/equipment/create", methods=["POST"])
def create_equipment():
    """Create a new equipment entry in the database."""
    name = request.form.get("name", "").strip()
    category_id = request.form.get("category_id")
    lab_id = request.form.get("lab_id")
    supplier_id = request.form.get("supplier_id") or None
    asset_tag = request.form.get("asset_tag", "").strip()
    model = request.form.get("model", "").strip() or None
    serial_number = request.form.get("serial_number", "").strip() or None
    purchase_date = request.form.get("purchase_date") or None
    cost = request.form.get("cost", "0.00").strip() or 0.00
    status = request.form.get("status", "Available")
    condition_state = request.form.get("condition_state", "Good")

    if not name or not category_id or not lab_id or not asset_tag:
        flash("Please fill in all required fields (Name, Category, Laboratory, Asset Tag).", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check for unique asset tag
            cursor.execute("SELECT equipment_id FROM equipment WHERE asset_tag = %s", (asset_tag,))
            if cursor.fetchone():
                flash(f"An equipment asset with tag '{asset_tag}' already exists.", "warning")
                return redirect(url_for("index"))

            # Check for unique serial number if provided
            if serial_number:
                cursor.execute("SELECT equipment_id FROM equipment WHERE serial_number = %s", (serial_number,))
                if cursor.fetchone():
                    flash(f"An asset with serial number '{serial_number}' already exists.", "warning")
                    return redirect(url_for("index"))

            cursor.execute("""
                INSERT INTO equipment 
                (category_id, lab_id, supplier_id, asset_tag, name, model, serial_number, purchase_date, cost, status, condition_state)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (category_id, lab_id, supplier_id, asset_tag, name, model, serial_number, purchase_date, cost, status, condition_state))
            
            # Log initial setup in transactions table
            new_eq_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO transactions (equipment_id, from_lab_id, to_lab_id, transferred_by_user_id, transaction_date, transaction_type, reason)
                VALUES (%s, NULL, %s, 1, NOW(), 'Initial Setup', 'Newly registered equipment intake')
            """, (new_eq_id, lab_id))

        flash(f"Equipment '{name}' ({asset_tag}) was successfully added to inventory!", "success")
    except Exception as e:
        flash(f"Database error while creating equipment: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("index"))


@app.route("/equipment/<int:equipment_id>/json")
def get_equipment_json(equipment_id):
    """API endpoint to get single equipment details for modals or AJAX."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    e.*,
                    c.category_name,
                    l.lab_name,
                    l.room_number,
                    l.building,
                    s.supplier_name,
                    s.contact_person AS supplier_contact,
                    s.phone AS supplier_phone,
                    s.email AS supplier_email
                FROM equipment e
                JOIN equipment_categories c ON e.category_id = c.category_id
                JOIN laboratories l ON e.lab_id = l.lab_id
                LEFT JOIN suppliers s ON e.supplier_id = s.supplier_id
                WHERE e.equipment_id = %s
            """, (equipment_id,))
            item = cursor.fetchone()
            if not item:
                return jsonify({"error": "Equipment not found"}), 404
            
            # Convert dates & decimals for JSON serialization
            if item.get("purchase_date"):
                item["purchase_date"] = str(item["purchase_date"])
            if item.get("cost"):
                item["cost"] = float(item["cost"])
            if item.get("created_at"):
                item["created_at"] = str(item["created_at"])
            if item.get("updated_at"):
                item["updated_at"] = str(item["updated_at"])

            return jsonify(item)
    finally:
        conn.close()


@app.route("/equipment/<int:equipment_id>/edit", methods=["POST"])
def update_equipment(equipment_id):
    """Update existing equipment details."""
    name = request.form.get("name", "").strip()
    category_id = request.form.get("category_id")
    lab_id = request.form.get("lab_id")
    supplier_id = request.form.get("supplier_id") or None
    asset_tag = request.form.get("asset_tag", "").strip()
    model = request.form.get("model", "").strip() or None
    serial_number = request.form.get("serial_number", "").strip() or None
    purchase_date = request.form.get("purchase_date") or None
    cost = request.form.get("cost", "0.00").strip() or 0.00
    status = request.form.get("status", "Available")
    condition_state = request.form.get("condition_state", "Good")

    if not name or not category_id or not lab_id or not asset_tag:
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check asset tag collision
            cursor.execute(
                "SELECT equipment_id FROM equipment WHERE asset_tag = %s AND equipment_id != %s", 
                (asset_tag, equipment_id)
            )
            if cursor.fetchone():
                flash(f"Asset tag '{asset_tag}' is already used by another item.", "warning")
                return redirect(url_for("index"))

            # Check original lab for transfer transaction logging
            cursor.execute("SELECT lab_id FROM equipment WHERE equipment_id = %s", (equipment_id,))
            current = cursor.fetchone()
            if current and int(current["lab_id"]) != int(lab_id):
                # Log relocation transaction
                cursor.execute("""
                    INSERT INTO transactions (equipment_id, from_lab_id, to_lab_id, transferred_by_user_id, transaction_date, transaction_type, reason)
                    VALUES (%s, %s, %s, 1, NOW(), 'Relocation', 'Equipment relocated via inventory management dashboard')
                """, (equipment_id, current["lab_id"], lab_id))

            cursor.execute("""
                UPDATE equipment 
                SET category_id = %s,
                    lab_id = %s,
                    supplier_id = %s,
                    asset_tag = %s,
                    name = %s,
                    model = %s,
                    serial_number = %s,
                    purchase_date = %s,
                    cost = %s,
                    status = %s,
                    condition_state = %s
                WHERE equipment_id = %s
            """, (category_id, lab_id, supplier_id, asset_tag, name, model, serial_number, purchase_date, cost, status, condition_state, equipment_id))

        flash(f"Equipment '{name}' ({asset_tag}) updated successfully!", "success")
    except Exception as e:
        flash(f"Database error while updating equipment: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("index"))


@app.route("/equipment/<int:equipment_id>/delete", methods=["POST"])
def delete_equipment(equipment_id):
    """Delete an equipment asset and its cascade records."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name, asset_tag FROM equipment WHERE equipment_id = %s", (equipment_id,))
            item = cursor.fetchone()
            if not item:
                flash("Equipment asset not found.", "warning")
                return redirect(url_for("index"))

            cursor.execute("DELETE FROM equipment WHERE equipment_id = %s", (equipment_id,))
        flash(f"Asset '{item['name']}' ({item['asset_tag']}) has been permanently deleted.", "info")
    except Exception as e:
        flash(f"Error deleting equipment: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("index"))


@app.route("/equipment/export")
def export_equipment():
    """Export current equipment inventory as a downloadable CSV file."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    e.equipment_id,
                    e.asset_tag,
                    e.name,
                    c.category_name,
                    l.lab_name,
                    l.room_number,
                    l.building,
                    s.supplier_name,
                    e.model,
                    e.serial_number,
                    e.purchase_date,
                    e.cost,
                    e.status,
                    e.condition_state,
                    e.created_at
                FROM equipment e
                JOIN equipment_categories c ON e.category_id = c.category_id
                JOIN laboratories l ON e.lab_id = l.lab_id
                LEFT JOIN suppliers s ON e.supplier_id = s.supplier_id
                ORDER BY e.equipment_id ASC
            """)
            rows = cursor.fetchall()

        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow([
            "ID", "Asset Tag", "Equipment Name", "Category", "Laboratory", 
            "Room", "Building", "Supplier", "Model", "Serial Number", 
            "Purchase Date", "Cost (USD)", "Status", "Condition", "Date Added"
        ])
        for r in rows:
            writer.writerow([
                r["equipment_id"], r["asset_tag"], r["name"], r["category_name"],
                r["lab_name"], r["room_number"], r["building"], r.get("supplier_name") or "N/A",
                r.get("model") or "", r.get("serial_number") or "",
                r.get("purchase_date") or "", f"{float(r['cost']):.2f}",
                r["status"], r["condition_state"], r.get("created_at") or ""
            ])

        output = si.getvalue()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=labtrace_equipment_inventory.csv"}
        )
    finally:
        conn.close()


@app.route("/database/seed", methods=["POST"])
def trigger_seed():
    """Allows manual re-seeding or resetting of the 100+ database records."""
    force = request.form.get("force") == "true"
    try:
        count = seed_database(force=force)
        flash(f"Database successfully seeded! {count} equipment records now active across all 12 tables.", "success")
    except Exception as e:
        flash(f"Error during seeding: {str(e)}", "danger")
    return redirect(url_for("index"))

# -----------------------------------------------------------------------------
# 3. Relational Table Views (Laboratories, Borrowings, Maintenance, Consumables, Schema)
# -----------------------------------------------------------------------------
@app.route("/laboratories")
def laboratories():
    """View all university laboratories, buildings, managers and assigned equipment count."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    l.lab_id,
                    l.lab_name,
                    l.room_number,
                    l.building,
                    l.capacity,
                    d.department_name,
                    d.code AS dept_code,
                    CONCAT(u.first_name, ' ', u.last_name) AS manager_name,
                    u.email AS manager_email,
                    COUNT(e.equipment_id) AS equipment_count,
                    COALESCE(SUM(e.cost), 0) AS total_lab_value
                FROM laboratories l
                JOIN departments d ON l.department_id = d.department_id
                LEFT JOIN users u ON l.in_charge_user_id = u.user_id
                LEFT JOIN equipment e ON l.lab_id = e.lab_id
                GROUP BY l.lab_id
                ORDER BY l.lab_name ASC
            """)
            labs = cursor.fetchall()
            return render_template("laboratories.html", labs=labs)
    finally:
        conn.close()


@app.route("/borrowings")
def borrowings():
    """View equipment issue, checkout, and return logs."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    b.borrowing_id,
                    b.equipment_id,
                    b.user_id,
                    b.borrow_date,
                    b.expected_return_date,
                    b.actual_return_date,
                    b.status,
                    b.purpose,
                    b.remarks,
                    e.name AS equipment_name,
                    e.asset_tag,
                    CONCAT(u.first_name, ' ', u.last_name) AS borrower_name,
                    u.email AS borrower_email,
                    r.role_name
                FROM borrowings b
                JOIN equipment e ON b.equipment_id = e.equipment_id
                JOIN users u ON b.user_id = u.user_id
                JOIN roles r ON u.role_id = r.role_id
                ORDER BY b.borrow_date DESC
            """)
            borrowing_list = cursor.fetchall()
            lookups = get_form_lookups()
            return render_template("borrowings.html", borrowings=borrowing_list, lookups=lookups)
    finally:
        conn.close()


@app.route("/borrowings/create", methods=["POST"])
def create_borrowing():
    """Issue equipment to a user."""
    equipment_id = request.form.get("equipment_id")
    user_id = request.form.get("user_id")
    borrow_date = request.form.get("borrow_date")
    expected_return_date = request.form.get("expected_return_date")
    purpose = request.form.get("purpose", "")

    if not equipment_id or not user_id or not borrow_date or not expected_return_date:
        flash("All borrowing fields are required.", "danger")
        return redirect(url_for("borrowings"))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO borrowings (equipment_id, user_id, borrow_date, expected_return_date, status, purpose)
                VALUES (%s, %s, %s, %s, 'Issued', %s)
            """, (equipment_id, user_id, borrow_date, expected_return_date, purpose))

            cursor.execute("UPDATE equipment SET status = 'In Use' WHERE equipment_id = %s", (equipment_id,))
        flash("Equipment checkout logged successfully!", "success")
    except Exception as e:
        flash(f"Error logging checkout: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("borrowings"))


@app.route("/borrowings/<int:borrowing_id>/return", methods=["POST"])
def return_borrowing(borrowing_id):
    """Mark borrowed equipment as returned."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT equipment_id FROM borrowings WHERE borrowing_id = %s", (borrowing_id,))
            b = cursor.fetchone()
            if b:
                cursor.execute("""
                    UPDATE borrowings 
                    SET status = 'Returned', actual_return_date = NOW() 
                    WHERE borrowing_id = %s
                """, (borrowing_id,))
                cursor.execute("UPDATE equipment SET status = 'Available' WHERE equipment_id = %s", (b["equipment_id"],))
                flash("Equipment returned and marked Available in inventory.", "success")
            else:
                flash("Borrowing record not found.", "warning")
    except Exception as e:
        flash(f"Error updating return: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for("borrowings"))


@app.route("/maintenance")
def maintenance():
    """View maintenance and calibration logs."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    m.maintenance_id,
                    m.service_date,
                    m.maintenance_type,
                    m.description,
                    m.cost,
                    m.next_scheduled_date,
                    m.status,
                    e.name AS equipment_name,
                    e.asset_tag,
                    CONCAT(u.first_name, ' ', u.last_name) AS technician_name
                FROM maintenance m
                JOIN equipment e ON m.equipment_id = e.equipment_id
                LEFT JOIN users u ON m.technician_id = u.user_id
                ORDER BY m.service_date DESC
            """)
            logs = cursor.fetchall()
            lookups = get_form_lookups()
            return render_template("maintenance.html", logs=logs, lookups=lookups)
    finally:
        conn.close()


@app.route("/consumables")
def consumables():
    """View laboratory consumables, supplies, and stock levels."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.consumable_id,
                    c.item_name,
                    c.sku,
                    c.quantity,
                    c.unit,
                    c.min_stock_level,
                    c.reorder_status,
                    c.last_restocked,
                    l.lab_name,
                    l.room_number,
                    l.building
                FROM consumables c
                JOIN laboratories l ON c.lab_id = l.lab_id
                ORDER BY 
                    CASE c.reorder_status 
                        WHEN 'Out of Stock' THEN 1 
                        WHEN 'Low Stock' THEN 2 
                        ELSE 3 
                    END, c.item_name ASC
            """)
            items = cursor.fetchall()
            return render_template("consumables.html", consumables=items)
    finally:
        conn.close()


@app.route("/consumables/<int:consumable_id>/restock", methods=["POST"])
def restock_consumable(consumable_id):
    """Add stock to a consumable supply."""
    add_qty = int(request.form.get("quantity", 10))
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT quantity, min_stock_level FROM consumables WHERE consumable_id = %s", (consumable_id,))
            c = cursor.fetchone()
            if c:
                new_qty = c["quantity"] + add_qty
                new_status = "Adequate" if new_qty > c["min_stock_level"] else ("Low Stock" if new_qty > 0 else "Out of Stock")
                cursor.execute("""
                    UPDATE consumables 
                    SET quantity = %s, reorder_status = %s, last_restocked = CURDATE()
                    WHERE consumable_id = %s
                """, (new_qty, new_status, consumable_id))
                flash(f"Consumable restocked! New quantity is {new_qty}.", "success")
    except Exception as e:
        flash(f"Error updating stock: {str(e)}", "danger")
    finally:
        conn.close()
    return redirect(url_for("consumables"))


@app.route("/schema-viewer")
def schema_viewer():
    """
    Relational Database Schema Explorer:
    Shows all 12 tables, their exact structure, row counts, and relational foreign keys.
    """
    conn = get_db_connection()
    table_metadata = [
        {"name": "roles", "desc": "User permissions and access roles (e.g., Admin, Student, Technician)", "fks": []},
        {"name": "departments", "desc": "University academic & engineering departments", "fks": []},
        {"name": "users", "desc": "Students, faculty, technicians, administrators", "fks": ["roles.role_id", "departments.department_id"]},
        {"name": "laboratories", "desc": "Labs, buildings, and physical locations", "fks": ["departments.department_id", "users.user_id"]},
        {"name": "equipment_categories", "desc": "Equipment classification and asset taxonomy", "fks": []},
        {"name": "suppliers", "desc": "Supplier information, vendors, and contact details", "fks": []},
        {"name": "equipment", "desc": "Individual equipment assets", "fks": ["equipment_categories.category_id", "laboratories.lab_id", "suppliers.supplier_id"]},
        {"name": "consumables", "desc": "Laboratory supplies, units, and inventory thresholds", "fks": ["laboratories.lab_id"]},
        {"name": "borrowings", "desc": "Equipment issue, checkout, and return logs", "fks": ["equipment.equipment_id", "users.user_id"]},
        {"name": "maintenance", "desc": "Repairs, servicing, and calibration history", "fks": ["equipment.equipment_id", "users.user_id"]},
        {"name": "transactions", "desc": "Equipment transfers and physical location movements", "fks": ["equipment.equipment_id", "laboratories.lab_id", "users.user_id"]},
        {"name": "purchase_orders", "desc": "Procurement orders, PO numbers, and vendor invoices", "fks": ["suppliers.supplier_id", "users.user_id"]}
    ]

    try:
        with conn.cursor() as cursor:
            for t in table_metadata:
                cursor.execute(f"SELECT COUNT(*) AS cnt FROM `{t['name']}`")
                t["count"] = cursor.fetchone()["cnt"]

                cursor.execute(f"DESCRIBE `{t['name']}`")
                t["columns"] = cursor.fetchall()
            
            # Fetch recent transactions
            cursor.execute("""
                SELECT 
                    t.transaction_id,
                    t.transaction_date,
                    t.transaction_type,
                    t.reason,
                    e.name AS equipment_name,
                    e.asset_tag,
                    l_from.lab_name AS from_lab,
                    l_to.lab_name AS to_lab,
                    CONCAT(u.first_name, ' ', u.last_name) AS actor
                FROM transactions t
                JOIN equipment e ON t.equipment_id = e.equipment_id
                LEFT JOIN laboratories l_from ON t.from_lab_id = l_from.lab_id
                JOIN laboratories l_to ON t.to_lab_id = l_to.lab_id
                LEFT JOIN users u ON t.transferred_by_user_id = u.user_id
                ORDER BY t.transaction_date DESC
                LIMIT 10
            """)
            recent_txns = cursor.fetchall()

            # Fetch recent POs
            cursor.execute("""
                SELECT 
                    po.po_number,
                    po.order_date,
                    po.total_amount,
                    po.status,
                    s.supplier_name,
                    CONCAT(u.first_name, ' ', u.last_name) AS ordered_by
                FROM purchase_orders po
                JOIN suppliers s ON po.supplier_id = s.supplier_id
                LEFT JOIN users u ON po.ordered_by_user_id = u.user_id
                ORDER BY po.order_date DESC
                LIMIT 10
            """)
            recent_pos = cursor.fetchall()

            return render_template(
                "tables.html", 
                tables=table_metadata, 
                recent_txns=recent_txns, 
                recent_pos=recent_pos
            )
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

