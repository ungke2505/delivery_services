import frappe


def on_submit(doc, method):
    pass


def on_cancel(doc, method):
    doc.status = "Cancelled"
    # Cancel delivery task if exists
    task = frappe.db.exists("DS Delivery Task", {"order": doc.name})
    if task:
        task_doc = frappe.get_doc("DS Delivery Task", task)
        task_doc.status = "Failed"
        task_doc.notes = "Order dibatalkan oleh system."
        task_doc.save(ignore_permissions=True)
