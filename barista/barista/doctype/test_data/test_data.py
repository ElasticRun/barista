# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import ast, json, requests, urllib3, re, math, difflib, base64, operator, copy, traceback, urllib, ssl, binascii, six, html.parser, os
import bs4, sys, pymysql, html2text, warnings, markdown2, csv, calendar, unittest,random, datetime,dateutil



class TestData(Document):
	def validate(self):
		docfields = [docfield.fieldname for docfield in frappe.get_meta(self.doctype_name).fields]
		docfields.append('docstatus')
		docfields.append('name')
		for row in self.docfield_value:
			if row.docfield_fieldname not in docfields:
				frappe.throw(f"Invalid DocField {row.docfield_fieldname} in {self.doctype_name}")
		