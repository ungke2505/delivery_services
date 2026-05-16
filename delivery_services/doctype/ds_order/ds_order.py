import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint


class DSOrder(Document):
    def validate(self):
        self._calculate_total()

    def _calculate_total(self):
        total = 0
        for item in self.items:
            item.subtotal = flt(item.price) * cint(item.qty)
            total += item.subtotal
        self.total_amount = total

    def on_submit(self):
        pass

    def on_cancel(self):
        self.status = "Cancelled"
