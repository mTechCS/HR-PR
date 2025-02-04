from odoo import api, fields, models, _
from odoo.exceptions import UserError

class Employee(models.Model):

    _inherit = "hr.employee"
    
    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        res = super(Employee, self).toggle_active()
        for record in self:
            record.address_home_id.toggle_active()
        return res
    
    @api.model
    def create(self, vals):
        # print'vals',vals
#        if 'address_home_id' in vals:
#            if len(self.sudo().search([('address_home_id','=',vals['address_home_id'])])):
#                raise UserError(_('Related partner already exist.'))
            
        address_home_vals={
            'name':vals['name'].strip()+' (E)',
            'employee':True,
            'supplier':True,
            'company_id':vals['company_id']
        }
        vals['address_home_id'] = self.env['res.partner'].create(address_home_vals).id
        
        return super(Employee, self).create(vals)
    
    @api.multi
    def write(self, vals):
        
        if 'name' in vals:
            self.address_home_id.write({'name':vals['name'].strip()+' (E)'})
        if 'address_home_id' in vals:
            if len(self.sudo().search([('address_home_id','=',vals['address_home_id']),('id','!=',self.id)])):
                raise UserError(_('Related partner already exist.'))
        return super(Employee, self).write(vals)
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('name', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('code', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('code', operator, name)] + args, limit=limit)
        if not recs:
            recs = self.search([('identification_id', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('identification_id', operator, name)] + args, limit=limit)
        return recs.name_get()
    
    
    code = fields.Char('Code')
    identification_id = fields.Char(string='Identification No', groups='hr.group_hr_user', required=True)
    medical = fields.Boolean('Medical')
    iqama_fees = fields.Boolean('New Iqama Fees')
    insurance = fields.Boolean('Insurance')
    contract_prep = fields.Boolean('Contract Preparation')
    bank_atm_expire = fields.Date('ATM Card Expire Date')
    address_home_id = fields.Many2one('res.partner', string='Related Partner',domain="[('employee','=',True)]")
    contract_type_id = fields.Many2one('hr.contract.type', string="Contract Type", readonly=True)
    subcontractor_id = fields.Many2one('hr.subcontractor', string="Subcontractor", readonly=True)
    is_contractor = fields.Boolean(related='contract_id.type_id.contractor',string='Is Subcontractor',readonly=True)
    emp_grade = fields.Many2one('emp.grade', string="Grade", readonly=False)
    
    
    _sql_constraints = [
        ('identification_id_uniq', 'unique (identification_id)', 'The identification number must be unique !')
    ]