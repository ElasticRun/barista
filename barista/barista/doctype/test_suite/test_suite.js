// Copyright (c) 2019, elasticrun and contributors
// For license information, please see license.txt

frappe.ui.form.on('Test Suite', {
    refresh: function(frm) {
        debugger
        cur_frm.doc.testcase.forEach((test_case) => {
            // Get the test-case row, in which 'info' button is to be added:
            let fieldDiv = $(`.frappe-control[data-fieldname='testcase']`);
            console.log(fieldDiv);
            // Check if there's a button already present:
            debugger
            if (!fieldDiv.find(`.test_case-details-${test_case.idx}`).length){
                
                // get the div at end of the row, and add a info-button-div:
                let divToAppend = fieldDiv.find(`.grid-row[data-idx=${test_case.idx}]`);
                let infoDiv = `
                    <span class="enable-history glyphicon glyphicon-info-sign test_case-${test_case.idx}" style="color: grey; float: right"></span>
                `;
                let divPresent = fieldDiv.find(
                    `.glyphicon.glyphicon-info-sign.test_case-${test_case.idx}`
                );
                
                // Prepend the info-button-div:
                if (!divPresent.length) {
                    divPresent = $(infoDiv).prependTo(divToAppend);
                    divPresent.removeClass(`test_case-${test_case.idx}`);
                }

                // Update the class name:
                let cls = `test_case-details-${test_case.idx}`;
                divPresent.addClass(`${cls}`);

                // click event listener
                $(`.${cls}`)
                .off("click")
                .on("click", () => {
                    get_test_case_info(test_case.testcase)
                    frm.refresh()
                });
            }
            
        })
    }
});

// Function to fire API to get the test case info in form of HTML:
function get_test_case_info(test_case) {
	frappe.call({
		method: "barista.barista.doctype.test_case.test_case.get_test_case_info",
		args: {
			"test_case": test_case,
		},
        freeze: true,
		freeze_message: "Getting Details",
		callback: function(r, rt){
			console.log("get-test-case-info: ", r)

            // Show dialog box with the details:
			var dialog = new frappe.ui.Dialog({
			        title: __('Details of Test Case: '+ (test_case)),
			          fields: [],

			      });
			dialog.show_message("<div style='color:#000000 !important'>"+r.message+"</div>");
			dialog.show()
			dialog.$wrapper.find('.modal-dialog').css({"width":"850px","color":""});
		}
	});
}