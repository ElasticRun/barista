// Copyright (c) 2019, elasticrun and contributors
// For license information, please see license.txt

frappe.ui.form.on('Test Case', {
	refresh: function(frm) {

	}
});

frappe.ui.form.on('Testdatafield', {
	refresh: function(frm,cdt,cdn){

	},
	update_fields_add: function(frm,cdt,cdn){
		if(cur_frm.doc.testcase_doctype){
			debugger;
			var row = locals[cdt][cdn];
			row.doctype_name = cur_frm.doc.testcase_doctype;
			cur_frm.refresh_fields();
			var options = [];
			frappe.model.with_doctype(cur_frm.doc.testcase_doctype, function () {
				var options = $.map(frappe.get_meta(cur_frm.doc.testcase_doctype).fields,
					function (d) {
					if (d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype) === -1) {
						return d.fieldname;
					}
					return null;
					}
				);
				options.push("docstatus");
				frappe.meta.get_docfield("Testdatafield","docfield_fieldname", cur_frm.doc.name).options = options;
			});
		} else {
			cur_frm.refresh_fields();
			frappe.throw("Please Add the Doctype Name to Proceed")
		}
	}
});