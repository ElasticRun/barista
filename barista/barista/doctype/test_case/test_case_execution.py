# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from barista.barista.doctype.test_data.test_data_generator import TestDataGenerator
from frappe.model.workflow import apply_workflow
import frappe.model.rename_doc as rd
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
from barista.barista.doctype.test_data.test_data_generator import set_record_name_in_child_table_test_record

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

error_log_title_len = 1000


class TestCaseExecution():
    def run_testcase(self, testcase, test_suite, testcase_srno, total_testcases,suite_srno,total_suites):
        try:
            start_time = None
            function_result = None
            testcase_doc = frappe.get_doc("Test Case", testcase)
            print("\033[0;36;96m>> " + str(testcase_doc.name) + ' ('+str(suite_srno)+'/'+str(total_suites)+')'+
                  ' ['+str(testcase_srno)+'/'+str(total_testcases)+']'+':')
            # Populate generic test result fields
            test_result_doc = frappe.new_doc("Test Result")
            test_result_doc.test_suite = test_suite
            test_result_doc.action = "Test Case"
            test_result_doc.test_case = testcase_doc.name
            test_result_doc.test_data_id = testcase_doc.test_data
            test_result_doc.test_case_status = "Passed"
            test_result_doc.test_case_execution = "Executed"
            # test result fields ended

            TestDataGeneratorobj = TestDataGenerator()
            # Test Data record doc
            if testcase_doc.test_data:
                # print("testcase_doc.test_data",testcase_doc.test_data)
                testdata_doc = frappe.get_doc(
                    "Test Data", testcase_doc.test_data)
                # print("tesdata_doc--",testdata_doc)
                # cannot use insert scripts in test case data generation as doctype.name will not be recorded
                if (testdata_doc.use_script == 1):
                    test_result_doc.test_case_execution = "Execution Failed"
                    test_result_doc.execution_result = "The test data - " + testdata_doc.name + \
                        " selected is genereted using script for which record name cannot be recorded"
                    test_result_doc.test_case_status = "Failed"

                # check if test case is create and test data already created then recreate the data

                if (testdata_doc.test_record_name and testcase_doc.testcase_type == "CREATE"):
                    testdata_doc.test_record_name = None
                    testdata_doc.save()

                # get record document
                new_record_doc = TestDataGeneratorobj.create_testdata(
                    testcase_doc.test_data)
                error_message = None
            if (testcase_doc.testcase_type == "CREATE"):
                start_time = time.time()
                try:
                    new_record_doc.save()

                    testdata_doc.test_record_name = new_record_doc.name
                    testdata_doc.status = "CREATED"
                    testdata_doc.save()
                    set_record_name_in_child_table_test_record(
                        new_record_doc, testdata_doc, True)
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(
                    ), ('barista-'+testcase_doc.name+'-CREATE-'+str(e))[:error_log_title_len])
                    error_message = str(e)
                    print('\033[0;31;91m   Error occurred ---', str(e))
                print("\033[0;33;93m    >>> Test Data created")

            elif (testcase_doc.testcase_type == "UPDATE"):
                start_time = time.time()
                if testcase_doc.testcase_doctype != testdata_doc.doctype_name:
                    # testdata_doc = frappe.get_doc("Test Data", testcase_doc.test_data)
                    value_from_test_record_doc = frappe.db.get_value(
                        testdata_doc.doctype_name, testdata_doc.test_record_name, testcase_doc.test_data_docfield)
                    all_existing_docs = frappe.get_all(testcase_doc.testcase_doctype, filters={
                                                       testcase_doc.test_case_docfield: value_from_test_record_doc})
                    if len(all_existing_docs) == 1:
                        existing_doc_name = all_existing_docs[0]['name']
                        new_record_doc = frappe.get_doc(
                            testcase_doc.testcase_doctype, existing_doc_name)
                    else:
                        test_result_doc.test_case_execution = "Execution Failed"
                        test_result_doc.execution_result = "The test case doctype - " + testcase_doc.testcase_doctype + " with reference field " + \
                            testcase_doc.test_case_docfield + " value " + testdata_doc.test_record_name + \
                            " records found "+str(len(all_existing_docs))
                        test_result_doc.test_case_status = "Failed"
                        return

                # create the record if already not created
                if(new_record_doc.name == None):
                    new_record_doc = new_record_doc.save()
                    testdata_doc.test_record_name = new_record_doc.name
                    testdata_doc.status = "CREATED"

                    testdata_doc.save()

                # now take the fields to be updated
                update_fields = frappe.get_list("Testdatafield", filters={
                                                "parent": testcase_doc.name})
                fields = frappe.get_meta(testcase_doc.testcase_doctype).fields
                create_new = False
                for update_field in update_fields:

                    update_field_doc = frappe.get_doc(
                        "Testdatafield", update_field['name'])

                    for field in fields:
                        if field.fieldname == update_field_doc.docfield_fieldname:
                            field_doc = field
                            break

                    if update_field_doc.docfield_fieldname == "name":
                        new_name = update_field_doc.docfield_value
                        if update_field_doc.docfield_code_value == "Code":
                            new_name = eval(update_field_doc.docfield_code)

                        rd.rename_doc(update_field_doc.doctype_name,
                                      testdata_doc.test_record_name, new_name, force=True)
                        # setting the new updated name in the Test Data record name
                        testdata_doc.test_record_name = new_name
                        # frappe.db.commit()
                        new_record_doc = frappe.get_doc(
                            update_field_doc.doctype_name, new_name)

                    elif update_field_doc.docfield_fieldname == "docstatus":
                        new_record_doc.set(update_field_doc.docfield_fieldname, int(
                            update_field_doc.docfield_value))
                    else:
                        # fields = frappe.get_all("DocField", filters={'parent':update_field_doc.doctype_name, 'fieldname': update_field_doc.docfield_fieldname } )
                        # field_doc = frappe.get_doc("DocField", fields[0].name)

                        if (field_doc.fieldtype == "Table"):
                            # if it is table then user will have to add multiple rows for multiple records.
                            # each test data field will link to one record.
                            child_testdata_doc = frappe.get_doc(
                                "Test Data", update_field_doc.linkfield_name)
                            if(child_testdata_doc.doctype_type == "Transaction"):
                                create_new = True
                            child_doc = TestDataGeneratorobj.create_testdata(
                                update_field_doc.linkfield_name)
                            # TODO: Fetch child test data doc and update child doc
                            child_doc.parentfield = field_doc.fieldname
                            child_doc.parenttype = testcase_doc.testcase_doctype
                            new_record_doc.append(
                                field_doc.fieldname, child_doc)
                            # new_record_doc.get(field_doc.fieldname).append(child_doc)
                            # check the link for pretestdata
                            # create pretestdata
                            # create_pretestdata(field_doc.linkfield_name)

                            # link parent to this record

                        elif (field_doc.fieldtype in ["Link", "Dynamic Link"] and update_field_doc.docfield_code_value == "Fixed Value"):
                            new_record_doc.set(
                                field_doc.fieldname, update_field_doc.docfield_value)

                        elif (field_doc.fieldtype in ["Link", "Dynamic Link"]):

                            child_testdata_doc = frappe.get_doc(
                                'Test Data', update_field_doc.linkfield_name)
                            if (child_testdata_doc.doctype_type == "Transaction"):

                                # since transaction remove existing record ref if any
                                child_testdata_doc.test_record_name = None
                                child_testdata_doc.save()

                            child_doc = TestDataGeneratorobj.create_testdata(
                                update_field_doc.linkfield_name)
                            child_doc.save()
                            child_testdata_doc = frappe.get_doc(
                                'Test Data', update_field_doc.linkfield_name)
                            child_testdata_doc.test_record_name = child_doc.name
                            child_testdata_doc.save()

                            # TODO: Fetch child test data doc and update child doc
                            new_record_doc.set(
                                field_doc.fieldname, child_doc.name)

                        # for rest of data type.. either it should be code or fixed value
                        elif (update_field_doc.docfield_code_value == "Code"):
                            new_record_doc.set(field_doc.fieldname, eval(
                                update_field_doc.docfield_code))

                        else:
                            new_record_doc.set(
                                update_field_doc.docfield_fieldname, update_field_doc.docfield_value)

                try:
                    new_record_doc.save()
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(
                    ), ('barista-'+testcase_doc.name+'-UPDATE-'+str(e))[:error_log_title_len])
                    error_message = str(e)
                    print('\033[0;31;91m   Error occurred ---', str(e))
                print("\033[0;33;93m    >>> Test Data updated")

                set_record_name_in_child_table_test_record(
                    new_record_doc, testcase_doc, create_new)
            elif (testcase_doc.testcase_type == "READ"):
                start_time = time.time()
                pass
            elif (testcase_doc.testcase_type == "DELETE"):
                start_time = time.time()
                pass
            elif (testcase_doc.testcase_type == "WORKFLOW"):
                start_time = time.time()
                if(new_record_doc.name == None):
                    new_record_doc = new_record_doc.save()
                    testdata_doc.test_record_name = new_record_doc.test_record_name
                    testdata_doc.status = "CREATED"
                    testdata_doc.save()

                try:
                    apply_workflow(new_record_doc, testcase_doc.workflow_state)
                    print("\033[0;32;92m    >>> Workflow Applied")
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(), ('barista-'+testcase_doc.name+'-WORKFLOW-'+str(
                        e)+'-'+new_record_doc.doctype+'-'+new_record_doc.workflow_state+'-'+testcase_doc.workflow_state)[:error_log_title_len])
                    error_message = str(e)
                    print(
                        "\033[0;31;91m    >>> Error in applying Workflow - "+str(e))

            elif (testcase_doc.testcase_type == "FUNCTION"):
                start_time = time.time()
                kwargs = {}
                try:
                    for param in testcase_doc.function_parameters:
                        parameter = param.parameter
                        test_record_name = frappe.db.get_value(
                            'Test Data', param.test_data, 'test_record_name')
                        test_record_doctype = frappe.db.get_value(
                            'Test Data', param.test_data, 'doctype_name')
                        test_record_doc = frappe.get_doc(
                            test_record_doctype, test_record_name)
                        if param.is_object == 1:
                            kwargs[parameter] = test_record_doc.as_dict()
                        else:
                            kwargs[parameter] = test_record_doc.get(
                                param.field)

                    print("\033[0;33;93m   >>> Executing Function --",
                          testcase_doc.function_name)
                    if testcase_doc.json_parameter and testcase_doc.json_parameter.strip() != '':
                        kwargs.update(eval(str(testcase_doc.json_parameter)))

                    method = testcase_doc.function_name
                    if method and '.' in method:
                        args = []
                        function_result = frappe.get_attr(
                            method)(*args, **kwargs)
                    else:
                        test_data_record_name = frappe.db.get_value(
                            'Test Data', testcase_doc.test_data, 'test_record_name')
                        test_record_doc = frappe.get_doc(
                            testcase_doc.testcase_doctype, test_data_record_name)
                        function_result = test_record_doc.run_method(
                            method, **kwargs)
                    # print('Result of the executed function -- ',function_result)
                except Exception as e:
                    frappe.log_error(frappe.get_traceback(
                    ), ('barista-'+testcase_doc.name+'-FUNCTION-'+str(e))[:error_log_title_len])
                    error_message = str(e)
                    print(
                        "\033[0;31;91m       >>>> Execution of function failed\n    ", e)
                print("\033[0;32;92m     >>> Function Executed")

            test_result_doc.execution_time = get_execution_time(start_time)

            assertions = frappe.get_list(
                "Assertion", filters={'parent': testcase})

            if len(assertions) == 0:
                test_result_doc.execution_result = 'Assertions are not present in the TestCase. Please add atleast one assertion.'
                test_result_doc.test_case_status = "Failed"
                test_result_doc.save()

            for assertion in assertions:

                assertion_doc = frappe.get_doc("Assertion", assertion['name'])
                value_type = 'Fixed Value'
                record_count = 1

                if assertion_doc.value_type:
                    value_type = assertion_doc.value_type

                if assertion_doc.record_count:
                    record_count = assertion_doc.record_count

                print("\033[0;37;97m       >>>> Applying assertion : " +
                      str(assertion['name']))
                assertion_result = frappe.new_doc("Assertion Result")
                assertion_result.assertion = assertion_doc.name
                assertion_result.assertion_status = "Passed"
                if(assertion_doc.assertion_type != "RESPONSE" and assertion_doc.assertion_type != "ERROR"):
                    validation_doctype = frappe.get_all(assertion_doc.doctype_name, filters={
                                                        assertion_doc.reference_field: testdata_doc.test_record_name})

                if (assertion_doc.assertion_type == "FIELD VALUE"):
                    if (len(validation_doctype) != 1):
                        assertion_result.assertion_status = "Failed"
                        assertion_result.assertion_result = "Actual number of record(s) found - " + str(len(validation_doctype)) + \
                            ". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
                            ". Value - " + str(testdata_doc.test_record_name)

                        if(error_message):
                            # there was some error as well.
                            assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
                                + error_message

                        test_result_doc.test_case_status = "Failed"
                        print("\033[0;31;91m       >>>> Assertion failed")

                    else:

                        validation_doctype_doc = frappe.get_doc(
                            assertion_doc.doctype_name, validation_doctype[0]['name'])
                        result = validation_doctype_doc.get(
                            assertion_doc.docfield_name)
                        # print(result)
                        # print(eval(assertion_doc.code),assertion_doc.code)
                        if((str(validation_doctype_doc.get(assertion_doc.docfield_name)) == str(assertion_doc.docfield_value)) and value_type == 'Fixed Value'):
                            #Assertion is successful
                            assertion_result.assertion_result = "Value matched - " + \
                                str(validation_doctype_doc.get(
                                    assertion_doc.docfield_name))
                            print("\033[0;32;92m       >>>> Assertion Passed")
                        elif value_type == 'Code' and eval(assertion_doc.code):
                            assertion_result.assertion_result = "Value matched - " + \
                                str(validation_doctype_doc.get(
                                    assertion_doc.docfield_name))
                            print("\033[0;32;92m       >>>> Assertion Passed")
                        else:
                            # Assertion failed
                            # test case also fails
                            assertion_result.assertion_status = "Failed"
                            assertion_result.assertion_result = "Value Found - " + str(validation_doctype_doc.get(assertion_doc.docfield_name))  \
                                + ". Where as expected value is - " + \
                                str(assertion_doc.docfield_value)

                            if(error_message):
                                # there was some error as well.
                                assertion_result.assertion_result = assertion_result.assertion_result + "\n\nError Encountered : " \
                                    + error_message

                            test_result_doc.test_case_status = "Failed"
                            print("\033[0;31;91m       >>>> Assertion Failed")

                elif (assertion_doc.assertion_type == "RECORD VALIDATION"):
                    if (len(validation_doctype) == record_count):
                        records = [doc['name'] for doc in validation_doctype]
                        #Assertion is successful
                        assertion_result = frappe.new_doc("Assertion Result")
                        assertion_result.assertion = assertion_doc.name
                        assertion_result.assertion_status = "Passed"
                        assertion_result.assertion_result = "Record found - " + \
                            ','.join(records)
                        print("\033[0;32;92m       >>>> Assertion Passed")
                    else:
                        assertion_result.assertion_status = "Failed"
                        assertion_result.assertion_result = "Actual number of record(s) found - " + str(len(validation_doctype)) + \
                            ". For Doctype - " + assertion_doc.doctype_name + " . Name - " + assertion_doc.reference_field +\
                            ". Value - " + \
                            (testdata_doc.test_record_name or '')
                        test_result_doc.test_case_status = "Failed"
                        print("\033[0;31;91m       >>>> Assertion Failed")

                        if(error_message):
                            # there was some error as well.
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
                        if function_result:
                            result = function_result

                            def to_json_converter(value):
                                if isinstance(value, datetime.datetime):
                                    return value.__str__()

                            test_result_doc.execution_result = json.dumps(
                                function_result, default=to_json_converter).replace('": "', '":"').replace('": ', '":')

                        if response_regex and response_regex != '' and (response_regex in test_result_doc.execution_result) and value_type=='Fixed Value':
                            assertion_result.assertion_status = "Passed"
                            assertion_result.assertion_result = response_regex + \
                                " -> is present in the response received from the function"
                            print("\033[0;32;92m       >>>> Assertion Passed")
                        elif test_result_doc.execution_result != '' and value_type=='Fixed Value':
                            assertion_result.assertion_status = "Failed"
                            test_result_doc.test_case_status = "Failed"
                            if response_regex == '':
                                assertion_result.assertion_result = 'Please check value of any key in response'
                            else:
                                assertion_result.assertion_result = response_regex + \
                                    "-> is not found in the response received from the function"
                            print("\033[0;31;91m       >>>> Assertion Failed")
                        elif test_result_doc.execution_result == '' and response_regex == '' and value_type=='Fixed Value':
                            assertion_result.assertion_status = "Passed"
                            print("\033[0;32;92m       >>>> Assertion Passed")

                        if value_type == 'Code' and eval(assertion_doc.code):
                            assertion_result.assertion_status = "Passed"
                            print("\033[0;32;92m       >>>> Assertion Passed")

                assertion_result.parentfield = "assertion_results"
                test_result_doc.get("assertion_results").append(
                    assertion_result)
                test_result_doc.save()

        except Exception as e:
            frappe.log_error(frappe.get_traceback(
            ), ('barista-Critical Error-'+testcase_doc.name+'-'+str(e))[:error_log_title_len])
            test_result_doc.test_case_execution = "Execution Failed"
            test_result_doc.execution_result = str(e)
            test_result_doc.test_case_status = "Failed"
            test_result_doc.save()
            # raise e
        finally:
            print("\033[0;36;96m>> " + "Execution Ended \n\n")


def get_execution_time(start_time):
    end_time = round(time.time() - start_time, 4)
    time_uom = 'seconds'
    if(end_time >= 60):
        end_time = round(end_time/60, 4)
        time_uom = 'minutes'

    return str(end_time)+' '+time_uom
