# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
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
import string

error_log_title_len = 1000
yellow = '\033[0;33;93m'
red = '\033[0;31;91m'


class TestDataGenerator():
    def create_pretest_data(self, suite, run_name):
        # select all the test data for a suite...
        all_testdata = frappe.db.sql_list(
            """select distinct td.name from `tabTest Data` td join `tabTestdata Item` tdi on tdi.test_data=td.name where tdi.parent=%(parent)s order by tdi.idx""", {'parent': suite})
        if len(all_testdata) != 0:
            print(f'{yellow}Creating Pre-Test Data')
        for testdata in all_testdata:
            try:
                testdata_doc = frappe.get_doc("Test Data", testdata)
                if (testdata_doc.create_using == 'Sql Script'):
                    self.create_testdata(testdata, run_name)
                elif (testdata_doc.create_using == 'Function'):
                    self.create_testdata_function(testdata, run_name)
                else:
                    new_doc, error_message = self.create_testdata(testdata, run_name)
                    if testdata_doc.doctype_type == 'Transaction':
                        new_doc.save(True)
                        created_doc = new_doc
                        testdata_doc = frappe.get_doc("Test Data", testdata)
                        create_test_run_log(
                            run_name, testdata, created_doc.name)
                    elif testdata_doc.doctype_type == 'Master':
                        try:
                            new_doc.save(True)
                            created_doc = new_doc
                        except frappe.DuplicateEntryError as e:
                            created_doc = resolve_duplicate_entry_error(
                                e, testdata_doc, run_name)
                        except frappe.UniqueValidationError as e:
                            created_doc = resolve_unique_validation_error(
                                e, testdata_doc, run_name)
                        create_test_run_log(
                            run_name, testdata, created_doc.name)
                    self.set_record_name_child_table(
                        created_doc, testdata_doc, run_name=run_name)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(
                ), (f'barista-TestDataGenerator-{testdata}-{str(e)}')[:error_log_title_len])
        if len(all_testdata) != 0:
            print(f'{yellow}Pre-Test Data created successfully')
        print('')
        frappe.db.commit()

    def create_testdata(self, testdata, run_name):
        current_fieldname = ''
        error_message = ''
        new_doc = None
        try:
            testdata_doc = frappe.get_doc('Test Data', testdata)
            # first check if use script is true
            if (testdata_doc.create_using == 'Sql Script'):
                # if Yes run the script
                frappe.db.sql(testdata_doc.insert_script, auto_commit=1)
            elif (testdata_doc.create_using == 'Function'):
                return self.create_testdata_function(testdata, run_name)
            else:
                testdata_doc_test_record_name = frappe.db.get_value(
                    'Test Run Log', {'test_run_name': run_name, 'test_data': testdata}, 'test_record')
                if (testdata_doc_test_record_name):
                    new_doc = frappe.get_doc(
                        testdata_doc.doctype_name, testdata_doc_test_record_name)
                    # return created_doc_earlier
                else:
                    # start creating the insert statement
                    new_doc = frappe.get_doc(
                        {"doctype": testdata_doc.doctype_name})
                    fields = frappe.get_meta(testdata_doc.doctype_name).fields
                    declared_fields = frappe.get_list('Testdatafield', filters={
                                                    'parent': testdata_doc.name})
                    # for each field
                    for field in fields:
                        # check if the field values are in provided.. use it
                        field_doc = field
                        flag_field = False

                        for declared_field in declared_fields:
                            declared_field_doc = frappe.get_doc(
                                'Testdatafield', declared_field['name'])
                            current_fieldname = declared_field_doc.docfield_fieldname
                            if (declared_field_doc.docfield_fieldname == "docstatus"):
                                if (declared_field_doc.docfield_value is None):
                                    declared_field_doc.docfield_value = 0
                                new_doc.set(declared_field_doc.docfield_fieldname, int(
                                    declared_field_doc.docfield_value))
                            elif(declared_field_doc.docfield_fieldname == field_doc.fieldname):
                                flag_field = True
                                if (declared_field_doc.is_default):
                                    # ignore
                                    pass
                                elif (field_doc.fieldtype == "Table"):
                                    # if it is table then user will have to add multiple rows for multiple records.
                                    child_testdata_doc = frappe.get_doc(
                                        'Test Data', declared_field_doc.linkfield_name)
                                    if (child_testdata_doc.doctype_type == "Transaction"):
                                        create_test_run_log(
                                            run_name, child_testdata_doc.name, None)
                                    # each test data field will link to one record. create a new record
                                    child_doc, error_message = self.create_testdata(
                                        declared_field_doc.linkfield_name, run_name)
                                    if child_doc:
                                        child_doc.parent_doc = new_doc
                                        create_test_run_log(
                                            run_name, child_testdata_doc.name, child_doc.name)

                                        child_doc.parentfield = field_doc.fieldname
                                        new_doc.get(field_doc.fieldname).append(
                                            child_doc)
                                    else:
                                        frappe.throw(
                                            f'Child Doc is None. Test Data of Child {declared_field_doc.linkfield_name}. Test Data of Parent {testdata}')

                                # link parent to this record
                                elif ("Link" in field_doc.fieldtype and declared_field_doc.docfield_code_value == "Fixed Value"):
                                    new_doc.set(field_doc.fieldname,
                                                declared_field_doc.docfield_value)
                                elif ("Link" in field_doc.fieldtype):
                                    child_testdata_doc = frappe.get_doc(
                                        'Test Data', declared_field_doc.linkfield_name)
                                    if (child_testdata_doc.doctype_type == "Transaction"):
                                        create_test_run_log(
                                            run_name, child_testdata_doc.name, None)

                                    child_doc, error_message = self.create_testdata(
                                        declared_field_doc.linkfield_name, run_name)
                                    try:
                                        child_doc.save()
                                    except frappe.DuplicateEntryError as e:
                                        child_doc = resolve_duplicate_entry_error(
                                            e, child_testdata_doc, run_name)
                                    except frappe.UniqueValidationError as e:
                                        child_doc = resolve_unique_validation_error(
                                            e, child_testdata_doc, run_name)

                                    create_test_run_log(
                                        run_name, child_testdata_doc.name, child_doc.name)
                                    new_doc.set(field_doc.fieldname,
                                                child_doc.get(declared_field_doc.linkfield_key or 'name'))

                                elif (declared_field_doc.docfield_code_value == "Code"):
                                    if declared_field_doc.docfield_code and not declared_field_doc.linkfield_name:
                                        new_doc.set(declared_field_doc.docfield_fieldname, eval(
                                            str(declared_field_doc.docfield_code)))
                                    if not declared_field_doc.docfield_code and declared_field_doc.linkfield_name:
                                        value = frappe.db.get_value(
                                            'Test Run Log', {'test_run_name': run_name, 'test_data': declared_field_doc.linkfield_name}, 'test_record')
                                        new_doc.set(
                                            declared_field_doc.docfield_fieldname, value)
                                else:
                                    if field_doc.fieldtype in ['Currency', 'Float', 'Percent']:
                                        new_doc.set(declared_field_doc.docfield_fieldname, float(
                                            declared_field_doc.docfield_value))
                                    elif field_doc.fieldtype == 'Int':
                                        new_doc.set(declared_field_doc.docfield_fieldname, int(
                                            declared_field_doc.docfield_value))
                                    else:
                                        new_doc.set(declared_field_doc.docfield_fieldname, str(
                                            declared_field_doc.docfield_value))

                        # self.assign_random_value(
                        #     flag_field, field_doc, new_doc, declared_field_doc)

                    # return new_doc
        except Exception as e:
            error_message = str(error_message)
            frappe.log_error(frappe.get_traceback(
            ), (f'barista-TestDataGenerator-{testdata}-DocTypeField-[{current_fieldname}]-'+str(e))[:error_log_title_len])
        return new_doc, error_message

    def assign_random_value(self, flag_field, field_doc, new_doc, declared_field_doc):
        if(flag_field == False and not field_doc.fetch_from):
            # no declared field necessary for the test case. Create random field.
            value = None
            if (field_doc.fieldtype == "Data"):
                # its a string of 140
                value = (field_doc.label.split()[
                    0] + str(random.randrange(0, 20000, 1)))[0:139]
            elif (field_doc.fieldtype == "Check"):
                # its a check
                value = random.choice([0, 1])
            elif(field_doc.fieldtype == "Currency"):
                value = round(random.uniform(500.12, 22000.34), 2)
            elif(field_doc.fieldtype == "Date"):
                value = datetime.date.today() + datetime.timedelta(days=(random.randrange(0, 15, 1)))
            elif(field_doc.fieldtype == "Datetime"):
                value = datetime.datetime.now() + datetime.timedelta(minutes=(random.randrange(0, 200, 2)))
            elif(field_doc.fieldtype == "Float"):
                value = round(random.uniform(0, 22000.34), 2)
            elif(field_doc.fieldtype == "Int"):
                value = random.randrange(0, 200, 1)
            elif(field_doc.fieldtype == "Long Text" or field_doc.fieldtype == "Small Text" or field_doc.fieldtype == "Text"):
                value = (field_doc.label +
                         str(random.randrange(0, 20000, 1)))
            elif(field_doc.fieldtype == "Password"):
                value = "Frappe@12345"
            elif (field_doc.fieldtype == "Percent"):
                value = round(random.uniform(0, 100), 2)
            elif ("Link" in field_doc.fieldtype or field_doc.fieldtype == "Table"):
                # it looks like table or link field is not declared by user... test data generation failed..
                pass
            elif("Attach" in field_doc.fieldtype):
                value = "assets/barista/sample-file.html"

            if value != None:
                new_doc.set(
                    field_doc.fieldname, value)

    def create_testdata_function(self, testdata, run_name):
        generated_doc = None
        error_message = ''
        try:
            args = []
            kwargs = {}
            result = None
            test_record_to_save = None

            testdata_doc = frappe.get_doc('Test Data', testdata)
            method = testdata_doc.function_name
            print("\033[0;33;93m   >>> Executing Function --",method)
            if frappe.db.get_value('Test Run Log',{'test_data':testdata,'test_run_name':run_name},'test_record'):
                create_test_run_log(run_name,testdata,frappe.db.get_value('Test Run Log',{'test_data':testdata,'test_run_name':run_name},'test_record'))
                return frappe.get_doc(testdata_doc.doctype_name,frappe.db.get_value('Test Run Log',{'test_data':testdata,'test_run_name':run_name},'test_record')), error_message

            for param in testdata_doc.function_parameters:
                key = param.parameter

                if param.value and param.value.strip()[0] in ['{', '['] and '{{' not in param.value and param.type == "json":
                    value = eval(param.value)
                elif param.value and '{{' in param.value:
                    value = self.resolve_jinja(
                        param.value, param.test_data, run_name)
                elif param.value and param.type == 'eval':
                    value = eval(param.value)
                else:
                    value = param.value

                kwargs[key] = value
                if param.test_data:
                    test_record_name = frappe.db.get_value(
                        'Test Run Log', {'test_run_name': run_name, 'test_data': param.test_data}, 'test_record')
                    test_record_doctype = frappe.db.get_value(
                        'Test Data', param.test_data, 'doctype_name')
                    if test_record_name:
                        test_record_doc = frappe.get_doc(
                            test_record_doctype, test_record_name)
                        if param.is_object:
                            if param.object_type == 'dict':
                                kwargs[key] = test_record_doc.as_dict()
                            elif param.object_type == 'json':
                                kwargs[key] = test_record_doc.as_json()
                        elif param.field and not param.value:
                            kwargs[key] = test_record_doc.get(
                                param.field)

            if method and '.' in method:
                try:
                    result = frappe.get_attr(
                        method)(*args, **kwargs)
                except frappe.DuplicateEntryError as e:
                    result = resolve_duplicate_entry_error(
                        e, testdata_doc, run_name)
                except frappe.UniqueValidationError as e:
                    result = resolve_unique_validation_error(
                        e, testdata_doc, run_name)

            if testdata_doc.eval_function_result:
                test_record_to_save = eval(testdata_doc.eval_function_result)
            else:
                if result and type(result) != str:
                    test_record_to_save = result.get('name')

            if len(testdata_doc.conditions):
                filter_dct = {}
                for c in testdata_doc.conditions:
                    filter_dct[c.reference_field] = c.value
                    if c.test_data:
                        test_record_name = frappe.db.get_value(
                            'Test Run Log', {'test_run_name': run_name, 'test_data': c.test_data}, 'test_record')
                        test_record_doctype = frappe.db.get_value(
                            'Test Data', c.test_data, 'doctype_name')
                        test_record_doc = frappe.get_doc(
                            test_record_doctype, test_record_name)
                        if c.field:
                            filter_dct[c.reference_field] = test_record_doc.get(
                                c.field)
                        else:
                            filter_dct[c.reference_field] = test_record_doc.get(
                                'name')

                    records = frappe.get_all(
                        c.reference_doctype, filters=filter_dct, fields=["*"])
                    if len(records):
                        if not c.field_to_refer:
                            c.field_to_refer = 'name'
                        if records[0].get(c.field_to_refer):
                            test_record_to_save = records[0].get(
                                c.field_to_refer)

            create_test_run_log(run_name, testdata, test_record_to_save)

            generated_doc = frappe.get_doc(
                testdata_doc.doctype_name, test_record_to_save)
        except Exception as e:
            error_message = str(e)
            print("\033[0;31;91m       >>>> Execution of function failed\n       Error occurred :", str(e))
            frappe.log_error(frappe.get_traceback(
            ), (f'barista-TestDataGenerator-{testdata}-Function-[{method}]-'+str(e))[:error_log_title_len])
        return generated_doc, error_message

    def resolve_jinja(self, jinja, testdata, run_name):
        resolved_jinja = ''
        try:
            context_dict = {"doc": {}}
            if testdata:
                test_record_name = frappe.db.get_value(
                    'Test Run Log', {'test_run_name': run_name, 'test_data': testdata}, 'test_record')
                test_record_doctype = frappe.db.get_value(
                    'Test Data', testdata, 'doctype_name')
                context = frappe.get_doc(
                    test_record_doctype, test_record_name).as_dict()
                context_dict = {"doc": context}
            try:
                validate_template(jinja)
                resolved_jinja = render_template(
                    jinja, context_dict)
            except Exception as e:
                print(f"{red}       >>>> Error in Json Parameter\n      ", str(e))
        except Exception as e:
            frappe.log_error(frappe.get_traceback(
            ), (f'barista-TestDataGenerator-{testdata}-Jinja-'+str(e))[:error_log_title_len])
        return resolved_jinja

    def set_record_name_child_table(self, created_doc, parent_doc, create_new_child=False, run_name=None):
        parenttype = None
        if created_doc:
            parenttype = created_doc.doctype
        new_record_fields = frappe.db.sql(
            f"select fieldname from `tabDocField` where parent = '{parenttype}'and fieldtype = 'Table'", as_dict=True)
        for new_record_field in new_record_fields:
            child_records = created_doc.get(new_record_field.fieldname)
            test_data_field_values = frappe.db.sql('select linkfield_name from `tabTestdatafield` where docfield_fieldname = "' +
                                                   new_record_field.fieldname + '" and parent = "' + parent_doc.name + '" order by idx', as_dict=True)
            child_record_index = 0
            for test_data_field_value in test_data_field_values:
                if child_record_index < len(child_records):
                    if (test_data_field_value.linkfield_name is not None):
                        child_test_data_doc = frappe.get_doc(
                            'Test Data', test_data_field_value.linkfield_name)
                        child_test_data_doc_status = frappe.db.get_value('Test Run Log', {
                            'test_run_name': run_name, 'test_data': child_test_data_doc.name}, 'test_data_status')
                        if(child_test_data_doc_status != "Created") and parent_doc.doctype == "Test Data":
                            create_test_run_log(
                                run_name, child_test_data_doc.name, child_records[child_record_index].name)
                        elif create_new_child:
                            create_test_run_log(
                                run_name, child_test_data_doc.name, child_records[child_record_index].name)
                child_record_index += 1


def create_test_run_log(run_name, test_data, test_record):
    try:
        existing_trl_doc = frappe.get_all(
            'Test Run Log', {'test_run_name': run_name, 'test_data': test_data})
        if len(existing_trl_doc):
            trl_doc = frappe.get_doc(
                'Test Run Log', existing_trl_doc[0]['name'])
        else:
            trl_doc = frappe.new_doc('Test Run Log')
        trl_doc.test_run_name = run_name
        trl_doc.test_data = test_data
        if test_record:
            trl_doc.test_data_status = 'Created'
        else:
            trl_doc.test_data_status = 'Failed'
        trl_doc.test_record = test_record
        if frappe.db.exists('Test Run Log', {'test_run_name': run_name, 'test_data': test_data}):
            trl_doc.save(True)
        else:
            trl_doc.insert(True)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(
        ), (f'barista-TRL-{test_data}-{str(e)}')[:error_log_title_len])


def resolve_unique_validation_error(e, testdata_doc, run_name):
    args = e.args
    doctype = args[0]
    e = str(args[2])
    v = e.split('Duplicate entry ')[1]
    k = v.split(' for key ')
    v = k[0]
    k = k[1]
    v = v.replace("'", "")
    k = k.replace("'", "").replace('")', "")

    new_record_doc = frappe.get_doc(doctype, {k: v})
    if new_record_doc:
        create_test_run_log(
            run_name, testdata_doc.name, new_record_doc.name)
        return new_record_doc


def resolve_duplicate_entry_error(e, testdata_doc, run_name):
    args = e.args
    doctype = args[0]
    docname = args[1]

    new_doc = frappe.get_doc(
        doctype, docname)

    if new_doc:
        create_test_run_log(
            run_name, testdata_doc.name, new_doc.name)
        return new_doc
