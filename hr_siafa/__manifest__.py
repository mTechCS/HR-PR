# -*- coding: utf-8 -*-
{
    'name': "hr_siafa",

    'summary': """
    """,

    'description': """
        HR Customization for Siafa
        Comment hr_payroll.HRPayslip.unlink()
    """,

    'author': "Aasim Ahmed Ansari",
    'website': "http://aasimania.wordpress.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr','hr_contract','hr_payroll','hr_payroll_account','account','report_xlsx','ohrms_loan'],

    # always loaded
    'data': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'wizard/hr_payroll_payslips_by_employees_views.xml',
        'views/res_config_views.xml',
        'views/hr_report.xml',
        'views/hr_contract_views.xml',
        'views/hr_views.xml',
        'views/hr_holidays_views.xml',
        'views/hr_payroll_views.xml',
        'views/res_partner_view.xml',
        'views/account_payment_view.xml',
        'views/templates.xml',
        'views/report_payslip_templates.xml',
        'views/bank_salary_head_views.xml',
        'views/emp_grade_view.xml',
        'wizard/update_salary_rule_hr_contract_views.xml',
        'wizard/confirm_payslip_views.xml',
        'wizard/generate_bank_transfer_sheet_views.xml',
        'wizard/payslip_regenrate_journal_entries_views.xml',
        'report/subcontractor_report_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}