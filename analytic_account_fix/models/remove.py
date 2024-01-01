from odoo import models, fields, api
from collections import defaultdict
from odoo.osv import expression

class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    @api.depends('line_ids.amount')
    def _compute_debit_credit_balance(self):
        Curr = self.env['res.currency']
        analytic_line_obj = self.env['account.analytic.line']
        domain = [
            ('account_id', 'in', self.ids),
            ('company_id', 'in', [False] + self.env.companies.ids)
        ]
        if self._context.get('from_date', False):
            domain.append(('date', '>=', self._context['from_date']))
        if self._context.get('to_date', False):
            domain.append(('date', '<=', self._context['to_date']))
        if self._context.get('tag_ids'):
            tag_domain = expression.OR([[('tag_ids', 'in', [tag])] for tag in self._context['tag_ids']])
            domain = expression.AND([domain, tag_domain])

        user_currency = self.env.company.currency_id
        credit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '>=', 0.0)],
            fields=['account_id', 'currency_id', 'amount'],
            groupby=['account_id', 'currency_id'],
            lazy=False,
        )
        data_credit = defaultdict(float)
        for l in credit_groups:
            currency_id = l['currency_id'] and l['currency_id'][0] or False
            if currency_id:
                data_credit[l['account_id'][0]] += Curr.browse(currency_id)._convert(
                    l['amount'], self.env.company.currency_id, self.env.company, fields.Date.today())

        debit_groups = analytic_line_obj.read_group(
            domain=domain + [('amount', '<', 0.0)],
            fields=['account_id', 'currency_id', 'amount'],
            groupby=['account_id', 'currency_id'],
            lazy=False,
        )
        data_debit = defaultdict(float)
        for l in debit_groups:
            currency_id = l['currency_id'] and l['currency_id'][0] or False
            if currency_id:
                data_debit[l['account_id'][0]] += Curr.browse(currency_id)._convert(
                    l['amount'], self.env.company.currency_id, self.env.company, fields.Date.today())
        for account in self:
            account.debit = abs(data_debit.get(account.id, 0.0))
            account.credit = data_credit.get(account.id, 0.0)
            account.balance = account.credit - account.debit
