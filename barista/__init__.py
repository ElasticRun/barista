# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time
import sys
import frappe
from frappe.model.rename_doc import rename_doc
from barista.barista.doctype.test_suite.run_test import RunTest, resolve_run_name


__version__ = '0.0.1'


def run(app_name, suites=[], reset_testdata=False, clear_testresult=False, run_name='Pass-1'):
    # sys.stdout = open('barista_log.txt', 'w')
    # bench execute barista.run --kwargs "{'app_name':'velocityduos','suites':[],'reset_testdata':0,'clear_testresult':0,'run_name':'Release 1'}"
    # bench execute barista.run --kwargs "{'app_name':'velocityduos'}"

    if reset_testdata and bool(reset_testdata):
        reset_test_data(suites, clear_testresult)

    run_name = resolve_run_name(run_name)
    print('Test Run Name >>> ', run_name)
    RunTest().run_complete_suite(app_name, suites, run_name)

    # sys.stdout.close()


'''
def resolve_run_name1(run_name):
    if run_name and run_name.strip() != '':

        run_name_parts1 = run_name.split('-')
        if len(run_name_parts1):
            existing_run_name = frappe.db.sql_list(f"""
                                                    SELECT max(test_run_name)
                                                    FROM
                                                (
                                                    SELECT max(test_run_name) as 'test_run_name'
                                                    FROM `tabTest Run Log`
                                                    WHERE test_run_name LIKE '%{run_name_parts1[0]}%'
                                                    UNION ALL 
                                                    SELECT max(test_run_name) AS 'test_run_name'
                                                    FROM `tabTest Result`
                                                    WHERE test_run_name LIKE '%{run_name_parts1[0]}%' 
                                                ) st
                                                    """)
            if len(existing_run_name):
                if existing_run_name[0]:
                    existing_run_name = existing_run_name[0]
                    run_name_parts = existing_run_name.split('-')
                    run_name = f'{run_name_parts1[0]}-{safe_cast(run_name_parts.pop(),int,0)+1}'

        run_name_parts2 = run_name.split(' ')
        if len(run_name_parts2):
            existing_run_name = frappe.db.sql_list(f"""
                                                    SELECT max(test_run_name)
                                                    FROM
                                                (
                                                    SELECT max(test_run_name) as 'test_run_name'
                                                    FROM `tabTest Run Log`
                                                    WHERE test_run_name LIKE '%{run_name_parts2[0]}%'
                                                    UNION ALL 
                                                    SELECT max(test_run_name) AS 'test_run_name'
                                                    FROM `tabTest Result`
                                                    WHERE test_run_name LIKE '%{run_name_parts2[0]}%' ) st
                                                    """)
            if len(existing_run_name):
                if existing_run_name[0]:
                    existing_run_name = existing_run_name[0]
                    run_name_parts = existing_run_name.split(' ')
                    run_name = f'{run_name_parts2[0]} {safe_cast(run_name_parts.pop(),int,0)+1}'
    else:
        # if run_name is not provided use default run_name as Run 1
        existing_run_name = frappe.db.sql_list("""
                                                SELECT max(test_run_name)
                                                FROM
                                                (SELECT max(test_run_name) AS 'test_run_name'
                                                FROM `tabTest Run Log`
                                                # WHERE test_run_name LIKE '%Run%'
                                                UNION ALL 
                                                SELECT max(test_run_name) AS 'test_run_name'
                                                FROM `tabTest Result`
                                                # WHERE test_run_name LIKE '%Run%' 
                                                ) st
                                                """)
        if len(existing_run_name):
            if existing_run_name[0]:
                existing_run_name = existing_run_name[0]
                run_name_parts = existing_run_name.split(' ')
                run_name = f'Run {safe_cast(run_name_parts.pop(),int,0)+1}'
            else:
                run_name = 'Run 1'

    return run_name
'''


def reset_test_data(suites=[], clear_testresult=False):
    # bench execute barista.reset_test_data --kwargs "{'suites':[]}"

    if len(suites) == 0:
        test_data_lst = frappe.db.sql_list("""
											SELECT td.name
											FROM `tabTest Data` td
											WHERE td.status='CREATED' or td.test_record_name is not NULL
											""")
        clear_test_data(test_data_lst)
    else:
        for suite in suites:
            test_data_lst = frappe.db.sql_list("""
												SELECT ti.test_data
												FROM `tabTestdata Item` ti
												INNER JOIN `tabTest Suite` ts ON ts.name=ti.parent
												INNER JOIN `tabTest Data` td ON td.name=ti.test_data
												WHERE (td.status='CREATED' or td.test_record_name is not NULL)
												AND ts.name=%(suite)s
												UNION
												select td.name as 'test_data' from `tabTest Data` td inner join `tabTest Case` tc on td.name=tc.test_data inner join `tabTestcase Item` ti on ti.testcase=tc.name inner join `tabTest Suite` ts on ts.name=ti.parent where (td.status='CREATED' or td.test_record_name is not NULL)
												AND ts.name=%(suite)s
												""", {'suite': suite})
            clear_test_data(test_data_lst, suite)

    if clear_testresult and bool(clear_testresult):
        clear_test_result()


def clear_test_result():
    print('Clearing Test Result...')
    frappe.db.sql('''TRUNCATE `tabTest Result`''', auto_commit=1)


def clear_test_data(test_data_lst, suite=None):
    total = len(test_data_lst)
    i = 0

    if suite:
        print(f'Resetting Test Data for this Test Suite ---> {suite}')

    # if total != 0:
    # 	printProgressBar(0, total, prefix='Progress:',
    # 					 suffix='Complete')
    # else:
    # 	printProgressBar(total+1, total, prefix='Progress:',
    # 					 suffix='Complete')

    for test_data in test_data_lst:

        time.sleep(0.1)

        doctype = frappe.db.get_value('Test Data', test_data, 'doctype_name')
        is_single = frappe.db.get_value('DocType', doctype, 'issingle')

        record = frappe.db.get_value(
            'Test Data', test_data, 'test_record_name')

        if is_single == 0:
            frappe.db.sql(
                f"""
				DELETE
				FROM `tab{doctype}`
				WHERE name='{record}'
				""", debug=1, auto_commit=1)

        frappe.db.set_value('Test Data', test_data, 'status', 'PENDING')
        frappe.db.set_value('Test Data', test_data, 'test_record_name', None)

        # printProgressBar(i + 1, total, prefix='Progress:',
        # 				 suffix='Complete')

    frappe.db.commit()


def ping():
    # bench execute barista.ping

    total = 10

    # Initial call to print 0% progress
    printProgressBar(0, total, prefix='Progress:',
                     suffix='Complete')
    for i in range(total):
        # Do stuff...
        time.sleep(0.1)
        # Update Progress Bar
        printProgressBar(i + 1, total, prefix='Progress:',
                         suffix='Complete')


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', printEnd="\r"):
    # Print iterations progress
    """
    Call in a loop to create terminal progress bar
    @params:
                    iteration   - Required  : current iteration (Int)
                    total       - Required  : total iterations (Int)
                    prefix      - Optional  : prefix string (Str)
                    suffix      - Optional  : suffix string (Str)
                    decimals    - Optional  : positive number of decimals in percent complete (Int)
                    length      - Optional  : character length of bar (Int)
                    fill        - Optional  : bar fill character (Str)
                    printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    if total == 0:
        total = 1

    step = int(100 * (iteration / int(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    print(f'''\r{prefix} |{bar}| {step}% {suffix}''', end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def get_commands():
    from .commands import commands as barista_commands

    return list(barista_commands)


commands = get_commands()


def update_series():
    # bench execute barista.update_series
    bs = ''
    if frappe.conf.get('barista_series'):
        bs = f"{frappe.conf.get('barista_series')}-"

    test_data_lst = frappe.get_all('Test Data')
    for test_data in test_data_lst:
        rename_doc(
            'Test Data', test_data['name'], f"{bs}{test_data['name']}", force=True)

    test_case_lst = frappe.get_all('Test Case')
    for test_case in test_case_lst:
        rename_doc(
            'Test Case', test_case['name'], f"{bs}{test_case['name']}", force=True)

    frappe.db.commit()
