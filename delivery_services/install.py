"""
delivery_services/install.py
Dijalankan otomatis oleh Frappe setelah `bench install-app delivery_services`.
"""
import frappe


def after_install():
    """Setup awal: buat roles, user default, sample data."""
    _create_roles()
    _create_custom_roles_for_website()
    frappe.db.commit()
    print("✅ delivery_services installed successfully.")


def _create_roles():
    for role_name in ["Delivery Admin", "Delivery Driver"]:
        if not frappe.db.exists("Role", role_name):
            role = frappe.get_doc({"doctype": "Role", "role_name": role_name})
            role.insert(ignore_permissions=True)
            print(f"  Created role: {role_name}")


def _create_custom_roles_for_website():
    """Pastikan role Customer ada untuk registrasi dari PWA."""
    if not frappe.db.exists("Role", "Customer"):
        frappe.get_doc({"doctype": "Role", "role_name": "Customer"}).insert(ignore_permissions=True)
        print("  Created role: Customer")
