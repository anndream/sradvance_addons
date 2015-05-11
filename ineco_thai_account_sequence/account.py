# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today INECO LTD,. PART. (<http://www.ineco.co.th>).
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



from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import time
from openerp.osv import fields, osv
#import openerp.decimal_precision as dp
from openerp.tools.translate import _

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def button_billing_no(self, cr, uid, ids, context=None):
        next_no = self.pool.get('ir.sequence').get(cr, uid, 'ineco.billing.no') or '/'
        self.write(cr, uid, ids, {'reference':next_no})
        return True

    def button_receipt_no(self, cr, uid, ids, context=None):
        next_no = self.pool.get('ir.sequence').get(cr, uid, 'ineco.receipt.no') or '/'
        self.write(cr, uid, ids, {'bill_number':next_no})
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: