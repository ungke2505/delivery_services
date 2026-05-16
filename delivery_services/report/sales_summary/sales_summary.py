import frappe
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}

    columns = [
        {"fieldname": "order_date",    "label": "Tanggal",         "fieldtype": "Date",     "width": 110},
        {"fieldname": "name",          "label": "Order ID",        "fieldtype": "Link",     "options": "DS Order", "width": 180},
        {"fieldname": "customer_user", "label": "Customer",        "fieldtype": "Data",     "width": 160},
        {"fieldname": "payment_method","label": "Metode Bayar",    "fieldtype": "Data",     "width": 100},
        {"fieldname": "status",        "label": "Status",          "fieldtype": "Data",     "width": 120},
        {"fieldname": "total_amount",  "label": "Total (Rp)",      "fieldtype": "Currency", "width": 130},
    ]

    conditions = "1=1"
    if filters.get("from_date"):
        conditions += f" AND DATE(order_date) >= '{filters['from_date']}'"
    if filters.get("to_date"):
        conditions += f" AND DATE(order_date) <= '{filters['to_date']}'"
    if filters.get("status"):
        conditions += f" AND status = '{filters['status']}'"

    data = frappe.db.sql(f"""
        SELECT
            DATE(order_date) as order_date,
            name, customer_user, payment_method, status, total_amount
        FROM `tabDS Order`
        WHERE {conditions}
        ORDER BY order_date DESC
        LIMIT 500
    """, as_dict=True)

    return columns, data
