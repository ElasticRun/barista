# -*- coding: utf-8 -*-
# Copyright (c) 2019, elasticrun and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from barista.barista.doctype.test_data.test_data_generator import TestDataGenerator
from frappe.model.workflow import apply_workflow
import coverage
from barista.barista.doctype.test_case.test_case_execution import TestCaseExecution
import time
import shutil
import sqlite3
from coverage.numbits import register_sqlite_functions


error_log_title_len = 1000


class RunTest():
    # Run all the suites for the given app
    def run_complete_suite(self, app_name, suites=[], run_name=None):
        start_time = time.time()
        alter_error_log()
        print("\033[0;33;93m************ Running all test cases for App - " +
              app_name + " *************\n\n")
        if len(suites) == 0:
            suites = frappe.get_all("Test Suite", filters={
                                    'app_name': app_name}, order_by='creation asc')
        else:
            suite_name = []
            for suite in suites:
                suite_name.append({'name': suite})
            suites = suite_name

        barista_app_path = frappe.get_app_path(
            'barista') + '/public/test-coverage/'
        shutil.rmtree(barista_app_path, ignore_errors=True)

        generatorObj = TestDataGenerator()
        objCoverage = coverage.Coverage(source=[frappe.get_app_path(app_name)], data_file=str(
            barista_app_path+app_name+'.coverage'), omit=['*test_*'], config_file=False)
        objCoverage.erase()
        objCoverage.start()
        total_suites = len(suites)
        suite_srno = 0
        for suite in suites:
            suite_srno += 1
            print("\033[0;32;92m************ Suite - " +
                  suite.get('name') + " *************\n\n")
            try:
                generatorObj.create_pretest_data(suite.get('name'), run_name)
                testcases = frappe.get_list('Testcase Item', filters={
                                            'parent': suite.get('name')}, fields=["testcase"], order_by="idx")
                total_testcases = len(testcases)
                testcase_srno = 0
                for testcase in testcases:
                    testcase_srno += 1
                    self.run_testcase(
                        testcase, suite, testcase_srno, total_testcases, suite_srno, total_suites, run_name)

            except Exception as e:
                frappe.log_error(frappe.get_traceback(
                ), ('barista-Suite Execution Failed-'+suite.get('name')+'-'+str(e))[:error_log_title_len])
                print(
                    "\033[0;31;91mAn Error occurred which will cause false test case result in the suite - " + str(suite.get('name')))
                print("\033[0;31;91m*************ERROR****************")
                print(
                    "\033[0;31;91m The error encountered is - " + str(e) + "\n")
                print("\033[0;31;91m*************ERROR****************")

        objCoverage.stop()
        objCoverage.save()
        #objCoverage.annotate(directory=frappe.get_app_path('barista') + '/public/test-coverage/')

        objCoverage.html_report(
            directory=barista_app_path, skip_empty=True, omit=['*test_*'])

        print("\033[0;33;93m************ Execution ends. Verify coverage at - " +
              "/assets/barista/test-coverage/index.html")

        end_time = round(time.time() - start_time, 2)
        time_uom = 'seconds'
        if(end_time >= 60):
            end_time = round(end_time/60, 2)
            time_uom = 'minutes'
        print("--- Executed in %s %s ---" % (end_time, time_uom))

    def run_testcase(self, testcase, suite, testcase_srno, total_testcases, suite_srno, total_suites, run_name):
        executionObj = TestCaseExecution()
        executionObj.run_testcase(testcase['testcase'], suite.get(
            'name'), testcase_srno, total_testcases, suite_srno, total_suites, run_name)
        frappe.db.commit()

    def get_executed_lines(self, app_name, file_name):
        sql_query_result = []
        try:
            barista_app_path = frappe.get_app_path(
                'barista') + '/public/test-coverage/'
            data_file_path = str(barista_app_path+app_name+'.coverage')

            def dict_factory(cursor, row):
                d = {}
                for idx, col in enumerate(cursor.description):
                    d[col[0]] = row[idx]
                return d

            conn = sqlite3.connect(data_file_path)
            conn.row_factory = dict_factory
            register_sqlite_functions(conn)
            c = conn.cursor()
            sql_query = """SELECT lb.file_id,
									f.path,
									lb.numbits
								FROM 'line_bits' lb
								INNER JOIN 'file' f ON f.id=lb.file_id
								WHERE f.path LIKE '%{0}'""".format(file_name)
            c.execute(sql_query)
            sql_query_result = c.fetchall()
            for row in sql_query_result:
                if row:
                    numbits = row.get('numbits')
                    if numbits:
                        lines = coverage.numbits.numbits_to_nums(numbits)
                        row['numbits'] = lines

            conn.commit()
            conn.close()
        except Exception as e:
            frappe.log_error(frappe.get_traceback(
            ), ('barista-get_executed_lines-'+str(e))[:error_log_title_len])
        return sql_query_result


@frappe.whitelist()
# bench execute barista.barista.doctype.test_suite.run_test.generate_merge_commit_coverage --kwargs "{'app_name':'velocityduos','file_name':'trip.py','new_lines':[]}"
def generate_merge_commit_coverage(app_name, file_name, new_lines):
    output = {
        'file_name': file_name,
        'file_path': '',
        'executed_lines': [],
        'missed_lines': []
    }
    try:
        new_executed_lines = []
        missed_lines = []
        run_test_obj = RunTest()

        if type(new_lines) == str:
            new_lines = [int(l) for l in new_lines.split(',')]

        executed_lines = run_test_obj.get_executed_lines(app_name, file_name)
        if len(executed_lines) != 0:
            record = executed_lines[0]
            file_path = record.get('path')
            record_file_name = file_path.split('/').pop()
            if '/' in file_name:
                file_name = file_name.split('/').pop()
            if record_file_name == file_name:
                output['file_path'] = file_path
                executed_lines = record.get('numbits')
                new_executed_lines = executed_lines
                for line in new_lines:
                    if line not in executed_lines:
                        missed_lines.append(line)
                for line in missed_lines:
                    if line in executed_lines:
                        new_executed_lines.remove(line)
            else:
                frappe.throw('Multiple files of the same name found.')

        output['executed_lines'] = new_executed_lines
        output['missed_lines'] = missed_lines
    except Exception as e:
        frappe.log_error(frappe.get_traceback(
        ), ('barista-generate_merge_commit_coverage-'+str(e))[:error_log_title_len])
    return output


@frappe.whitelist()
# barista.barista.doctype.test_suite.run_test.read_file
def read_file(file_path):
    lines = []
    try:
        opened_file = open(file_path, 'r')
        lines = opened_file.readlines()
    except Exception:
        frappe.log_error(frappe.get_traceback(), 'barista-read_file')
    return lines


def alter_error_log():
    frappe.db.sql("""UPDATE `tabDocField`
							SET fieldtype="Small Text"
							WHERE parent= "Error Log"
							AND fieldname= "method"
							AND label= "Title";""", auto_commit=1)
    frappe.db.sql(
        """ALTER TABLE `tabError Log` CHANGE `method` `method` text;""", auto_commit=1)
    if frappe.conf.get('developer_mode') == 1:
        frappe.get_doc('DocType', 'Error Log').save(True)


# bench execute barista.barista.doctype.test_suite.run_test.fix_series
def fix_series():
    print('Previous Series-', frappe.db.sql(
        """select * from `tabSeries` where name in ('TestData-','TestCase-')""", as_dict=1))
    test_data_series = frappe.db.sql_list(
        """select * from `tabSeries` where name='TestData-';""")
    max_test_data_series = frappe.db.sql_list(
        """select ifnull(max(name),'TestData-0') from `tabTest Data`;""")
    if len(max_test_data_series):
        max_test_data_series = int(max_test_data_series[0].split('-')[1])
    if len(test_data_series) == 0:
        frappe.db.sql(
            f"""Insert into `tabSeries` (name,current) values ('TestData-',{max_test_data_series});""", auto_commit=1)
    else:
        frappe.db.sql(
            f"""update `tabSeries` set current={max_test_data_series} where name="TestData-";""", auto_commit=1)

    test_case_series = frappe.db.sql_list(
        """select * from `tabSeries` where name='TestCase-';""")
    max_test_case_series = frappe.db.sql_list(
        """select ifnull(max(name),'TestCase-0') from `tabTest Case`;""")
    if len(max_test_case_series):
        max_test_case_series = int(max_test_case_series[0].split('-')[1])
    if len(test_case_series) == 0:
        frappe.db.sql(
            f"""Insert into `tabSeries` (name,current) values ('TestCase-',{max_test_case_series});""", auto_commit=1)
    else:
        frappe.db.sql(
            f"""update `tabSeries` set current={max_test_case_series} where name="TestCase-";""", auto_commit=1)

    print('Current Series-', frappe.db.sql(
        """select * from `tabSeries` where name in ('TestData-','TestCase-')""", as_dict=1))


# bench execute barista.barista.doctype.test_suite.run_test.run_test --kwargs "{'app_name':'velocityduos','suites':[]}"
def run_test(app_name, suites=[]):
    RunTest().run_complete_suite(app_name, suites)
