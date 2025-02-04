from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract

class ExportBankFileXlsx(ReportXlsxAbstract):

    def generate_xlsx_report(self, workbook, data, lines):
        # print "inside generate_xlsx_report: ", data
        sheet = workbook.add_worksheet()
        header = workbook.add_format({'bold': True, 'font_size': 18})
#        payslip_batch_ids = data['result']
#        df_payslip_summary = self.env['bank.transfer.sheet']._fetch_payslip_summary(payslip_batch_ids)
#        unique_payslips = df_payslip_summary.index.get_level_values(0).unique().tolist()
#        unique_categories = df_payslip_summary.index.get_level_values(1).unique().tolist()
#
#        sheet.write(0, 0, 'Sr. No.')
#        sheet.write(0, 1, 'Employee ID')
#        sheet.write(0, 2, 'Present Days')
#        sheet.write(0, 3, 'Employee Account No/IBAN')
#        sheet.write(0, 4, 'Employee Name')
#        sheet.write(0, 5, 'Bank Code')
#        column_index = 6
#        category_columns_index = {}
#        for category in unique_categories:
#            category_columns_index[category] = column_index
#            sheet.write(0, column_index, category)
#            column_index += 1
#        sheet.write(0, 5 + len(unique_categories) + 1, 'Total')
#
#        row_index = 1
#        for payslip in unique_payslips:
#            employee = payslip.employee_id
#            sheet.write(row_index, 0, str(row_index))
#            sheet.write(row_index, 1, employee.identification_id or employee.passport_id)
#            sheet.write(row_index, 2, payslip.worked_days)
#            sheet.write(row_index, 3, employee.bank_account_id.bank_id.iban_code)
#            sheet.write(row_index, 4, employee.name)
#            sheet.write(row_index, 5, employee.bank_account_id.bank_id.bic)
#            total = 0
#            for category in unique_categories:
#                categ_value = df_payslip_summary.loc[(payslip,category)]['Total']
#                total += categ_value
#                sheet.write(row_index, category_columns_index[category], categ_value)
#
#            sheet.write(row_index, 5 + len(unique_categories) + 1, str(total))
#            row_index += 1

# ExportBankFileXlsx('report.hr_siafa.export_bank_file_xlsx.xlsx', 'export.bank.file')