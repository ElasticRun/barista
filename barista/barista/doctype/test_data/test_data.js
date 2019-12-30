// Copyright (c) 2019, elasticrun and contributors
// For license information, please see license.txt

frappe.ui.form.on('Test Data', {
	refresh: function(frm) {
			cur_frm.set_query("doctype_name", function(doc){
				if(cur_frm.doc.module_name) {
					return {
						filters: {
							'module':cur_frm.doc.module_name
						}
					}
				} else {
					frappe.throw("Please Add Module Name First")		
				}
			});
			if(cur_frm.doc.doctype_name){
				var row = locals[cdt][cdn];
				row.doctype_name = cur_frm.doc.doctype_name;
				cur_frm.refresh_fields();
				frappe.model.with_doctype(cur_frm.doc.doctype_name, function () {
					var options = $.map(frappe.get_meta(cur_frm.doc.doctype_name).fields,
						function (d) {
						if (d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype) === -1) {
							return d.fieldname;
						} else if(d.fieldname && d.fieldtype == 'Table') {
							return d.fieldname;
						}
						return null;
						}
					);
					options.push("docstatus");
					frappe.meta.get_docfield("Testdatafield","docfield_fieldname", cur_frm.doc.name).options = options;
				});
			}
	}
});


frappe.ui.form.on('Testdatafield', {
	refresh: function(frm,cdt,cdn){

	},
	docfield_value_add: function(frm,cdt,cdn){
		if(cur_frm.doc.doctype_name){
			var row = locals[cdt][cdn];
			row.doctype_name = cur_frm.doc.doctype_name;
			cur_frm.refresh_fields();
			frappe.model.with_doctype(cur_frm.doc.doctype_name, function () {
				var options = $.map(frappe.get_meta(cur_frm.doc.doctype_name).fields,
					function (d) {
					if (d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype) === -1) {
						return d.fieldname;
					} else if(d.fieldname && d.fieldtype == 'Table') {
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