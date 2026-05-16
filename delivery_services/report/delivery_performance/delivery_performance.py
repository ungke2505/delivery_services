import frappe


def execute(filters=None):
    filters = filters or {}

    columns = [
        {"fieldname": "driver_name",   "label": "Driver",          "fieldtype": "Data",     "width": 160},
        {"fieldname": "total_tasks",   "label": "Total Tugas",     "fieldtype": "Int",      "width": 100},
        {"fieldname": "delivered",     "label": "Terkirim",        "fieldtype": "Int",      "width": 100},
        {"fieldname": "failed",        "label": "Gagal",           "fieldtype": "Int",      "width": 80},
        {"fieldname": "success_rate",  "label": "Sukses (%)",      "fieldtype": "Percent",  "width": 100},
        {"fieldname": "avg_minutes",   "label": "Rata-rata Menit", "fieldtype": "Float",    "width": 130},
    ]

    conditions = "1=1"
    if filters.get("from_date"):
        conditions += f" AND DATE(creation) >= '{filters['from_date']}'"
    if filters.get("to_date"):
        conditions += f" AND DATE(creation) <= '{filters['to_date']}'"
    if filters.get("driver_user"):
        conditions += f" AND driver_user = '{filters['driver_user']}'"

    data = frappe.db.sql(f"""
        SELECT
            driver_name,
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status='Delivered' THEN 1 ELSE 0 END) as delivered,
            SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) as failed,
            ROUND(
                100.0 * SUM(CASE WHEN status='Delivered' THEN 1 ELSE 0 END) / COUNT(*), 1
            ) as success_rate,
            ROUND(
                AVG(CASE WHEN status='Delivered' AND departed_at IS NOT NULL AND delivered_at IS NOT NULL
                    THEN TIMESTAMPDIFF(MINUTE, departed_at, delivered_at) END), 1
            ) as avg_minutes
        FROM `tabDS Delivery Task`
        WHERE {conditions}
        GROUP BY driver_user, driver_name
        ORDER BY delivered DESC
    """, as_dict=True)

    return columns, data
