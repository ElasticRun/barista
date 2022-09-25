// Copyright (c) 2020, ElasticRun and contributors
// For license information, please see license.txt

frappe.ui.form.on('Barista Job Setting', {
	refresh: run_job,
});
function run_job(frm) {
        frm.add_custom_button("Run Barista", () => { 
            frappe.dom.freeze()
            frappe.call('barista.barista.api.barista_trigger.barista_job').then(() => frappe.dom.unfreeze());
        })
        frm.custom_buttons["Run Barista"].addClass("btn-danger");
    
}
