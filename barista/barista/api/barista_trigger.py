import frappe
import os
import math
import coverage
import shutil
import warnings
from barista.barista.doctype.test_suite.run_test import resolve_run_name
import itertools
from barista.barista.doctype.test_suite.run_test import RunTest
from frappe.desk.query_report import run
from frappe.utils.password import get_decrypted_password
import datetime

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def truncate(number, decimals=0):
    """
    Returns a value truncated to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return math.trunc(number)

    factor = 10.0 ** decimals
    return math.trunc(number * factor) / factor

@frappe.whitelist()
def barista_job():

    disable_execution = frappe.utils.cint(frappe.db.get_value('Barista Job Setting','Barista Job Setting','disable_execution'))

    if disable_execution:
      return

    # send do not refresh email
    send_do_not_refresh_mail()

    print("Barista Job Started")
    if not frappe.local.conf.developer_mode:
        return

    run_name = 'Pass-1'
    barista_job_setting = frappe.get_single("Barista Job Setting")
    app_name = [app.app_name for app in barista_job_setting.barista_app] or []
    
    suite = [suite.barista_suite for suite in barista_job_setting.barista_suite] or []

    run_name = resolve_run_name(run_name)
    run_name_path = run_name.replace(' ', '__').replace('-', '_')
    barista_app_path = f'{frappe.get_site_path()}/public/files/test-coverage/{run_name_path}/'
    # data_file_path = os.path.abspath(str(f"{barista_app_path}{app_name[0]}.coverage"))
    source_app_path = frappe.get_app_path(app_name[0])
    
    warnings.filterwarnings("ignore")

    shutil.rmtree('{barista_app_path}', ignore_errors=True)
    objCoverage = coverage.Coverage(source=[source_app_path],
                                    omit=['*test_*'],
                                    config_file=False,
                                    debug=[],
                                    data_file=None)  
                                    
    objCoverage.erase()
    objCoverage.start()

    RunTest().run_complete_suite(app_name[0], list(suite), run_name)

    objCoverage.stop()
    objCoverage.save()
    objCoverage.html_report(directory=barista_app_path,
                        skip_empty=True,
                        omit=['*test_*'])

    print("Barista Job Ended")

    send_report(run_name)

def send_report(run_name):

    disable_report = frappe.utils.cint(frappe.db.get_value('Barista Job Setting','Barista Job Setting','disable_report'))

    if disable_report:
      return

    today = datetime.date.today().strftime("%d-%b-%Y")
    barista_job_setting = frappe.get_single("Barista Job Setting")
    app_name = [app.app_name for app in barista_job_setting.barista_app] or []

    report_name = 'Test Execution Statistics'
    filters = {"app_name":app_name[0],"run_name":run_name}

    data = run(report_name, filters)
    data_list = data.get('result')

    # Get URL and name of environment
    url = barista_job_setting.url or ''
    env = barista_job_setting.platform or ''

    # Get sorting attribute to sort the test suites
    sort_att = barista_job_setting.sort_using

    if sort_att == 'Module':
      col = 1
      module_tup = frappe.db.sql("""
    SELECT DISTINCT ts.module AS 'Module' FROM `tabTest Suite` ts INNER JOIN `tabTest Result` tr ON ts.name=tr.test_suite AND tr.test_run_name='{run_name}' WHERE ts.module IS NOT NULL AND ts.module != '';""".format(run_name = run_name))
    elif sort_att == 'Workgroup':
      col = 6
      module_tup = frappe.db.sql("""
    SELECT DISTINCT ts.workgroup AS 'Workgroup' FROM `tabTest Suite` ts INNER JOIN `tabTest Result` tr ON ts.name=tr.test_suite AND tr.test_run_name='{run_name}' WHERE ts.workgroup IS NOT NULL AND ts.workgroup != '';""".format(run_name = run_name))
    elif sort_att == 'SPOC':
      col = 7
      module_tup = frappe.db.sql("""
    SELECT DISTINCT ts.spoc AS 'SPOC' FROM `tabTest Suite` ts INNER JOIN `tabTest Result` tr ON ts.name=tr.test_suite AND tr.test_run_name='{run_name}' WHERE ts.spoc IS NOT NULL AND ts.spoc != '';""".format(run_name = run_name))

    module_list = list(itertools.chain(*module_tup))
    module_cnt = len(module_list)

    # Collect the report data
    d1 = []
    d2 = []
    d3 = []
    d4 = []
    d5 = []

    suites = {}
    tc = {}
    pc = {}
    fc = {}
    per = {}

    for x in range(module_cnt):
        suites["module{0}".format(x)] = 0
        tc["module{0}".format(x)] = 0
        pc["module{0}".format(x)] = 0
        fc["module{0}".format(x)] = 0
        per["module{0}".format(x)] = 0

    for i in range(len(data_list)):
        d1.append(data_list[i][0])
        if d1[i] == None or d1[i] == '':
            d1[i] = 0

        d2.append(data_list[i][2])
        if d2[i] == None or d2[i] == '':
            d2[i] = 0
        else:
            d2[i] = round(d2[i],2)

        for x in range(module_cnt):
            if data_list[i][col] == module_list[x].upper():
                tc["module{0}".format(x)] += d2[i]
                suites["module{0}".format(x)] += 1
                break

        d3.append(data_list[i][3])
        if d3[i] == None or d3[i] == '':
            d3[i] = 0
        else:
            d3[i] = round(d3[i],2)

        for x in range(module_cnt):
            if data_list[i][col] == module_list[x].upper():
                pc["module{0}".format(x)] += d3[i]
                break

        d4.append(data_list[i][4])
        if d4[i] == None or d4[i] == '':
            d4[i] = 0
        else:
            d4[i] = round(d4[i],2)

        for x in range(module_cnt):
            if data_list[i][col] == module_list[x].upper():
                fc["module{0}".format(x)] += d4[i]
                break

        d5.append(data_list[i][5])
        if d5[i] == None or d5[i] == '':
            d5[i] = 0
        else:
            d5[i] = round(d5[i],2)

    # Collect data for the summary table
    data_list_len = len(data_list)

    if data_list[data_list_len - 1][2] == '':
      total_tc = 0
    else:
      total_tc = 0
      for x in range(module_cnt):
        total_tc += tc["module{0}".format(x)]


    if data_list[data_list_len - 1][3] == '':
      passed_tc = 0
    else:
      passed_tc = 0
      for x in range(module_cnt):
        passed_tc += pc["module{0}".format(x)]

    if data_list[data_list_len - 1][4] == '':
      failed_tc = 0
    else:
      failed_tc = 0
      for x in range(module_cnt):
        failed_tc += fc["module{0}".format(x)]

    for x in range(len(tc)):
        if tc["module{0}".format(x)]:
            per["module{0}".format(x)] = round((pc["module{0}".format(x)]/tc["module{0}".format(x)])*100,2)
    
    percentage_tot = 0
    for x in range(module_cnt):
        percentage_tot += per["module{0}".format(x)]

    percentage_fin_tot = 0
    for x in range(data_list_len):
        if data_list[x][col] in module_list:
          percentage_fin_tot += d5[x]

    suites_tot = 0
    for x in range(module_cnt):
        suites_tot += suites["module{0}".format(x)]

    percentage = round(percentage_tot / module_cnt, 2)

    percentage_fin = round(percentage_fin_tot / suites_tot, 2)

    pass_name = barista_job_setting.from_email_id[0].name

    # me == my email address
    # you == recipient's email address
    me = barista_job_setting.from_email_id[0].from_email_id
    me1 = ((me.split('@')[0]).replace('.',' ')).title()
    password = get_decrypted_password('From Email ID', pass_name, fieldname='password')
    you = [to.to_email_id for to in barista_job_setting.to_email_id] or []
    cc = [cc.cc_email_id for cc in barista_job_setting.cc_email_id] or []

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "{env} Barista Test Suites Execution Report - {today} , {run_name}".format(env = env, today = today, run_name = run_name)
    msg['From'] = me1
    msg['To'] = ", ".join(you)
    msg['Cc'] = ", ".join(cc)

    # Create the body of the message (a plain-text and an HTML version).
    text = ""
    html = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <style type="text/css">
      table {{
        background: white;
        border-radius:3px;
        border-collapse: collapse;
        height: auto;
        max-width: 900px;
        padding:5px;
        width: 100%;
        animation: float 5s infinite;
      }}
      th {{
        color:#D5DDE5;;
        background:#1b1e24;
        border-bottom: 4px solid #9ea7af;
        font-size:14px;
        font-weight: 300;
        padding:10px;
        text-align:center;
        vertical-align:middle;
      }}
      tr {{
        border-top: 1px solid #C1C3D1;
        border-bottom: 1px solid #C1C3D1;
        border-left: 1px solid #C1C3D1;
        color:#1b1e24;
        font-size:16px;
        font-weight:normal;
      }}
      td {{
        background:#FFFFFF;
        padding:10px;
        text-align:left;
        vertical-align:middle;
        font-weight:300;
        font-size:13px;
        border-right: 1px solid #C1C3D1;
      }}
    </style>
  </head>
  <body>
    Hi all,<br><br>
    Below is the {sort_att} wise summary of today's execution.<br><br>
    <table>
      <thead>
        <tr style="border: 1px solid #1b1e24;">
          <th style="background-color:#2F4F4F">{sort_att}</th>
          <th style="background-color:#2F4F4F">Total Test Cases</th>
          <th style="background-color:#2F4F4F">Passed Test Cases</th>
          <th style="background-color:#2F4F4F">Failed Test Cases</th>
          <th style="background-color:#2F4F4F">Percentage Passed</th>
        </tr>
      </thead>
      <tbody>
        <tr>
            <td><b>{module}</b></td>
            <td>{tc}</td>
            <td>{pc}</td>
            <td>{fc}</td>
            <td>{per}%</td>
        </tr>""".format(sort_att = sort_att,module = module_list[0].upper(),tc = tc["module0"],pc = pc["module0"],fc = fc["module0"],per = per["module0"])

    for x in range(1,module_cnt):
        html += """
        <tr>
            <td><b>{module}</b></td>
            <td>{tc}</td>
            <td>{pc}</td>
            <td>{fc}</td>
            <td>{per}%</td>
        </tr>""".format(module = module_list[x].upper(),tc = tc["module{0}".format(x)],pc = pc["module{0}".format(x)],fc = fc["module{0}".format(x)],per = per["module{0}".format(x)])
        
    html += """<tr>
            <td style="background-color:#D3D3D3"><b>Total</b></td>
            <td style="background-color:#D3D3D3"><b>{total_tc}</b></td>
            <td style="background-color:#D3D3D3"><b>{passed_tc}</b></td>
            <td style="background-color:#D3D3D3"><b>{failed_tc}</b></td>
            <td style="background-color:#D3D3D3"><b>{percentage}%</b></td>
        </tr>
      </tbody>
      </table><br><br>
    Below is the detailed execution result of Barista Automation as of today<br><br>
    <a href = "{url}/desk#query-report/Test%20Execution%20Statistics">Click here</a> for the Test Execution Statistics.<br>Set App as <b>{app_name}</b> and Test Run Name as <b>{run_name}</b> in filters of the report for the details.<br><br>
    <table>
      <thead>
        <tr style="border: 1px solid #1b1e24;">
          <th>{sort_att}</th>
          <th>Test Suite</th>
          <th>Total Test Cases</th>
          <th>Passed Test Cases</th>
          <th>Failed Test Cases</th>
          <th>Percentage Passed</th>
        </tr>
      </thead>
       <tbody>
         <tr>""".format(total_tc = total_tc, passed_tc = passed_tc, failed_tc = failed_tc, percentage = percentage, url = url, app_name = app_name[0], run_name = run_name, sort_att = sort_att)

    for x in range(module_cnt):
        if tc["module{0}".format(x)]:      
            html += """<td rowspan = "{ts}"><b>{module}</b></td>""".format(ts = suites["module{0}".format(x)],module = module_list[x])
    
        for i in range(len(data_list)):
            if data_list[i][col] == module_list[x].upper():
                if 100 > d5[i] >= 50:
                    tdc = '#FFB997'
                elif d5[i] < 50:
                    tdc = '#F04E4C'
                else:
                    tdc = '#FFFFFF'
                if i != len(data_list) - 1:
                    html += """
                    <td style="background-color:%s"><a href = "%s/desk#Form/Test%%20Suite/%s" style="color:inherit; display:block; text-decoration:none;">%s<a></td>
                    <td style="background-color:%s">%s</td>
                    <td style="background-color:%s">%s</td>
                    <td style="background-color:%s">%s</td>
                    <td style="background-color:%s">%s%%</td>
                    </tr>
                    <tr>
                    """%(tdc, url ,d1[i], d1[i], tdc, truncate(d2[i]), tdc, truncate(d3[i]), tdc, truncate(d4[i]), tdc, d5[i])

    for i in range(len(data_list)):
        if i == len(data_list) - 1:
              tdc = '#D3D3D3'
              html += """
                <td style="background-color:%s"><b>-</b></td>
                <td style="background-color:%s"><b>%s</b></td>
                <td style="background-color:%s"><b>%s</b></td>
                <td style="background-color:%s"><b>%s</b></td>
                <td style="background-color:%s"><b>%s</b></td>
                <td style="background-color:%s"><b>%s%%</b></td>
                </tr>
                <tr>
                """%(tdc, tdc, d1[i],tdc, total_tc,tdc, passed_tc,tdc, failed_tc,tdc, percentage_fin)

    html += """</tbody>
            </table>
        </body>
    </HTML>
    """

    # html = report.get_html()


    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)

    mail.ehlo()

    mail.starttls()

    mail.login(me, password)
    mail.send_message(msg)
    mail.quit()

    print('------------------Report sent-------------------')

def send_do_not_refresh_mail():

    barista_job_setting = frappe.get_single("Barista Job Setting")
    pass_name = barista_job_setting.from_email_id[0].name

    disable_email = frappe.utils.cint(frappe.db.get_value('Barista Job Setting','Barista Job Setting','disable_request'))

    if disable_email:
      return

    # me == my email address
    # you == recipient's email address
    # me = [from_email.from_email_id for from_email in barista_job_setting.from_email_id] or []
    me = barista_job_setting.from_email_id[0].from_email_id
    me1 = ((me.split('@')[0]).replace('.',' ')).title()
    password = get_decrypted_password('From Email ID', pass_name, fieldname='password')
    you = [to.to_email_id for to in barista_job_setting.to_email_id] or []
    cc = [cc.cc_email_id for cc in barista_job_setting.cc_email_id] or []

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Please do not Refresh Doha Environment for an Hour <EOM>"
    msg['From'] = me1
    msg['To'] = ", ".join(you)
    msg['Cc'] = ", ".join(cc)

    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)
      
    mail.ehlo()

    mail.starttls()

    mail.login(me, password)
    mail.send_message(msg)
    mail.quit()

    print('------------------Request email sent-------------------')
