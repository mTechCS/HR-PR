from odoo import fields, models, api


class HrPayrollConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    salary_payable_account_setting = fields.Many2one('account.account', string='Salary Payable Account')
    subcontractor_payable_account_setting = fields.Many2one('account.account', string='Subcontractor Payable Account')
    bank_account_journal_setting = fields.Many2one('account.journal', string='Bank Journal', domain=[('type','=','bank')])    
    cash_account_journal_setting = fields.Many2one('account.journal', string='Cash Journal', domain=[('type','=','cash')])    
#    subcontractor_account_journal_setting = fields.Many2one('account.journal', string='Subcontractor Journal', domain=[('type','in',('cash','bank'))])    
    rounding_account_setting = fields.Many2one('account.account', string='Rounding Account')
    rounding_journal_setting = fields.Many2one('account.journal', string='Journal')
#    rounding_payable_account_setting = fields.Many2one('account.account', string='Payable Account')
    
    @api.multi
    def set_bank_account_journal_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'res.config.settings', 'bank_account_journal_setting', self.bank_account_journal_setting.id, company_id=self.env.user.company_id.id)
            
    @api.multi
    def set_cash_account_journal_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'res.config.settings', 'cash_account_journal_setting', self.cash_account_journal_setting.id, company_id=self.env.user.company_id.id)
            
#    @api.multi
#    def set_subcontractor_account_journal_defaults(self):
#        return self.env['ir.values'].sudo().set_default(
#            'res.config.settings', 'subcontractor_account_journal_setting', self.subcontractor_account_journal_setting.id, company_id=self.env.user.company_id.id)
            
    @api.multi
    def set_rounding_account_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'res.config.settings', 'rounding_journal_setting', self.rounding_journal_setting.id, company_id=self.env.user.company_id.id)

    @api.multi
    def set_rounding_journal_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'res.config.settings', 'rounding_account_setting', self.rounding_account_setting.id, company_id=self.env.user.company_id.id)

#    @api.multi
#    def set_rounding_payable_account_defaults(self):
#        return self.env['ir.values'].sudo().set_default(
#            'res.config.settings', 'rounding_payable_account_setting', self.rounding_payable_account_setting.id, company_id=self.env.user.company_id.id)
            
    @api.multi
    def set_salary_payable_account_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'res.config.settings', 'salary_payable_account_setting', self.salary_payable_account_setting.id, company_id=self.env.user.company_id.id)
            
    @api.multi
    def set_subcontractor_payable_account_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'res.config.settings', 'subcontractor_payable_account_setting', self.subcontractor_payable_account_setting.id, company_id=self.env.user.company_id.id)