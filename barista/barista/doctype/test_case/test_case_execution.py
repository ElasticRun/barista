# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from barista.barista.doctype.test_data.test_data_generator import TestDataGenerator
from frappe.model.workflow import apply_workflow
import frappe.model.rename_doc as rd
import ast, json, requests, urllib3, re, math, difflib, base64, operator, copy, traceback, urllib, ssl, binascii, six, html.parser, os
import bs4, sys, pymysql, html2text, warnings, markdown2, csv, calendar, unittest,random, datetime,dateutil


class TestCaseExecution():
	def run_testcase(self,testcase, test_suite):
		try:
			
			testcase_doc = frappe.get_doc("Test Case", testcase)

			#Populate generic test result fields
			test_result_doc = frappe.new_doc("Test Result")
			test_result_doc.test_suite = test_suite
			test_result_doc.action = "Test Case"
			test_result_doc.test_case =testcase_doc.name
			test_result_doc.test_case_status = "Passed"
			test_result_doc.test_case_execution = "Executed"
			#test result fields ended 

			TestDataGeneratorobj = TestDataGenerator()
			#Test Data record doc
			testdata_doc = frappe.get_doc("Test Data", testcase_doc.test_data)
			
			#print (testdata_doc.as_dict())
			print ("\033[0;36;96m>> Test Case : " + str(testcase_doc.name))

			#cannot use insert scritps in test case data generation as doctype.name will not be recorded
			if (testdata_doc.use_script == 1):
				test_result_doc.test_case_execution = "Execution Failed"
				test_result_doc.execution_result = "The test data - " + testdata_doc.name + " selected is genereted using script for which record name cannot be recorded"
				test_result_doc.test_case_status = "Failed"

			#check if test case is create and test data already created then recreate the data
			
			if (testdata_doc.test_record_name and testcase_doc.testcase_type == "CREATE"):				
				testdata_doc.test_record_name = None
				testdata_doc.save()
			
			#get record document
			new_record_doc = TestDataGeneratorobj.create_testdata(testcase_doc.test_data)
			error_message = None
			if (testcase_doc.testcase_type == "CREATE"):

				#check if it is old test data - 
				new_record_doc.save()
				testdata_doc.test_record_name = new_record_doc.name
				testdata_doc.status = "CREATED"				
				try:
					testdata_doc.save()
				except Exception as e: 
					error_message = str(e)
					print('Error occurred ---',str(e))
				print("\033[0;33;93m    >>> test data created")

			
			elif (testcase_doc.testcase_type == "UPDATE"):
				if testcase_doc.testcase_doctype != testdata_doc.doctype_name:
					value_from_test_record_doc = frappe.db.get_value(testdata_doc.doctype_name,testdata_doc.test_record_name,testcase_doc.test_data_docfield)
					all_existing_docs = frappe.get_all(testcase_doc.testcase_doctype,filters={testcase_doc.test_case_docfield : value_from_test_record_doc})
					if len(all_existing_docs)==1:
						existing_doc_name = all_existing_docs[0]['name']
						new_record_doc = frappe.get_doc(testcase_doc.testcase_doctype,existing_doc_name)
					else:
						test_result_doc.test_case_execution = "Execution Failed"
						test_result_doc.execution_result = "The test case doctype - " + testcase_doc.testcase_doctype + " with reference field "+ testcase_doc.test_case_docfield + " value "+ testdata_doc.test_record_name +" records found "+str(len(all_existing_docs))
						test_result_doc.test_case_status = "Failed"
						return

				#create the record if already not created
				if(new_record_doc.name == None):
					new_record_doc = new_record_doc.save()
					testdata_doc.test_record_name = new_record_doc.name
					testdata_doc.status = "CREATED"
					
					testdata_doc.save()
					
				#now take the fields to be updated 
				update_fields = frappe.get_list("Testdatafield", filters={"parent":testcase_doc.name} )
				for update_field in update_fields:
					
					update_field_doc = frappe.get_doc("Testdatafield", update_field['name'])
					
					if update_field_doc.docfield_fieldname == "name":
						rd.rename_doc(update_field_doc.doctype_name,testdata_doc.test_record_name,update_field_doc.docfield_value,force=True)
					elif update_field_doc.docfield_fieldname == "docstatus":
						new_record_doc.set(update_field_doc.docfield_fieldname, int(update_field_doc.docfield_value))
					else:
						fields = frappe.get_all("DocField", filters={'parent':update_field_doc.doctype_name, 'fieldname': update_field_doc.docfield_fieldname } )
						field_doc = frappe.get_doc("DocField", fields[0].name)

						if (field_doc.fieldtype == "Table"):
							#if it is table then user will have to add multiple rows for multiple records.
							#each test data field will link to one record.
							
							
							child_doc = TestDataGeneratorobj.create_testdata(update_field_doc.linkfield_name)
							#TODO: Fetch child test data doc and update child doc
							child_doc.parentfield = field_doc.fieldname
							child_doc.parenttype=testcase_doc.testcase_doctype
							new_record_doc.append(field_doc.fieldname,child_doc)
							# new_record_doc.get(field_doc.fieldname).append(child_doc)
							#check the link for pretestdata
							#create pretestdata
							#create_pretestdata(field_doc.linkfield_name)

							#link parent to this record						
								
						elif (field_doc.fieldtype == "Link" and update_field_doc.docfield_code_value == "Fixed Value"):
							new_record_doc.set(field_doc.fieldname, update_field_doc.docfield_value)

						elif (field_doc.fieldtype == "Link"):						
							

							child_testdata_doc = frappe.get_doc('Test Data',update_field_doc.linkfield_name)
							if (child_testdata_doc.doctype_type == "Transaction"):
							
								#since transaction remove existing record ref if any
								child_testdata_doc.test_record_name = None
								child_testdata_doc.save()
							
							child_doc = TestDataGeneratorobj.create_testdata(update_field_doc.linkfield_name)
							child_doc.save()

							child_testdata_doc = frappe.get_doc('Test Data', update_field_doc.linkfield_name)
							child_testdata_doc.test_record_name = child_doc.name
							child_testdata_doc.save()


							#TODO: Fetch child test data doc and update child doc
							new_record_doc.set(field_doc.fieldname,child_doc.name)
						
						#for rest of data type.. either it should be code or fixed value
						elif (update_field_doc.docfield_code_value == "Code"):
							new_record_doc.set(field_doc.fieldname, eval(update_field_doc.docfield_code))
							
						else:
							new_record_doc.set(update_field_doc.docfield_fieldname, update_field_doc.docfield_value) 


						try:
							new_record_doc.save()
						except Exception as e: 
							error_message = str(e)
							print('Error occurred ---',str(e))
						print("\033[0;33;93m    >>> Test data updated")
			

			elif (testcase_doc.testcase_type == "READ"):
				pass
			elif (testcase_doc.testcase_type == "DELETE"):
				pass
			elif (testcase_doc.testcase_type == "WORKFLOW"):
				if(new_record_doc.name == None):
					new_record_doc = new_record_doc.save()
					testdata_doc.test_record_name = new_record_doc.test_record_name
					testdata_doc.status = "CREATED"
					testdata_doc.save()
				
				try:
					apply_workflow(new_record_doc, testcase_doc.workflow_state)
				except Exception as e: 
					error_message = str(e)
				print("\033[0;32;92m    >>> workflow applied")

			
			elif (testcase_doc.testcase_type == "FUNCTION"):
				if(new_record_doc.name == None):
					new_record_doc = new_record_doc.save()
					testdata_doc.test_record_name = new_record_doc.test_record_name
					testdata_doc.status = "CREATED"
					testdata_doc.save()
				
				if ((not testcase_doc.testcase_type) or testcase_doc.testcase_type == None):
					#empty paramter call function diretly.
					pass
				# Executes the function  block in test case
				# try:
				# 	print("Function--",testcase_doc.function_name)
				# 	print("Type of--",type(testcase_doc.function_name))
				# 	exec(testcase_doc.function_name)
				# except Exception as e:
				# 	error_message = str(e)
				# print("    >>> function executed")

			assertions = frappe.get_list("Assertion", filters={'parent': testcase})

			
			for assertion in assertions:

				assertion_doc = frappe.get_doc("Assertion", assertion['name'])
				print("\033[0;37;97m       >>>> Applying assertion : " + str(assertion['name'])) 
				assertion_result = frappe.new_doc("Assertion Result")
				assertion_result.assertion = assertion_doc.name
				assertion_result.assertion_status = "Passed"
				if(assertion_doc.assertion_type != "RESPONSE" and assertion_doc.assertion_type != "ERROR"):
					validation_doctype = frappe.get_all(assertion_doc.doctype_name, filters={assertion_doc.reference_field : testdata_doc.test_record_name })
				
				if (assertion_doc.assertion_type == "FIELD VALUE"):					
					if (len(validation_doctype) != 1):
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + str(len(validation_doctype)) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + str(testdata_doc.test_record_name)

						if(error_message):
							#there was some error as well. 
							assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message

						test_result_doc.test_case_status = "Failed"					
						print("\033[0;31;91m       >>>> Assertion failed")
					

					else:
						
						validation_doctype_doc = frappe.get_doc(assertion_doc.doctype_name, validation_doctype[0]['name'])
						if(str(validation_doctype_doc.get(assertion_doc.docfield_name)) == str(assertion_doc.docfield_value)):
							#Assertion is successful						
							assertion_result.assertion_result = "Value matched - " + str(validation_doctype_doc.get(assertion_doc.docfield_name))
							print("\033[0;32;92m       >>>> Assertion Passed")
							
						else:
							#Assertion failed
							#test case also fails
							assertion_result.assertion_status = "Failed"
							assertion_result.assertion_result = "Value Found - " + str(validation_doctype_doc.get(assertion_doc.docfield_name))  \
															+ ". Where as expected value is - " +  str(assertion_doc.docfield_value )

							if(error_message):
								#there was some error as well. 
								assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message
							 
							test_result_doc.test_case_status = "Failed"
							print("\033[0;31;91m       >>>> Assertion Failed")
							

				elif (assertion_doc.assertion_type == "RECORD VALIDATION"):
					if (len(validation_doctype) == 1):
						#Assertion is successful
						assertion_result = frappe.new_doc("Assertion Result")
						assertion_result.assertion = assertion_doc.name
						assertion_result.assertion_status = "Passed"
						assertion_result.assertion_result = "record found - " + validation_doctype[0]['name']
						print("\033[0;32;92m       >>>> Assertion Passed")
					else:
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + str(len(validation_doctype)) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + testdata_doc.test_record_name
						test_result_doc.test_case_status = "Failed"
						print("\033[0;31;91m       >>>> Assertion Failed")

						if(error_message):
								#there was some error as well. 
							assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message



				elif (assertion_doc.assertion_type == "WORKFLOW"):
					if (len(validation_doctype) != 1):
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + str(len(validation_doctype)) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + testdata_doc.test_record_name
						test_result_doc.test_case_status = "Failed"
						print("\033[0;31;91m       >>>> Assertion Failed")
						if(error_message):
							#there was some error as well. 
							assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message
					else:
						validation_doctype_doc = frappe.get_doc(assertion_doc.doctype_name, validation_doctype[0]['name'])
						if (assertion_doc.workflow_state == validation_doctype_doc.workflow_state):
							assertion_result.assertion_result = "Workflow matched - " + assertion_doc.workflow_state
							print("\033[0;32;92m       >>>> Assertion Passed")
						else:
							assertion_result.assertion_status = "Failed"
							assertion_result.assertion_result = "Workflow State found - " + str(validation_doctype_doc.workflow_state) \
																+ ". Expected Workflow state is - " + str(assertion_doc.workflow_state)							
							if(error_message):
								#there was some error as well. 
								assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message
							test_result_doc.test_case_status = "Failed"
							print("\033[0;31;91m       >>>> Assertion Failed")


				elif (assertion_doc.assertion_type == "ERROR"):
					if (error_message):
						if (error_message in assertion_doc.error_message):
							assertion_result.assertion_result = "error received as expected - " + error_message
							print("\033[0;32;92m       >>>> Assertion Passed")
						else:
							assertion_result.assertion_result = "error received - " + error_message + \
																"\n\nExcepted error - " + assertion_doc.error_message
							assertion_result.assertion_status = "Failed"
							test_result_doc.test_case_status = "Failed"
							print("\033[0;31;91m       >>>> Assertion Failed")
					else:
						assertion_result.assertion_result = "No Error received however following error was expected - " + assertion_doc.error_message
						assertion_result.assertion_status = "Failed"
						test_result_doc.test_case_status = "Failed"
						print("\033[0;31;91m       >>>> Assertion Failed") 
															
 					

				elif (assertion_doc.assertion_type == "RESPONSE"):
					pass

				assertion_result.parentfield = "assertion_results"
				test_result_doc.get("assertion_results").append(assertion_result)
				test_result_doc.save()


				
		
		except Exception as e:
			
			test_result_doc.test_case_execution = "Execution Failed"
			test_result_doc.execution_result = str(e)		
			test_result_doc.test_case_status = "Failed"
			test_result_doc.save()
			raise e
		finally:
			print ("\033[0;36;96m>> Test Case : " + str(testcase_doc.name) + " Execution Ended \n\n")	
		
		
