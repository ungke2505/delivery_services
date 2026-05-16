import frappe


def on_update(doc, method):
    """Sinkronisasi status ke DS Order saat task diupdate dari ERPNext UI."""
    status_map = {
        "Assigned": "Assigned",
        "On The Way": "On The Way",
        "Arrived": "Arrived",
        "Delivered": "Delivered",
        "Failed": "Delivery Failed",
    }
    mapped = status_map.get(doc.status)
    if mapped:
        order = frappe.get_doc("DS Order", doc.order)
        if order.status != mapped:
            order.status = mapped
            order.save(ignore_permissions=True)
