from odoo import api, fields, models, _
from odoo.exceptions import UserError

class BankSalaryHead(models.Model):

    _name = "bank.salary.head"
    _order = 'sequence'
    
    sequence = fields.Integer(help='Used to order bank salary heads', default=10)
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', string='Company')