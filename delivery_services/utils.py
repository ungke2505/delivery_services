import frappe


def format_idr(amount):
    """Format angka ke format Rupiah Indonesia."""
    try:
        return "Rp {:,.0f}".format(float(amount)).replace(",", ".")
    except Exception:
        return "Rp 0"
