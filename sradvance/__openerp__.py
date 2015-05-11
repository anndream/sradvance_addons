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


{
    'name': 'Extension for SR Advance Co.,Ltd.',
    'version': '0.10',
    'category': 'Extension',
    'description': """
This module will add some new requirement for SR Advance Co.,Ltd.
[__init__.py]
    - remove purchase_requisistion_wizard.py
    - remove purchase_seq.py
[purchase_requisition.py]
    - Remove purchase.requisition.line Class
    - On view_ineco_purchase_requisition_form Block All
    - Change res.partner.address -> res.partner
[purchase_seq.py] Delete
    - Comment purchase.order -> create, action_picking_create
[product.py]
    - product.product mask uom_category_id
[product_view.xml]
    - On view_sradvance_product_form (Comment Block)
    - On view_sradvance_product_form2 (Comment Block)
[sale_view.xml]
    - On view_sradvance_sale_order_form (Comment Block)
    - On view_sradvance_sale_order_inherited_form (Comment Block)
    - On view_sradvance_sale_order_inherited2_form (Comment Block)
    - On view_sradvance_sale_order_inherited3_form (Comment Block)
    - view_sradvance_sale_order_form_support (Comment Block)
    - ineco_view_sales_order_filter (Comment Block)
    - On view_sradvance2_sale_order_form_support (Comment Block)
[mrp_view.xml]
    - On ineco_mrp_production_form_view_note (Comment Block)
    - On ineco_mrp_production_form_view (Comment Block)
    - On view_ineco_mrp_production_filter (Comment Block)
[stock.py]
    - Change res.partner.address -> res.partner 
[stock_view.xml]
    - On view_inventory_sradvance_inherited_form (Comment Block)
    - On view_sradvance_picking_out_form (Comment Block)
    
    """,
    'author': 'INECO',
    'depends': [
        'product',
        'sale',
        'sale_order_dates',
        'purchase_requisition',
        'purchase',
        'mrp'],
    'website': 'http://www.ineco.co.th',
    'update_xml': [
        'security.xml',
        #'security/sradvance_security.xml',
        #'security/ir.model.access.csv',
        #'create_cost_line_wizard.xml',
        #'wizard_find_schedule_finish_date.xml',
        'thick_view.xml',
        'product_view.xml',
        'sale_view.xml',
        'mrp_view.xml',
        'purchase_requisition_view.xml',
        'mrp_workflow.xml',
        'invoice_view.xml',
        'stock_view.xml',
        'partner_view.xml',
        #'wizard/report_workorder_view.xml',
        'wizard/wizard_force_production_view.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
