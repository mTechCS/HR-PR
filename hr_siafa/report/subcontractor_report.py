from odoo import tools
from odoo import api, fields, models


class SubcontractorReport(models.Model):
    _name = "subcontractor.report"
    _description = "Subcontractor Fees Analysis"
    _auto = False
    _rec_name = 'subcontractor_id'
    
    subcontractor_id = fields.Many2one('hr.subcontractor', 'Subcontractor', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    subcontractor_fees = fields.Float("Subcontractor Fees", readonly=True)
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True)
    date = fields.Date(string='Date To', readonly=True)
    
    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT min(p.id) as id,
                c.subcontractor_id AS subcontractor_id,
                p.employee_id AS employee_id,
                c.analytic_account_id AS analytic_account_id,
                p.subcontractor_fees AS subcontractor_fees,
                p.payslip_run_id AS payslip_run_id,
                p.date_to AS date
            FROM hr_payslip p
                join hr_contract c ON (p.contract_id=c.id)
            WHERE c.subcontractor_id IS NOT NULL
            GROUP BY c.subcontractor_id,
                p.employee_id,
                c.analytic_account_id,
                p.subcontractor_fees,
                p.payslip_run_id,
                p.date_to
        )""" % (self._table,))
    
    