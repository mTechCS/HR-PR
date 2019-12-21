from odoo import api, fields, models

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    employee = fields.Boolean(string='Is an Employee', default=False,
                        help="Check this box if this contact is company's employee.")
