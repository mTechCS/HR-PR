from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract

class BankTransferXlsx(ReportXlsxAbstract):

    def generate_xlsx_report(self, workbook, data, lines):
        # print "inside generate_xlsx_report: ", data
        sheet = workbook.add_worksheet()
        header = workbook.add_format({'bold': True, 'font_size': 18})
        payslip_batch_ids = data['result']
        df_payslip_summary = self.env['bank.transfer.sheet']._fetch_payslip_summary(payslip_batch_ids)
        prec = self.env['decimal.precision'].precision_get('Payroll')
        sheet.write(0, 0, 'Sr. No.')
        sheet.write(0, 1, 'Employee ID')
        sheet.write(0, 2, 'Present Days')
        sheet.write(0, 3, 'Employee Account No/IBAN')
        sheet.write(0, 4, 'Employee Name')
        sheet.write(0, 5, 'Bank Code')

        sheet.set_column(1, 2, 15)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 50)
        sheet.set_column(5, 5, 15)

        bank_salary_heads = [h['name'] for h in self.env['bank.salary.head'].search_read([], ['name'])]

        column_index = 6
        category_columns_index = {}
        for each_salary_head in bank_salary_heads:
            sheet.write(0, column_index, each_salary_head)
            category_columns_index[each_salary_head] = column_index
            column_index += 1
        sheet.write(0, column_index, 'Total')
        category_columns_index['Total'] = column_index

        sheet.set_column(6, column_index, 20)

        row_index = 1
        for payslip, salary_data in df_payslip_summary.iterrows():
            salary_amount = salary_data['Total']
            employee = payslip.employee_id
            sheet.write(row_index, 0, str(row_index))
            sheet.write(row_index, 1, employee.identification_id or employee.passport_id)
            sheet.write(row_index, 2, payslip.worked_days)
            sheet.write(row_index, 3, employee.bank_account_id.acc_number)
            sheet.write(row_index, 4, employee.name)
            sheet.write(row_index, 5, employee.bank_account_id.bank_id.bic)

            total = 0
            for each_salary_head in bank_salary_heads:
                head_amount = round(salary_amount.get(each_salary_head, 0.0), prec)
                total += head_amount
                sheet.write(row_index, category_columns_index[each_salary_head], head_amount)

            sheet.write(row_index, category_columns_index['Total'], round(total, prec))
            row_index += 1

# BankTransferXlsx('report.hr_siafa.bank_transfer_xlsx.xlsx', 'bank.transfer.sheet')