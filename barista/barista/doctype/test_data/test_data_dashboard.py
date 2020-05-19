from frappe import _


def get_data():
    return {
        'fieldname': 'test_data',
        'non_standard_fieldnames': {
            'Test Case': 'test_data',
            'Test Result': 'test_data_id',
        },
        'internal_links': {

        },
        'transactions': [
            {
                'items': ['Test Case', 'Test Run Log'],
            },
            {
                'items': ['Test Result']
            },
        ]
    }
