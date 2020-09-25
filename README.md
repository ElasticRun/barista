<div align="center"> <h1><strong> BARISTA </h1></strong></div>
<div align="center"> Frappe App Testing Framework </div>

---
## Table of contents :
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Material](#material)
- [License](#license)

#### Installation
- Clone : `bench get-app https://engg.elasticrun.in/sancharun/barista.git --branch=master`
- Install : `bench install-app barista`
- Confirm Installation : `./env/bin/pip install -e apps/barista`
- Wrapping up Installation : 
    - `bench build`
    - `bench setup requirements`
    - `bench migrate`

### Getting Started
- Basic Structure : Add Test Case(s) to Test Suite. Test Data or Pre-Test Data are optional. Test Results + Test Run Log is connected to Test Suite.
- Command to execute : `bench run-barista <app-name> -s <test-suite-name>` *Not setting the '-s' arg will run all the available Test Suites.*
- Debugging : Test Run Log (Barista Module), Test Result (Barista Module), Error Log
- <ins>For detailed documentation </ins>[Check the Wiki for this project.](https://engg.elasticrun.in/sudhanshu.kulkarni/barista/-/wikis/home)
### Material
- [Official Overview](https://discuss.erpnext.com/t/automating-functional-testing-of-frappe-apps-by-frappe-app/60274)
- [Frappe Developer API docs](https://frappeframework.com/docs/user/en/api)
- [Frappe Developer Cheatsheet](https://github.com/frappe/frappe/wiki/Developer-Cheatsheet)

#### License

MIT
