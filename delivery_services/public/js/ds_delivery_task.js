frappe.ui.form.on("DS Delivery Task", {
    refresh(frm) {
        const colors = {
            "Assigned": "blue",
            "On The Way": "purple",
            "Arrived": "orange",
            "Delivered": "green",
            "Failed": "red",
        };
        frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || "grey");
    },
});
