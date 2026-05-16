app_name = "delivery_services"
after_install = "delivery_services.install.after_install"
app_title = "Delivery Services"
app_publisher = "Your Company"
app_description = "Delivery Services PWA for ERPNext v15"
app_email = "admin@yourcompany.com"
app_license = "MIT"
app_version = "1.0.0"

# ─── Website Routes ───────────────────────────────────────────────────────────
website_route_rules = [
    {"from_route": "/delivery", "to_route": "delivery/index"},
    {"from_route": "/delivery/driver", "to_route": "delivery/driver"},
]

# ─── DocType JS (form customizations) ─────────────────────────────────────────
# Frappe v15: path relatif dari root app, file di-serve langsung (tidak di-bundle esbuild)
doctype_js = {
    "DS Order":         "public/js/ds_order.js",
    "DS Payment":       "public/js/ds_payment.js",
    "DS Delivery Task": "public/js/ds_delivery_task.js",
}

# ─── Fixtures ─────────────────────────────────────────────────────────────────
fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Delivery Driver", "Delivery Admin"]]]},
]

# ─── Scheduled Tasks ──────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "delivery_services.tasks.daily_order_reminder",
    ],
    "hourly": [
        "delivery_services.tasks.check_stale_orders",
    ],
}

# ─── Jinja ────────────────────────────────────────────────────────────────────
jinja = {
    "methods": [
        "delivery_services.utils.format_idr",
    ]
}

# ─── Permissions ──────────────────────────────────────────────────────────────
has_permission = {
    "DS Order":         "delivery_services.permissions.has_order_permission",
    "DS Delivery Task": "delivery_services.permissions.has_delivery_task_permission",
    "DS Payment":       "delivery_services.permissions.has_payment_permission",
}

# ─── Document Events ──────────────────────────────────────────────────────────
doc_events = {
    "DS Order": {
        "on_submit": "delivery_services.controllers.order_controller.on_submit",
        "on_cancel": "delivery_services.controllers.order_controller.on_cancel",
    },
    "DS Payment": {
        "after_insert": "delivery_services.controllers.payment_controller.after_insert",
        "on_update":    "delivery_services.controllers.payment_controller.on_update",
    },
    "DS Delivery Task": {
        "on_update": "delivery_services.controllers.delivery_controller.on_update",
    },
}
