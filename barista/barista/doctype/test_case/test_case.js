// Copyright (c) 2019, elasticrun and contributors
// For license information, please see license.txt

frappe.ui.form.on('Test Case', {
	refresh: function (frm) {

		if (cur_frm.doc.doctype_name) {
			var row = locals[cdt][cdn];
			row.doctype_name = cur_frm.doc.doctype_name;
			cur_frm.refresh_fields();
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
		cur_frm.set_query("test_data", function (doc) {
			if (cur_frm.doc.testcase_doctype) {
				if (cur_frm.doc.is_test_data_on_different_doctype == 1) {
					return {
						filters: {}
					}
				}
				else {
					return {
						filters: {
							"doctype_name": cur_frm.doc.testcase_doctype
						}
					}
				}
			}

			else {
				frappe.throw("Please Choose TestCase Doctype first")
			}
		});
		cur_frm.set_query("doctype_name", "assertion", function (doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			if (row.module) {
				return {
					filters: {
						'module': row.module
					}
				}
			} else {
				frappe.throw("Please Select Module")
			}
		});
		if (cur_frm.doc.assertion && cur_frm.doc.assertion.length > 0 && cur_frm.doc.assertion[0].doctype_name) {
			var doctype_name = cur_frm.doc.assertion[0].doctype_name;
			frappe.model.with_doctype(doctype_name, function () {
				var options = $.map(frappe.get_meta(doctype_name).fields,
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
				options.push("name");

				frappe.meta.get_docfield("Assertion", "reference_field", cur_frm.doc.name).options = options;
				frappe.meta.get_docfield("Assertion", "docfield_name", cur_frm.doc.name).options = options;
			});
			cur_frm.refresh_fields();
		}
		$("[data-fieldname=dummy_chkbox]").find("i.disabled-check").css("display", "none");
		$("[data-fieldname=dummy_chkbox]").find("label").css("min-height", "16px");

		if (cur_frm.doc.testcase_doctype) {
			addTestCaseDocFields(cur_frm);
		}

		if (cur_frm.doc.test_data) {
			addTestDataDocFields(cur_frm);
		}
	},
	testcase_doctype: function (cur_frm) {
		if (cur_frm.doc.testcase_doctype) {
			addTestCaseDocFields(cur_frm);
		}
	},
	test_data: function (cur_frm) {
		if (cur_frm.doc.test_data) {
			addTestDataDocFields(cur_frm);
		}
	}



});

frappe.ui.form.on('Testdatafield', {
	refresh: function (frm, cdt, cdn) {

	},
	update_fields_add: function (frm, cdt, cdn) {
		if (cur_frm.doc.testcase_doctype) {
			var row = locals[cdt][cdn];
			row.doctype_name = cur_frm.doc.testcase_doctype;
			cur_frm.refresh_fields();
			var options = [];
			frappe.model.with_doctype(cur_frm.doc.testcase_doctype, function () {
				var options = $.map(frappe.get_meta(cur_frm.doc.testcase_doctype).fields,
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
				options.push("name");
				frappe.meta.get_docfield("Testdatafield", "docfield_fieldname", cur_frm.doc.name).options = options;
			});
		} else {
			cur_frm.refresh_fields();
			frappe.throw("Please Add the Doctype Name to Proceed")
		}
	}
});

frappe.ui.form.on("Assertion", {
	refresh: function (frm, cdt, cdn) {

	},
	doctype_name: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.doctype_name) {
			frappe.model.with_doctype(row.doctype_name, function () {
				var options = $.map(frappe.get_meta(row.doctype_name).fields,
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
				options.push("name");
				frappe.meta.get_docfield("Assertion", "reference_field", cur_frm.doc.name).options = options;
				frappe.meta.get_docfield("Assertion", "docfield_name", cur_frm.doc.name).options = options;
			});
			cur_frm.refresh_fields();
		}
	}
});

function addTestCaseDocFields(cur_frm) {
	frappe.model.with_doctype(cur_frm.doc.testcase_doctype, function () {
		var options = $.map(frappe.get_meta(cur_frm.doc.testcase_doctype).fields,
			function (d) {
				if (d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype) === -1) {
					return d.fieldname;
				} else if (d.fieldname && d.fieldtype == 'Table') {
					return d.fieldname;
				}
				return null;
			}
		);
		options.push("name");
		cur_frm.fields_dict.test_case_docfield.df.options = options;
		cur_frm.refresh_field("test_case_docfield")

	});
	// cur_frm.refresh_fields();

}

function addTestDataDocFields(cur_frm) {
	frappe.call({
		"method": "frappe.client.get_value",
		"args": {
			doctype: "Test Data",
			fieldname: "doctype_name",
			filters: { name: cur_frm.doc.test_data }
		},
		freeze: true,
		callback: function (r) {
			var testDataDoc = r.message.doctype_name;
			frappe.model.with_doctype(testDataDoc, function () {
				var options = $.map(frappe.get_meta(testDataDoc).fields,
					function (d) {
						if (d.fieldname && frappe.model.no_value_type.indexOf(d.fieldtype) === -1) {
							return d.fieldname;
						} else if (d.fieldname && d.fieldtype == 'Table') {
							return d.fieldname;
						}
						return null;
					}
				);
				options.push("name");
				cur_frm.fields_dict.test_data_docfield.df.options = options;
				cur_frm.refresh_field("test_data_docfield");
			});
		}

	})

	// cur_frm.refresh_fields();
}

frappe.ui.form.on("Function Parameter", "test_data", function (frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let docFields = [];
	frappe.db.get_value('Test Data', row.test_data, 'doctype_name').then((d) => {
		let testDataDoctype = d.message.doctype_name;
		frappe.model.with_doctype(testDataDoctype);
		frappe.call({
			method: 'frappe.desk.form.load.getdoctype',
			args: {
				'doctype': testDataDoctype,
				'with_parent': 1
			},
			freeze: true,
			callback: function (r) {
				if (!r.exc) {
					frappe.model.with_doctype(testDataDoctype, function () {
						let fields = frappe.get_meta(testDataDoctype).fields;
						let options = [];
						fields.forEach((f) => {
							if (!['Section Break', 'Column Break'].includes(f.fieldtype)) {
								options.push(f.fieldname);
							}
						})
						options.push("docstatus");
						options.push('name');
						docFields = options;
						frappe.meta.get_docfield("Function Parameter", "field", cur_frm.doc.name).options = docFields;
					});
					cur_frm.refresh_fields();
				}
			}
		});
	});

});