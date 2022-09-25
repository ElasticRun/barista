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
import click
import sys
import os
from pathlib import Path
from coverage.numbits import register_sqlite_functions
from tabulate import tabulate

error_log_title_len = 1000
yellow = '\033[0;33;93m'
green = '\033[0;32;92m'
red = '\033[0;31;91m'
white = '\033[0;37m'


class RunTest():
    # Run all the suites for the given app
    def run_complete_suite(self, app_name, suites=[], run_name=None):
        start_time = time.time()
        # alter_error_log()
        print(f"{yellow}************ Running all Test Cases for App - " +
              app_name + " *************\n\n")
        if len(suites) == 0:
            suites = frappe.get_all("Test Suite", filters={
                'app_name': app_name}, order_by='creation asc')
        else:
            suite_name = []
            for suite in suites:
                suite_name.append({'name': suite})
            suites = suite_name

        run_name_path = run_name.replace(' ', '__').replace('-', '_')
        # barista_app_path = f"{frappe.get_app_path('barista')}/public/test-coverage/{run_name_path}/"
        barista_app_path = f'{frappe.get_site_path()}/public/files/test-coverage/{run_name_path}/'

        data_file_path = str(f"{barista_app_path}{app_name}.coverage")

        shutil.rmtree(barista_app_path, ignore_errors=True)

        generatorObj = TestDataGenerator()
        objCoverage = coverage.Coverage(source=[frappe.get_app_path(
            app_name)], data_file=None, omit=['*test_*'], config_file=False)
        objCoverage.erase()
        objCoverage.start()
        total_suites = len(suites)
        suite_srno = 0
        for suite in suites:
            suite_srno += 1
            print(f"{green}************ Suite - " +
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
                    f"{red}An Error occurred which will cause false test case result in the suite - " + str(suite.get('name')))
                print(f"{red}*************ERROR****************")
                print(
                    f"{red}The error encountered is - " + str(e) + "\n")
                print(f"{red}*************ERROR****************")

        objCoverage.stop()
        objCoverage.save()
        #objCoverage.annotate(directory=frappe.get_app_path('barista') + '/public/test-coverage/')

        objCoverage.html_report(
            directory=barista_app_path, skip_empty=True, omit=['*test_*'])

        print(
            f"{green}************ Execution ends. Verify coverage at - /files/test-coverage/{run_name_path}/index.html")

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
    # barista.barista.doctype.test_suite.run_test.alter_error_log
    print(f'{yellow}Barista is altering the table `tabError Log`')
    frappe.db.sql("""ALTER TABLE `tabError Log` DROP INDEX IF EXISTS `index_on_method`;""")
    # frappe.db.sql('TRUNCATE `tabError Log`;')
    frappe.db.sql("""UPDATE `tabDocField`
							SET fieldtype="Small Text"
							WHERE parent= "Error Log"
							AND fieldname= "method"
							AND label= "Title";""", auto_commit=1)
    frappe.db.sql(
        """ALTER TABLE `tabError Log` CHANGE `method` `method` text;""", auto_commit=1)

    print(f'{yellow}Barista is turning ON Developer Mode{white}')
    from frappe.installer import update_site_config
    update_site_config('developer_mode', 1)

    if bool(frappe.conf.get('developer_mode')):
        frappe.get_doc('DocType', 'Error Log').save(True)


# bench execute barista.barista.doctype.test_suite.run_test.fix_series
def fix_series():
    bs = ''
    if frappe.conf.get('barista_series'):
        bs = f"{frappe.conf.get('barista_series')}-"

    previous_series = frappe.db.sql(
        f"""select * from `tabSeries` where name in ('{bs}TestData-','{bs}TestCase-')""", as_dict=1)

    test_data_lst = [0]
    for test_data in frappe.get_all('Test Data'):
        test_data_lst.append(int(test_data['name'].split('-')[-1]))

    max_test_data_series = max(test_data_lst)

    # max_test_data_series = frappe.db.sql_list(
    #     f"""select ifnull(max(name),'{bs}TestData-0') from `tabTest Data`;""")
    # if len(max_test_data_series):
    #     max_test_data_series = int(max_test_data_series[0].split('-')[-1])
    test_data_series = frappe.db.sql_list(
        f"""select * from `tabSeries` where name='{bs}TestData-';""")

    if len(test_data_series) == 0:
        frappe.db.sql(
            f"""Insert into `tabSeries` (name,current) values ('{bs}TestData-',{max_test_data_series});""", auto_commit=1)
    else:
        frappe.db.sql(
            f"""update `tabSeries` set current={max_test_data_series} where name="{bs}TestData-";""", auto_commit=1)

    test_case_lst = [0]
    for test_case in frappe.get_all('Test Case'):
        test_case_lst.append(int(test_case['name'].split('-')[-1]))

    max_test_case_series = max(test_case_lst)

    # max_test_case_series = frappe.db.sql_list(
    #     f"""select ifnull(max(name),'{bs}TestCase-0') from `tabTest Case`;""")
    # if len(max_test_case_series):
    #     max_test_case_series = int(max_test_case_series[0].split('-')[-1])
    test_case_series = frappe.db.sql_list(
        f"""select * from `tabSeries` where name='{bs}TestCase-';""")

    if len(test_case_series) == 0:
        frappe.db.sql(
            f"""Insert into `tabSeries` (name,current) values ('{bs}TestCase-',{max_test_case_series});""", auto_commit=1)
    else:
        frappe.db.sql(
            f"""update `tabSeries` set current={max_test_case_series} where name="{bs}TestCase-";""", auto_commit=1)

    current_series = frappe.db.sql(
        f"""select * from `tabSeries` where name in ('{bs}TestData-','{bs}TestCase-')""", as_dict=1)

    print(f'{yellow}Barista is fixing Test Data and Test Case series:\nPrevious Series-\n', end='')
    print(tabulate(previous_series, headers="keys", tablefmt="fancy_grid"))
    print(f'{yellow}Current Series-\n', end='')
    print(tabulate(current_series, headers="keys", tablefmt="fancy_grid"))


def fix_assertion_type_status():
    frappe.db.sql(
        "update `tabAssertion` set assertion_type='Field Value' where assertion_type='FIELD VALUE'", auto_commit=1)
    frappe.db.sql(
        "update `tabAssertion` set assertion_type='Record Validation' where assertion_type='RECORD VALIDATION'", auto_commit=1)
    frappe.db.sql(
        "update `tabAssertion` set assertion_type='Workflow' where assertion_type='WORKFLOW'", auto_commit=1)
    frappe.db.sql(
        "update `tabAssertion` set assertion_type='Response' where assertion_type='RESPONSE'", auto_commit=1)
    frappe.db.sql(
        "update `tabAssertion` set assertion_type='Error' where assertion_type='ERROR'", auto_commit=1)


def fix_testcase_type_status():
    frappe.db.sql(
        "update `tabTest Case` set testcase_type='Create' where testcase_type='CREATE'", auto_commit=1)
    frappe.db.sql(
        "update `tabTest Case` set testcase_type='Update' where testcase_type='UPDATE'", auto_commit=1)
    frappe.db.sql(
        "update `tabTest Case` set testcase_type='Read' where testcase_type='READ'", auto_commit=1)
    frappe.db.sql(
        "update `tabTest Case` set testcase_type='Delete' where testcase_type='DELETE'", auto_commit=1)
    frappe.db.sql(
        "update `tabTest Case` set testcase_type='Workflow' where testcase_type='WORKFLOW'", auto_commit=1)
    frappe.db.sql(
        "update `tabTest Case` set testcase_type='Function' where testcase_type='FUNCTION'", auto_commit=1)


def resolve_run_name(run_name='Pass-1'):
    # bench execute barista.resolve_run_name --kwargs "{'run_name':''}"

    if frappe.db.exists('Test Run Log', {'test_run_name': run_name}):
        if 'Pass-' in run_name:
            return resolve_run_name(
                f"Pass-{safe_cast(run_name.split('-')[1],int,1)+1}")
        else:
            click.echo(
                f'Provided Run Name [{run_name}] already exists. Please provide other Run Name.')
            sys.exit(1)
    else:
        frappe.get_doc({
            "run_name":run_name,
            "doctype": "Run Name",
        }).db_insert()
        frappe.db.commit()
        return run_name


def safe_cast(value, value_type, default):
    try:
        return value_type(value)
    except Exception:
        return default


@frappe.whitelist()
def get_test_coverage():
    # bench execute barista.barista.doctype.test_suite.run_test.get_test_coverage
    test_coverage_lst = []
    try:
        # barista_app_path = frappe.get_app_path('barista')
        barista_app_path = frappe.get_site_path()
        test_coverage_path = f"{barista_app_path}/public/files/test-coverage"

        process_paths(test_coverage_path, test_coverage_lst)
    except OSError as o:
        frappe.log_error(frappe.get_traceback(),
                         'barista-get_test_coverage-OSError')
        test_coverage_path = './site1.docker/public/files/test-coverage'
        process_paths(test_coverage_path, test_coverage_lst)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'barista-get_test_coverage')

    return test_coverage_lst


def process_paths(directory_path, test_coverage_lst):
    paths = sorted(Path(directory_path).iterdir(),
                   key=os.path.getmtime)

    for path in paths:
        if path.is_dir():
            path_parts = str(path).split('/')
            d = path_parts.pop()
            run_name = d.replace('__', ' ').replace('_', '-')
            test_coverage_lst.append({
                'coverage_path': f"/files/test-coverage/{d}/index.html",
                'test_run_name': run_name
            })


@frappe.whitelist()
def delete_test_coverage(run_name):
    # barista.barista.doctype.test_suite.run_test.delete_test_coverage
    try:
        run_name_path = run_name.replace(' ', '__').replace('-', '_')
        # barista_app_path = f"{frappe.get_app_path('barista')}/public/test-coverage/{run_name_path}/"
        barista_app_path = f'{frappe.get_site_path()}/public/files/test-coverage/{run_name_path}/'

        shutil.rmtree(barista_app_path, ignore_errors=True)
        frappe.db.sql('''
					delete from `tabTest Run Log` where test_run_name=%(run_name)s
		''', {'run_name': run_name}, auto_commit=1)
        frappe.db.sql('''
					delete from `tabTest Result` where test_run_name=%(run_name)s
		''', {'run_name': run_name}, auto_commit=1)
    except Exception:
        frappe.log_error(frappe.get_traceback(),
                         'barista-delete_test_coverage')


def fix_create_using():
    frappe.db.sql(
        "update `tabTest Data` set create_using='Data' where create_using is null or create_using=''", auto_commit=1)


def fix_object_type():
    frappe.db.sql(
        "update `tabFunction Parameter` set object_type='json' where object_type is null or object_type=''", auto_commit=1)
