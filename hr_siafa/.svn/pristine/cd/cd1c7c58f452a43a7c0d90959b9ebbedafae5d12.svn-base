from odoo import api, fields, models

class EmpGrade(models.Model):

    _name = 'emp.grade'
    _description = 'Employee Grade'

    name = fields.Char('Grade', required=True)
    code = fields.Char('Code', required=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)',
         'The code of the device must '
         'be unique!'),
        ('name_uniq', 'unique (name)',
         'The Grade must '
         'be unique!')
    ]
