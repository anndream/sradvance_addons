# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields,osv
import openerp.addons.decimal_precision as dp

class res_partner(osv.osv):

    def _get_total_sale(self, cr, uid, ids, prop, unknow_none, context=None):
        result = {}
        for partner in self.browse(cr, uid, ids):
            total_sales = 0.0
            total_receipt = 0.0
            credit_over_limit = False
            credit_limit = 0.0
            result[partner.id] = {
                'total_sales': 0.0,
                'total_receipt': 0.0,
                'credit_over_limit': False,
            }
            partner_ids = []
            partner_ids.append(partner.id)
            if partner.parent_id: 
                partner_ids.append(partner.parent_id.id)
            if partner_ids:
                sql = """
                    select round(coalesce(sum(amount_total),0.00),2) from sale_order
                    where  state not in ('draft','cancel') and partner_id in %s                
                """ % str(tuple(partner_ids)).replace(',)',')')
                cr.execute(sql)
                total_sales = cr.fetchone()[0] or 0.0    
                sql = """
                    select round(coalesce(sum(amount),0.0),2) from account_voucher
                    where type in ('sale','receipt') and  partner_id in %s and state = 'posted'
                """ % str(tuple(partner_ids)).replace(',)',')')
                cr.execute(sql)
                total_receipt = cr.fetchone()[0] or 0.0    
                sql = """
                    select coalesce(max(credit_limit),0) from res_partner
                    where id in %s                
                """ % str(tuple(partner_ids)).replace(',)',')')
                cr.execute(sql)
                credit_limit = cr.fetchone()[0] or 0.0
                if credit_limit:             
                    credit_over_limit = credit_limit < (total_sales - total_receipt)
                else:
                    credit_over_limit = False
            result[partner.id]['credit_over_limit'] = credit_over_limit
            result[partner.id]['total_sales'] = total_sales
            result[partner.id]['total_receipt'] = total_receipt
        return result
    
    _inherit="res.partner"
    _columns={
        'round_method': fields.selection([('up','Round Up'),('no','No Round'),('down','Round Down')],string="Rounding"),
        'total_sales': fields.function(_get_total_sale, 
                type='float', digits_compute=dp.get_precision('Account'), 
                string='Total Sales', multi="_credit"),   
        'total_receipt': fields.function(_get_total_sale, 
                type='float', digits_compute=dp.get_precision('Account'), 
                string='Total Receipted', multi="_credit"),   
        'credit_over_limit': fields.function(_get_total_sale, 
                type='boolean', digits_compute=dp.get_precision('Account'), 
                string='Credit Over Limit', multi="_credit"),
    }
    
    _defaults = {
        'round_method': 'up',
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

