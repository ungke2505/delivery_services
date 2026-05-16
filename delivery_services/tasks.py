import frappe
from frappe.utils import add_days, now_datetime


def daily_order_reminder():
    """Kirim reminder ke customer yang ordernya masih pending > 1 hari."""
    old_pending = frappe.get_all(
        "DS Order",
        filters={
            "status": "Pending",
            "payment_method": "Transfer",
            "order_date": ["<", add_days(now_datetime(), -1)],
        },
        fields=["name", "customer_user", "total_amount"],
    )
    for order in old_pending:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": "Selesaikan Pembayaran Anda",
                "email_content": (
                    f"Pesanan #{order['name']} senilai Rp {order['total_amount']:,.0f} "
                    "masih menunggu bukti transfer. Segera upload agar pesanan segera diproses."
                ),
                "for_user": order["customer_user"],
                "type": "Alert",
            }).insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "DS Daily Reminder Error")
    frappe.db.commit()


def check_stale_orders():
    """Log warning untuk order yang stuck terlalu lama."""
    stale = frappe.db.sql("""
        SELECT name, status, order_date
        FROM `tabDS Order`
        WHERE status IN ('Confirmed','Assigned')
        AND TIMESTAMPDIFF(HOUR, order_date, NOW()) > 24
    """, as_dict=True)
    if stale:
        frappe.log_error(
            f"Stale orders found: {[o['name'] for o in stale]}",
            "DS Stale Orders Warning"
        )
