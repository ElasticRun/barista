# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class TestCase(Document):
    def autoname(self):
        bs = ''
        if frappe.conf.get('barista_series'):
            bs = f"{frappe.conf.get('barista_series')}-"
        
        if self.naming_series:
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
