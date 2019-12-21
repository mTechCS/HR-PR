from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PayslipRegenrateJournalEntries(models.TransientModel):
    _name = "payslip.regenrate.journal.entries"
    
    @api.multi
    def action_regenrate_journal_entries(self):
        if self._context.get('active_ids',False):
            hr_payslip_obj = self.env['hr.payslip']
            for hr_payslip in hr_payslip_obj.browse(self._context['active_ids']):
                if not hr_payslip.move_id:
                    raise UserError(_('There is no journal entry generated for this payslip yet!!!'))
                move_name = hr_payslip.move_id.name
                hr_payslip.move_id.button_cancel()
                hr_payslip.move_id.unlink()
                hr_payslip.with_context({'move_name': move_name}).action_payslip_done()
        return True
    
    
        
        
    
    