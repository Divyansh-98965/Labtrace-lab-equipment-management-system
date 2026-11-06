"""
LabTrace - Database Theory & Schema Analysis Blueprint
Provides interactive routes and mathematical proofs for ER modeling,
relational schema mapping, normalization up to BCNF, lossless join decomposition,
dependency preservation, and minimal cover derivations.
"""

from flask import Blueprint, render_template, jsonify
from db import get_db_connection

analysis_bp = Blueprint("analysis", __name__, url_prefix="/analysis", template_folder="../templates/analysis")

@analysis_bp.route("/")
def index():
    """Analysis Dashboard: Schema Overview, Metrics, and Normalization Scorecard."""
    conn = get_db_connection()
    table_stats = []
    try:
        with conn.cursor() as cursor:
            tables = [
                ("roles", "User permissions and RBAC roles", "BCNF", 0),
                ("departments", "Academic and research divisions", "BCNF", 0),
                ("users", "Students, faculty, technicians, admins", "BCNF", 2),
                ("laboratories", "Physical research facilities & rooms", "BCNF", 2),
                ("equipment_categories", "Asset classification taxonomy", "BCNF", 0),
                ("suppliers", "Vendors, manufacturers, distributors", "BCNF", 0),
                ("equipment", "Individual serialized equipment assets", "BCNF", 3),
                ("consumables", "Reagents, supplies, stock thresholds", "BCNF", 1),
                ("borrowings", "Equipment checkout and return log", "BCNF", 2),
                ("maintenance", "Calibration, servicing & repairs", "BCNF", 2),
                ("transactions", "Movement & relocation audit trail", "BCNF", 4),
                ("purchase_orders", "Procurement & vendor orders", "BCNF", 2)
            ]
            for name, desc, nf, fk_count in tables:
                cursor.execute(f"SELECT COUNT(*) AS count FROM `{name}`")
                row = cursor.fetchone()
                table_stats.append({
                    "name": name,
                    "description": desc,
                    "normal_form": nf,
                    "fk_count": fk_count,
                    "row_count": row["count"] if row else 0
                })
    finally:
        conn.close()

    total_rows = sum(t["row_count"] for t in table_stats)
    return render_template(
        "analysis/index.html",
        table_stats=table_stats,
        total_tables=len(table_stats),
        total_rows=total_rows
    )

@analysis_bp.route("/er-diagram")
def er_diagram():
    """Interactive ER Diagram Visualization: Crow's Foot & Chen-style notations."""
    return render_template("analysis/er_diagram.html")

@analysis_bp.route("/mapping")
def mapping():
    """ER-to-Relational Mapping Interactive Guide & Complete SQL DDL Script."""
    mapping_rules = [
        {
            "step": 1,
            "rule": "Strong Entity Types",
            "concept": "Regular entities with autonomous keys (roles, departments, equipment_categories, suppliers)",
            "relational": "Direct relation mapping with primary keys as surrogate INT AUTO_INCREMENT and natural candidate keys as UNIQUE constraints.",
            "examples": "roles (role_id PK, role_name UQ), departments (department_id PK, code UQ)"
        },
        {
            "step": 2,
            "rule": "1:N Binary Relationships",
            "concept": "Parent-to-child dependencies (e.g. Department operates Laboratories, Category classifies Equipment)",
            "relational": "Foreign key is placed on the N-side (child table) referencing the 1-side primary key. Cascades are set to RESTRICT for lookup data to prevent accidental orphan deletions.",
            "examples": "laboratories.department_id -> departments.department_id, equipment.category_id -> equipment_categories.category_id"
        },
        {
            "step": 3,
            "rule": "Associative Entities & M:N Relationships",
            "concept": "Multi-way associations between assets and users (borrowings, maintenance) or assets and physical movements (transactions)",
            "relational": "Modeled as associative bridge relations with surrogate PK, multiple foreign keys, timestamps, and contextual attributes.",
            "examples": "borrowings (equipment_id FK, user_id FK, borrow_date), transactions (equipment_id FK, from_lab_id FK, to_lab_id FK, transferred_by_user_id FK)"
        },
        {
            "step": 4,
            "rule": "Multi-Valued & Composite Attributes",
            "concept": "Composite names/addresses and multi-valued events (repeated maintenance, multiple checkouts)",
            "relational": "Composites decomposed into atomic columns (first_name, last_name). Multi-valued attributes extracted into separate child relations.",
            "examples": "User full name decomposed to first_name, last_name; historical repairs extracted to maintenance table."
        },
        {
            "step": 5,
            "rule": "Integrity & Check Constraints",
            "concept": "Domain validity, non-negativity of financial/quantity fields, date sequence validation",
            "relational": "CHECK constraints and ENUM domain definitions enforced at schema level.",
            "examples": "CHECK (cost >= 0), CHECK (quantity >= 0), CHECK (expected_return_date >= borrow_date)"
        }
    ]

    # Read the full schema.sql to render directly in syntax-highlighted code block
    try:
        with open("schema.sql", "r", encoding="utf-8") as f:
            ddl_content = f.read()
    except Exception:
        ddl_content = "-- schema.sql file could not be read."

    return render_template(
        "analysis/mapping.html",
        mapping_rules=mapping_rules,
        ddl_content=ddl_content
    )

@analysis_bp.route("/normalization")
def normalization():
    """Step-by-Step Normalization Breakdown from UNF to BCNF with Functional Dependencies."""
    return render_template("analysis/normalization.html")

@analysis_bp.route("/proofs")
def proofs():
    """Mathematical Database Proofs: Lossless Join, Dependency Preservation, Minimal Cover."""
    return render_template("analysis/proofs.html")

