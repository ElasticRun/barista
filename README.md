While developing an application using a framework like Frappe which adds most of the required paraphernalia automatically the developer is mainly required to code the business logic. And hence making functional testing one of the most important aspects.
 

We have developed a frappe application, named BARISTA, which automates testing of server-side code for all our frappe apps.

 

<h2>Overview</h2>

 

A simple manual test would require a test suite, usually a spreadsheet, on which the tester adds test cases. Each test case defines:

* Test case Name and description

* Test case Steps – Each test case would layout detailed steps to create the test data with field values and required action to test.

* Expected result - Based on the field values, expected result is specified for the tester to validate.

* Actual result - Following the steps the tester runs the test case and publishes the actual test result.

* Finally the test case is passed or failed based on actual results.
![Manual testing sample](/images/sample-manual-testcase.png)


Similarly in Barista there are four doctypes:

* **Test Suite** – declare a test suite here and select the set of test cases to run under that suite. One or more test suites can be executed based on the test scope.

 * **Test Data** – declare the application doctype here and required field values. Barista will create the record using values mentioned here while executing the test case. It also lets you select option to generate random value for the field.

* **Test Case** – Select the test data, specify the action to be triggerred like save, workflow change etc. and define assertions here like validate value of a field which is expected to change or expected error message etc.

* **Test Result** – Barista executes the test cases in a suite and publishes the result of each test case. Whether a test case passed or failed and what is the actual result for defect analysis.

![Dashboard](/images/dashboard.png)


<h2>How it works</h2>

 

Barista is installed on the same bench where the application to be tested is installed. This gives it access to the metadata of the application and its methods. While execution, it first creates the test record using values provided on test data and saves document name for further execution and assertion validation. It then triggers the action on the test data using respective frappe methods like save(). Finally, fetches all assertions (child table in Test case) of the test case and validates with the actual record.

  

**Create test data**


Simply select the doctype on which the test case has to execute. Declare required field values which will be used to create the record/document while executing the test case.


![test-data](/images/td.gif)


**Create test case**

 

Test case creation has three steps:

 

*  Select the action like create a document or update or change workflow state etc.

* Select the test data on which the above action will be triggered.

* Declare assertions to validate. When test cases are executed each assertion is validated and if any assertion fails, Barista marks test case status as failed with the details of the actual result found. Assertions can validate field value of a doctype, validate a record, validate workflow state, validate error and error message or validate response of a method.

**Create test case**

 

Test case creation has three steps:

 

*  Select the action like create a document or update or change workflow state etc.

* Select the test data on which the above action will be triggered.

* Declare assertions to validate. When test cases are executed each assertion is validated and if any assertion fails, Barista marks test case status as failed with the details of the actual result found. Assertions can validate field value of a doctype, validate a record, validate workflow state, validate error and error message or validate response of a method.

![test-result](/images/tc.gif)

**Execute and view the results**


Barista executes all test cases and saves the test results for further analysis.

**Execute and view the results**


Barista executes all test cases and saves the test results for further analysis.

![test-result](/images/test-result.gif)

<h2>Test Effectiveness</h2>

 

**Overall Code Coverage**

 

Barista uses Coverage.py  to track the coverage while test execution and publishes the detailed report which can be used to ensure test effectiveness. Higher the coverage higher is the effectiveness of the test.


**Incremental code coverage**

 

Code coverage of the new change which is going to be released is important information to verify. To achieve this we are integrating with repositories like Gitlab from where we can get details of the change in a merge request and cross verify it with the test code coverage. This can ensure the change which is getting released has been tested and is part of the test cases.

  
 

**Overall Code Coverage**

 

Barista uses Coverage.py  to track the coverage while test execution and publishes the detailed report which can be used to ensure test effectiveness. Higher the coverage higher is the effectiveness of the test.


**Incremental code coverage**

 

Code coverage of the new change which is going to be released is important information to verify. To achieve this we are integrating with repositories like Gitlab from where we can get details of the change in a merge request and cross verify it with the test code coverage. This can ensure the change which is getting released has been tested and is part of the test cases.


