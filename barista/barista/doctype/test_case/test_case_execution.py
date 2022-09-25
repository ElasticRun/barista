# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from barista.barista.doctype.test_data.test_data_generator import TestDataGenerator, create_test_run_log, resolve_unique_validation_error, resolve_duplicate_entry_error
from frappe.model.workflow import apply_workflow
import frappe.model.rename_doc as rd
from frappe.utils.jinja import validate_template, render_template
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
import time
import string
import random

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

error_log_title_len = 1000


class TestCaseExecution():
    def run_testcase(self, testcase, test_suite, testcase_srno, total_testcases, suite_srno, total_suites, run_name):
        error_message = ''
        test_result_doc = frappe.get_doc({"doctype":"Test Result"})
        new_record_doc = frappe._dict()
        testdata_doc = frappe._dict()
        testdata_doc_test_record_name = None
        try:
            start_time = time.time()
            function_result = None
            
            # Populate generic test result fields
            
            test_result_doc.test_run_name = run_name
            test_result_doc.test_suite = test_suite
            test_result_doc.action = "Test Case"
            testcase_doc = frappe.get_doc("Test Case", testcase)
            frappe.set_user(testcase_doc.run_as or 'Administrator')
            testcase_doc.testcase_type = testcase_doc.testcase_type.upper()
            test_result_doc.test_case = testcase_doc.name
            test_result_doc.test_data_id = testcase_doc.test_data
            test_result_doc.test_case_status = "Passed"
            test_result_doc.test_case_execution = "Executed"
            # test result fields ended
            print(
                f"\033[0;36;96m>> ({str(suite_srno)}/{str(total_suites)}) {str(testcase)}:{testcase_doc.testcase_type} [{str(testcase_srno)}/{str(total_testcases)}] :")
            testdata_generator = TestDataGenerator()
            # Test Data record doc
            if testcase_doc.test_data:
                testdata_doc = frappe.get_doc(
                    "Test Data", testcase_doc.test_data)
                # cannot use insert scripts in test case data generation as doctype.name will not be recorded
                if (testdata_doc.create_using == 'Sql Script'):
                    test_result_doc.test_case_execution = "Execution Failed"
                    test_result_doc.execution_result = "The test data - " + testdata_doc.name + \
                        " selected is genereted using script for which record name cannot be recorded"
                    test_result_doc.test_case_status = "Failed"

                # check if test case is create and test data already created then recreate the data
                testdata_doc_test_record_name = frappe.db.get_value(
                    'Test Run Log', {'test_run_name': run_name, 'test_data': testcase_doc.test_data}, 'test_record')

                if (testdata_doc_test_record_name and testcase_doc.testcase_type == "CREATE"):
                    testdata_doc_test_record_name = None
                    create_test_run_log(run_name, testcase_doc.test_data, None)
                # get record document
                new_record_doc, error_message = testdata_generator.create_testdata(
                    testcase_doc.test_data, run_name)
                
            if (testcase_doc.testcase_type == "CREATE"):
                try:
                    if new_record_doc:
                        try:
                            new_record_doc.save(True)
                        except frappe.DuplicateEntryError as e:
                            new_record_doc = resolve_duplicate_entry_error(
                                e, testdata_doc, run_name)

                        testdata_doc_test_record_name = new_record_doc.name

                        create_test_run_log(
                            run_name, testcase_doc.test_data, new_record_doc.name)

                        if testdata_doc.create_using == 'Data':
                            testdata_generator.set_record_name_child_table(
                                new_record_doc, testdata_doc, True, run_name)
                        print("\033[0;33;93m    >>> Test Data created")
                    else:
                        frappe.throw(
                            f'Test Data {testcase_doc.test_data} generated None doc. Please check Test Data {testcase_doc.test_data}')
                except Exception as e:
                    frappe.db.rollback()
                    frappe.log_error(frappe.get_traceback(
                    ), ('barista-CREATE-'+testcase_doc.name+'-'+str(e))[:error_log_title_len])
                    error_message += '\n' + str(e)
                    print('\033[0;31;91m   Error occurred ---', str(e))

            elif (testcase_doc.testcase_type == "UPDATE"):
                create_new = False
                try:
                    
                    if testcase_doc.testcase_doctype != testdata_doc.doctype_name:
                        value_from_test_record_doc = frappe.db.get_value(
                            testdata_doc.doctype_name, testdata_doc_test_record_name, testcase_doc.test_data_docfield)

                        all_existing_docs = frappe.get_all(testcase_doc.testcase_doctype, filters={
                            testcase_doc.test_case_docfield: value_from_test_record_doc})
                        if len(all_existing_docs) == 1:
                            existing_doc_name = all_existing_docs[0]['name']
                            new_record_doc = frappe.get_doc(
                                testcase_doc.testcase_doctype, existing_doc_name)
                        else:
                            test_result_doc.test_case_execution = "Execution Failed"
                            test_result_doc.execution_result = f"The Test Case DocType - {testcase_doc.testcase_doctype} with reference field {testcase_doc.test_case_docfield} value {testdata_doc_test_record_name} records found {str(len(all_existing_docs))}"
                            test_result_doc.test_case_status = "Failed"
                            frappe.throw(test_result_doc.execution_result)

                    # create the record if already not created
                    if(new_record_doc and new_record_doc.name == None):
                        try:
                            new_record_doc.save(True)
                        except frappe.UniqueValidationError as e:
                            new_record_doc = resolve_unique_validation_error(
                                e, testdata_doc, run_name)
                        testdata_doc_test_record_name = new_record_doc.name

                        create_test_run_log(
                            run_name, testdata_doc.name, new_record_doc.name)

                    # now take the fields to be updated
                    fields = frappe.get_meta(
                        testcase_doc.testcase_doctype).fields

                    for update_field in testcase_doc.update_fields:
                        field_doc = frappe._dict()
                        update_field_doc = frappe.get_doc(
                            "Testdatafield", update_field.name)

                        for field in fields:
                            if field.fieldname == update_field_doc.docfield_fieldname:
                                field_doc = field
                                break

                        if update_field_doc.docfield_fieldname == "name":
                            new_name = update_field_doc.docfield_value
                            if update_field_doc.docfield_code_value == "Code":
                                new_name = eval(update_field_doc.docfield_code)

                            rd.rename_doc(update_field_doc.doctype_name,
                                          testdata_doc_test_record_name, new_name, force=True)

                            testdata_doc_test_record_name = new_name

                            new_record_doc = frappe.get_doc(
                                update_field_doc.doctype_name, new_name)
                            create_test_run_log(
                                run_name, testdata_doc.name, new_record_doc.name)
                        elif new_record_doc and update_field_doc.docfield_fieldname == "docstatus":
                            new_record_doc.set(update_field_doc.docfield_fieldname, int(
                                update_field_doc.docfield_value))
                        elif new_record_doc:
                            if (field_doc.fieldtype in ["Table", "Table MultiSelect"]):
                                # if it is table then user will have to add multiple rows for multiple records.
                                # each test data field will link to one record.
                                child_testdata_doc = frappe.get_doc(
                                    "Test Data", update_field_doc.linkfield_name)
                                if(child_testdata_doc.doctype_type == "Transaction"):
                                    create_new = True
                                child_doc, error_message = testdata_generator.create_testdata(
                                    update_field_doc.linkfield_name, run_name)

                                child_doc.parentfield = field_doc.fieldname
                                child_doc.parenttype = testcase_doc.testcase_doctype
                                new_record_doc.append(
                                    field_doc.fieldname, child_doc)

                            elif (field_doc.fieldtype in ["Link", "Dynamic Link"] and update_field_doc.docfield_code_value == "Fixed Value"):
                                new_record_doc.set(
                                    field_doc.fieldname, update_field_doc.docfield_value)

                            elif (field_doc.fieldtype in ["Link", "Dynamic Link"]):
                                child_testdata_doc = frappe.get_doc(
                                    'Test Data', update_field_doc.linkfield_name)
                                if (child_testdata_doc.doctype_type == "Transaction"):
                                    create_test_run_log(
                                        run_name, child_testdata_doc.name, None)

                                child_doc, error_message = testdata_generator.create_testdata(
                                    update_field_doc.linkfield_name, run_name)
                                try:
                                    if child_doc:
                                        child_doc.save(True)
                                    else:
                                        frappe.throw(
                                            f"Child Doc is None. Test Data of Child {update_field_doc.linkfield_name}. Test Data of Parent {testdata_doc.name}")
                                except frappe.DuplicateEntryError as e:
                                    child_doc = resolve_duplicate_entry_error(
                                        e, child_testdata_doc, run_name)
                                except frappe.UniqueValidationError as e:
                                    child_doc = resolve_unique_validation_error(
                                        e, child_testdata_doc, run_name)

                                child_testdata_doc_test_record_name = child_doc.name
                                create_test_run_log(
                                    run_name, child_testdata_doc.name, child_doc.name)
                                new_record_doc.set(
                                    field_doc.fieldname, child_doc.get(update_field_doc.linkfield_key or "name"))
                            # for rest of data type.. either it should be code or fixed value
                            elif (update_field_doc.docfield_code_value == "Code"):
                                if update_field_doc.docfield_code and not update_field_doc.linkfield_name:
                                    new_record_doc.set(field_doc.fieldname, eval(
                                        update_field_doc.docfield_code))
                                if not update_field_doc.docfield_code and update_field_doc.linkfield_name:
                                    value = frappe.db.get_value(
                                        'Test Run Log', {'test_run_name': run_name, 'test_data': update_field_doc.linkfield_name}, 'test_record')
                                    new_record_doc.set(
                                        field_doc.fieldname, value)
                            elif new_record_doc:
                                new_record_doc.set(
                                    update_field_doc.docfield_fieldname, update_field_doc.docfield_value)
                    try:
                        if new_record_doc:
                            new_record_doc.save(True)
                            print("\033[0;33;93m    >>> Test Data updated")
                        else:
                            frappe.throw(
                                f"Test Data {testdata_doc.name} generated None doc. Please check Test Data {testcase_doc.test_data}")
                    except frappe.UniqueValidationError as e:
                        new_record_doc = resolve_unique_validation_error(
                            e, testdata_doc, run_name)

                except Exception as e:
                    frappe.db.rollback()
                    frappe.log_error(frappe.get_traceback(
                    ), ('barista-UPDATE-'+testcase_doc.name+'-'+str(e))[:error_log_title_len])
                    error_message += '\n' + str(e)
                    print('\033[0;31;91m   Error occurred ---', str(e))

                testdata_generator.set_record_name_child_table(
                    new_record_doc, testcase_doc, create_new, run_name)
            elif (testcase_doc.testcase_type == "READ"):
                pass
            elif (testcase_doc.testcase_type == "DELETE"):
                try:
                    record_doc = frappe.get_doc(
                        testdata_doc.doctype_name, testdata_doc_test_record_name)
                    record_doc.delete()
                except Exception as e:
                    frappe.db.rollback()
                    frappe.log_error(frappe.get_traceback(
                    ), ('barista-'+testcase_doc.name+'-DELETE-'+str(e))[:error_log_title_len])
                    error_message += '\n' + str(e)
                    print(
                        "\033[0;31;91m    >>> Error in deleting - "+str(e))
            elif (testcase_doc.testcase_type == "WORKFLOW"):
                current_workflow_state = None
                try:
                    start_time = time.time()
                    
                    if(new_record_doc and new_record_doc.name == None):
                        current_workflow_state = new_record_doc.workflow_state
                        try:
                            new_record_doc = new_record_doc.save(True)
                        except frappe.UniqueValidationError as e:
                            new_record_doc = resolve_unique_validation_error(
                                e, testdata_doc, run_name)
                        testdata_doc_test_record_name = new_record_doc.name

                        create_test_run_log(
                            run_name, testdata_doc.name, new_record_doc.name)
                    apply_workflow(new_record_doc, testcase_doc.workflow_state)
                    print("\033[0;32;92m    >>> Workflow Applied")
                except Exception as e:
                    frappe.db.rollback()
                    frappe.log_error(frappe.get_traceback(), (f"""barista-WORKFLOW-{testcase_doc.name}-{str(
						e)}-DocType-[{testdata_doc.doctype_name}]-WorkflowState-[{current_workflow_state}]-Action-[{testcase_doc.workflow_state}]""")[:error_log_title_len])
                    error_message += '\n' + str(e)
                    print(
                        "\033[0;31;91m    >>> Error in applying Workflow - "+str(e))

            elif (testcase_doc.testcase_type == "FUNCTION"):
                kwargs = {}
                context_dict = {}
                resolved_jinja = ' '
                try:
                    for param in testcase_doc.function_parameters:
                        parameter = param.parameter
                        value = None
                        if param.value and (param.value.strip()[0] in ['{', '[']) and ('{{' not in param.value):
                            value = eval(param.value)
                        elif param.type == 'eval':
                            value = eval(param.value)
                        elif param.value and '{{' not in param.value:
                            value = param.value
                        kwargs[parameter] = value

                        if param.test_data:
                            test_record_name = frappe.db.get_value(
                                'Test Run Log', {'test_run_name': run_name, 'test_data': param.test_data}, 'test_record')

                            test_record_doctype = frappe.db.get_value(
                                'Test Data', param.test_data, 'doctype_name')
                            test_record_doc = frappe.get_doc(
                                test_record_doctype, test_record_name)
                            if param.is_object == 1:
                                if param.object_type == 'dict':
                                    kwargs[parameter] = test_record_doc.as_dict()
                                elif param.object_type == 'json':
                                    kwargs[parameter] = test_record_doc.as_json()
                            elif param.field:
                                kwargs[parameter] = test_record_doc.get(param.field)
                            else:
                                try:
                                    if '{{' in param.value:
                                        context_dict = {'doc':test_record_doc.as_dict()}
                                        jinja, context_dict = self.fetch_context(param.value, context_dict, run_name)
                                        resolved_jinja = render_template(jinja, context_dict)
                                        kwargs[parameter] = eval(str(resolved_jinja))
                                except Exception as e:

                                    frappe.log_error(frappe.get_traceback(), ('barista-FUNCTION-'+testcase_doc.name+'-'+str(e))[:error_log_title_len])
                                    print(
                                        "\033[0;31;91m       >>>> Error in Function Parameter\n      ", str(e))

                    print("\033[0;33;93m   >>> Executing Function --",
                          testcase_doc.function_name)
                    if testcase_doc.json_parameter and testcase_doc.json_parameter.strip() != '':
                        
                        try:
                            testcase_doc.json_parameter = testcase_doc.json_parameter.replace('null', 'None').replace('true', 'True').replace('false', 'False')
                            if testcase_doc.testcase_doctype and testcase_doc.test_data:
                                test_record_name = frappe.db.get_value(
                                    'Test Run Log', {'test_run_name': run_name, 'test_data': testcase_doc.test_data}, 'test_record')

                                context = frappe.get_doc(
                                    testcase_doc.testcase_doctype, test_record_name).as_dict()
                                context_dict = {"doc": context}
                            validate_template(testcase_doc.json_parameter)
                            resolved_jinja = render_template(
                                testcase_doc.json_parameter, context_dict)
                            kwargs.update(eval(str(resolved_jinja)))
                        except Exception as e:
                            frappe.db.rollback()
                            frappe.log_error(frappe.get_traceback(), ('barista-FUNCTION-'+testcase_doc.name+'-'+str(e))[:error_log_title_len])
                            print(
                                "\033[0;31;91m       >>>> Error in Json Parameter\n      ", str(e))
                    method = testcase_doc.function_name
                    if method and '.' in method:
                        args = []
                        function_result = frappe.get_attr(
                            method)(*args, **kwargs)
                    else:
                        test_data_record_name = frappe.db.get_value(
                            'Test Run Log', {'test_run_name': run_name, 'test_data': testcase_doc.test_data}, 'test_record')

                        test_record_doc = frappe.get_doc(
                            testcase_doc.testcase_doctype, test_data_record_name)
                        function_result = test_record_doc.run_method(
                            method, **kwargs)
                    print("\033[0;32;92m     >>> Function Executed")
                except Exception as e:
                    frappe.db.rollback()
                    frappe.log_error(frappe.get_traceback(
                    ), ('barista-FUNCTION-'+testcase_doc.name+'-'+str(e))[:error_log_title_len])
                    error_message += '\n' + str(e)
                    print(
                        "\033[0;31;91m       >>>> Execution of function failed\n       Error occurred :", str(e))

            test_result_doc.execution_time = get_execution_time(start_time)

            assertions = frappe.get_list(
                "Assertion", filters={'parent': testcase})

            if len(assertions) == 0:
                test_result_doc.execution_result = 'Assertions are not present in the TestCase. Please add atleast one assertion.'
                test_result_doc.test_case_status = "Failed"
                test_result_doc.save(True)
            frappe.db.commit()
            # Sleep For Time
            if testcase_doc.wait_for:
                time.sleep(testcase_doc.wait_for)

            for assertion in assertions:
                self.process_assertion(
                    assertion, testcase_doc, run_name, error_message, function_result, test_result_doc)

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(
            ), ('barista-Critical Error-'+testcase+'-'+str(e))[:error_log_title_len])
            test_result_doc.test_case_execution = "Execution Failed"
            test_result_doc.execution_result = str(e)
            test_result_doc.test_case_status = "Failed"
        finally:
            print("\033[0;36;96m>> " + "Execution Ended \n\n")
            test_result_doc.save(True)
            frappe.set_user("Administrator")
            

    def process_assertion(self, assertion, testcase_doc, run_name, error_message, function_result, test_result_doc):
        assertion_doc = frappe.get_doc("Assertion", assertion['name'])
        assertion_doc.assertion_type = assertion_doc.assertion_type.upper()

        value_type = 'Fixed Value'
        record_count = 1
        testdata_doc_test_record_name = None
        test_record_doc = None
        validation_doctype = []
        testdata_doc = frappe._dict()

        if assertion_doc.value_type:
            value_type = assertion_doc.value_type

        if assertion_doc.record_count is not None:
            record_count = assertion_doc.record_count

        if not assertion_doc.reference_field:
            assertion_doc.reference_field = 'name'

        print(
            f"\033[0;37;97m       >>>> Applying {assertion_doc.assertion_type} assertion :{str(assertion['name'])}")
        assertion_result = frappe.new_doc("Assertion Result")
        assertion_result.assertion = assertion_doc.name
        assertion_result.assertion_status = "Passed"
        if testcase_doc.test_data:
            testdata_doc = frappe.get_doc(
                'Test Data', testcase_doc.test_data)
            testdata_doc_test_record_name = frappe.db.get_value('Test Run Log', {'test_run_name': run_name, 'test_data': testcase_doc.test_data}, 'test_record')
        if(assertion_doc.assertion_type != "RESPONSE" and assertion_doc.assertion_type != "ERROR"):
            validation_doctype = frappe.get_all(assertion_doc.doctype_name, filters={assertion_doc.reference_field: testdata_doc_test_record_name})
        if (assertion_doc.assertion_type == "FIELD VALUE"):
            if (len(validation_doctype) != 1):
                assertion_result.assertion_status = "Failed"
                assertion_result.assertion_result = "Actual number of record(s) found - " + str(len(validation_doctype)) + \
                    ". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
                    ". Value - " + str(testdata_doc_test_record_name)

                if(error_message):
                    # there was some error as well.
                    assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
                        + error_message

                test_result_doc.test_case_status = "Failed"
                print("\033[0;31;91m       >>>> Assertion failed")

            else:
                validation_doctype_doc = frappe.get_doc(
                    assertion_doc.doctype_name, validation_doctype[0]['name'])
                if not assertion_doc.docfield_name:
                    assertion_doc.docfield_name = 'name'

                result = validation_doctype_doc.get(
                    assertion_doc.docfield_name)
                try:
                    if((str(validation_doctype_doc.get(assertion_doc.docfield_name)) == str(assertion_doc.docfield_value)) and value_type == 'Fixed Value'):
                        # Assertion is successful
                        assertion_result.assertion_result = "Value matched - " + \
                            str(validation_doctype_doc.get(
                                assertion_doc.docfield_name))
                        print(
                            "\033[0;32;92m       >>>> Assertion Passed")
                    elif value_type == 'Code' and eval(assertion_doc.code):
                        assertion_result.assertion_result = "Value matched - " + \
                            str(validation_doctype_doc.get(
                                assertion_doc.docfield_name))
                        print(
                            "\033[0;32;92m       >>>> Assertion Passed")
                    else:
                        # Assertion failed
                        # test case also fails
                        assertion_result.assertion_status = "Failed"
                        assertion_result.assertion_result = "Value Found - " + str(validation_doctype_doc.get(assertion_doc.docfield_name))  \
                            + ". Where as expected value is - " + \
                            str(assertion_doc.docfield_value)

                        if(error_message):
                            # there was some error as well.
                            assertion_result.assertion_result = f"{assertion_result.assertion_result} \n\nError Encountered :{error_message}"

                        test_result_doc.test_case_status = "Failed"
                        print(
                            "\033[0;31;91m       >>>> Assertion Failed")
                except AttributeError as e:
                    assertion_result.assertion_status = "Failed"
                    test_result_doc.test_case_status = "Failed"
                    test_result_doc.test_case_status = "Failed"
                    assertion_result.assertion_result = f"Error Encountered :{str(e)}"

        elif (assertion_doc.assertion_type == "RECORD VALIDATION"):
            filter_field_to_refer = 'name'
            if assertion_doc.docfield_name and assertion_doc.docfield_name.strip() != '':
                filter_field_to_refer = assertion_doc.docfield_name
            if testdata_doc_test_record_name:
                test_record_doc = frappe.get_doc(testdata_doc.doctype_name, testdata_doc_test_record_name)

            if test_record_doc:
                filter_field_value = test_record_doc.get(filter_field_to_refer)
            else:
                filter_field_value = ''
            validation_doctype = frappe.get_all(assertion_doc.doctype_name, filters={
                assertion_doc.reference_field: filter_field_value})
            if (len(validation_doctype) == record_count):
                records = [str(doc['name']) for doc in validation_doctype]
                # Assertion is successful
                assertion_result = frappe.new_doc("Assertion Result")
                assertion_result.assertion = assertion_doc.name
                assertion_result.assertion_status = "Passed"
                assertion_result.assertion_result = f"Record found - {','.join(records)}"
                print("\033[0;32;92m       >>>> Assertion Passed")
            else:
                assertion_result.assertion_status = "Failed"
                assertion_result.assertion_result = "Actual number of record(s) found - " + str(len(validation_doctype)) + \
                    ". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
                    ". Value - " + \
                    (testdata_doc_test_record_name or '')
                test_result_doc.test_case_status = "Failed"
                print("\033[0;31;91m       >>>> Assertion Failed")

                if(error_message):
                    # there was some error as well.
                    assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
                        + error_message

        elif (assertion_doc.assertion_type == "WORKFLOW"):
            if (len(validation_doctype) != 1):
                assertion_result.assertion_status = "Failed"
                assertion_result.assertion_result = f"""Actual number of record(s) found - {str(len(validation_doctype))}. For Doctype - {assertion_doc.doctype_name}. Name - {assertion_doc.reference_field}. Value - {testdata_doc_test_record_name}"""
                test_result_doc.test_case_status = "Failed"
                print("\033[0;31;91m       >>>> Assertion Failed")
                if(error_message):
                    # there was some error as well.
                    assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
                        + error_message
            else:
                validation_doctype_doc = frappe.get_doc(
                    assertion_doc.doctype_name, validation_doctype[0]['name'])
                if (assertion_doc.workflow_state == validation_doctype_doc.workflow_state):
                    assertion_result.assertion_result = "Workflow matched - " + \
                        assertion_doc.workflow_state
                    print("\033[0;32;92m       >>>> Assertion Passed")
                else:
                    assertion_result.assertion_status = "Failed"
                    assertion_result.assertion_result = "Workflow State found - " + str(validation_doctype_doc.workflow_state) \
                        + ". Expected Workflow state is - " + \
                        str(assertion_doc.workflow_state)
                    if(error_message):
                        # there was some error as well.
                        assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
                            + error_message
                    test_result_doc.test_case_status = "Failed"
                    print("\033[0;31;91m       >>>> Assertion Failed")

        elif (assertion_doc.assertion_type == "ERROR"):
            if (error_message):
                if (assertion_doc.error_message in error_message):
                    assertion_result.assertion_result = "Error received as expected - " + error_message
                    print("\033[0;32;92m       >>>> Assertion Passed")
                else:
                    assertion_result.assertion_result = "Error received - " + error_message + \
                        "\n\nExpected error - " + assertion_doc.error_message
                    assertion_result.assertion_status = "Failed"
                    test_result_doc.test_case_status = "Failed"
                    print("\033[0;31;91m       >>>> Assertion Failed")
            else:
                assertion_result.assertion_result = "No Error received however following error was expected - " + \
                    assertion_doc.error_message
                assertion_result.assertion_status = "Failed"
                test_result_doc.test_case_status = "Failed"
                print("\033[0;31;91m       >>>> Assertion Failed")

        elif (assertion_doc.assertion_type == "RESPONSE"):
            if assertion_doc.response_regex and assertion_doc.response_regex.strip() != '':
                response_regex = assertion_doc.response_regex.replace(
                    '": "', '":"').replace('": ', '":')
            else:
                response_regex = ''
            if testcase_doc.testcase_type == "FUNCTION":
                test_result_doc.execution_result = ''
                result = function_result
                if function_result:

                    def to_json_converter(value):
                        if isinstance(value, datetime.datetime):
                            return value.__str__()

                    test_result_doc.execution_result = json.dumps(
                        function_result, default=to_json_converter).replace('": "', '":"').replace('": ', '":')
                if value_type == 'Fixed Value':
                    if response_regex and response_regex != '' and (response_regex in test_result_doc.execution_result):
                        assertion_result.assertion_status = "Passed"
                        assertion_result.assertion_result = response_regex + \
                            " -> is present in the response received from the function"
                        print(
                            "\033[0;32;92m       >>>> Assertion Passed")
                    elif test_result_doc.execution_result != '':
                        assertion_result.assertion_status = "Failed"
                        test_result_doc.test_case_status = "Failed"
                        if response_regex == '':
                            assertion_result.assertion_result = 'Please check value of any key in response'
                        else:
                            assertion_result.assertion_result = response_regex + \
                                "-> is not found in the response received from the function"
                        print(
                            "\033[0;31;91m       >>>> Assertion Failed")
                    elif test_result_doc.execution_result == '' and response_regex == '':
                        assertion_result.assertion_status = "Passed"
                        print(
                            "\033[0;32;92m       >>>> Assertion Passed")
                elif value_type == 'Code':
                    if eval(assertion_doc.code):
                        assertion_result.assertion_status = "Passed"
                        print(
                            "\033[0;32;92m       >>>> Assertion Passed")
                    else:
                        assertion_result.assertion_status = "Failed"
                        test_result_doc.test_case_status = "Failed"
                        assertion_result.assertion_result = 'Written Code condition was False'
                        print(
                            "\033[0;31;91m       >>>> Assertion Failed")

        assertion_result.parentfield = "assertion_results"
        test_result_doc.get("assertion_results").append(
            assertion_result)
        test_result_doc.save(True)

    def fetch_context(self, value, context_dict, run_name):
        """Fetches the Context For all TestData"""
        for data in list(set(re.findall('{{([^.]*)',value))):
            i = 1
            if frappe.db.exists("Test Data", data):
                test_record_name = frappe.db.get_value('Test Run Log', {'test_run_name': run_name, 'test_data': data}, ['test_data_doctype','test_record'])
                if test_record_name:
                    key = f"doc{i}"
                    context_dict[key] = frappe.get_doc(test_record_name[0], test_record_name[1]).as_dict()
                    value = value.replace(data, key)
        
        return (value, context_dict)

def get_execution_time(start_time):
    end_time = round(time.time() - start_time, 4)
    time_uom = 'seconds'
    if(end_time >= 60):
        end_time = round(end_time/60, 4)
        time_uom = 'minutes'

    return str(end_time)+' '+time_uom


