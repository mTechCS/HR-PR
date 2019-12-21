from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ConfirmPayslip(models.TransientModel):
    _name = "confirm.payslip"
    
    @api.multi
    def action_payslip_confirm(self):
        if self._context.get('active_ids',False):
            hr_payslip_obj = self.env['hr.payslip']
            hr_payslip = hr_payslip_obj.browse(self._context['active_ids'])
            hr_payslip.action_payslip_done()
        return True
    
    
        
        
    
    