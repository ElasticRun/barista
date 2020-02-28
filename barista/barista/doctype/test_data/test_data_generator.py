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

		#if (testdata_doc):
		#first check if use script is true
		if (testdata_doc.use_script == 1):
		#if Yes run the script
			#insert_stmt = frappe.db.sql( testdata_doc.insert_script )
			# try:
			frappe.db.sql( testdata_doc.insert_script )
			frappe.db.commit()
			#exec(insert_stmt)
			# except expression as identifier:
			# 	pass
		else:

			if (testdata_doc.test_record_name):
				#this means test data already created.... 
				#send the created doc
				created_doc_earlier = frappe.get_doc( testdata_doc.doctype_name , testdata_doc.test_record_name)
				return created_doc_earlier

			#start creating the insert statement
			new_doc  = frappe.get_doc({"doctype": testdata_doc.doctype_name})
			# fields = frappe.get_list('DocField', filters={'parent': testdata_doc.doctype_name })
			fields=frappe.get_meta(testdata_doc.doctype_name).fields
			declared_fields = frappe.get_list('Testdatafield', filters={'parent': testdata_doc.name})
			#for each field
			for field in fields:
				#check if the field values are in provided.. use it 
				# field_doc = frappe.get_doc("DocField", field.name)
				field_doc=field
				flag_field = False
				
				for declared_field in declared_fields:
					declared_field_doc = frappe.get_doc('Testdatafield', declared_field['name'])

					if (declared_field_doc.docfield_fieldname == "docstatus"):
						if (declared_field_doc.docfield_value is None):
							declared_field_doc.docfield_value =0
						new_doc.set(declared_field_doc.docfield_fieldname, int(declared_field_doc.docfield_value))
					elif(declared_field_doc.docfield_fieldname == field_doc.fieldname):
						flag_field = True
						if (declared_field_doc.is_default):
							#ignore
							pass 

						elif (field_doc.fieldtype == "Table"):
							#if it is table then user will have to add multiple rows for multiple records.

							
							#each test data field will link to one record. create a new record
							child_doc = self.create_testdata(declared_field_doc.linkfield_name)
							#child_doc.save()
							
							child_testdata_doc = frappe.get_doc('Test Data', declared_field_doc.linkfield_name)
							child_testdata_doc.test_record_name = child_doc.name
							child_testdata_doc.save()

							child_doc.parentfield = field_doc.fieldname
							new_doc.get(field_doc.fieldname).append(child_doc)
							###new_doc[field_doc.fieldname].append(child_doc)
							
						#link parent to this record											
						elif ("Link" in field_doc.fieldtype and declared_field_doc.docfield_code_value == "Fixed Value"):
							new_doc.set(field_doc.fieldname,declared_field_doc.docfield_value)
						elif ("Link" in field_doc.fieldtype):

							child_testdata_doc = frappe.get_doc('Test Data', declared_field_doc.linkfield_name)
							if (child_testdata_doc.doctype_type == "Transaction"):
								#since transaction remove existing record ref if any
								child_testdata_doc.test_record_name = None
								child_testdata_doc.save()

							child_doc = self.create_testdata(declared_field_doc.linkfield_name)
							child_doc.save()

							child_testdata_doc = frappe.get_doc('Test Data', declared_field_doc.linkfield_name)							
							child_testdata_doc.test_record_name = child_doc.name
							child_testdata_doc.save()

							#new_doc.set(field_doc.fieldname,created_child_doc)
							new_doc.set(field_doc.fieldname, child_doc.name)
							###new_doc[field_doc.fieldname] = created_child_doc.name

						elif (declared_field_doc.docfield_code_value == "Code"):
							# try:
							new_doc.set(declared_field_doc.docfield_fieldname, eval( str(declared_field_doc.docfield_code) ) )
							###new_doc[declared_field_doc.docfield_fieldname] = eval(declared_field_doc.docfield_code)
							# except expression as identifier:
							# 	pass
						else:
							if field_doc.fieldtype in ['Currency','Float','Percent']:
								new_doc.set(declared_field_doc.docfield_fieldname, float(declared_field_doc.docfield_value))
							elif field_doc.fieldtype=='Int':
								new_doc.set(declared_field_doc.docfield_fieldname, int(declared_field_doc.docfield_value))
							else:
								new_doc.set(declared_field_doc.docfield_fieldname, str(declared_field_doc.docfield_value))
							###new_doc[declared_field_doc.docfield_fieldname] = declared_field_doc.docfield_value
			
			if(flag_field == False and not field_doc.fetch_from):
				#no declared field necessary for the test case. Create random field.
				value = None
				if (field_doc.fieldtype == "Data"):
					#its a string of 140							
					value = (field_doc.label.split()[0]	+ str(random.randrange(0,20000,1)))[0:139]					

					###new_doc[declared_field_doc.docfield_fieldname] = (field_doc.label.split()[0]	+ random.randrange(0,20000,1))[0:139]
				elif (field_doc.fieldtype == "Check"):
					#its a check
					value = random.choice([0,1])					
					###new_doc[declared_field_doc.docfield_fieldname] = random.choice([0,1])
				elif(field_doc.fieldtype == "Currency"):
					value = round(random.uniform(500.12, 22000.34),2)					
					###new_doc[declared_field_doc.docfield_fieldname] = round(random.uniform(500.12, 22000.34),2)
				elif(field_doc.fieldtype == "Date"):
					value = datetime.date.today() + datetime.timedelta(days=(random.randrange(0,15,1)))					
					###new_doc[declared_field_doc.docfield_fieldname] = datetime.date.today() + datetime.timedelta(days=(random.randrange(0,15,1)))
				elif(field_doc.fieldtype == "Datetime"):
					value = datetime.datetime.now() + datetime.timedelta(minutes=(random.randrange(0,200,2)))					
					###new_doc[declared_field_doc.docfield_fieldname] = datetime.datetime.now() + datetime.timedelta(minutes=(random.randrange(0,20000,2)))
				elif(field_doc.fieldtype == "Float"):
					value = round(random.uniform(0, 22000.34),2)					
					###new_doc[declared_field_doc.docfield_fieldname] = round(random.uniform(0, 22000.34),2)
				elif(field_doc.fieldtype == "Int"):
					value = random.randrange(0,200,1)
					###new_doc[declared_field_doc.docfield_fieldname] = random.randrange(0,200,1)
				elif(field_doc.fieldtype == "Long Text" or field_doc.fieldtype == "Small Text" or field_doc.fieldtype == "Text"):
					value = (field_doc.label + str(random.randrange(0,20000,1)))
					###new_doc[declared_field_doc.docfield_fieldname] = (field_doc.label + random.randrange(0,20000,1))
				elif(field_doc.fieldtype == "Password"):
					value = "Frappe@12345"
					###new_doc[declared_field_doc.docfield_fieldname] = "Frappe@12345"
				elif (field_doc.fieldtype == "Percent"):
					value = round(random.uniform(0, 100),2)
					###new_doc[declared_field_doc.docfield_fieldname] = round(random.uniform(0, 100),2)
				elif ("Link" in field_doc.fieldtype or field_doc.fieldtype == "Table" ):
					#it looks like table or link field is not declared by user... test data generation failed..
					pass					

				elif("Attach" in field_doc.fieldtype):
					value = "assets/barista/sample-file.html"	

				# if (value != None):
				# 	new_doc.set(declared_field_doc.docfield_fieldname, value) # commented by us
					
			#insert		
			return new_doc

	def create_pretest_data(self,suite):
		#select all the test data for a suite... 		
		all_testdata = frappe.db.sql_list("""select distinct td.name from `tabTest Data` td join `tabTestdata Item` tdi on tdi.test_data=td.name where tdi.parent=%(parent)s order by td.seq""",{'parent':suite})

		for testdata in all_testdata:
			
			testdata_doc = frappe.get_doc("Test Data", testdata)
			if (testdata_doc.use_script == 1):
				self.create_testdata(testdata)
			else:
				new_doc = self.create_testdata(testdata)
				new_doc.save()
				created_doc = new_doc
				testdata_doc = frappe.get_doc('Test Data', testdata)
				testdata_doc.test_record_name = created_doc.name
				testdata_doc.status = 'CREATED'
				testdata_doc.save()

				set_record_name_in_child_table_test_record(created_doc,testdata_doc)
		
		frappe.db.commit()

				
# barista.barista.doctype.test_data.test_data_generator.set_record_name_in_child_table_test_record
def set_record_name_in_child_table_test_record(created_doc,testdata_doc):
	new_record_fields = frappe.db.sql("select * from `tabDocField` where parent = '" + created_doc.doctype + "'and fieldtype = 'Table'", as_dict= True)
	for new_record_field in new_record_fields:
		child_records=created_doc.get(new_record_field.fieldname)
	
		test_data_field_values = frappe.db.sql('select * from `tabTestdatafield` where docfield_fieldname = "' + new_record_field.fieldname + '" and parent = "' + testdata_doc.name + '" order by idx', as_dict=True)

		child_record_index=0
		for test_data_field_value in test_data_field_values:
			if (test_data_field_value.linkfield_name is not None):
				child_test_data_doc = frappe.get_doc('Test Data', test_data_field_value.linkfield_name)
				if(child_test_data_doc.status != "CREATED"):
					#now we got the test data field row.. fetch linked test data 
					child_test_data_doc.status = 'CREATED'
					child_test_data_doc.test_record_name = child_records[child_record_index].name
					child_test_data_doc.save()
			child_record_index+=1