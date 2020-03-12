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
import time
import shutil


class RunTest():

    #Run all the suites for the given app
    def run_complete_suite(self, app_name,suites=[]):
        start_time = time.time()
    
        print("\033[0;33;93m************ Running all test cases for App - " + app_name + "*************\n\n")
        if len(suites)==0:
            suites = frappe.get_all("Test Suite", filters={'app_name' : app_name},order_by='creation asc')
        else:
            suite_name=[]
            for suite in suites:
                suite_name.append({'name':suite})
            suites=suite_name
            
        barista_app_path=frappe.get_app_path('barista') + '/public/test-coverage/'
        shutil.rmtree(barista_app_path,ignore_errors=True)

        generatorObj = TestDataGenerator()        
        objCoverage = coverage.Coverage(source=[frappe.get_app_path(app_name)],data_file=str(barista_app_path+app_name+'.coverage'),omit=['*test_*'],config_file=False)
        objCoverage.erase()
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
                frappe.log_error(frappe.get_traceback(),('barista-Suite Execution Failed'+suite.get('name'))[:140])
                print("\033[0;31;91mAn Error occurred which will cause false test case result in the suite - " + str(suite.get('name')) )
                print("\033[0;31;91m*************ERROR****************")
                print("\033[0;31;91m The error encountered is - " + str(e)  + "\n")
                print("\033[0;31;91m*************ERROR****************")
                # raise e


            
        objCoverage.stop()
        objCoverage.save()
        #objCoverage.annotate(directory=frappe.get_app_path('barista') + '/public/test-coverage/')

        objCoverage.html_report(directory=barista_app_path,skip_empty=True,omit=['*test_*'])

        print("\033[0;33;93m************ Execution ends. Verify coverage at - " + "/assets/barista/test-coverage/index.html")

        end_time=round(time.time() - start_time,2)
        time_uom='seconds'
        if(end_time>=60):
            end_time=round(end_time/60,2)
            time_uom='minutes'
        print("--- Executed in %s %s ---" % (end_time,time_uom))
    
    def run_testcase(self, testcase, suite):
        executionObj = TestCaseExecution()        
        executionObj.run_testcase(testcase['testcase'], suite.get('name'))
        frappe.db.commit()
