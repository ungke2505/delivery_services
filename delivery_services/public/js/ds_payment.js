frappe.ui.form.on("DS Payment", {
    refresh(frm) {
        if (
            frappe.user.has_role(["Delivery Admin", "System Manager"]) &&
            frm.doc.status === "Menunggu Verifikasi" &&
            !frm.is_new()
        ) {
            frm.add_custom_button(__("✓ Verifikasi"), () => {
                frappe.confirm("Konfirmasi pembayaran ini?", () => {
                    frappe.call({
                        method: "delivery_services.api.verify_payment",
                        args: { payment_id: frm.doc.name, action: "approve" },
                        callback(r) {
                            frappe.msgprint(r.message?.message || "Berhasil.");
                            frm.reload_doc();
                        },
                    });
                });
            }, __("Actions"));

            frm.add_custom_button(__("✗ Tolak"), () => {
                frappe.prompt(
                    { fieldname: "reason", fieldtype: "Small Text", label: "Alasan Penolakan", reqd: 1 },
                    (v) => {
                        frm.set_value("rejection_reason", v.reason);
                        frappe.call({
                            method: "delivery_services.api.verify_payment",
                            args: { payment_id: frm.doc.name, action: "reject" },
                            callback(r) {
                                frm.reload_doc();
                            },
                        });
                    },
                    "Tolak Pembayaran"
                );
            }, __("Actions"));
        }

        const colors = {
            "Menunggu Verifikasi": "orange",
            "Verified": "green",
            "Ditolak": "red",
        };
        frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "grey");
    },
});
