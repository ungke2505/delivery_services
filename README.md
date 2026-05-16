# Delivery Services - Frappe/ERPNext v15

PWA-based delivery management system built on Frappe Framework + ERPNext v15.

## Fitur
| Komponen | Fitur |
|---|---|
| **Customer PWA** | Register/Login, Katalog, Search, Cart, Checkout, COD/Transfer, Upload bukti, Tracking, Riwayat |
| **Driver PWA** | Login, Daftar tugas, Update status, Upload foto bukti |
| **Admin (ERPNext)** | Manajemen produk, Validasi pembayaran, Assign driver, Laporan penjualan |

---

## Prasyarat VPS

- Ubuntu 20.04 / 22.04
- RAM minimal 4 GB
- ERPNext v15 sudah terinstall via `bench`
- Domain/subdomain sudah pointing ke VPS (untuk HTTPS)

---

## Langkah Deploy

### 1. Upload app ke server

```bash
# Di VPS, masuk ke folder bench
cd /home/frappe/frappe-bench

# Copy folder delivery_services ke apps/
cp -r /path/to/delivery_services apps/delivery_services
```

Atau clone dari repo jika sudah di-push:
```bash
bench get-app https://github.com/youruser/delivery_services
```

### 2. Install app ke site

```bash
bench --site your-site.com install-app delivery_services
```

### 3. Migrate database (buat semua DocType)

```bash
bench --site your-site.com migrate
```

### 4. Generate PWA icons

```bash
cd apps/delivery_services/delivery_services/www/delivery/assets
python3 generate_icons.py
```

> Ganti icon-*.png dengan icon asli sebelum production.

### 5. Build assets

```bash
bench build --app delivery_services
```

### 6. Restart services

```bash
bench restart
# atau
sudo supervisorctl restart all
```

---

## Setup Awal di ERPNext

### Buat User Admin Delivery

1. Buka ERPNext → **Settings → User**
2. Buat user baru, assign role: **Delivery Admin**

### Buat User Driver

1. Buka ERPNext → **Settings → User**
2. Buat user baru, assign role: **Delivery Driver**

### Input Produk Pertama

1. Buka ERPNext → **Delivery Services → Produk**
2. Klik **New**, isi nama, harga, stok, kategori, foto
3. Centang **Aktif** → Save

---

## URL Akses

| Halaman | URL |
|---|---|
| Customer PWA | `https://your-site.com/delivery` |
| Driver PWA | `https://your-site.com/delivery/driver` |
| Admin ERPNext | `https://your-site.com` |

---

## API Endpoints

Semua endpoint di: `/api/method/delivery_services.api.<method_name>`

| Method | Auth | Deskripsi |
|---|---|---|
| `get_session_user` | Guest | Cek status login |
| `register_customer` | Guest | Registrasi customer baru |
| `get_products` | Guest | Daftar produk (pagination, search, filter) |
| `get_categories` | Guest | Daftar kategori |
| `create_order` | Customer | Buat pesanan dari cart |
| `get_my_orders` | Customer | Riwayat pesanan |
| `get_order_detail` | Customer/Admin/Driver | Detail pesanan |
| `upload_payment_proof` | Customer | Upload bukti transfer |
| `verify_payment` | Delivery Admin | Approve/reject pembayaran |
| `assign_driver` | Delivery Admin | Assign driver ke order |
| `get_pending_orders` | Delivery Admin | Daftar order aktif |
| `get_available_drivers` | Delivery Admin | Daftar driver tersedia |
| `get_my_tasks` | Delivery Driver | Tugas aktif driver |
| `update_delivery_status` | Delivery Driver | Update status pengiriman |
| `upload_delivery_proof` | Delivery Driver | Upload foto bukti kirim |
| `get_driver_history` | Delivery Driver | Riwayat pengiriman |
| `get_sales_dashboard` | Delivery Admin | Dashboard & chart penjualan |
| `get_customer_list` | Delivery Admin | Daftar customer |

---

## Alur Order

```
Customer Checkout
    ↓
DS Order (status: Pending)
    ↓ [Transfer]          ↓ [COD]
Upload Bukti          Langsung Confirmed
    ↓
Admin Verifikasi
    ↓
Confirmed → Assign Driver
    ↓
DS Delivery Task (Assigned)
    ↓ Driver berangkat
On The Way
    ↓ Driver tiba
Arrived
    ↓ Barang diserahkan + foto bukti
Delivered ✓
```

---

## Status Order

| Status | Keterangan |
|---|---|
| Pending | Order baru dibuat |
| Payment Uploaded | Bukti transfer sudah diupload |
| Confirmed | Pembayaran dikonfirmasi admin |
| Assigned | Driver sudah di-assign |
| On The Way | Driver sedang dalam perjalanan |
| Arrived | Driver sudah tiba |
| Delivered | Pesanan berhasil diterima |
| Delivery Failed | Pengiriman gagal |
| Cancelled | Order dibatalkan |

---

## Troubleshooting

**PWA tidak bisa diinstall:**
- Pastikan site menggunakan HTTPS
- Cek manifest.json bisa diakses di `/delivery/manifest.json`
- Cek service worker di `/delivery/assets/sw.js`

**Login gagal dari PWA:**
- Pastikan CORS tidak diblock (biasanya aman karena same-domain)
- Cek cookie `csrf_token` tersedia

**Endpoint 403:**
- Pastikan user punya role yang sesuai (Customer/Delivery Driver/Delivery Admin)
- Cek permissions di masing-masing DocType JSON

**Migrate gagal:**
```bash
bench --site your-site.com migrate --skip-failing
# Lalu cek error log
bench --site your-site.com console
# >>> frappe.get_all("DocType", filters={"module": "Delivery Services"})
```

---

## Struktur File

```
delivery_services/
├── delivery_services/
│   ├── hooks.py                    ← App config & events
│   ├── api.py                      ← Semua REST endpoints
│   ├── install.py                  ← Setup otomatis
│   ├── permissions.py              ← Custom permission logic
│   ├── utils.py                    ← Helper functions
│   ├── tasks.py                    ← Scheduled jobs
│   ├── doctype/
│   │   ├── ds_product/             ← Katalog produk
│   │   ├── ds_order/               ← Pesanan utama
│   │   ├── ds_order_item/          ← Child: item pesanan
│   │   ├── ds_payment/             ← Bukti pembayaran
│   │   ├── ds_delivery_task/       ← Tugas driver
│   │   ├── ds_delivery_proof/      ← Child: foto bukti
│   │   └── ds_customer_profile/    ← Profil customer
│   ├── controllers/
│   │   ├── order_controller.py
│   │   ├── payment_controller.py
│   │   └── delivery_controller.py
│   ├── public/js/
│   │   ├── ds_order.js             ← Form buttons ERPNext
│   │   ├── ds_payment.js
│   │   └── ds_delivery_task.js
│   ├── www/delivery/
│   │   ├── index.html              ← Customer PWA
│   │   ├── driver.html             ← Driver PWA
│   │   ├── manifest.json           ← PWA manifest customer
│   │   ├── manifest-driver.json    ← PWA manifest driver
│   │   └── assets/
│   │       ├── sw.js               ← Service Worker
│   │       ├── icon-192.png
│   │       ├── icon-512.png
│   │       ├── icon-driver-192.png
│   │       └── icon-driver-512.png
│   ├── report/
│   │   ├── sales_summary/          ← Laporan penjualan
│   │   └── delivery_performance/   ← Performa driver
│   └── config/
│       ├── desktop.py              ← Module icon di ERPNext
│       └── delivery_services.py    ← Sidebar menu
└── setup.py
```

---

## Pengembangan Lanjutan

- **Push Notification** via Web Push API + `pywebpush` library
- **WhatsApp notification** via Twilio / WA Cloud API di `controllers/`
- **Google Maps** embed di Driver PWA untuk navigasi
- **COD payment collection** tracking di DS Delivery Task
- **Multi-warehouse** support via ERPNext Warehouse linking
- **Promo & voucher** via DocType baru DS Promo
