# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class TestCase(Document):
	def run_testcase(self,testcase):
		testcase_doc = frappe.get_doc("Test Case", testcase)
		if (testcase_doc.testcase_type == "CREATE"):
			#test case is to create a record. 
			new_doc = create_testdata(self)
			pass
		elif (testcase_doc.testcase_type == "UPDATE"):
			pass
		elif (testcase_doc.testcase_type == "READ"):
			pass
		elif (testcase_doc.testcase_type == "DELETE"):
			pass
		elif (testcase_doc.testcase_type == "WORKFLOW"):
			pass
