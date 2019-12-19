# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class testdata(Document):
	# def start_testdata(self):
	# 	datanumber = 1
	# 	testdata = frappe.get_list('testdata', order_by="seq")
	# 	for testdatum in testdata:
	# 		testdata_doc = frappe.get_doc('testdata', testdatum.name)
	# 		new_doc = frappe.get_doc(testdata_doc.doctype_name)
	# 		docfields = frappe.get_all('DocField',filters={'parent':testdata_doc.doctype_name})
	# 		for docfield in docfields:
	# 			docfield_doc = frappe.get_doc('DocField',docfield.name)
	# 			#if (docfield.fieldtype == 'Data')
	pass
