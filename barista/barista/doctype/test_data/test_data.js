// Copyright (c) 2019, elasticrun and contributors
// For license information, please see license.txt
let docFields = [];

frappe.ui.form.on('Test Data', {
	refresh: function (frm) {
		$("[data-fieldname=read_only_7]").find("div.like-disabled-input").css("background", "white");
		$("[data-fieldname=data_7]").find("div.like-disabled-input").css("background", "white");
		$("[data-fieldname=data_7]").find("div.like-disabled-input").attr("style", "background: white !important;");
		$("[data-fieldname=data_8]").find("div.like-disabled-input").css("background", "white");
		$("div[data-fieldname=existing_record]").css("padding-top", "13px");
		cur_frm.set_query("doctype_name", function (doc) {
			if (cur_frm.doc.module_name) {
				return {
					filters: {
						'module': cur_frm.doc.module_name
					}
				}
			} else {
				frappe.throw("Please Add Module Name First")
			}
		});
		if (cur_frm.doc.doctype_name) {
			// var row = locals[cdt][cdn];
			// row.doctype_name = cur_frm.doc.doctype_name;
			// cur_frm.refresh_fields();
			if (cur_frm.doc.doctype_name) {
				frappe.model.with_doctype(cur_frm.doc.doctype_name, function () {
					var options = $.map(frappe.get_meta(cur_frm.doc.doctype_name).fields,
						function (d) {
							if (d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype) === -1) {
								return d.fieldname;
							} else if (d.fieldname && d.fieldtype == 'Table') {
								return d.fieldname;
							}
							return null;
						}
					);
					options.push("docstatus");
					frappe.meta.get_docfield("Testdatafield", "docfield_fieldname", cur_frm.doc.name).options = options;
				});
			}
		}
	}
});


frappe.ui.form.on('Testdatafield', {
	refresh: function (frm, cdt, cdn) {

	},
	docfield_value_add: function (frm, cdt, cdn) {
		if (cur_frm.doc.doctype_name) {
			var row = locals[cdt][cdn];
			row.doctype_name = cur_frm.doc.doctype_name;
			cur_frm.refresh_fields();
			frappe.model.with_doctype(cur_frm.doc.doctype_name, function () {
				// var prompt_name = frappe.get_meta(cur_frm.doc.doctype_name).autoname
				var options = $.map(frappe.get_meta(cur_frm.doc.doctype_name).fields,
					function (d) {
						if (d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype) === -1) {
							return d.fieldname;
						} else if (d.fieldname && d.fieldtype == 'Table') {
							return d.fieldname;
						}
						return null;
					}
				);
				// if(prompt_name === "Prompt"){
				// 	options.push("__newname")	
				// }
				
				options.push("docstatus");
				frappe.meta.get_docfield("Testdatafield", "docfield_fieldname", cur_frm.doc.name).options = options;
			});
		} else {
			cur_frm.refresh_fields();
			frappe.throw("Please Add the Doctype Name to Proceed")
		}
	},
	toggle_view: function (frm, cdt, cdn) {
		console.log('opened')
	}
});

frappe.ui.form.on("Test Data", "doctype_name", function (frm, cdt, cdn) {
	let tableFields = [];
	docFields = [];
	cur_frm.doc.docfield_value = [];
	cur_frm.doc.existing_record = '';
	cur_frm.refresh_fields();
	if (cur_frm.doc.doctype_name) {
		frappe.model.with_doctype(cur_frm.doc.doctype_name);
		frappe.call({
			method: 'frappe.desk.form.load.getdoctype',
			args: {
				'doctype': cur_frm.doc.doctype_name,
				'with_parent': 1
			},
			freeze: true,
			callback: function (r) {
				if (!r.exc) {
					frappe.model.with_doctype(cur_frm.doc.doctype_name, function () {
						var options = $.map(frappe.get_meta(cur_frm.doc.doctype_name).fields,
							function (d) {
								if (d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype) === -1) {
									return d.fieldname;
								} else if (d.fieldname && d.fieldtype == 'Table') {
									tableFields.push(d.fieldname);
									return d.fieldname;
								}
								return null;
							}
						);
						options.push("docstatus");
						options.push("name");
						docFields = options;
						frappe.meta.get_docfield("Testdatafield", "docfield_fieldname", cur_frm.doc.name).options = docFields;
					});
					docFields.forEach((d) => {
						var childTable = cur_frm.add_child("docfield_value");
						childTable.doctype_name = cur_frm.doc.doctype_name;
						childTable.docfield_fieldname = d;
						if (tableFields.includes(d)) {
							childTable.docfield_code_value = 'Code';
						} else {
							childTable.docfield_code_value = 'Fixed Value';
						}

						cur_frm.refresh_fields("docfield_value");
					});
				}
			}
		});
	}
})

frappe.ui.form.on("Test Data", "existing_record", function (frm, cdt, cdn) {
	if (cur_frm.doc.existing_record) {
		frappe.call({
			method: 'frappe.desk.form.load.getdoc',
			args: {
				'doctype': cur_frm.doc.doctype_name,
				'name': cur_frm.doc.existing_record
			},
			freeze: true,
			callback: function (r) {
				if (!r.exc) {
					if (r.docs) {
						if (r.docs[0]) {
							const doc = r.docs[0];
							cur_frm.doc.docfield_value.forEach((d) => {
								if (typeof (doc[d.docfield_fieldname]) === 'object') {
									// d.docfield_code = JSON.stringify(doc[d.docfield_fieldname])
									// currently setting as empty
								} else {
									d.docfield_value = doc[d.docfield_fieldname];
								}
							})
							cur_frm.refresh_fields()
						}
					}
				}
			}
		});
	}
})