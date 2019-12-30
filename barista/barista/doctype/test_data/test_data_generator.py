# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import ast, json, requests, urllib3, re, math, difflib, base64, operator, copy, traceback, urllib, ssl, binascii, six, html.parser, os
import bs4, sys, pymysql, html2text, warnings, markdown2, csv, calendar, unittest,random, datetime,dateutil


class TestDataGenerator():
	def create_testdata(self,testdata):
		testdata_doc = frappe.get_doc('Test Data', testdata )

		if (testdata_doc):
		#first check if use script is true
		if (testdata_doc.use_script == 1):				
		#if Yes run the script
			#insert_stmt = frappe.db.sql( testdata_doc.insert_script )
			# try:
			frappe.db.sql( testdata_doc.insert_script )
			frappe.db.commit
			#exec(insert_stmt)
			# except expression as identifier:
			# 	pass
		else:
			#start creating the insert statement
			new_doc = frappe.get_doc({"doctype": testdata_doc.doctype_name})
			fields = frappe.get_list('DocField', filters={'parent': testdata_doc.doctype_name })
			declared_fields = frappe.get_list('Testdatafield', filters={'parent': testdata_doc.name})
			#for each field
			for field in fields:					
				#check if the feild values are in provided.. use it 
				field_doc = frappe.get_doc("DocField", field.name)
				flag_field = False
				for declared_field in declared_fields:
					declared_field_doc = frappe.get_doc('Testdatafield', declared_field['name'])
					if (declared_field_doc.docfield_fieldname == field_doc.fieldname):
						flag_field = True
						if (field_doc.fieldtype == "Table"):
							#if it is table then user will have to add multiple rows for multiple records.
							#each test data field will link to one record.
							child_doc = self.create_testdata(field_doc.linkfield_name)
							child_doc.parentfield = field_doc.fieldname
							new_doc[field_doc.fieldname].append(child_doc)

							#link parent to this record											
						elif (if "Link" in field_doc.fieldtype and declared_field_doc.docfield_code_value == "Fixed Value"):
							new_doc[field_doc.fieldname] = declared_field_doc.docfield_value
						elif ("Link" in field_doc.fieldtype):
							child_doc = self.create_testdata(field_doc.linkfield_name)
							created_child_doc = child_doc.save()
							new_doc[field_doc.fieldname] = created_child_doc.name

						elif (declared_field_doc.docfield_code_value == "Code"):
							# try:
							new_doc[declared_field_doc.docfield_fieldname] = eval(declared_field_doc.docfield_code)
							# except expression as identifier:
							# 	pass
						else:
							new_doc[declared_field_doc.docfield_fieldname] = declared_field_doc.docfield_value
				
				if(flag_field == False):
					#no declared field necessary for the test case. Create random field.
					if (field_doc.fieldtype == "Data"):
						#its a string of 140							
						new_doc[declared_field_doc.docfield_fieldname] = (field_doc.label.split()[0]	+ random.randrange(0,20000,1))[0:139]
					elif (field_doc.fieldtype == "Check"):
						#its a check
						new_doc[declared_field_doc.docfield_fieldname] = random.choice([0,1])
					elif(field_doc.fieldtype == "Currency"):
						new_doc[declared_field_doc.docfield_fieldname] = round(random.uniform(500.12, 22000.34),2)
					elif(field_doc.fieldtype == "Date"):
						new_doc[declared_field_doc.docfield_fieldname] = datetime.date.today() + datetime.timedelta(days=(random.randrange(0,15,1)))
					elif(field_doc.fieldtype == "Datetime"):
						new_doc[declared_field_doc.docfield_fieldname] = datetime.datetime.now() + datetime.timedelta(minutes=(random.randrange(0,200,2)))
					elif(field_doc.fieldtype == "Float"):
						new_doc[declared_field_doc.docfield_fieldname] = round(random.uniform(0, 22000.34),2)
					elif(field_doc.fieldtype == "Int"):
						new_doc[declared_field_doc.docfield_fieldname] = random.randrange(0,200,1)
					elif(field_doc.fieldtype == "Long Text" or field_doc.fieldtype == "Small Text" or field_doc.fieldtype = "Text"):
						new_doc[declared_field_doc.docfield_fieldname] = (field_doc.label + random.randrange(0,20000,1))
					elif(field_doc.fieldtype == "Password"):
						new_doc[declared_field_doc.docfield_fieldname] = "Frappe@12345"
					elif (field_doc.fieldtype == "Percent"):
						new_doc[declared_field_doc.docfield_fieldname] = round(random.uniform(0, 100),2)
					
						
				#else create random data. 
 
			#once all fields value are assigned
			#insert
		return new_doc

	def create_pretest_data(self):
		all_testdata = frappe.get_list('Test Data', order_by='seq')
		for testdata in all_testdata:
			new_doc = self.create_testdata(testdata['name'])
			created_doc = new_doc.save()
			testdata_doc = frappe.get_doc('Test Data', testdata['name'])
			testdata_doc.test_record_name = created_doc.name
			testdata_doc.save()

	





