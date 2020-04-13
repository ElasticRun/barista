from frappe import _


def get_data():
    return {
        'fieldname': 'test_suite',
        'non_standard_fieldnames': {
            'Test Result': 'test_suite'
        },
        'internal_links': {

        },
        'transactions': [
            {
                'items': ['Test Result']
            },
        ]
    }
