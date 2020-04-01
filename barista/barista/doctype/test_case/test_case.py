# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TestCase(Document):
	def validate(self):
		# if self.test_data:
		# 	if frappe.db.get_value("Test Data",self.test_data,"doctype_name") != self.testcase_doctype:
		# 		frappe.throw("Invalid Test Data Doctype")
		if self.testcase_doctype:
			docfields = [docfield.fieldname for docfield in frappe.get_meta(self.testcase_doctype).fields]
			docfields.append('docstatus')
			docfields.append('name')
			docfields.append('parent')
			
			for row in self.update_fields:
				if row.docfield_fieldname not in docfields:
					frappe.throw(f"Invalid DocField {row.docfield_fieldname} in {self.testcase_doctype}")