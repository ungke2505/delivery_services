frappe.ui.form.on("DS Order", {
    refresh(frm) {
        if (!frm.is_new()) {
            // Tombol Assign Driver (untuk admin)
            if (
                frappe.user.has_role(["Delivery Admin", "System Manager"]) &&
                frm.doc.status === "Confirmed"
            ) {
                frm.add_custom_button(__("Assign Driver"), () => {
                    _show_assign_driver_dialog(frm);
                }, __("Actions"));
            }

            // Tombol Batalkan Order
            if (
                frappe.user.has_role(["Delivery Admin", "System Manager"]) &&
                !["Delivered", "Cancelled"].includes(frm.doc.status)
            ) {
                frm.add_custom_button(__("Batalkan Order"), () => {
                    frappe.confirm("Batalkan order ini?", () => {
                        frm.set_value("status", "Cancelled");
                        frm.save();
                    });
                }, __("Actions"));
            }
        }

        // Warna status
        const colors = {
            "Pending": "orange",
            "Payment Uploaded": "blue",
            "Confirmed": "green",
            "Assigned": "blue",
            "On The Way": "purple",
            "Arrived": "purple",
            "Delivered": "green",
            "Delivery Failed": "red",
            "Cancelled": "red",
        };
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "grey");
        }
    },
});

function _show_assign_driver_dialog(frm) {
    frappe.call({
        method: "delivery_services.api.get_available_drivers",
        callback(r) {
            if (!r.message) return;
            const drivers = r.message;
            const opts = drivers.map(d => ({
                label: `${d.full_name} (${d.active_tasks} tugas aktif)`,
                value: d.name,
            }));

            const d = new frappe.ui.Dialog({
                title: "Assign Driver",
                fields: [
                    {
                        fieldname: "driver_user",
                        fieldtype: "Select",
                        label: "Pilih Driver",
                        options: opts.map(o => o.label).join("\n"),
                        reqd: 1,
                    },
                    {
                        fieldname: "estimated_arrival",
                        fieldtype: "Datetime",
                        label: "Estimasi Tiba",
                    },
                ],
                primary_action_label: "Assign",
                primary_action(values) {
                    const selected = opts.find(o => o.label === values.driver_user);
                    if (!selected) return;
                    frappe.call({
                        method: "delivery_services.api.assign_driver",
                        args: {
                            order_id: frm.doc.name,
                            driver_user: selected.value,
                            estimated_arrival: values.estimated_arrival || "",
                        },
                        callback(res) {
                            if (res.message) {
                                frappe.msgprint(__("Driver berhasil di-assign."));
                                frm.reload_doc();
                            }
                        },
                    });
                    d.hide();
                },
            });
            d.show();
        },
    });
}
