from frappe import _


def get_data():
    return {
        'fieldname': 'test_case',
        'non_standard_fieldnames': {
            'Test Result': 'test_case'
        },
        'internal_links': {

        },
        'transactions': [
            {
                'items': ['Test Result']
            },
        ]
    }
