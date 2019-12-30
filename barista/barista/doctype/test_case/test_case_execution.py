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
		testcase_doc = frappe.get_doc("Test Case", testcase)

		#Populate generic test result fields
		test_result_doc = frappe.new_doc("Test Result")
		test_result_doc.test_suite = test_suite
		test_result_doc.action = "Test Case"
		test_result_doc.test_case =testcase_doc.name
		test_result_doc.test_case_status = "Passed"
		#test result fields ended 

		TestDataGeneratorobj = TestDataGenerator()
		#Test Data record doc
		testdata_doc = frappe.get_doc("Test Data", testcase_doc.testdata)

		#cannot use insert scritps in test case data generation as doctype.name will not be recorded
		if (testdata_doc.use_script == 1):
			test_result_doc.test_case_execution = "Execution Failed"
			test_result_doc.execution_result = "The test data - " + testdata_doc.name + " selected is genereted using script for which record name cannot be recorded"						
			test_result_doc.test_case_status = "Failed"

		#get record document
		new_record_doc = TestDataGeneratorobj.create_testdata(testcase_doc.testdata)

		try:
			if (testcase_doc.testcase_type == "CREATE"):
								
				record_created_doc = new_record_doc.save()
				testdata_doc.test_record_name = record_created_doc.test_record_name
				testdata_doc.save()
			
				
			elif (testcase_doc.testcase_type == "UPDATE"):

				
				#create the record if already not created
				if(new_record_doc.name == None):
					new_record_doc = new_record_doc.save()
					testdata_doc.test_record_name = new_record_doc.test_record_name
					testdata_doc.save()

				#now take the fields to be updated 
				update_fields = frappe.get_list("Testdatafield", filters={"parent":testcase_doc.name} )
				for update_field in update_fields:				
					update_field_doc = frappe.get_doc("Testdatafield", update_field['name'])
					field_doc = frappe.get_doc("DocField", filters={'parent':update_field_doc.doctype_name, \
																	'fieldname': update_field_doc.docfield_fieldname } )

					

					if (field_doc.fieldtype == "Table"):
						#if it is table then user will have to add multiple rows for multiple records.
						#each test data field will link to one record.
						child_doc = TestDataGeneratorobj.create_testdata(field_doc.linkfield_name)
						child_doc.parentfield = field_doc.fieldname
						new_record_doc[field_doc.fieldname].append(child_doc)

						#check the link for pretestdata
						#create pretestdata
						#create_pretestdata(field_doc.linkfield_name)

						#link parent to this record						
							
					elif (field_doc.fieldtype == "Link" and update_field_doc.docfield_code_value == "Fixed Value"):
						new_record_doc[field_doc.fieldname] = update_field_doc.docfield_value

					elif (field_doc.fieldtype == "Link"):
						child_doc = TestDataGeneratorobj.create_testdata(field_doc.linkfield_name)
						created_child_doc = child_doc.save()
						new_record_doc[field_doc.fieldname] = created_child_doc.name
					
					#for rest of data type.. either it should be code or fixed value
					elif (update_field_doc.docfield_code_value == "Code"):					
						new_record_doc[field_doc.docfield_fieldname] = eval(update_field_doc.docfield_code)
						
					else:
						new_record_doc[update_field_doc.docfield_fieldname] = update_field_doc.docfield_value
					
					new_record_doc.save()

				

			elif (testcase_doc.testcase_type == "READ"):
				pass
			elif (testcase_doc.testcase_type == "DELETE"):
				pass
			elif (testcase_doc.testcase_type == "WORKFLOW"):
				if(new_record_doc.name == None):
					new_record_doc = new_record_doc.save()
					testdata_doc.test_record_name = new_record_doc.test_record_name
					testdata_doc.save()
				
				apply_workflow(new_record_doc, testcase_doc.workflow_state)
			
			elif (testcase_doc.testcase_type == "FUNCTION"):
				if(new_record_doc.name == None):
					new_record_doc = new_record_doc.save()
					testdata_doc.test_record_name = new_record_doc.test_record_name
					testdata_doc.save()
				
				if ((not testcase_doc.testcase_type) or testcase_doc.testcase_type == None):
					#empty paramter call function diretly.
					pass
				
		
		except Exception as e:
			test_result_doc.test_case_execution = "Execution Failed"
			test_result_doc.execution_result = str(e)		
			test_result_doc.test_case_status = "Failed"


		assertions = frappe.get_list("Assertion", filters={'parent': testcase})

		for assertion in assertions:
				assertion_doc = frappe.get_doc("Assertion", assertion['name'])
				assertion_result = frappe.get_doc("Assertion Result")
				assertion_result.assertion = assertion_doc.name
				assertion_result.assertion_status = "Passed"
				validation_doctype = frappe.get_all(assertion_doc.doctype_name, filters={assertion_doc.reference_field : testdata_doc.test_record_name })
				
				if (assertion_doc.assertion_type == "FIELD VALUE"):
					

					if (len(validation_doctype) != 1):
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + len(validation_doctype) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + testdata_doc.test_record_name
						test_result_doc.test_case_status = "Failed"

					else:
						 						
						validation_doctype_doc = frappe.get_doc(assertion_doc.doctype_name, validation_doctype[0]['name'])
						if(validation_doctype_doc[assertion_doc.docfield_name] == assertion_doc.docfield_value):
							#Assertion is successful						
							assertion_result.assertion_result = "Valued matched - " + validation_doctype_doc[assertion_doc.docfield_name]
						else:
							#Assertion failed
							#test case also fails
							assertion_result.assertion_status = "Failed"
							assertion_result.assertion_result = "Valued Found - " + validation_doctype[assertion_doc.docfield_name]  \
															+ ". Where as expected value is - " +  assertion_doc.docfield_value
							test_result_doc.test_case_status = "Failed"

				elif (assertion_doc.assertion_type == "RECORD VALIDATION"):
					if (len(validation_doctype) == 1):
						#Assertion is successful
						assertion_result = frappe.get_doc("Assertion Result")
						assertion_result.assertion = assertion_doc.name
						assertion_result.assertion_status = "Passed"
						assertion_result.assertion_result = "record found - " + validation_doctype['name']
					else:
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + len(validation_doctype) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + testdata_doc.test_record_name
						test_result_doc.test_case_status = "Failed"



				elif (assertion_doc.assertion_type == "WORKFLOW"):
					if (len(validation_doctype) != 1):
						assertion_result.assertion_status = "Failed"
						assertion_result.assertion_result = "Actual number of record(s) found - " + len(validation_doctype) + \
															". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
																". Value - " + testdata_doc.test_record_name
						test_result_doc.test_case_status = "Failed"
					else:
						validation_doctype_doc = frappe.get_doc(assertion_doc.doctype_name, validation_doctype[0]['name'])
						if (assertion_doc.workflow_state == validation_doctype_doc.workflow_state):
							assertion_result.assertion_result = "Workflow matched - " + assertion_doc.workflow_state


				elif (assertion_doc.assertion_type == "RESPONSE"):
					pass
