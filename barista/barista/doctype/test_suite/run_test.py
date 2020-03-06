# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from barista.barista.doctype.test_data.test_data_generator import TestDataGenerator
from frappe.model.workflow import apply_workflow
import coverage
from barista.barista.doctype.test_case.test_case_execution import  TestCaseExecution


class RunTest():

    #Run all the suites for the given app
    def run_complete_suite(self, app_name,suites=[]):

        print("\033[0;33;93m************ Running all test cases for App - " + app_name + "*************\n\n")
        if len(suites)==0:
            suites = frappe.get_all("Test Suite", filters={'app_name' : app_name},order_by='creation asc')
        else:
            suite_name=[]
            for suite in suites:
                suite_name.append({'name':suite})
            suites=suite_name
            
    
        import shutil
        path=frappe.get_app_path('barista') + '/public/test-coverage/'
        shutil.rmtree(path,ignore_errors=True)
        generatorObj = TestDataGenerator()        
        objCoverage = coverage.Coverage(source=[frappe.get_app_path(app_name)] )
        objCoverage.start()
        
        for suite in suites:

            print("\033[0;32;92m************ Suite - " + suite.get('name') + "*************\n\n")
            try:
                generatorObj.create_pretest_data(suite.get('name'))            
                testcases = frappe.get_list('Testcase Item' , filters={'parent': suite.get('name')}, fields=["testcase"],order_by="idx")
                # print("\n \ntestcases---",testcases)  
                for testcase in testcases:                    
                    self.run_testcase(testcase,suite)

            except Exception as e:
                print("\033[0;31;91mAn Error occurred which will cause false test case result in the suite - " + str(suite.get('name')) )
                print("\033[0;31;91m*************ERROR****************")
                print("\033[0;31;91m The error encountered is - " + str(e)  + "\n")
                print("\033[0;31;91m*************ERROR****************")
                # raise e


            
        objCoverage.stop()
        #objCoverage.annotate(directory=frappe.get_app_path('barista') + '/public/test-coverage/')

        objCoverage.html_report(directory=frappe.get_app_path('barista') + '/public/test-coverage/')

        objCoverage.erase()
        print("\033[0;33;93m************ Execution ends. Verify coverage at - " + "/assets/barista/test-coverage/index.html")
    
    def run_testcase(self, testcase, suite):
        executionObj = TestCaseExecution()        
        executionObj.run_testcase(testcase['testcase'], suite.get('name'))
        frappe.db.commit()
