# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.modules.export_file import export_to_files

class TestCase(Document):
	def autoname(self):
		bs = ''
		if frappe.conf.get('barista_series'):
			bs = f"{frappe.conf.get('barista_series')}-"
		
		self.naming_series = 'TestCase-'
			
		self.naming_series = f"{bs}{self.naming_series}"

	def validate(self):
		if self.testcase_doctype:
			docfields = [docfield.fieldname for docfield in frappe.get_meta(
				self.testcase_doctype).fields]
			docfields.append('docstatus')
			docfields.append('name')
			docfields.append('parent')

			for row in self.update_fields:
				if row.docfield_fieldname not in docfields:
					frappe.throw(
						f"Invalid DocField {row.docfield_fieldname} in {self.testcase_doctype} of Test Case {self.name}")

	def on_update(self):
		if self.is_standard == "Yes" and frappe.local.conf.developer_mode and not frappe.flags.in_migrate:
			export_to_files(record_list=[[self.doctype, self.name]], record_module="barista", create_init=True)


# Get data for test-case-info:
@frappe.whitelist()
def get_test_case_info(test_case):
	# Get relevant data to pass to the template:
	test_case_doc = frappe.get_doc("Test Case", test_case).as_dict()
	assertions = test_case_doc.get("assertion", {})
	test_data_name, test_data_description = '', ''
	if test_case_doc.test_data:
		test_data_name, test_data_description = frappe.get_value("Test Data", test_case_doc.test_data, ['name', 'description'])

	# render template and fill JINJA values:
	rendered_info = frappe.render_template('barista/barista/doctype/test_case/templates/test_case_info.html',
											{'test_case_doc': test_case_doc,
											'test_data_name': test_data_name,
											'test_data_description': test_data_description,
											'assertions': assertions})
	
	return rendered_info