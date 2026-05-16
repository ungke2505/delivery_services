import frappe


def has_order_permission(doc, ptype="read", user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    if any(r in roles for r in ["System Manager", "Delivery Admin"]):
        return True
    if ptype in ("read", "write") and doc.customer_user == user:
        return True
    if "Delivery Driver" in roles:
        return ptype == "read"
    return False


def has_delivery_task_permission(doc, ptype="read", user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    if any(r in roles for r in ["System Manager", "Delivery Admin"]):
        return True
    if "Delivery Driver" in roles and doc.driver_user == user:
        return True
    return False


def has_payment_permission(doc, ptype="read", user=None):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    if any(r in roles for r in ["System Manager", "Delivery Admin"]):
        return True
    if ptype in ("read", "write") and doc.customer_user == user:
        return True
    return False
