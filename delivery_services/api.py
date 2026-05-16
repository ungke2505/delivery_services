"""
delivery_services/api.py
Semua endpoint publik (whitelisted) yang digunakan oleh Customer PWA dan Driver PWA.
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, flt, cint
import json


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist(allow_guest=True)
def register_customer(full_name, email, phone, password):
    """Registrasi customer baru."""
    if frappe.db.exists("User", email):
        frappe.throw(_("Email sudah terdaftar."), frappe.DuplicateEntryError)

    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": full_name,
        "mobile_no": phone,
        "send_welcome_email": 0,
        "roles": [{"role": "Customer"}],
    })
    user.new_password = password
    user.insert(ignore_permissions=True)

    # Buat DS Customer Profile
    profile = frappe.get_doc({
        "doctype": "DS Customer Profile",
        "user": email,
        "full_name": full_name,
        "phone": phone,
        "email": email,
    })
    profile.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"message": "Registrasi berhasil", "email": email}


@frappe.whitelist(allow_guest=True)
def get_session_user():
    """Kembalikan info user yang sedang login."""
    user = frappe.session.user
    if user == "Guest":
        return {"logged_in": False}

    profile = frappe.db.get_value(
        "DS Customer Profile", {"user": user},
        ["full_name", "phone", "email", "default_address"],
        as_dict=True
    ) or {}

    roles = frappe.get_roles(user)
    return {
        "logged_in": True,
        "user": user,
        "full_name": profile.get("full_name") or frappe.db.get_value("User", user, "full_name"),
        "phone": profile.get("phone"),
        "is_driver": "Delivery Driver" in roles,
        "is_admin": "Delivery Admin" in roles or "System Manager" in roles,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  PRODUCTS
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist(allow_guest=True)
def get_products(search="", category="", page=1, page_size=20):
    """Ambil daftar produk aktif dengan pagination dan search."""
    page = cint(page)
    page_size = cint(page_size)
    offset = (page - 1) * page_size

    filters = {"is_active": 1}
    if category:
        filters["category"] = category
    if search:
        filters["product_name"] = ["like", f"%{search}%"]

    products = frappe.get_all(
        "DS Product",
        filters=filters,
        fields=["name", "product_name", "description", "price",
                "stock_qty", "category", "image", "unit"],
        order_by="product_name asc",
        limit=page_size,
        start=offset,
    )

    total = frappe.db.count("DS Product", filters)

    return {
        "products": products,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": (offset + page_size) < total,
    }


@frappe.whitelist(allow_guest=True)
def get_product(name):
    """Detail satu produk."""
    doc = frappe.get_doc("DS Product", name)
    return {
        "name": doc.name,
        "product_name": doc.product_name,
        "description": doc.description,
        "price": doc.price,
        "stock_qty": doc.stock_qty,
        "category": doc.category,
        "image": doc.image,
        "unit": doc.unit,
        "is_active": doc.is_active,
    }


@frappe.whitelist(allow_guest=True)
def get_categories():
    """Daftar kategori produk yang ada."""
    cats = frappe.db.sql(
        "SELECT DISTINCT category FROM `tabDS Product` WHERE is_active=1 AND category IS NOT NULL ORDER BY category",
        as_dict=True,
    )
    return [c["category"] for c in cats if c["category"]]


# ══════════════════════════════════════════════════════════════════════════════
#  ORDERS
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def create_order(items, delivery_address, payment_method, notes=""):
    """
    Buat DS Order baru dari cart customer.
    items: JSON string list [{product, qty, price}]
    payment_method: 'COD' | 'Transfer'
    """
    frappe.only_for(["Customer", "System Manager"])
    user = frappe.session.user

    if isinstance(items, str):
        items = json.loads(items)

    if not items:
        frappe.throw(_("Cart kosong."))

    # Hitung total
    total = sum(flt(i["price"]) * cint(i["qty"]) for i in items)

    order = frappe.get_doc({
        "doctype": "DS Order",
        "customer_user": user,
        "delivery_address": delivery_address,
        "payment_method": payment_method,
        "notes": notes,
        "order_date": now_datetime(),
        "status": "Pending",
        "total_amount": total,
        "items": [
            {
                "doctype": "DS Order Item",
                "product": i["product"],
                "product_name": i.get("product_name", ""),
                "qty": cint(i["qty"]),
                "price": flt(i["price"]),
                "subtotal": flt(i["price"]) * cint(i["qty"]),
            }
            for i in items
        ],
    })
    order.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "order_id": order.name,
        "total_amount": total,
        "status": order.status,
        "payment_method": payment_method,
    }


@frappe.whitelist()
def get_my_orders(page=1, page_size=10):
    """Riwayat pesanan milik customer yang login."""
    user = frappe.session.user
    page = cint(page)
    page_size = cint(page_size)
    offset = (page - 1) * page_size

    orders = frappe.get_all(
        "DS Order",
        filters={"customer_user": user},
        fields=["name", "order_date", "status", "total_amount",
                "payment_method", "delivery_address"],
        order_by="order_date desc",
        limit=page_size,
        start=offset,
    )

    for o in orders:
        o["items"] = frappe.get_all(
            "DS Order Item",
            filters={"parent": o["name"]},
            fields=["product_name", "qty", "price", "subtotal"],
        )

    total = frappe.db.count("DS Order", {"customer_user": user})
    return {"orders": orders, "total": total}


@frappe.whitelist()
def get_order_detail(order_id):
    """Detail lengkap satu pesanan beserta status pengiriman."""
    user = frappe.session.user
    doc = frappe.get_doc("DS Order", order_id)

    # Pastikan hanya pemilik / admin / driver yang bisa lihat
    roles = frappe.get_roles(user)
    if doc.customer_user != user and not any(
        r in roles for r in ["Delivery Admin", "Delivery Driver", "System Manager"]
    ):
        frappe.throw(_("Akses ditolak."), frappe.PermissionError)

    # Cari delivery task terkait
    task = frappe.db.get_value(
        "DS Delivery Task", {"order": order_id},
        ["name", "driver_user", "driver_name", "status", "estimated_arrival"],
        as_dict=True,
    )

    # Cari payment
    payment = frappe.db.get_value(
        "DS Payment", {"order": order_id},
        ["name", "status", "payment_method", "bukti_transfer", "verified_at"],
        as_dict=True,
    )

    return {
        "order": doc.as_dict(),
        "delivery_task": task,
        "payment": payment,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  PAYMENTS
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def upload_payment_proof(order_id, file_url, bank_name="", account_name="", transfer_date=""):
    """Simpan bukti transfer dari customer."""
    user = frappe.session.user
    order = frappe.get_doc("DS Order", order_id)

    if order.customer_user != user:
        frappe.throw(_("Akses ditolak."), frappe.PermissionError)
    if order.payment_method != "Transfer":
        frappe.throw(_("Order ini menggunakan metode COD."))

    # Cek apakah sudah ada payment record
    existing = frappe.db.exists("DS Payment", {"order": order_id})
    if existing:
        payment = frappe.get_doc("DS Payment", existing)
        payment.bukti_transfer = file_url
        payment.bank_name = bank_name
        payment.account_name = account_name
        payment.transfer_date = transfer_date
        payment.status = "Menunggu Verifikasi"
        payment.save(ignore_permissions=True)
    else:
        payment = frappe.get_doc({
            "doctype": "DS Payment",
            "order": order_id,
            "customer_user": user,
            "payment_method": "Transfer",
            "bukti_transfer": file_url,
            "bank_name": bank_name,
            "account_name": account_name,
            "transfer_date": transfer_date,
            "status": "Menunggu Verifikasi",
            "amount": order.total_amount,
        })
        payment.insert(ignore_permissions=True)

    # Update status order
    order.status = "Payment Uploaded"
    order.save(ignore_permissions=True)
    frappe.db.commit()

    return {"message": "Bukti pembayaran berhasil dikirim.", "payment_id": payment.name}


@frappe.whitelist()
def verify_payment(payment_id, action):
    """Admin: verifikasi atau tolak pembayaran. action: 'approve' | 'reject'"""
    frappe.only_for(["Delivery Admin", "System Manager"])

    payment = frappe.get_doc("DS Payment", payment_id)
    order = frappe.get_doc("DS Order", payment.order)

    if action == "approve":
        payment.status = "Verified"
        payment.verified_by = frappe.session.user
        payment.verified_at = now_datetime()
        order.status = "Confirmed"
        _send_notification(order.customer_user, "Pembayaran Dikonfirmasi",
                           f"Pesanan #{order.name} telah dikonfirmasi. Kami sedang menyiapkan paket Anda.")
    elif action == "reject":
        payment.status = "Ditolak"
        order.status = "Pending"
        _send_notification(order.customer_user, "Pembayaran Ditolak",
                           f"Bukti transfer pesanan #{order.name} ditolak. Silakan upload ulang.")
    else:
        frappe.throw(_("Action tidak valid. Gunakan 'approve' atau 'reject'."))

    payment.save(ignore_permissions=True)
    order.save(ignore_permissions=True)
    frappe.db.commit()

    return {"message": f"Payment {action}d successfully."}


# ══════════════════════════════════════════════════════════════════════════════
#  DELIVERY TASKS (ADMIN)
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def assign_driver(order_id, driver_user, estimated_arrival=""):
    """Admin: assign driver ke order yang sudah Confirmed."""
    frappe.only_for(["Delivery Admin", "System Manager"])

    order = frappe.get_doc("DS Order", order_id)
    if order.status not in ("Confirmed",):
        frappe.throw(_(f"Order harus berstatus Confirmed untuk assign driver. Status saat ini: {order.status}"))

    driver_name = frappe.db.get_value("User", driver_user, "full_name")

    # Cek apakah sudah ada task
    existing = frappe.db.exists("DS Delivery Task", {"order": order_id})
    if existing:
        task = frappe.get_doc("DS Delivery Task", existing)
        task.driver_user = driver_user
        task.driver_name = driver_name
        task.estimated_arrival = estimated_arrival
        task.status = "Assigned"
        task.save(ignore_permissions=True)
    else:
        task = frappe.get_doc({
            "doctype": "DS Delivery Task",
            "order": order_id,
            "driver_user": driver_user,
            "driver_name": driver_name,
            "estimated_arrival": estimated_arrival,
            "status": "Assigned",
            "delivery_address": order.delivery_address,
            "customer_user": order.customer_user,
            "total_amount": order.total_amount,
            "payment_method": order.payment_method,
        })
        task.insert(ignore_permissions=True)

    order.status = "Assigned"
    order.assigned_driver = driver_user
    order.save(ignore_permissions=True)
    frappe.db.commit()

    _send_notification(driver_user, "Tugas Pengiriman Baru",
                       f"Anda mendapat tugas pengiriman untuk pesanan #{order_id}.")
    _send_notification(order.customer_user, "Driver Sedang Menuju",
                       f"Driver {driver_name} telah ditugaskan untuk pesanan #{order_id}.")

    return {"message": "Driver berhasil di-assign.", "task_id": task.name}


@frappe.whitelist()
def get_pending_orders():
    """Admin: daftar order yang butuh tindakan."""
    frappe.only_for(["Delivery Admin", "System Manager"])

    orders = frappe.db.sql("""
        SELECT
            o.name, o.customer_user, o.order_date, o.status,
            o.total_amount, o.payment_method, o.delivery_address,
            p.status as payment_status, p.bukti_transfer,
            t.driver_name, t.status as delivery_status
        FROM `tabDS Order` o
        LEFT JOIN `tabDS Payment` p ON p.order = o.name
        LEFT JOIN `tabDS Delivery Task` t ON t.order = o.name
        WHERE o.status NOT IN ('Delivered','Cancelled')
        ORDER BY o.order_date DESC
        LIMIT 100
    """, as_dict=True)

    return orders


@frappe.whitelist()
def get_available_drivers():
    """Admin: daftar driver yang tersedia."""
    frappe.only_for(["Delivery Admin", "System Manager"])

    drivers = frappe.db.sql("""
        SELECT u.name, u.full_name, u.mobile_no
        FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role = 'Delivery Driver'
        AND u.enabled = 1
    """, as_dict=True)

    # Tandai yang sedang bertugas
    active = frappe.db.sql("""
        SELECT driver_user, COUNT(*) as active_tasks
        FROM `tabDS Delivery Task`
        WHERE status IN ('Assigned','On The Way')
        GROUP BY driver_user
    """, as_dict=True)
    active_map = {a["driver_user"]: a["active_tasks"] for a in active}

    for d in drivers:
        d["active_tasks"] = active_map.get(d["name"], 0)
        d["is_available"] = d["active_tasks"] == 0

    return drivers


# ══════════════════════════════════════════════════════════════════════════════
#  DRIVER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_my_tasks(status=""):
    """Driver: ambil daftar tugas pengiriman milik driver yang login."""
    frappe.only_for(["Delivery Driver", "System Manager"])
    user = frappe.session.user

    filters = {"driver_user": user}
    if status:
        filters["status"] = status
    else:
        filters["status"] = ["in", ["Assigned", "On The Way"]]

    tasks = frappe.get_all(
        "DS Delivery Task",
        filters=filters,
        fields=["name", "order", "customer_user", "delivery_address",
                "status", "estimated_arrival", "total_amount", "payment_method",
                "driver_name", "creation"],
        order_by="creation desc",
    )

    for t in tasks:
        t["items"] = frappe.get_all(
            "DS Order Item",
            filters={"parent": t["order"]},
            fields=["product_name", "qty", "subtotal"],
        )

    return tasks


@frappe.whitelist()
def update_delivery_status(task_id, status, note=""):
    """
    Driver: update status pengiriman.
    status: 'On The Way' | 'Arrived' | 'Delivered' | 'Failed'
    """
    frappe.only_for(["Delivery Driver", "System Manager"])
    user = frappe.session.user

    task = frappe.get_doc("DS Delivery Task", task_id)

    if task.driver_user != user and "System Manager" not in frappe.get_roles(user):
        frappe.throw(_("Anda tidak berhak mengubah task ini."), frappe.PermissionError)

    valid_transitions = {
        "Assigned": ["On The Way"],
        "On The Way": ["Arrived", "Failed"],
        "Arrived": ["Delivered", "Failed"],
    }

    allowed = valid_transitions.get(task.status, [])
    if status not in allowed:
        frappe.throw(_(f"Tidak bisa mengubah dari '{task.status}' ke '{status}'."))

    task.status = status
    task.notes = note
    if status == "On The Way":
        task.departed_at = now_datetime()
    elif status == "Delivered":
        task.delivered_at = now_datetime()
    task.save(ignore_permissions=True)

    # Sync ke DS Order
    order = frappe.get_doc("DS Order", task.order)
    status_map = {
        "On The Way": "On The Way",
        "Arrived": "Arrived",
        "Delivered": "Delivered",
        "Failed": "Delivery Failed",
    }
    order.status = status_map.get(status, order.status)
    order.save(ignore_permissions=True)
    frappe.db.commit()

    # Notifikasi customer
    notif_map = {
        "On The Way": "Driver sedang dalam perjalanan menuju lokasi Anda.",
        "Arrived": "Driver telah tiba di lokasi Anda!",
        "Delivered": "Pesanan Anda telah berhasil diterima. Terima kasih!",
        "Failed": "Pengiriman pesanan gagal. Tim kami akan menghubungi Anda.",
    }
    _send_notification(order.customer_user, f"Update Pesanan #{order.name}",
                       notif_map.get(status, ""))

    return {"message": f"Status diperbarui ke '{status}'.", "task_status": status}


@frappe.whitelist()
def upload_delivery_proof(task_id, file_url, note=""):
    """Driver: upload foto bukti pengiriman."""
    frappe.only_for(["Delivery Driver", "System Manager"])
    user = frappe.session.user

    task = frappe.get_doc("DS Delivery Task", task_id)
    if task.driver_user != user and "System Manager" not in frappe.get_roles(user):
        frappe.throw(_("Akses ditolak."), frappe.PermissionError)

    proof = frappe.get_doc({
        "doctype": "DS Delivery Proof",
        "parent": task_id,
        "parenttype": "DS Delivery Task",
        "parentfield": "delivery_proofs",
        "photo": file_url,
        "note": note,
        "uploaded_at": now_datetime(),
        "uploaded_by": user,
    })
    proof.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"message": "Bukti pengiriman berhasil diupload.", "proof_id": proof.name}


@frappe.whitelist()
def get_driver_history(page=1, page_size=20):
    """Driver: riwayat pengiriman yang sudah selesai."""
    frappe.only_for(["Delivery Driver", "System Manager"])
    user = frappe.session.user
    page = cint(page)
    page_size = cint(page_size)
    offset = (page - 1) * page_size

    tasks = frappe.get_all(
        "DS Delivery Task",
        filters={"driver_user": user, "status": ["in", ["Delivered", "Failed"]]},
        fields=["name", "order", "delivery_address", "status",
                "delivered_at", "total_amount", "payment_method"],
        order_by="delivered_at desc",
        limit=page_size,
        start=offset,
    )

    total = frappe.db.count("DS Delivery Task", {
        "driver_user": user, "status": ["in", ["Delivered", "Failed"]]
    })

    return {"tasks": tasks, "total": total}


# ══════════════════════════════════════════════════════════════════════════════
#  REPORTS / DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_sales_dashboard(from_date="", to_date=""):
    """Admin: summary penjualan untuk dashboard."""
    frappe.only_for(["Delivery Admin", "System Manager"])

    filters_sql = ""
    params = {}
    if from_date:
        filters_sql += " AND DATE(o.order_date) >= %(from_date)s"
        params["from_date"] = from_date
    if to_date:
        filters_sql += " AND DATE(o.order_date) <= %(to_date)s"
        params["to_date"] = to_date

    summary = frappe.db.sql(f"""
        SELECT
            COUNT(*) as total_orders,
            SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
            SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled,
            SUM(CASE WHEN status NOT IN ('Delivered','Cancelled') THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'Delivered' THEN total_amount ELSE 0 END) as total_revenue,
            SUM(total_amount) as gross_amount
        FROM `tabDS Order` o
        WHERE 1=1 {filters_sql}
    """, params, as_dict=True)[0]

    # Chart harian
    daily = frappe.db.sql(f"""
        SELECT
            DATE(order_date) as date,
            COUNT(*) as orders,
            SUM(CASE WHEN status='Delivered' THEN total_amount ELSE 0 END) as revenue
        FROM `tabDS Order` o
        WHERE 1=1 {filters_sql}
        GROUP BY DATE(order_date)
        ORDER BY date DESC
        LIMIT 30
    """, params, as_dict=True)

    # Top produk
    top_products = frappe.db.sql(f"""
        SELECT
            oi.product_name,
            SUM(oi.qty) as total_qty,
            SUM(oi.subtotal) as total_revenue
        FROM `tabDS Order Item` oi
        JOIN `tabDS Order` o ON o.name = oi.parent
        WHERE o.status = 'Delivered' {filters_sql}
        GROUP BY oi.product_name
        ORDER BY total_qty DESC
        LIMIT 10
    """, params, as_dict=True)

    return {
        "summary": summary,
        "daily_chart": daily,
        "top_products": top_products,
    }


@frappe.whitelist()
def get_customer_list(search="", page=1, page_size=20):
    """Admin: daftar customer."""
    frappe.only_for(["Delivery Admin", "System Manager"])
    page = cint(page)
    page_size = cint(page_size)
    offset = (page - 1) * page_size

    search_filter = ""
    params = {"offset": offset, "page_size": page_size}
    if search:
        search_filter = "AND (cp.full_name LIKE %(search)s OR cp.email LIKE %(search)s)"
        params["search"] = f"%{search}%"

    customers = frappe.db.sql(f"""
        SELECT
            cp.user, cp.full_name, cp.email, cp.phone,
            COUNT(o.name) as total_orders,
            SUM(CASE WHEN o.status='Delivered' THEN o.total_amount ELSE 0 END) as total_spent
        FROM `tabDS Customer Profile` cp
        LEFT JOIN `tabDS Order` o ON o.customer_user = cp.user
        WHERE 1=1 {search_filter}
        GROUP BY cp.user
        ORDER BY total_spent DESC
        LIMIT %(page_size)s OFFSET %(offset)s
    """, params, as_dict=True)

    return customers


# ══════════════════════════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _send_notification(user, subject, message):
    """Kirim notifikasi in-app (dan opsional email)."""
    try:
        notif = frappe.get_doc({
            "doctype": "Notification Log",
            "subject": subject,
            "email_content": message,
            "for_user": user,
            "type": "Alert",
        })
        notif.insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "DS Notification Error")
