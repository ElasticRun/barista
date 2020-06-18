import click
import frappe
from frappe import _
from frappe.commands import pass_context, get_site
from barista.barista.doctype.test_suite.run_test import RunTest, resolve_run_name


@click.command('run-barista')
@click.argument('app_name')
@click.option('-r', '--run-name', default='Pass-1', help='Test Run Name for this execution run')
@click.option('-s', '--suite', multiple=True, help='Test Suite name')
@pass_context
def run_barista(context, app_name, suite=[], run_name='Pass-1'):
    site = get_site(context)
    frappe.init(site=site)
    frappe.connect(site)

    run_name = resolve_run_name(run_name)
    print('Test Run Name - ', run_name)
    RunTest().run_complete_suite(app_name, list(suite), run_name)

@click.command('clear-error-log')
@pass_context
def clear_error_log(context):
    site = get_site(context)
    frappe.init(site=site)
    frappe.connect(site)
    frappe.db.sql('TRUNCATE `tabError Log`;',auto_commit=1)
    print('`Error Log` cleared successfully')

commands = [
    run_barista,
    clear_error_log,
]
