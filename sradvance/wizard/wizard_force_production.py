# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import fields, osv
#from openerp.tools.translate import _
#import openerp.addons.decimal_precision as dp

class allconfirm_mrp_production(osv.osv_memory):
    _name = 'allconfirm.mrp.production'
    _description = 'Confirm All Production'

    _columns = {
    }

    def confirm_all(self, cr, uid, ids, context=None):
        record_ids = context and context.get('active_ids',False)
        for record_id in record_ids:
            production = self.pool.get("mrp.production").browse(cr, uid, record_id)
            if production.state == 'draft':
                production.action_confirm()
                production.force_production()
            elif production.state == 'confirmed' or production.state == 'picking_except':
                production.force_production()
        return {}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: