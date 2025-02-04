from odoo import api, fields, models, _

class ContractType(models.Model):

    _inherit = 'hr.contract.type'
    
    contractor = fields.Boolean(string='Is Subcontractor')
    

class HrSubcontractor(models.Model):

    _name = 'hr.subcontractor'
    _description = 'Subcontractor'
    
    name = fields.Char(string='Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner',required=True)
    contractor_fees = fields.Float(string='Fees (per day)', required=True, digits=0)
#    govt_fees = fields.Float(string='Govt. Fees', required=True, digits=0)
#    calc_days = fields.Integer(string='Calculation Days',default=30)
    expense_account_id = fields.Many2one('account.account', 'Expense Account')
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=[('active', '=', True)])
    
class Contract(models.Model):

    _inherit = 'hr.contract'
    
    wage_allowance = fields.Float('Other Allowance', digits=(16, 2))
    bank_wage_cash = fields.Float('Bank wage (Emp. with cash)', digits=(16, 2))
    ot_rate = fields.Float('Overtime Rate', digits=(4, 2))
    ded_rate = fields.Float('Deduction Rate', digits=(4, 2))
    subcontractor_id = fields.Many2one('hr.subcontractor', string='Subcontractor')
    is_contractor = fields.Boolean(related='type_id.contractor',string='Is Subcontractor', store=True, readonly=False)
    visa_no = fields.Char('Iqama No')
    visa_expire = fields.Date('Iqama Expire Date')
    baladiya_medical = fields.Boolean('Baladiya Medical')
    baladiya_medical_expire = fields.Date('Baladiya Medical Expire Date')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=False)
    journal_id = fields.Many2one('account.journal', 'Salary Journal', required=False)
    
    @api.multi    
    def write(self, vals):
        ### Customize: subcontractor_id,type_id
        # print'writeee@@@@@@valvals',vals
        vals_key = vals.keys()
        
        employee_vals = {}
        if 'employee_id' in vals_key:
            if 'subcontractor_id' in vals_key:
                subcontractor_id = vals['subcontractor_id']
            else:
                subcontractor_id = self.subcontractor_id
            employee_vals.update({'subcontractor_id':subcontractor_id})
            
            if 'type_id' in vals_key:
                type_id = vals['type_id']
            else:
                type_id = self.type_id
            employee_vals.update({'contract_type_id':type_id})  
            # print'employee_vals',employee_vals
            self.env['hr.employee'].browse(vals['employee_id']).write(employee_vals)
        elif 'employee_id' not in vals_key:
            if 'subcontractor_id' in vals_key:
                employee_vals.update({'subcontractor_id':vals['subcontractor_id']})
            if 'type_id' in vals_key:
                employee_vals.update({'contract_type_id':vals['type_id']})
            # print'employee_vals',employee_vals
            self.employee_id.write(employee_vals)  
            
        res = super(Contract, self).write(vals)
        return res
    
    @api.model
    def create(self, vals):
        ### Customize: subcontractor_id,type_id
        # print'create@@@',vals
        vals_key = vals.keys()
        employee_vals = {}
        if 'subcontractor_id' in vals_key:
            subcontractor_id = vals['subcontractor_id']
        else:
            subcontractor_id = False
        employee_vals.update({'subcontractor_id':subcontractor_id})

        if 'type_id' in vals_key:
            type_id = vals['type_id']
        else:
            type_id = False
        employee_vals.update({'contract_type_id':type_id})  
        self.env['hr.employee'].browse(vals['employee_id']).write(employee_vals)
        res = super(Contract, self).create(vals)
        return res
    