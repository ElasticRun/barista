# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import random
import datetime
import ast, json, requests, urllib3, re, math, difflib, base64, operator, copy, traceback, urllib, ssl, binascii, six, html.parser, os
import bs4, sys, pymysql, html2text, warnings, markdown2, csv, calendar, unittest
from frappe.modules.export_file import export_to_files


class TestSuite(Document):
	def on_update(self):
		if self.is_standard == "Yes" and frappe.local.conf.developer_mode and not frappe.flags.in_migrate:
			export_to_files(record_list=[[self.doctype, self.name]], record_module="barista", create_init=True)

