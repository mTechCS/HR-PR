from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import pandas as pd
_logger = logging.getLogger(__name__)

class BankTransferSheet(models.TransientModel):
    _name = "bank.transfer.sheet"

    def _fetch_payslip_summary(self, payslip_batch_ids):
        payslip_batches = self.env['hr.payslip.run'].browse(payslip_batch_ids)

        payslip_lines = payslip_batches.mapped('slip_ids').mapped('line_ids').filtered(lambda l: l.salary_rule_id.bank_salary_head_id)
        if not payslip_lines:
            raise UserError(_('Please set bank salary head in salary rules.'))
        df_data = [(l.slip_id,l.salary_rule_id.bank_salary_head_id.name,l.total)  for l in payslip_lines]

        df_payslip_line = pd.DataFrame(data=df_data, columns=['Payslip', 'Category', 'Total'])

        df_payslip_summary = df_payslip_line.groupby(['Payslip', 'Category']).sum()
        df_payslip_summary = pd.pivot_table(df_payslip_summary, index=['Payslip'], columns=['Category'])
        df_payslip_summary.fillna(0.0, inplace=True)
        return df_payslip_summary
    
    def generate_bank_sheet(self):
        # print "inside generate_bank_sheet: ",self._context
        # result = df_payslip_summary.to_json(orient='index')
        # print "result: ",result

        datas = {'ids': self._context.get('active_ids', [])}
        datas['model'] = 'bank.transfer.sheet'
        datas['form'] = self.read()[0]
        datas['result'] = self._context.get('active_ids', [])
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hr_siafa.bank_transfer_xlsx.xlsx',
            'datas': datas,
            'name': 'BankTransfer'
        }

        # Use this to iterate in xls file
        # unique_payslips = df_payslip_line['Payslip'].unique()
        # unique_categories = df_payslip_line['Category'].unique()
        #for each_payslip in unique_payslips:
        #    for each_category in unique_categories:
        #        total = df_payslip_summary.loc[(each_payslip,each_category)]

