# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _


def get_data():
    return [
        {
            "label": _("Barista"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Test Data",
                    "description": _("Test Data")
                },
                {
                    "type": "doctype",
                    "name": "Test Case",
                    "description": _("Test Case")
                },
                {
                    "type": "doctype",
                    "name": "Test Suite",
                    "description": _("Test Suite")
                },
                {
                    "type": "doctype",
                    "name": "Test Result",
                    "description": _("Test Result")
                },
                {
                    "type": "doctype",
                    "name": "Test Run Log",
                    "description": _("Test Run Log")
                }
            ]

        },
        {
            "label": "Reports",
            "items": [
                {
                     "type": "doctype",
                    "link": "query-report/Assertion Effectiveness",
                    "name": "Test Result",
                    "description": _("Assertion Effectiveness"),
                    "label": "Assertion Effectiveness"
                },
                {
                    "type": "doctype",
                    "link": "query-report/Types of Test Case on Doctype",
                    "name": "Test Result",
                    "description": _("Types of Test Case on Doctype"),
                    "label": "Types of Test Case on Doctype"
                },
                {
                    "type": "doctype",
                    "link": "query-report/Assertion Type Wise Test Cases",
                    "name": "Test Result",
                    "description": _("Assertion Type Wise Test Cases"),
                    "label": "Assertion Type Wise Test Cases"
                },
                {
                    "type": "doctype",
                    "link": "query-report/Test Execution Statistics",
                    "name": "Test Result",
                    "description": _("Test Execution Statistics"),
                    "label": "Test Execution Statistics"
                },
                {
                    "type": "doctype",
                    "link": "query-report/Test Run Log Test Data Statistics",
                    "name": "Test Result",
                    "description": _("Test Run Log Test Data Statistics"),
                    "label": "Test Run Log Test Data Statistics"
                }
            ]
        },
        {
            "label": _('Test Coverage'),
            "items": [
                {
                    'type': "doctype",
                    'name': 'Test Result',
                    'link': '#test-coverage',
                    "label": "Test Coverage"
                }
            ]
        }
    ]
