import frappe


def after_insert(doc, method):
    """Notifikasi admin saat bukti baru diupload."""
    admins = frappe.get_all(
        "Has Role",
        filters={"role": "Delivery Admin"},
        fields=["parent"],
    )
    for admin in admins:
        try:
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": f"Bukti Pembayaran Baru - {doc.order}",
                "email_content": (
                    f"Customer telah mengupload bukti transfer untuk order {doc.order}. "
                    f"Jumlah: Rp {doc.amount:,.0f}. Silakan verifikasi."
                ),
                "for_user": admin["parent"],
                "type": "Alert",
            }).insert(ignore_permissions=True)
        except Exception:
            pass


def on_update(doc, method):
    pass
