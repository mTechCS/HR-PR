from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import float_compare, float_is_zero
from odoo.tools.float_utils import float_round
import logging
import pandas as pd
from datetime import datetime

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    @api.model
    def create(self, values):
        if not values.get('payslip_run_id',False):
            raise UserError(_('You can create payslip only through batch!!!'))
        return super(HrPayslip, self).create(values)

    @api.multi
    def unlink(self):
        # print "context: ", self._context
        active_model = self._context['params'].get('model',False) or self._context.get('active_model',False) or False
        if not active_model == 'hr.payslip.run':
            raise UserError(_('Payslip can only be deleted from Batch when in draft state!'))

        if self.env['hr.payslip.run'].browse(self._context['active_id']).state != 'draft':
            raise UserError(_('Payslip can only be deleted from Batch when in draft state!'))

        payment = self.env['account.payment']
        done_payslips = self.filtered(lambda payslip: payslip.state == 'done')
        # print "done_payslips: ",done_payslips
        for payslip in done_payslips:
            # print "******Payslip*******",payslip.number
#            try:
#            if True:
            ### Delete payment
            payment = payment.search([('payslip_id','=',payslip.id)])
            payment.cancel()
            payment = payment.filtered(lambda p: p.name == 'Draft Payment')
            payment_del = payment.unlink()
            # print "payment_del: ", payment_del

            ### Delete salary journal entry
            payslip.move_id.button_cancel()
            move_del = payslip.move_id.unlink()
            # print "move_del: ", move_del

            if payslip.loan_line_ids:
                payslip.loan_line_ids.mapped('hr_loan_line_id').write({'paid': False, 'payslip_id': False})

            if move_del and payment_del:
                self._cr.execute("DELETE FROM hr_payslip WHERE id=%s",(payslip.id,))
#            except Exception, e:
#                print "Exception: ",e
#                continue
        return super(HrPayslip, self).unlink()

    @api.one
    @api.depends('line_ids')
    def _wage_net(self):
        """ Fetches Net Salary from Salary Computation"""
        self.wage_net = sum(self.line_ids.filtered(lambda l: l.code == 'NET').mapped('amount'))
        
    @api.one
    @api.depends('line_ids')
    def _bank_wage_net(self):
        """ Fetches Bank Salary from Salary Computation"""
        self.bank_wage_net = sum(self.line_ids.filtered(lambda l: l.code not in ('NET','GROSS') and not l.salary_rule_id.is_cash_payment).mapped('amount'))
        
    @api.one
    @api.depends('state')
    def _subcontractor_fees(self):
        """ Fetches Subcontractor Fees from Salary Computation"""
        fees = 0.0
        if not self.contract_id.type_id.contractor:
            self.subcontractor_fees = fees
            return True
            
        elif self.state != 'done':
            self.subcontractor_fees = fees
            return True
            
        no_of_hours_worked = 1.0 #sum(self.attendance_line_ids.mapped('number_of_hours'))
        calendar_uom = self.employee_id.calendar_id.uom_id
        hours_per_day = calendar_uom.factor
        rounding = calendar_uom.rounding
        no_of_days_worked = float_round(no_of_hours_worked / hours_per_day, precision_rounding=rounding)
        
        self.subcontractor_fees = float_round(self.contract_id.subcontractor_id.contractor_fees * no_of_days_worked, precision_digits=2)

    # @api.one
    # @api.depends('attendance_line_ids.number_of_hours')
    # def _worked_days(self):
    #     # print "_worked_days"
    #     no_of_hours_worked = sum(self.attendance_line_ids.mapped('number_of_hours'))
    #     calendar_uom = self.employee_id.calendar_id.uom_id
    #     hours_per_day = calendar_uom.factor
    #     rounding = calendar_uom.rounding
        
    #     if hours_per_day <= 0.0:
    #         self.worked_days = 0.0
    #         return False

    #     self.worked_days = float_round(no_of_hours_worked / hours_per_day, precision_rounding=rounding)

        
    wage_net = fields.Float("Net Wage", compute='_wage_net', store=True)
    bank_wage_net = fields.Float("Bank Wage", compute='_bank_wage_net')
    subcontractor_fees = fields.Float("Subcontractor Fees", compute='_subcontractor_fees', store=True)
    worked_days = fields.Float("Worked Days")

    @api.multi
    def action_payslip_done(self):
        ### Custom: 1. Calling compute_sheet only if compute_also is set in context
        ### 2. Analytic account pulling from contract
        ### 3. Merging all definition of function here
        ### 4. Fetching partner directly from employee's home address
        # print "self._context: ",self._context
        if self._context.get('compute_also',False):
            self.compute_sheet()
        
        precision = self.env['decimal.precision'].precision_get('Payroll')
        
        ir_values = self.env['ir.values']
        company_id = self.env.user.company_id.id
        salary_payable_account_id = ir_values.get_default('res.config.settings', 'salary_payable_account_setting', company_id=company_id)
        if not salary_payable_account_id:
            action = self.env.ref('hr_payroll.action_hr_payroll_configuration')
            msg = _('You should configure salary payable account. \nPlease go to Payroll Configuration.')
            raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
        
        subcontractor_payable_account_id = ir_values.get_default('res.config.settings', 'subcontractor_payable_account_setting', company_id=company_id)
        if not subcontractor_payable_account_id:
            action = self.env.ref('hr_payroll.action_hr_payroll_configuration')
            msg = _('You should configure subcontractor payable account. \nPlease go to Payroll Configuration.')
            raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

        for slip in self:
            _logger.info("Marking Payslip as done: %s", slip.name)
            
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to

            name = _('Payslip of %s') % (slip.employee_id.name)
            move_dict = {
                'narration': name,
                'ref': (slip.payslip_run_id and slip.payslip_run_id.name + ' / ' or '') + slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
            }
            if self._context.get('move_name',False):
                move_dict.update({'name': self._context['move_name']})
            
            payable_account_id = subcontractor_payable_account_id if slip.contract_id.subcontractor_id else salary_payable_account_id
            
            for line in slip.details_by_salary_rule_category:
                if not line.salary_rule_id.account_debit:
                    continue
                    
                amount = slip.credit_note and -line.total or line.total
                _logger.info("action_payslip_done amount: %s", amount)
                _logger.info("action_payslip_done line: %s", line)
                
                if float_is_zero(amount, precision_digits=precision):
                    continue
                    
                partner = line._get_emp_partner_id()
                if not partner:
                    raise UserError(_('Partner not configured for employee: %s') % (slip.employee_id.name))
                
                debit_account_id = amount > 0.0 and line.salary_rule_id.account_debit.id or payable_account_id
                credit_account_id = amount > 0.0 and payable_account_id or line.salary_rule_id.account_debit.id
                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': partner.id,
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amount > 0.0 and amount or -amount or 0.0,
                        'credit': 0.0,
                        'analytic_account_id': not line.salary_rule_id.ignore_analytic_account_id and amount > 0.0 and slip.contract_id.analytic_account_id.id or False,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': partner.id,
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': 0.0,
                        'credit': amount > 0.0 and amount or -amount or 0.0,
                        'analytic_account_id': not line.salary_rule_id.ignore_analytic_account_id and amount < 0.0 and slip.contract_id.analytic_account_id.id or False,
                        'tax_line_id': line.salary_rule_id.account_tax_id.id,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)

            move_dict['line_ids'] = line_ids
            # print "line_ids: ",line_ids
            move = self.env['account.move'].create(move_dict)
            slip.write({'move_id': move.id, 'date': date})
            move.post()

            paid_lines = slip.loan_line_ids.filtered(lambda l: l.paid)
            paid_lines.mapped('hr_loan_line_id').write({'paid': True, 'payslip_id': slip.id})
            unpaid_lines = slip.loan_line_ids - paid_lines
            # print "paid_lines: ",paid_lines
            # print "unpaid_lines: ",unpaid_lines
            unpaid_lines.unlink()
#        aaa
        return self.write({'state': 'done'})
    
class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'
    
    is_cash_payment = fields.Boolean(related='salary_rule_id.is_cash_payment', string='Cash Payment')
    
    def _get_emp_partner_id(self):
        ### Customize- Return partner_id from employee's Home address
        partner_id = self.slip_id.employee_id.address_home_id
        return partner_id or False
    
class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    name = fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False, index=True, default=lambda self: _('New'))
    description = fields.Char(required=True, readonly=True, states={'draft': [('readonly', False)]})
    payment_ids = fields.One2many('account.payment', 'payslip_run_id', string='Payments', readonly=True, domain=[('state','!=','cancel')])
    payment_count = fields.Integer(compute='_payment_count', string='# Payment')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('post', 'Post'),
        ('close', 'Close'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    
    @api.multi
    @api.depends('payment_ids')
    def _payment_count(self):
        for batch in self:
            batch.payment_count = len(self.payment_ids)

    @api.model
    def create(self, vals):
        # print "create vals: ",vals
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'hr.payslip.run') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.payslip.run') or _('New')

        result = super(HrPayslipRun, self).create(vals)
        return result
    
    @api.multi
    def action_view_payment(self):
        action = self.env.ref('account.action_account_payments_payable').read()[0]
        action['domain'] = [('payslip_run_id', 'in', self.ids)]
        return action
    
    @api.multi
    def action_view_paylsip(self):
        action = self.env.ref('hr_payroll.action_view_hr_payslip_form').read()[0]
        action['domain'] = [('payslip_run_id', 'in', self.ids)]
        return action
    
    @api.multi
    def close_payslip_run(self):
        ### Customize- 1. Make all draft payslips as done
        ### 2. Generate bank and cash payment
        self.write({'state': 'post'})
        if not self.slip_ids:
            raise UserError(_("No Payslip added."))
        todo_slips = self.slip_ids.filtered(lambda s: s.state in ('draft','verify'))
        todo_slips.action_payslip_done()
        
        ### Generate vendor payments
        # print'todo_slips',todo_slips
        self._generate_outbound_payment(todo_slips)
        
        return True
    
    @api.multi
    def regenerate_payment(self):
        # print "inside regenerate_payment"
        done_payslips = self.slip_ids.filtered(lambda payslip: payslip.state == 'done')
        todo_slips = self.env['hr.payslip']
        payment = self.env['account.payment']
        for payslip in done_payslips:
            payments = payment.search([('payslip_id','=',payslip.id)])
            if payments:
                for payment in payments:
                    if payment.state == 'cancel':
                        todo_slips |= payslip
            else:
               todo_slips |= payslip     
                
        self._generate_outbound_payment(todo_slips)
        return True

    @api.multi
    def compute_close_payslip_run(self):
        if not self.slip_ids:
            raise UserError(_("No Payslip added."))

        res = super(HrPayslipRun, self).with_context({'compute_also': True}).close_payslip_run()
        return res
    
    def _get_payment_vals(self, payslip, journal_id, amount, payment_type, payment_method_id):
        # print "inside _get_payment_vals"
        return {
            'payslip_run_id': self.id,
            'payslip_id': payslip.id,
            'amount': amount,
            'payment_date': self.date_end,
            'communication': payslip.payslip_run_id.name + ": " + payslip.name ,
            'partner_id': payslip.employee_id.address_home_id.id,
            'partner_type': 'supplier',
            'journal_id': journal_id,
            'payment_type': payment_type,
            'payment_method_id': payment_method_id,
        }

    @api.multi
    def lock_payslip_run(self):
        ### Generate rounding entry if any
        self._generate_rounding_entry()

        ### Generate subcontractor bills
#        self._generate_subcontractor_bill(self.slip_ids)
        return self.write({'state': 'close'})

    def _create_subcontractor_bill(self, subcontractor, fees, total_wage, description_fees, description_wage):
        if fees <= 0:
            return False

        journal = self.env['account.invoice'].with_context({'type': 'in_invoice'})._default_journal()
        currency = self.env['account.invoice'].with_context({'type': 'in_invoice'})._default_currency()
        
        if not (subcontractor.expense_account_id and subcontractor.tax_id):
            raise UserError(_('No Expense Account or Tax configured. \nSubcontractor: %s') % subcontractor.name)
        
        invoice_vals = {
            'name': self.name,
            'date_invoice': self.date_end,
            'type': 'in_invoice',
            'account_id': subcontractor.partner_id.property_account_payable_id.id,
            'partner_id': subcontractor.partner_id.id,
            'journal_id': journal.id,
            'currency_id': currency.id,
            'company_id': self.env.user.company_id.id,
        }
        invoice = self.env['account.invoice'].create(invoice_vals)

        InvoiceLine = self.env['account.invoice.line']
        ### Fees
        line_vals = {
            'name': description_fees,
            'account_id': subcontractor.expense_account_id.id,
            'price_unit': fees,
            'quantity': 1.0,
            'invoice_line_tax_ids': [(6, 0, subcontractor.tax_id.ids)],
            'invoice_id': invoice.id
        }
        InvoiceLine.create(line_vals)
        ### Wage
        line_vals = {
                'name': description_wage,
                'account_id': subcontractor.expense_account_id.id,
                'price_unit': total_wage,
                'quantity': 1.0,
                'invoice_line_tax_ids': [(6, 0, subcontractor.tax_id.ids)],
                'invoice_id': invoice.id
        }
        InvoiceLine.create(line_vals)
        invoice._onchange_invoice_line_ids()
        return True
    
    def _generate_subcontractor_bill(self, slip_ids):
        ### Customize: We are not generating now as we are giving them report
        # print "inside _generate_subcontractor_bill"
        subcontractor_slips = slip_ids.filtered(lambda s: s.contract_id.type_id.contractor)
        df_value = [(s.contract_id.subcontractor_id,s.subcontractor_fees,s.bank_wage_net) for s in subcontractor_slips]
        df_sc_fees = pd.DataFrame(data=df_value)
        df_sc_fees.columns = ['Subcontractor','Fees','Net Wage']
        df_sc_fees = df_sc_fees.groupby('Subcontractor').sum().reset_index()
        # print "df_sc_fees: ", df_sc_fees

        year = datetime.strftime(datetime.strptime(self.date_end, '%Y-%m-%d'), '%Y')
        month = datetime.strftime(datetime.strptime(self.date_end, '%Y-%m-%d'), '%b')
        description_fees = 'Fees for the month of ' + month + ', ' + year
        description_wage = 'Salary for the month of ' + month + ', ' + year
        for index,row in df_sc_fees.iterrows():
            subcontractor = row['Subcontractor']
            fees = row['Fees']
            total_wage = row['Net Wage']
            self._create_subcontractor_bill(subcontractor, fees, total_wage, description_fees, description_wage)

        return True
        
    def _generate_outbound_payment(self, slip_ids):
        # print "inside _generate_outbound_payment"
        ir_values = self.env['ir.values']
        account_journal = self.env['account.journal']
        company_id = self.env.user.company_id.id
        
        ### Check if all employee related partner has right payable account set
        salary_payable_account_id = ir_values.get_default('res.config.settings', 'salary_payable_account_setting', company_id=company_id)
        if not salary_payable_account_id:
            action = self.env.ref('hr_payroll.action_hr_payroll_configuration')
            msg = _('You should configure salary payable account. \nPlease go to Payroll Configuration.')
            raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
        partner_with_incorrect_payable_acc = slip_ids.mapped('employee_id').mapped('address_home_id').filtered(lambda p: p.property_account_payable_id.id != salary_payable_account_id)
        # print "partner_with_incorrect_payable_acc: ",partner_with_incorrect_payable_acc
        partner_with_incorrect_payable_acc.write({'property_account_payable_id': salary_payable_account_id})
                
        bank_account_journal_id = ir_values.get_default('res.config.settings', 'bank_account_journal_setting', company_id=company_id)
        if not bank_account_journal_id:
            action = self.env.ref('hr_payroll.action_hr_payroll_configuration')
            msg = _('You should configure bank journal. \nPlease go to Payroll Configuration.')
            raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
        bank_journal = account_journal.browse(bank_account_journal_id)
        
        cash_account_journal_id = ir_values.get_default('res.config.settings', 'cash_account_journal_setting', company_id=company_id)
        if not cash_account_journal_id:
            action = self.env.ref('hr_payroll.action_hr_payroll_configuration')
            msg = _('You should configure cash journal. \nPlease go to Payroll Configuration.')
            raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
        cash_journal = account_journal.browse(cash_account_journal_id)
                
#        subcontrator_account_journal_id = ir_values.get_default('res.config.settings', 'subcontractor_account_journal_setting', company_id=company_id)
#        if not subcontrator_account_journal_id:
#            action = self.env.ref('hr_payroll.action_hr_payroll_configuration')
#            msg = _('You should configure subcontractor journal. \nPlease go to Payroll Configuration.')
#            raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
#        subcontractor_journal = account_journal.browse(subcontrator_account_journal_id)
        
        payment_type = self.credit_note and 'inbound' or 'outbound'
        if payment_type == 'inbound':
            payment_method = self.env.ref('account.account_payment_method_manual_in')
            bank_journal_payment_methods = bank_journal.inbound_payment_method_ids
            cash_journal_payment_methods = cash_journal.inbound_payment_method_ids
#            subcontractor_journal_payment_methods = subcontractor_journal.inbound_payment_method_ids
        else:
            payment_method = self.env.ref('account.account_payment_method_manual_out')
            bank_journal_payment_methods = bank_journal.outbound_payment_method_ids
            cash_journal_payment_methods = cash_journal.outbound_payment_method_ids
#            subcontractor_journal_payment_methods = subcontractor_journal.outbound_payment_method_ids

        if (payment_method not in bank_journal_payment_methods):
            raise UserError(_('No appropriate payment method enabled on journal %s') % bank_journal.name)
        elif (payment_method not in cash_journal_payment_methods):
            raise UserError(_('No appropriate payment method enabled on journal %s') % cash_journal.name)
#        elif (payment_method not in subcontractor_journal_payment_methods):
#            raise UserError(_('No appropriate payment method enabled on journal %s') % subcontractor_journal.name)
        
        account_payment = self.env['account.payment']
        for payslip in slip_ids:
            if payslip.contract_id.subcontractor_id: ### No payment for contractor employee
                continue
                
            account_payment = account_payment.search([('payslip_run_id','=',self.id),('payslip_id','=',payslip.id),('state','!=','cancel')])
            if account_payment:
                continue
                
            cash_salary_lines = payslip.line_ids.filtered(lambda l: l.salary_rule_id.is_cash_payment == True)
            cash_amount = sum([l.total for l in cash_salary_lines])
            
            ### Create Cash Payment
            if cash_amount >  0.0:
                payment_vals = self._get_payment_vals(payslip, cash_journal.id, round(cash_amount), payment_type, payment_method.id)
                cash_payment = account_payment.create(payment_vals)

            bank_amount = payslip.wage_net - round(cash_amount) if cash_amount > 0.0 else payslip.wage_net
            
            if round(bank_amount) > 0.0:
                payment_vals = self._get_payment_vals(payslip, bank_journal.id, round(bank_amount), payment_type, payment_method.id)
                bank_payment = account_payment.create(payment_vals)

        return True

    def _generate_rounding_entry(self):
        rounding_amount = 0.0
        for slip in self.slip_ids:
            rounding_amount += round(slip.wage_net) - slip.wage_net
        # print "rounding_amount: ",rounding_amount
        if rounding_amount:
            ir_values = self.env['ir.values']
            company_id = self.env.user.company_id.id
            rounding_account_id = ir_values.get_default('res.config.settings', 'rounding_account_setting', company_id=company_id)
            if not rounding_account_id:
                action = self.env.ref('hr_payroll.action_hr_payroll_configuration')
                msg = _('You should configure rounding account. \nPlease go to Payroll Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            rounding_journal_id = ir_values.get_default('res.config.settings', 'rounding_journal_setting', company_id=company_id)
            if not rounding_journal_id:
                action = self.env.ref('hr_payroll.action_hr_payroll_configuration')
                msg = _('You should configure rounding journal. \nPlease go to Payroll Configuration.')
                raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))

            rounding_payable_account_id = ir_values.get_default('res.config.settings', 'salary_payable_account_setting', company_id=company_id)

            self._create_account_move_entry(rounding_journal_id, rounding_account_id, rounding_payable_account_id, rounding_amount)

        return True

    def _create_account_move_entry(self, journal_id, rounding_account_id, payable_account_id, rounding_amount):
        debit_line_vals = {
            'name': self.name,
            'debit': rounding_amount if rounding_amount > 0 else 0,
            'credit': -rounding_amount if rounding_amount < 0 else 0,
            'account_id': rounding_account_id,
        }
        credit_line_vals = {
            'name': self.name,
            'credit': rounding_amount if rounding_amount > 0 else 0,
            'debit': -rounding_amount if rounding_amount < 0 else 0,
            'account_id': payable_account_id,
        }
        move_lines = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
        new_account_move = self.env['account.move'].sudo().create({
            'ref': 'Rounding for Batch: ' + self.name,
            'journal_id': journal_id,
            'date': self.date_end,
            'line_ids': move_lines,
        })
        new_account_move.post()
        return True



class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    account_debit = fields.Many2one('account.account', 'Expense Account', domain=[('deprecated', '=', False)])
    bank_salary_head_id = fields.Many2one('bank.salary.head', 'Bank Salary Head')
    is_cash_payment = fields.Boolean('Cash Payment')
    ignore_analytic_account_id = fields.Boolean('Ignore Analytic Account')
    structure_ids = fields.Many2many('hr.payroll.structure', 'hr_structure_salary_rule_rel', 'rule_id', 'struct_id',
                                string='Salary Structures')