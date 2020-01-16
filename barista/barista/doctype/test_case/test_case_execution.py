# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from barista.barista.doctype.test_data.test_data_generator import TestDataGenerator
from frappe.model.workflow import apply_workflow

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
			print ("&***********############################################################")
			print (testdata_doc.as_dict())
			print ("&***********############################################################")

			#cannot use insert scritps in test case data generation as doctype.name will not be recorded
			if (testdata_doc.use_script == 1):
				test_result_doc.test_case_execution = "Execution Failed"
				test_result_doc.execution_result = "The test data - " + testdata_doc.name + " selected is genereted using script for which record name cannot be recorded"
				test_result_doc.test_case_status = "Failed"

			#check if test case is create and test data already created then recreate the data
			if (testdata_doc.new_record_doc and testcase_doc.testcase_type == "CREATE"):
				testdata_doc.new_record_doc = None
				testdata_doc.save()

			#get record document
			new_record_doc = TestDataGeneratorobj.create_testdata(testcase_doc.test_data)
			error_message = None
			if (testcase_doc.testcase_type == "CREATE"):

				#check if it is old test data - 
				new_record_doc.save()
				testdata_doc.test_record_name = new_record_doc.name
				testdata_doc.status = "CREATED"
				print ("$$$$$$$$$$$$$$ before save test data")
				testdata_doc.save()
				print ("$$$$$$$$$$$$$$ after save test data")
			
			elif (testcase_doc.testcase_type == "UPDATE"):

				#create the record if already not created
				if(new_record_doc.name == None):
					new_record_doc = new_record_doc.save()
					testdata_doc.test_record_name = new_record_doc.name
					testdata_doc.status = "CREATED"
					try:
						testdata_doc.save()
					except Exception as e: 
						error_message = str(e)

				#now take the fields to be updated 
				update_fields = frappe.get_list("Testdatafield", filters={"parent":testcase_doc.name} )
				for update_field in update_fields:
					update_field_doc = frappe.get_doc("Testdatafield", update_field['name'])
					fields = frappe.get_all("DocField", filters={'parent':update_field_doc.doctype_name, \
																	'fieldname': update_field_doc.docfield_fieldname } )
					field_doc = frappe.get_doc("DocField", fields[0].name)

					if (field_doc.fieldtype == "Table"):
						#if it is table then user will have to add multiple rows for multiple records.
						#each test data field will link to one record.
						child_doc = TestDataGeneratorobj.create_testdata(update_field_doc.linkfield_name)
						#TODO: Fetch child test data doc and update child doc
						child_doc.parentfield = field_doc.fieldname
						new_record_doc.get(field_doc.fieldname).append(child_doc)

						#check the link for pretestdata
						#create pretestdata
						#create_pretestdata(field_doc.linkfield_name)

						#link parent to this record						
							
					elif (field_doc.fieldtype == "Link" and update_field_doc.docfield_code_value == "Fixed Value"):
						new_record_doc.set(field_doc.fieldname, update_field_doc.docfield_value)

					elif (field_doc.fieldtype == "Link"):
						child_doc = TestDataGeneratorobj.create_testdata(field_doc.linkfield_name)
						created_child_doc = child_doc.save()
						#TODO: Fetch child test data doc and update child doc
						new_record_doc.set(field_doc.fieldname,created_child_doc.name)
					
					#for rest of data type.. either it should be code or fixed value
					elif (update_field_doc.docfield_code_value == "Code"):
						new_record_doc.set(field_doc.docfield_fieldname, eval(update_field_doc.docfield_code))
						
					else:
						new_record_doc.set(update_field_doc.docfield_fieldname, update_field_doc.docfield_value) 
					
					print ("$$$$$$$$$$ - ")
					try:
						new_record_doc.save()
					except Exception as e: 
						error_message = str(e)

				

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

			
			elif (testcase_doc.testcase_type == "FUNCTION"):
				if(new_record_doc.name == None):
					new_record_doc = new_record_doc.save()
					testdata_doc.test_record_name = new_record_doc.test_record_name
					testdata_doc.status = "CREATED"
					testdata_doc.save()
				
				if ((not testcase_doc.testcase_type) or testcase_doc.testcase_type == None):
					#empty paramter call function diretly.
					pass



			assertions = frappe.get_list("Assertion", filters={'parent': testcase})

			for assertion in assertions:

				assertion_doc = frappe.get_doc("Assertion", assertion['name'])
				assertion_result = frappe.new_doc("Assertion Result")
				assertion_result.assertion = assertion_doc.name
				assertion_result.assertion_status = "Passed"

				if(assertion_doc.assertion_type != "RESPONSE" and assertion_doc.assertion_type != "ERROR"):
					validation_doctype = frappe.get_all(assertion_doc.doctype_name, filters={assertion_doc.reference_field : testdata_doc.test_record_name })
				
				if (assertion_doc.assertion_type == "FIELD VALUE"):					
					if (len(validation_doctype) != 1):
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + len(validation_doctype) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + testdata_doc.test_record_name

						if(error_message):
							#there was some error as well. 
							assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message

						test_result_doc.test_case_status = "Failed"					
					

					else:
						
						validation_doctype_doc = frappe.get_doc(assertion_doc.doctype_name, validation_doctype[0]['name'])
						if(validation_doctype_doc.get(assertion_doc.docfield_name) == assertion_doc.docfield_value):
							#Assertion is successful						
							assertion_result.assertion_result = "Valued matched - " + validation_doctype_doc.get(assertion_doc.docfield_name)
						else:
							#Assertion failed
							#test case also fails
							assertion_result.assertion_status = "Failed"
							assertion_result.assertion_result = "Valued Found - " + str(validation_doctype_doc.get(assertion_doc.docfield_name))  \
															+ ". Where as expected value is - " +  str(assertion_doc.docfield_value )

							if(error_message):
								#there was some error as well. 
								assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message
							 
							test_result_doc.test_case_status = "Failed"

				elif (assertion_doc.assertion_type == "RECORD VALIDATION"):
					if (len(validation_doctype) == 1):
						#Assertion is successful
						assertion_result = frappe.new_doc("Assertion Result")
						assertion_result.assertion = assertion_doc.name
						assertion_result.assertion_status = "Passed"
						assertion_result.assertion_result = "record found - " + validation_doctype['name']
					else:
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + len(validation_doctype) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + testdata_doc.test_record_name
						test_result_doc.test_case_status = "Failed"

						if(error_message):
								#there was some error as well. 
							assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message



				elif (assertion_doc.assertion_type == "WORKFLOW"):
					if (len(validation_doctype) != 1):
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + len(validation_doctype) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + testdata_doc.test_record_name
						test_result_doc.test_case_status = "Failed"
						if(error_message):
							#there was some error as well. 
							assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message
					else:
						validation_doctype_doc = frappe.get_doc(assertion_doc.doctype_name, validation_doctype[0]['name'])
						if (assertion_doc.workflow_state == validation_doctype_doc.workflow_state):
							assertion_result.assertion_result = "Workflow matched - " + assertion_doc.workflow_state
						else:
							assertion_result.assertion_status = "Failed"
							assertion_result.assertion_result = "Workflow State found - " + str(validation_doctype_doc.workflow_state) \
																+ ". Expected Workflow state is - " + str(assertion_doc.workflow_state)							
							if(error_message):
								#there was some error as well. 
								assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
															+ error_message
							test_result_doc.test_case_status = "Failed"


				elif (assertion_doc.assertion_type == "ERROR"):
					if (error_message):
						if (assertion_doc.error_message == error_message):
							assertion_result.assertion_result = "error received as expected - " + error_message
						else:
							assertion_result.assertion_result = "error received - " + error_message + \
																"\n\nExcepted error - " + assertion_doc.error_message
							assertion_result.assertion_status = "Failed"
							test_result_doc.test_case_status = "Failed"
					else:
						assertion_result.assertion_result = "No Error received however following error was expected - " + assertion_doc.error_message
						assertion_result.assertion_status = "Failed"
						test_result_doc.test_case_status = "Failed"
															
 					

				elif (assertion_doc.assertion_type == "RESPONSE"):
					pass

				assertion_result.parentfield = "assertion_results"
				test_result_doc.get("assertion_results").append(assertion_result)
				test_result_doc.save()
				print ("******************** ENDED  TEST RESULT SAVED******************")

				
		
		except Exception as e:
			
			test_result_doc.test_case_execution = "Execution Failed"
			test_result_doc.execution_result = str(e)		
			test_result_doc.test_case_status = "Failed"
			test_result_doc.save()
			raise e

			

		
		