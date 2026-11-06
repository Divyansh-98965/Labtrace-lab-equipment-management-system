# LabTrace - Laboratory Inventory & Asset Management System
## Production-Grade Academic Relational Database & Web Platform

LabTrace is an enterprise-grade academic laboratory equipment and inventory management web application built with **Python Flask**, **MySQL** (compatible with XAMPP phpMyAdmin), and a **Bootstrap 5** frontend dashboard.

It features an operational inventory management system and an interactive, dedicated **"Database Theory & Schema Analysis"** academic suite accessible directly via `/analysis`.

---

## 🗄️ Relational Database Architecture (12 Tables)

The schema satisfies **Boyce-Codd Normal Form (BCNF)** across all 12 interconnected tables:

1. **`roles`**: User permissions and access governance (`Admin`, `Lab Technician`, `Faculty`, `Student`, `Lab Assistant`).
2. **`departments`**: Academic and engineering departments (`CSE`, `EEE`, `MECH`, `BIO`, `CHEM`, `PHYS`).
3. **`users`**: Students, faculty, technicians, administrators (Foreign keys to `roles` and `departments`).
4. **`laboratories`**: Specialized research labs, room numbers, buildings, and supervisor assignments.
5. **`equipment_categories`**: Classification taxonomy (Measurement, Computing, Optical, Fabrication, Environmental, etc.).
6. **`suppliers`**: Vendors, OEM manufacturers, and authorized distributors with contact information.
7. **`equipment`**: Individual equipment assets with unique asset tags, serial numbers, cost, status, and condition.
8. **`consumables`**: Laboratory supplies, stock quantities, units, and minimum reorder alert levels.
9. **`borrowings`**: Issue, checkout, due date, and return custody logs.
10. **`maintenance`**: Routine servicing, calibration records, technician notes, and ISO compliance.
11. **`transactions`**: Physical movement audit trails (transfers, relocations, intake setup).
12. **`purchase_orders`**: Procurement records, PO numbers, supplier links, and delivery tracking.

---

## 🎓 Dedicated Database Theory & Analysis Suite (`/analysis`)

The web application includes an interactive academic analysis suite:

| Route | Feature Description |
| :--- | :--- |
| **`/analysis`** | Overview scorecard displaying normalization grades, live record counts, and architectural metrics. |
| **`/analysis/er-diagram`** | **Interactive ER Diagram Visualizer**: Toggleable between **Crow's Foot** physical database models and **Chen-style** conceptual diagrams with zoom, pan, and entity inspector. |
| **`/analysis/mapping`** | **ER-to-Relational Mapping Guide**: 5-step conversion matrix mapping entities, 1:N relations, associative entities, and composite keys into SQL DDL, featuring an integrated SQL DDL viewer with one-click copy. |
| **`/analysis/normalization`** | **Step-by-Step Normalization**: Progressive decomposition from Unnormalized Form (**UNF**) $\to$ **1NF** $\to$ **2NF** $\to$ **3NF** $\to$ **BCNF**, complete with functional dependency sets ($F$) and relational anomaly simulations. |
| **`/analysis/proofs`** | **Mathematical Database Proofs**: Step-by-step mathematical verification of **Lossless-Join Decomposition** ($R_1 \bowtie R_2 = R$) using attribute closure algorithms, **Dependency Preservation** verification, and **Minimal Cover ($F_c$)** algorithmic derivation. |

---

## 🚀 Getting Started & Local Execution

### Prerequisites
- **Python 3.10+** (tested on Python 3.14)
- **XAMPP / MySQL Server** running on `localhost:3306` with user `root` and no password.

### Option A: One-Click Startup (Recommended)

#### On Windows (PowerShell)
```powershell
.\run.ps1
```

#### On Linux / macOS (Bash)
```bash
chmod +x run.sh
./run.sh
```

### Option B: Manual Execution
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed database (creates labtrace_db and populates 120+ assets across 12 tables)
python verify_seed.py

# 3. Launch Flask server
python app.py
```

Open your browser and navigate to:
* **Operational Dashboard:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
* **Theory & Analysis Suite:** [http://127.0.0.1:5000/analysis](http://127.0.0.1:5000/analysis)
* **Interactive ER Diagram:** [http://127.0.0.1:5000/analysis/er-diagram](http://127.0.0.1:5000/analysis/er-diagram)
* **Relational Mapping & DDL:** [http://127.0.0.1:5000/analysis/mapping](http://127.0.0.1:5000/analysis/mapping)
* **Normalization (UNF $\to$ BCNF):** [http://127.0.0.1:5000/analysis/normalization](http://127.0.0.1:5000/analysis/normalization)
* **Mathematical Proofs:** [http://127.0.0.1:5000/analysis/proofs](http://127.0.0.1:5000/analysis/proofs)

---

## 🧪 Automated Test Suite
To verify all 11 Flask routes, CRUD endpoints, and CSV exports:
```bash
python test_suite.py
```
