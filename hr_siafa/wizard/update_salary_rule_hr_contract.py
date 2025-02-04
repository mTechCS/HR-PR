from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class UpdateSalaryRuleHrContract(models.TransientModel):
    _name = "update.salary.rule.hr.contract"
    
    salary_rules_ids = fields.Many2many('hr.salary.rule',string='Salary Rules')
    
    @api.multi
    def action_remove_salary_rules(self):
        if self._context.get('active_ids',False):
            hr_contract_obj = self.env['hr.contract']
            for hr_contract in hr_contract_obj.browse(self._context['active_ids']):
                if hr_contract.struct_id:
                    if hr_contract.struct_id.rule_ids:
                        rule_ids = hr_contract.struct_id.rule_ids.ids
                        final_rule_ids= list(set(rule_ids).difference(set(self.salary_rules_ids.ids)))
                        hr_contract.struct_id.write({'rule_ids':[(6, 0, final_rule_ids)]})
        return True
    
    @api.multi
    def action_add_salary_rules(self):
        if self._context.get('active_ids',False):
            hr_contract_obj = self.env['hr.contract']
            for hr_contract in hr_contract_obj.browse(self._context['active_ids']):
                if hr_contract.struct_id:
                    rule_ids = hr_contract.struct_id.rule_ids.ids
                    final_rule_ids = list(set(rule_ids + self.salary_rules_ids.ids))
                    hr_contract.struct_id.write({'rule_ids':[(6, 0, final_rule_ids)]})
        return True
        
        
    
    