from odoo import api, fields, models
import math

class HolidaysType(models.Model):
    _inherit = "hr.holidays.status"
    
    ignore_holdays = fields.Boolean('Count Weekends',
        help='If you select this check box, the system will consider weekends and company holidays '
             'in calculating number of leaves.')
             
class Holidays(models.Model):
    _inherit = "hr.holidays"
    
    def _get_number_of_days(self, date_from, date_to, employee_id):
        res = super(Holidays, self)._get_number_of_days(date_from, date_to, employee_id)
        if not self.holiday_status_id:
            return res
        
        if self.holiday_status_id.ignore_holdays:
            weekends_count = 0
            if employee_id:
                employee = self.env['hr.employee'].browse(employee_id)
                weekends_count = employee.calendar_id.count_weekends(date_from, date_to)
                # print "_get_number_of_days res weekends_count: ",res, weekends_count
            
            return res + weekends_count
        
        return res