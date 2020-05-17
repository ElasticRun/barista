frappe.pages['test-coverage'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Test Coverage',
		single_column: true
	});

	$('head').append(`
	<style>
	table, th, td {
	  border: 1px solid black;
	}
	td,th{
		text-align:center;
		line-height: 40px;
	}
	th {
		background: lightgray;
	}
	</style>
	`);
	getTestCoverage();
	$('.ellipsis.title-text').append(`<span> <i class="fa fa-repeat" style="cursor: pointer;color: blue;" title="Click to refresh" onClick="getTestCoverage();"></i></span>`);
}

function getTestCoverage() {
	$('.row.layout-main').empty();
	frappe.call({
		method: 'barista.barista.doctype.test_suite.run_test.get_test_coverage',
		freeze: true,
		callback: function (r) {
			if (!r.exc) {
				const testCoverages = r.message;
				let srNo = 1;
				let tableContent = '';

				testCoverages.forEach(t => {
					tableContent += `
					<tr>
					<td>${srNo}</td>
					<td><a href="${t.coverage_path}" title="Click to view coverage">${t.test_run_name} <i class="fa fa-external-link"></i></a></td>
					<td><i class="fa fa-trash-o" style="color:red;cursor: pointer;scale: 2;" onClick="deleteTestCoverage('${t.test_run_name}')"></i></td>
				  </tr>
				  `;
					srNo += 1;
				})

				const table = `
				<br>
				<table id="tc-table" style="width:100%">
				<tr>
				  <th>Sr.No.</th>
				  <th>Test Run Name</th>
				  <th>Delete Test Coverage</th>
				</tr>
				${tableContent}
			  </table>
			  `;

				$('.row.layout-main').append(table);
			}
		}
	});
}

function deleteTestCoverage(run_name) {
	frappe.call({
		method: 'barista.barista.doctype.test_suite.run_test.delete_test_coverage',
		args: {
			run_name: run_name
		},
		freeze: true,
		freeze_message: `Deleting Test Coverage of Test Run ${run_name}`,
		callback: function (r) {
			if (!r.exc) {
				getTestCoverage();
			}
		}
	});
}