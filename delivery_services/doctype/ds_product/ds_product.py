import frappe
from frappe.model.document import Document


class DSProduct(Document):
    def validate(self):
        if self.price and self.price < 0:
            frappe.throw("Harga tidak boleh negatif.")
        if self.stock_qty and self.stock_qty < 0:
            frappe.throw("Stok tidak boleh negatif.")
