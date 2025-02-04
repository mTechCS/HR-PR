from odoo import models, fields, api, _
from odoo.exceptions import UserError

class account_payment(models.Model):
    _inherit = "account.payment"
    
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payslip Batches', readonly=True, copy=False)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', readonly=True, copy=False, index=True)
    
    @api.multi
    def post(self):
        ### Customize- 1. Mark as paid in hr payslip
        res = super(account_payment, self).post()
        payslips = self.mapped('payslip_id')
        if payslips:
            payslips.write({'paid': True})
        
        return res
    
    @api.multi
    def cancel(self):
        ### Customize- 1. Mark as paid in hr payslip
        res = super(account_payment, self).cancel()
        payslips = self.mapped('payslip_id')
        if payslips:
            payslips.write({'paid': False})
        
        return res
        
        
        
        