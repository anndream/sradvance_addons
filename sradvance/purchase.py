# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

#import time
#from datetime import datetime
#from dateutil.relativedelta import relativedelta

from openerp.osv import osv
#from openerp import netsvc
#import openerp.pooler
#from openerp.tools.translate import _
#import decimal_precision as dp

class purchase_order(osv.osv):

    _name = "purchase.order"
    _description = "Extended for OMG Holding (Thailand) Co,.Ltd."
    _inherit = "purchase.order"
    _defaults = {
        'name': '/',
    }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
