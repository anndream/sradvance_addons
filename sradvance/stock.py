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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from operator import itemgetter
from itertools import groupby

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
from openerp import tools
import openerp.addons.decimal_precision as dp
import logging

class stock_inventory_line(osv.osv):

    def _get_width_product(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.product_id.product_width
        return res

    def _get_length_product(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.product_id.product_length
        return res

    _inherit = "stock.inventory.line"
    _description = "Extended for Inventory Line"
    _columns = {
        'product_width': fields.function(_get_width_product, method=True, string='Width', digits_compute= dp.get_precision('Sale Price')),
        'product_length': fields.function(_get_length_product, method=True, string='Length', digits_compute= dp.get_precision('Sale Price')),
    }

class stock_picking(osv.osv):
    
    _inherit = 'stock.picking'
    _columns = {
        'ineco_delivery_date': fields.date('Actual Delivery Date'),
        'partner_invoice_id': fields.many2one('res.partner','Invoice Address'),
    }
    _defaults = {
        'ineco_delivery_date': False,
    }


class stock_picking_out(osv.osv):
    _inherit = "stock.picking.out"
    _description = "change create invoice"    
    _columns = {
        'ineco_delivery_date': fields.date('Actual Delivery Date'),
        'problem_note': fields.char('Problem', size=100),
        'partner_invoice_id': fields.many2one('res.partner','Invoice Address'),
    }
    _defaults = {
        'ineco_delivery_date': False,
        'problem_note': False,
    }
    
    def sradvanced_action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        if context is None:
            context = {}

        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        #address_obj = self.pool.get('res.partner.address')
        address_obj = self.pool.get('res.partner')
        invoices_group = {}
        res = {}
        inv_type = type
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.invoice_state != '2binvoiced':
                continue
            payment_term_id = False
            partner =  picking.address_id and picking.address_id.partner_id
            if not partner:
                raise osv.except_osv(_('Error, no partner !'),
                    _('Please put a partner on the picking list if you want to generate invoice.'))

            if not inv_type:
                inv_type = self._get_invoice_type(picking)

            if inv_type in ('out_invoice', 'out_refund'):
                account_id = partner.property_account_receivable.id
                payment_term_id = self._get_payment_term(cr, uid, picking)
            else:
                account_id = partner.property_account_payable.id

            address_contact_id, address_invoice_id = \
                    self._get_address_invoice(cr, uid, picking).values()
            address = address_obj.browse(cr, uid, address_contact_id, context=context)

            comment = self._get_comment_invoice(cr, uid, picking)
            if group and partner.id in invoices_group:
                invoice_id = invoices_group[partner.id]
                invoice = invoice_obj.browse(cr, uid, invoice_id)
                invoice_vals = {
                    'name': (invoice.name or '') + ', ' + (picking.name or ''),
                    'origin': (invoice.origin or '') + ', ' + (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
                    'comment': (comment and (invoice.comment and invoice.comment+"\n"+comment or comment)) or (invoice.comment and invoice.comment or ''),
                    'date_invoice':context.get('date_inv',False),
                    'user_id':uid
                }
                invoice_obj.write(cr, uid, [invoice_id], invoice_vals, context=context)
            else:
                invoice_vals = {
                    'name': picking.name,
                    'origin': (picking.name or '') + (picking.origin and (':' + picking.origin) or ''),
                    'type': inv_type,
                    'account_id': account_id,
                    'partner_id': address.partner_id.id,
                    'address_invoice_id': address_invoice_id,
                    'address_contact_id': address_contact_id,
                    'comment': comment,
                    'payment_term': payment_term_id,
                    'fiscal_position': partner.property_account_position.id,
                    'date_invoice': context.get('date_inv',False),
                    'company_id': picking.company_id.id,
                    'user_id':uid
                }
                cur_id = self.get_currency_id(cr, uid, picking)
                if cur_id:
                    invoice_vals['currency_id'] = cur_id
                if journal_id:
                    invoice_vals['journal_id'] = journal_id
                invoice_id = invoice_obj.create(cr, uid, invoice_vals,
                        context=context)
                invoices_group[partner.id] = invoice_id
            res[picking.id] = invoice_id
            for move_line in picking.move_lines:
                if move_line.state == 'cancel':
                    continue
                origin = move_line.picking_id.name or ''
                if move_line.picking_id.origin:
                    origin += ':' + move_line.picking_id.origin
                if group:
                    name = (picking.name or '') + '-' + move_line.name
                else:
                    name = move_line.name

                if inv_type in ('out_invoice', 'out_refund'):
                    account_id = move_line.product_id.product_tmpl_id.\
                            property_account_income.id
                    if not account_id:
                        account_id = move_line.product_id.categ_id.\
                                property_account_income_categ.id
                else:
                    account_id = move_line.product_id.product_tmpl_id.\
                            property_account_expense.id
                    if not account_id:
                        account_id = move_line.product_id.categ_id.\
                                property_account_expense_categ.id

                price_unit = self._get_price_unit_invoice(cr, uid,
                        move_line, inv_type)
                discount = self._get_discount_invoice(cr, uid, move_line)
                tax_ids = self._get_taxes_invoice(cr, uid, move_line, inv_type)
                account_analytic_id = self._get_account_analytic_invoice(cr, uid, picking, move_line)

                #set UoS if it's a sale and the picking doesn't have one
                uos_id = move_line.product_uos and move_line.product_uos.id or False
                if not uos_id and inv_type in ('out_invoice', 'out_refund'):
                    uos_id = move_line.product_uom.id

                account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, partner.property_account_position, account_id)
                invoice_line_id = invoice_line_obj.create(cr, uid, {
                    'name': name,
                    'origin': origin,
                    'invoice_id': invoice_id,
                    'uos_id': uos_id,
                    'product_id': move_line.product_id.id,
                    'account_id': account_id,
                    'price_unit': price_unit,
                    'discount': discount,
                    'quantity': move_line.product_uos_qty or move_line.product_qty,
                    'invoice_line_tax_id': [(6, 0, tax_ids)],
                    'account_analytic_id': account_analytic_id,
                    'product_width': move_line.sale_line_id.sr_width or 0.0,
                    'product_length': move_line.sale_line_id.sr_length or 0.0,
                }, context=context)
                self._invoice_line_hook(cr, uid, move_line, invoice_line_id)

            invoice_obj.button_compute(cr, uid, [invoice_id], context=context,
                    set_total=(inv_type in ('in_invoice', 'in_refund')))
            self.write(cr, uid, [picking.id], {
                'invoice_state': 'invoiced',
                }, context=context)
            self._invoice_hook(cr, uid, picking, invoice_id)
        self.write(cr, uid, res.keys(), {
            'invoice_state': 'invoiced',
            }, context=context)
        return res

class stock_move(osv.osv):

    def _get_length(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.sale_line_id.sr_length or 0.0
        return res

    def _get_width(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.sale_line_id.sr_width or 0.0
        return res

    def _action_explode(self, cr, uid, move, context=None):
        """ Explodes pickings.
        @param move: Stock moves
        @return: True
        """
        bom_obj = self.pool.get('mrp.bom')
        move_obj = self.pool.get('stock.move')
        procurement_obj = self.pool.get('procurement.order')
        product_obj = self.pool.get('product.product')
        wf_service = netsvc.LocalService("workflow")
        processed_ids = [move.id]
        if move.product_id.supply_method == 'produce' and move.product_id.procure_method == 'make_to_order':
            bis = bom_obj.search(cr, uid, [
                ('product_id','=',move.product_id.id),
                ('bom_id','=',False),
                ('type','=','phantom')])
#             if bis:
#                 factor = move.product_qty
#                 bom_point = bom_obj.browse(cr, uid, bis[0], context=context)
#                 res = bom_obj._bom_explode(cr, uid, bom_point, factor, [])
#                 state = 'confirmed'
#                 if move.state == 'assigned':
#                     state = 'assigned'
#                 for line in res[0]: 
#                     valdef = {
#                         'picking_id': move.picking_id.id,
#                         'product_id': line['product_id'],
#                         'product_uom': line['product_uom'],
#                         'product_qty': line['product_qty'],
#                         'product_uos': line['product_uos'],
#                         'product_uos_qty': line['product_uos_qty'],
#                         'move_dest_id': move.id,
#                         'state': state,
#                         'name': line['name'],
#                         'move_history_ids': [(6,0,[move.id])],
#                         'move_history_ids2': [(6,0,[])],
#                         'procurements': [],
#                     }
#                     mid = move_obj.copy(cr, uid, move.id, default=valdef)
#                     processed_ids.append(mid)
#                     prodobj = product_obj.browse(cr, uid, line['product_id'], context=context)
#                     proc_id = procurement_obj.create(cr, uid, {
#                         'name': (move.picking_id.origin or ''),
#                         'origin': (move.picking_id.origin or ''),
#                         'date_planned': move.date,
#                         'product_id': line['product_id'],
#                         'product_qty': line['product_qty'],
#                         'product_uom': line['product_uom'],
#                         'product_uos_qty': line['product_uos'] and line['product_uos_qty'] or False,
#                         'product_uos':  line['product_uos'],
#                         'location_id': move.location_id.id,
#                         'procure_method': prodobj.procure_method,
#                         'move_id': mid,
#                     })
#                     wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
#                 move_obj.write(cr, uid, [move.id], {
#                     'location_dest_id': move.location_id.id, # dummy move for the kit
#                     'auto_validate': True,
#                     'picking_id': False,
#                     'state': 'confirmed'
#                 })
#                 for m in procurement_obj.search(cr, uid, [('move_id','=',move.id)], context):
#                     wf_service.trg_validate(uid, 'procurement.order', m, 'button_confirm', cr)
#                     wf_service.trg_validate(uid, 'procurement.order', m, 'button_wait_done', cr)
        return processed_ids

    _inherit = "stock.move"
    
    _columns = {
        #'product_length': fields.function(_get_length, method=True, store=True, string="Length", type="float"),
        #'product_width': fields.function(_get_width, method=True, store=True, string="Width", type="float"),        
        'product_width': fields.related('sale_line_id', 'sr_width',  string='Width', store=True, type='float'),
        'product_length': fields.related('sale_line_id', 'sr_length',  string='Length', store=True, type='float'),
        'sale_product_description': fields.related('sale_line_id', 'name',  string='Sale Description', store=True, size=256, type='char'),
    }

class stock_partial_picking(osv.osv_memory):

    def _partial_move_for(self, cr, uid, move):
        partial_move = {
            'product_id' : move.product_id.id,
            'quantity' : move.product_qty if move.state in ('assigned','draft','confirmed') else 0,
            'product_uom' : move.product_uom.id,
            'prodlot_id' : move.prodlot_id.id,
            'move_id' : move.id,
            'location_id' : move.location_id.id,
            'location_dest_id' : move.location_dest_id.id,
            'delivery_description': move.name,
            'product_length': move.product_length,
            'product_width': move.product_width,
        }
        #print 'Move ID %s' % move.id
        if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
            partial_move.update(update_cost=True, **self._product_cost_for_average_update(cr, uid, move))
        return partial_move

    _inherit = "stock.partial.picking"
    
class stock_partial_picking_line(osv.TransientModel):

    def _get_length(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            print "Move ID ", line.move_id.id
            res[line.id] = line.move_id.sale_line_id.sale_line_id.sr_length or 0.0
        return res

    def _get_width(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.move_id.sale_line_id.sr_width or 0.0
        return res

    _inherit = "stock.partial.picking.line"
    _columns = {
        'delivery_description': fields.char('Description', size=256),
        'product_width': fields.integer('Width'),
        'product_length': fields.integer('Length'),
    }
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
