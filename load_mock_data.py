"""
Load mock shipment, LC, and vessel data into database for real-time monitoring.
Run this once to populate test data: python load_mock_data.py
"""

import sqlite3
import json
from datetime import datetime, timedelta
from database import Database


def load_mock_data():
    """Load mock data into database."""

    # Initialize database first (creates tables)
    db = Database()

    db_path = "audit_logs.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("[SHIPMENTS] Loading mock shipment data...")

    # Mock shipments (some delayed, some on time)
    shipments = [
        {
            "shipment_id": "SHP-2024-001",
            "vessel_name": "MV Samudra",
            "expected_arrival": (datetime.now() - timedelta(days=5)).isoformat(),
            "actual_arrival": None,
            "status": "IN_TRANSIT",
            "daily_dd_rate": 50000
        },
        {
            "shipment_id": "SHP-2024-002",
            "vessel_name": "MV Horizon",
            "expected_arrival": (datetime.now() - timedelta(days=10)).isoformat(),
            "actual_arrival": None,
            "status": "IN_TRANSIT",
            "daily_dd_rate": 60000
        },
        {
            "shipment_id": "SHP-2024-003",
            "vessel_name": "MV Atlantic",
            "expected_arrival": (datetime.now() + timedelta(days=2)).isoformat(),
            "actual_arrival": None,
            "status": "IN_TRANSIT",
            "daily_dd_rate": 45000
        },
        {
            "shipment_id": "SHP-2024-004",
            "vessel_name": "MV Swift",
            "expected_arrival": (datetime.now() + timedelta(days=5)).isoformat(),
            "actual_arrival": None,
            "status": "IN_TRANSIT",
            "daily_dd_rate": 55000
        },
        {
            "shipment_id": "SHP-2024-005",
            "vessel_name": "MV Ganges",
            "expected_arrival": (datetime.now() - timedelta(days=4)).isoformat(),
            "actual_arrival": None,
            "status": "IN_TRANSIT",
            "daily_dd_rate": 55000
        },
    ]

    for shipment in shipments:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO shipments
                (shipment_id, vessel_name, expected_arrival, actual_arrival, status, daily_dd_rate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                shipment["shipment_id"],
                shipment["vessel_name"],
                shipment["expected_arrival"],
                shipment["actual_arrival"],
                shipment["status"],
                shipment["daily_dd_rate"]
            ))
        except Exception as e:
            print(f"  [WARN] Shipment {shipment['shipment_id']}: {e}")

    print(f"  [OK] Loaded {len(shipments)} shipments")

    print("\n[LCS] Loading mock LC data...")

    # Mock LCs (some with missing docs)
    lcs = [
        {
            "lc_id": "LC-2024-001",
            "lc_number": "HDFC/2024/001",
            "expiry_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "lc_amount": 5000000,
            "required_documents": ["Bill of Lading", "Invoice", "Certificate of Origin"],
            "received_documents": ["Invoice"],
            "status": "ACTIVE"
        },
        {
            "lc_id": "LC-2024-002",
            "lc_number": "ICICI/2024/001",
            "expiry_date": (datetime.now() + timedelta(days=20)).isoformat(),
            "lc_amount": 8000000,
            "required_documents": ["Bill of Lading", "Invoice", "Packing List"],
            "received_documents": ["Bill of Lading", "Invoice", "Packing List"],
            "status": "ACTIVE"
        },
        {
            "lc_id": "LC-2024-003",
            "lc_number": "AXIS/2024/001",
            "expiry_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "lc_amount": 3500000,
            "required_documents": ["Bill of Lading", "Invoice", "Certificate of Origin"],
            "received_documents": ["Certificate of Origin"],
            "status": "ACTIVE"
        },
        {
            "lc_id": "LC-2024-004",
            "lc_number": "BOB/2024/001",
            "expiry_date": (datetime.now() + timedelta(days=15)).isoformat(),
            "lc_amount": 6000000,
            "required_documents": ["Bill of Lading", "Invoice"],
            "received_documents": ["Bill of Lading", "Invoice"],
            "status": "ACTIVE"
        },
    ]

    for lc in lcs:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO lcs
                (lc_id, lc_number, expiry_date, lc_amount, required_documents, received_documents, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lc["lc_id"],
                lc["lc_number"],
                lc["expiry_date"],
                lc["lc_amount"],
                json.dumps(lc["required_documents"]),
                json.dumps(lc["received_documents"]),
                lc["status"]
            ))
        except Exception as e:
            print(f"  [WARN] LC {lc['lc_id']}: {e}")

    print(f"  [OK] Loaded {len(lcs)} LCs")

    print("\n[VESSELS] Loading mock vessel data...")

    # Mock vessels (some approaching laytime expiry)
    vessels = [
        {
            "vessel_name": "MV Atlantic",
            "port": "Visakhapatnam",
            "laytime_expiry": (datetime.now() + timedelta(days=2)).isoformat(),
            "daily_dd_rate": 75000,
            "status": "DISCHARGING"
        },
        {
            "vessel_name": "MV Ganges",
            "port": "Kandla",
            "laytime_expiry": (datetime.now() + timedelta(days=8)).isoformat(),
            "daily_dd_rate": 55000,
            "status": "DISCHARGING"
        },
        {
            "vessel_name": "MV Brahmaputra",
            "port": "Chennai",
            "laytime_expiry": (datetime.now() + timedelta(days=15)).isoformat(),
            "daily_dd_rate": 60000,
            "status": "DISCHARGING"
        },
        {
            "vessel_name": "MV Indus",
            "port": "Mumbai",
            "laytime_expiry": (datetime.now() + timedelta(days=3)).isoformat(),
            "daily_dd_rate": 70000,
            "status": "DISCHARGING"
        },
        {
            "vessel_name": "MV Yamuna",
            "port": "Cochin",
            "laytime_expiry": (datetime.now() + timedelta(days=25)).isoformat(),
            "daily_dd_rate": 50000,
            "status": "DISCHARGING"
        },
    ]

    for vessel in vessels:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO vessels
                (vessel_name, port, laytime_expiry, daily_dd_rate, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                vessel["vessel_name"],
                vessel["port"],
                vessel["laytime_expiry"],
                vessel["daily_dd_rate"],
                vessel["status"]
            ))
        except Exception as e:
            print(f"  [WARN] Vessel {vessel['vessel_name']}: {e}")

    print(f"  [OK] Loaded {len(vessels)} vessels")

    conn.commit()
    conn.close()

    print("\n[SUCCESS] Mock data loading complete!")
    print("\nData Summary:")
    print(f"  - Shipments: {len(shipments)} (some delayed)")
    print(f"  - LCs: {len(lcs)} (some with missing docs)")
    print(f"  - Vessels: {len(vessels)} (some approaching laytime expiry)")
    print("\nRun 'streamlit run app.py' to start the platform.")
    print("The real-time monitor will detect exceptions automatically.")


if __name__ == "__main__":
    load_mock_data()
