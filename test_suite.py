from app import app
from db import get_db_connection

def run_tests():
    client = app.test_client()

    print("Running LabTrace Test Suite...")

    # 1. Test Authentication Guard (Unauthenticated Access Redirects to /login)
    resp = client.get("/")
    assert resp.status_code == 302, f"Expected 302 redirect for unauthenticated root, got {resp.status_code}"
    assert "/login" in resp.headers["Location"]
    print("[✓] Unauthenticated GET / redirects to /login OK")

    resp = client.get("/analysis/er-diagram")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    print("[✓] Unauthenticated GET /analysis/er-diagram redirects to /login OK")

    # 2. Test Login Page UI & Mandated Hint
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Demo Credentials: Username: admin@Labtrace | Password: password" in resp.data
    assert b"Sign In to System" in resp.data
    print("[✓] GET /login renders login UI with mandated credentials hint OK")

    # 3. Test Invalid Login Attempt
    resp = client.post("/login", data={"username": "wrong@user.com", "password": "wrongpassword"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data
    print("[✓] POST /login with invalid credentials correctly rejected OK")

    # 4. Test Successful Login (admin@Labtrace / password)
    resp = client.post("/login", data={"username": "admin@Labtrace", "password": "password"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Welcome to LabTrace" in resp.data
    assert b"Equipment Inventory" in resp.data
    print("[✓] POST /login with valid credentials successfully authenticated OK")

    # 5. Test Authenticated Dashboard / and /dashboard
    resp = client.get("/")
    assert resp.status_code == 200, f"Dashboard failed with {resp.status_code}"
    assert b"LabTrace" in resp.data
    assert b"Total Equipment" in resp.data
    print("[✓] GET / (Dashboard & Inventory Table) OK")

    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert b"Total Equipment" in resp.data
    print("[✓] GET /dashboard OK")

    # 6. Test Single Equipment JSON Endpoint
    resp = client.get("/equipment/1/json")
    assert resp.status_code == 200, f"JSON failed with {resp.status_code}"
    data = resp.get_json()
    assert "asset_tag" in data
    assert "category_name" in data
    print(f"[✓] GET /equipment/1/json OK: {data['asset_tag']} - {data['name']}")

    # 7. Test Export CSV
    resp = client.get("/equipment/export")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/csv")
    assert b"EQ-2024-" in resp.data
    print("[✓] GET /equipment/export (CSV Download) OK")

    # 8. Test Laboratories View
    resp = client.get("/laboratories")
    assert resp.status_code == 200
    assert b"Robotics" in resp.data
    print("[✓] GET /laboratories OK")

    # 9. Test Borrowings View
    resp = client.get("/borrowings")
    assert resp.status_code == 200
    assert b"Borrowing" in resp.data
    print("[✓] GET /borrowings OK")

    # 10. Test Maintenance View
    resp = client.get("/maintenance")
    assert resp.status_code == 200
    assert b"Maintenance" in resp.data
    print("[✓] GET /maintenance OK")

    # 11. Test Consumables View
    resp = client.get("/consumables")
    assert resp.status_code == 200
    assert b"Consumables" in resp.data
    print("[✓] GET /consumables OK")

    # 12. Test Schema Viewer
    resp = client.get("/schema-viewer")
    assert resp.status_code == 200
    assert b"Relational Database Architecture" in resp.data
    print("[✓] GET /schema-viewer (12-Table Schema) OK")

    # 13. Test Analysis Blueprint Routes
    resp = client.get("/analysis/")
    assert resp.status_code == 200
    assert b"Database Theory" in resp.data
    print("[✓] GET /analysis/ (Analysis Overview & Scorecard) OK")

    resp = client.get("/analysis/er-diagram")
    assert resp.status_code == 200
    assert b"Chen" in resp.data
    assert b"Rectangles" in resp.data
    print("[✓] GET /analysis/er-diagram (Strict Chen ER Diagram) OK")

    resp = client.get("/analysis/mapping")
    assert resp.status_code == 200
    assert b"ER-to-Relational Mapping" in resp.data
    print("[✓] GET /analysis/mapping (Mapping Guide & DDL) OK")

    resp = client.get("/analysis/normalization")
    assert resp.status_code == 200
    assert b"BCNF" in resp.data
    print("[✓] GET /analysis/normalization (UNF to BCNF Breakdown) OK")

    resp = client.get("/analysis/proofs")
    assert resp.status_code == 200
    assert b"Lossless" in resp.data
    print("[✓] GET /analysis/proofs (Mathematical Proofs & Minimal Cover) OK")

    # 14. Test Create Equipment CRUD
    test_tag = "EQ-TEST-9999"
    create_payload = {
        "asset_tag": test_tag,
        "name": "Integration Test Spectrometer",
        "category_id": "2",
        "lab_id": "1",
        "supplier_id": "1",
        "model": "SPEC-9999",
        "serial_number": "SN-TEST-9999",
        "purchase_date": "2024-01-15",
        "cost": "4500.00",
        "status": "Available",
        "condition_state": "New"
    }
    resp = client.post("/equipment/create", data=create_payload, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Integration Test Spectrometer" in resp.data
    print(f"[✓] POST /equipment/create OK: Successfully registered {test_tag}")

    # Verify in DB and get equipment_id
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT equipment_id FROM equipment WHERE asset_tag = %s", (test_tag,))
            created_item = cursor.fetchone()
            assert created_item is not None
            test_eq_id = created_item["equipment_id"]
    finally:
        conn.close()

    # 15. Test Update Equipment CRUD
    update_payload = {
        "asset_tag": test_tag,
        "name": "Updated Test Spectrometer 2.0",
        "category_id": "2",
        "lab_id": "2",  # Relocated to Lab 2
        "supplier_id": "1",
        "model": "SPEC-9999-V2",
        "serial_number": "SN-TEST-9999",
        "purchase_date": "2024-01-15",
        "cost": "4950.00",
        "status": "In Use",
        "condition_state": "Excellent"
    }
    resp = client.post(f"/equipment/{test_eq_id}/edit", data=update_payload, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Updated Test Spectrometer 2.0" in resp.data
    print(f"[✓] POST /equipment/{test_eq_id}/edit OK: Successfully updated")

    # 16. Test Delete Equipment CRUD
    resp = client.post(f"/equipment/{test_eq_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    print(f"[✓] POST /equipment/{test_eq_id}/delete OK: Successfully deleted test item")

    # 17. Test Logout Route
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Demo Credentials" in resp.data
    assert b"You have been signed out" in resp.data
    print("[✓] GET /logout successfully terminates session and redirects to /login OK")

    # 18. Verify unauthenticated again after logout
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    print("[✓] Verification: Session terminated, access again blocked to protected routes OK")

    print("\n=======================================================")
    print(" ALL 18 AUTHENTICATION & SYSTEM TESTS PASSED SUCCESSFULLY! ")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()


