# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-Today INECO LTD., Part. (<http://www.ineco.co.th>).
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


{
    'name' : 'INECO THAI Accounting Sequence',
    'version' : '0.1',
    'depends' : ["ineco_thai_account"],
    'author' : 'INECO LTD.,PART.',
    'category': 'Accounting',
    'description': """
Feature: 
1. Add Billing Number Button (Auto Sequence)
2. Add Reeipt Number Button (Auto Sequence)
    """,
    'website': 'http://www.ineco.co.th',
    'data': [
        'sequence.xml',
    ],
    'update_xml': [
        'account_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'images': [],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
