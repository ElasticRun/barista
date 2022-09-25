# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import ast
import json
import requests
import urllib3
import re
import math
import difflib
import base64
import operator
import copy
import traceback
import urllib
import ssl
import binascii
import six
import html.parser
import os
import bs4
import sys
import pymysql
import html2text
import warnings
import markdown2
import csv
import calendar
import unittest
import random
import datetime
import dateutil
from frappe.modules.export_file import export_to_files

class TestData(Document):
	def autoname(self):
		bs = ''
		if frappe.conf.get('barista_series'):
			bs = f"{frappe.conf.get('barista_series')}-"
		
		self.naming_series = 'TestData-'
			
		self.naming_series = f"{bs}{self.naming_series}"

	def validate(self):
		docfields = [docfield.fieldname for docfield in frappe.get_meta(
			self.doctype_name).fields]
		docfields.append('docstatus')
		docfields.append('name')
		docfields.append('parent')
		if self.create_using == 'Data':
			for row in self.docfield_value:
				if row.docfield_fieldname not in docfields:
					frappe.throw(
						f"Invalid DocField {row.docfield_fieldname} in {self.doctype_name} of {self.name}")

	def on_update(self):
		if self.is_standard == "Yes" and frappe.local.conf.developer_mode and not frappe.flags.in_migrate:
			export_to_files(record_list=[[self.doctype, self.name]], record_module="barista", create_init=True)