from frappe import _


def get_data():
    return [
        {
            "label": _("Pesanan"),
            "items": [
                {
                    "type": "doctype",
                    "name": "DS Order",
                    "label": _("Orders"),
                    "description": _("Kelola semua pesanan masuk"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "DS Payment",
                    "label": _("Pembayaran"),
                    "description": _("Verifikasi bukti transfer"),
                    "onboard": 1,
                },
                {
                    "type": "doctype",
                    "name": "DS Delivery Task",
                    "label": _("Tugas Pengiriman"),
                    "description": _("Monitor status pengiriman"),
                    "onboard": 1,
                },
            ],
        },
        {
            "label": _("Produk"),
            "items": [
                {
                    "type": "doctype",
                    "name": "DS Product",
                    "label": _("Produk"),
                    "description": _("Kelola katalog produk"),
                    "onboard": 1,
                },
            ],
        },
        {
            "label": _("Customer"),
            "items": [
                {
                    "type": "doctype",
                    "name": "DS Customer Profile",
                    "label": _("Customer"),
                    "description": _("Data profil customer"),
                },
            ],
        },
        {
            "label": _("Laporan"),
            "items": [
                {
                    "type": "report",
                    "name": "Sales Summary DS",
                    "doctype": "DS Order",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Delivery Performance DS",
                    "doctype": "DS Delivery Task",
                    "is_query_report": True,
                },
            ],
        },
        {
            "label": _("PWA Links"),
            "items": [
                {
                    "type": "page",
                    "name": "delivery-customer-pwa",
                    "label": _("Customer PWA"),
                    "route": "/delivery",
                },
                {
                    "type": "page",
                    "name": "delivery-driver-pwa",
                    "label": _("Driver PWA"),
                    "route": "/delivery/driver",
                },
            ],
        },
    ]
