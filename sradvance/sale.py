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

# 13-02-2012    POP-001    Add Delivery Date in Delivery Order.
#               POP-002    ADd Delivery Date in Production.
# 14-05-2012    POP-003    Add Sale Line Id IN MRP.PRODUCTION

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import netsvc
import math
from operator import itemgetter

class sale_order_line_addtionalcost(osv.osv):

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        pricelist_obj = self.pool.get('product.pricelist')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'price_unit_sale': 0.0,
                'price_subtotal': 0.0,
            }
            price_unit = pricelist_obj.price_get(cr, uid, [line.order_line_id.order_id.pricelist_id.id], line.product_id.id, 1.0, line.order_line_id.order_id.partner_id.id, {'date': line.order_line_id.order_id.date_order, 'uom': line.product_id.uom_id.id })[line.order_line_id.order_id.pricelist_id.id]
            price = price_unit * (1 - (line.discount or 0.0) / 100.0) * line.product_qty
            cur = line.order_line_id.order_id.pricelist_id.currency_id            
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, price)
            res[line.id]['price_unit_sale'] = cur_obj.round(cr, uid, cur, price_unit)
        return res

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        pricelist_obj = self.pool.get('product.pricelist')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            price_unit = pricelist_obj.price_get(cr, uid, [line.order_line_id.order_id.pricelist_id.id], line.product_id.id, 1.0, line.order_line_id.order_id.partner_id.id, {'date': line.order_line_id.order_id.date_order, 'uom': line.product_id.uom_id.id })[line.order_line_id.order_id.pricelist_id.id]
            price = price_unit * (1 - (line.discount or 0.0) / 100.0) * line.product_qty
            cur = line.order_line_id.order_id.pricelist_id.currency_id            
            res[line.id] = cur_obj.round(cr, uid, cur, price)
        return res

    def _price_unit_line(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        pricelist_obj = self.pool.get('product.pricelist')
        res = {}
        if context is None:
            context = {}         
        for line in self.browse(cr, uid, ids, context=context):
            price_unit = pricelist_obj.price_get(cr, uid, [line.order_line_id.order_id.pricelist_id.id], line.product_id.id, 1.0, line.order_line_id.order_id.partner_id.id, {'date': line.order_line_id.order_id.date_order, 'uom': line.product_id.uom_id.id })[line.order_line_id.order_id.pricelist_id.id]            
            cur = line.order_line_id.order_id.pricelist_id.currency_id            
            res[line.id] = cur_obj.round(cr, uid, cur, price_unit)
        return res

    _name = "sale.order.line.addtionalcost"
    _description = "Addtional Cost for SR Advance Co.,Ltd."

    _columns = {
        'order_line_id': fields.many2one('sale.order.line','Order Line Reference', ondelete='cascade'),
        'name': fields.char('Description', size=256, required=True, select=True),
        'product_id': fields.many2one('product.product', 'Product', ondelete='restrict'),
        'product_qty': fields.float('Quantity', digits=(16, 3), required=True ),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure ', required=True, ondelete='restrict'),
        'price_unit': fields.float('Base Price', required=True, digits_compute = dp.get_precision('Sale Price')),
        'price_unit_sale': fields.function(_amount_all, string='Sale Price', 
                                           digits_compute= dp.get_precision('Sale Price'), multi='sums',
                                           store={
                                                'sale.order.line.addtionalcost': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                                           },), #store=True
        'discount': fields.float('Discount (%)', digits=(16, 3), readonly=True),
        'price_subtotal': fields.function(_amount_all, string='Subtotal', 
                                          store={
                                                'sale.order.line.addtionalcost': (lambda self, cr, uid, ids, c={}: ids, [], 10),
                                          },
                                          digits_compute= dp.get_precision('Sale Price'), multi='sums'), #store=True
        'pricelist_id' : fields.many2one('product.pricelist', 'pricelist', ondelete='restrict'),
        'w1': fields.boolean('W1'),
        'w2': fields.boolean('W2'),
        'l1': fields.boolean('L1'),
        'l2': fields.boolean('L2'),
    }

    _defaults = {
        'discount': 0.0,
        'product_qty': 1,
        'price_unit': 1.0,
        'pricelist_id': lambda self, cr, uid, c: c.get('pricelist_id', False),
        'w1': True,
        'w2': True,
        'l1': True,
        'l2': True,
    }

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def onchange_myproduct_id(self, cr, uid, ids, context, product_id, w1, w2, l1, l2):
        v = {}
        ft2 = 0.0
        value1 = 0.0
        value2 = 0.0
        pid = context['sale_product_id']
        width = context['myWidth']
        length = context['myLength']
        if w1: 
            value1 = value1 + width
        if w2:
            value1 = value1 + width
        if l1:
            value2 = value2 + length
        if l2:
            value2 = value2 + length
        #change date: 07/10/2011
        #m2 = round((value1/1000) + (value2/1000),2)
        m2 = (value1/1000) + (value2/1000)
        if width and length:
            #change date: 07/10/2011
            #ft2 = round((width * length) / (304.79 * 304.79),2)
            ft2 = (width * length) / (304.79 * 304.79)
        #context = {'lang': lang}
        context = {}
        if product_id and pid :
            product = self.pool.get('product.product').browse(cr, uid, product_id)
            v['product_uom'] = product.uom_id.id
            v['name'] = self.pool.get('product.product').name_get(cr, uid, [product_id], context=context)[0][1] #product.name
            v['price_unit'] = product.lst_price
            sale_product_id = self.pool.get('product.product').browse(cr, uid, pid)
            new_qty = 1.0
            if sale_product_id:
                if product.product_use_ft2 :
                    new_qty = ft2 or 1.0 
                if product.product_use_m2 :
                    new_qty = m2 or 1.0        
            v['product_qty'] = new_qty 

        return {'value': v}

class sale_order(osv.osv):

    def _prepare_order_picking(self, cr, uid, order, context=None):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        return {
            'name': pick_name,
            'origin': order.name,
            'date': order.effective_date,
            'type': 'out',
            'state': 'auto',
            'move_type': order.picking_policy,
            'sale_id': order.id,
            'partner_id': order.partner_shipping_id.id,
            'note': order.note,
            'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
            'company_id': order.company_id.id,
            'ineco_delivery_date': order.date_finished,
            'partner_invoice_id': order.partner_invoice_id.id
        }

    def _prepare_order_line_move(self, cr, uid, order, line, picking_id, date_planned, context=None):
        location_id = order.shop_id.warehouse_id.lot_stock_id.id
        output_id = order.shop_id.warehouse_id.lot_output_id.id
        return {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'product_packaging': line.product_packaging.id,
            'partner_id': line.address_allotment_id.id or order.partner_shipping_id.id,
            'location_id': location_id,
            'location_dest_id': output_id,
            'sale_line_id': line.id,
            'tracking_id': False,
            'state': 'draft',
            #'state': 'waiting',
            'company_id': order.company_id.id,
            'price_unit': line.product_id.standard_price or 0.0,
            #ST Advance
            'note': line.line_note,        
        }

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        """Create the required procurements to supply sales order lines, also connecting
        the procurements to appropriate stock moves in order to bring the goods to the
        sales order's requested location.

        If ``picking_id`` is provided, the stock moves will be added to it, otherwise
        a standard outgoing picking will be created to wrap the stock moves, as returned
        by :meth:`~._prepare_order_picking`.

        Modules that wish to customize the procurements or partition the stock moves over
        multiple stock pickings may override this method and call ``super()`` with
        different subsets of ``order_lines`` and/or preset ``picking_id`` values.

        :param browse_record order: sales order to which the order lines belong
        :param list(browse_record) order_lines: sales order line records to procure
        :param int picking_id: optional ID of a stock picking to which the created stock moves
                               will be added. A new picking will be created if ommitted.
        :return: True
        """
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []
        seq = 1
        start_time = time.time()
        for line in order_lines:
            #print "Line %s start %f" % (line.id, time.time())
            if line.state == 'done':
                continue

            #date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)
            date_planned = line.order_id.effective_date

            if line.product_id:
                if line.product_id.type in ('product', 'consu'):
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
                    move_obj.write(cr, uid, move_id, {'name': line.name+'#'+'%02d' % (seq,)})
                else:
                    # a service has no stock move
                    move_id = False

                proc_id = procurement_obj.create(cr, uid, self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context))
                proc_ids.append(proc_id)
                line.write({'procurement_id': proc_id})
                self.ship_recreate(cr, uid, order, line, move_id, proc_id)

                #check with addition cost Line
                if line.product_id:
                    if line.additional_line:
                        #new additional cost for create bom 
                        routing_obj = self.pool.get('mrp.routing')
                        routing_id = routing_obj.create(cr, uid, {
                            'code': order.name,
                            'name': 'Process of '+line.product_id.name_template                            
                        })
                        master_bom_obj = self.pool.get('mrp.bom')
                        master_bom_id = master_bom_obj.create(cr, uid, {
                            'name': line.product_id.name_template ,
                            'product_id': line.product_id.id,
                            'code': order.name,
                            'product_qty': 1,
                            'product_uom': line.product_uom.id,
                            'type': 'normal',
                            'routing_id': routing_id, #map routing to new bom
                        })
                        if order.requested_date:
                            #production_date = order.plan_ids[0].date_start
                            #production_date = datetime.strptime(order.requested_date, '%Y-%m-%d')
                            production_date = datetime.now().replace(microsecond=0)
                        else:
                            production_date = datetime.now() + relativedelta(days=line.product_id.sale_delay) - relativedelta(days=1)
                        hour_total = 0
                        for additional_line in line.additional_line :
                            #print "Line %s Additional Line %02d" % (line.id, int(time.time() - start_time))
                            bom_ids = self.pool.get('mrp.bom').search(cr, uid, 
                                [('product_id', '=', additional_line.product_id.id),('routing_id','!=',False)], context=None)
                            bom_obj = self.pool.get('mrp.bom').browse(cr, uid, bom_ids,context=None)                            
                            #print "Line %s Bom Search Line %02d" % (line.id, int(time.time() - start_time))
                            if bom_obj:
                                #routing_id = bom_obj[0].routing_id.id
                                routing = self.pool.get('mrp.routing').browse(cr, uid, bom_obj[0].routing_id.id, context=None)                                
                                #print routing
                                if routing:
                                    #print "Line %s Routing %02d" % (line.id, int(time.time() - start_time))
                                    for wkline in routing.workcenter_lines:
                                        product_id_new = additional_line.product_id
                                        workcenter_id_new = wkline.workcenter_id
                                        dt_from = production_date #datetime.strptime(production_date[:10], '%Y-%m-%d')
                                        dt_to = production_date #datetime.strptime(production_date[:10], '%Y-%m-%d')
                                        #print "%s %s" % (dt_from, dt_to)
                                        hour_caps = wkline.workcenter_id.resource_id.calendar_id.ineco_interval_hours_get(dt_from, dt_to )

                                        hour = 0
                                        capacity = None
                                        if workcenter_id_new and product_id_new:
                                            capacity_ids = self.pool.get('ineco.workcenter.capacity').search(cr, uid, [('workcenter_id','=',workcenter_id_new.id),('categ_id','=',product_id_new.categ_id.id)])
                                            if capacity_ids:
                                                capacity = self.pool.get('ineco.workcenter.capacity').browse(cr, uid, capacity_ids)[0]
                                                hour = additional_line.product_qty / capacity.cycle_per_hour or 0.00     
                                                hour_total = (line.product_uom_qty * additional_line.product_qty) / capacity.cycle_per_hour or 0.00   
                                        day = math.floor(hour_total / hour_caps) or 1.0 #Default 1 Days
                                        #print day, hour, hour_caps, dt_from, dt_to
                                        #print abc
                                        day_sec = hour_total % hour_caps       
                                        loop = 0
                                        workcenter_line_obj = self.pool.get('mrp.routing.workcenter')
                                        #Disable Capacity per workcenter
                                        while loop < day:                     
                                            if capacity:
                                                cycle_nbr = capacity.cycle_per_hour * (((hour_total - day_sec ) / line.product_uom_qty) / day)
                                            else:
                                                cycle_nbr = 0.0
                                            workcenter_line_id = workcenter_line_obj.create(cr, uid, {
                                                'routing_id': routing_id,
                                                'sequence': (int(wkline.sequence) * 10) + loop,
                                                #'name': wkline.name + "-"+additional_line.product_id.name+"-Day " + str(loop+1) or "",
                                                'name': additional_line.product_id.name_template.replace(u'ค่า','',1)+"-Day " + str(loop+1) or "",                                                
                                                'workcenter_id' : wkline.workcenter_id.id or False,
                                                'cycle_nbr': cycle_nbr,
                                                'hour_nbr': ((hour_total - day_sec ) / line.product_uom_qty) / day , #hour
                                            })
                                            loop += 1
                                        if day_sec:
                                            if capacity:
                                                cycle_nbr = capacity.cycle_per_hour * (day_sec / line.product_uom_qty)
                                            else:
                                                cycle_nbr = 0.0
                                            workcenter_line_id = workcenter_line_obj.create(cr, uid, {
                                                'routing_id': routing_id,
                                                'sequence': (int(wkline.sequence) * 10) + loop,
                                                'name': additional_line.product_id.name_template.replace(u'ค่า','',1)+"-Day " + str(loop+1) or "",                                                
                                                'workcenter_id' : wkline.workcenter_id.id or False,
                                                'cycle_nbr': cycle_nbr,
                                                'hour_nbr': day_sec / line.product_uom_qty , #hour
                                            })
                                            
                            #disable semigoods in new boms
                            if additional_line.product_id.type == 'product' and additional_line.product_id.supply_method == 'buy' and additional_line.product_qty > 0 :                                
                                child_bom_obj = self.pool.get('mrp.bom')
                                child_bom_id = child_bom_obj.create(cr, uid, {
                                    'name': additional_line.product_id.name_template ,
                                    'product_id': additional_line.product_id.id,
                                    'code': order.name,
                                    'product_qty': additional_line.product_qty,
                                    'product_uom': additional_line.product_uom.id,
                                    #'routing_id' : routing_id,
                                    'type': 'normal',
                                    'bom_id': master_bom_id,
                                })
                        mrp_order_obj = self.pool.get('mrp.production')
                        stock_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal'),('name','=','Stock')], context=None)
                        stock_location_obj = self.pool.get('stock.location').browse(cr, uid,stock_location_ids,context=None)[0]
                        sticker_note = ''
                        if order.sticker_note:
                            sticker_note = order.sticker_note
                        if line.line_note: 
                            sticker_note = sticker_note + line.line_note 
                        mrp_order_id = mrp_order_obj.create(cr, uid, {
                            #must change date planned after scheduling
                            'name': order.name+'#'+'%02d' % (seq,),
                            'date_planned' : production_date,
                            'origin': order.name,
                            'product_qty': line.product_uom_qty,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'bom_id': master_bom_id,
                            'location_src_id': stock_location_obj.id,
                            'location_dest_id': stock_location_obj.id,
                            'routing_id': routing_id,
                            'partner_id': order.partner_id.id,
                            'sr_width': line.sr_width,
                            'sr_length': line.sr_length,
                            'sale_target_date': order.requested_date,
                            #POP-002
                            'delivery_date': order.date_finished,
                            'note': sticker_note ,
                            #POP-003
                            'sale_line_id': line.id,
                        })
                        seq = seq + 1
            #print "Line %s start %f - %f = %02d" % (line.id, start_time, time.time(), int(time.time() - start_time))


        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        #for proc_id in proc_ids:
        #    wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        val = {}
        if order.state == 'shipping_except':
            val['state'] = 'progress'
            val['shipped'] = False

            if (order.order_policy == 'manual'):
                for line in order.order_line:
                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                        val['state'] = 'manual'
                        break
        order.write(val)
        return True
    
    _inherit = "sale.order"
    _description = "Extend for SR Advanced Co.,Ltd."

    _columns = {
        'plan_ids': fields.one2many('sale.order.line.plan','order_id','Plan List'),
        'user_support_id': fields.many2one('res.users', 'Sale Support', states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'date_finished': fields.date('Delivery Date' ),
        'sticker_note': fields.char('Sticker Note', size=50),
        'force_production': fields.boolean('Force Production'),
        #James
        'has_attachment': fields.boolean('Has Attachment'),
        'datetime_receivedoc': fields.datetime('Receive Doc Date'),
        'sender_name': fields.char('Sender Name', size=64),
        'is_f': fields.boolean('F'),
        'is_af': fields.boolean('AF'),
        'is_e': fields.boolean('E'),
        'is_logistic': fields.boolean('Logistic'),
        #
        'inform_date': fields.datetime('Inform Date'),
        'inform_customer_name': fields.char('Inform Customer Name', size=64),
        'inform_date_complete': fields.datetime('Inform Complete Date'),
        'inform_user_name': fields.char('Inform User Name', size=64),
        #fax
        'faxout_date': fields.datetime('Fax Out Date'),
        'faxout_user_name': fields.char('Fax Out User Name', size=64),
        'faxout_customer_name': fields.char('Fax Out Customer Name', size=64),
        #conmmit
        'commitment_date': fields.datetime('Commit Date'),
        'commitment_customer_name': fields.char('Commit Customer Name', size=64),
        #deliver
        'deliver_confirm_date': fields.datetime('Deliver Confirm Date'),
        'deliver_customer_name': fields.char('Deliver Customer Name', size=64),
        'deliver_user_name': fields.char('Deliver User Name', size=64),
        #payment
        'is_cash': fields.boolean('Cash'),
        'slip_date': fields.datetime('Slip Date'),
        #delivery
        'logistic_date': fields.datetime('Logistic Date'),
        'logistic_qty': fields.datetime('Logistic Quantity'),
        'is_logistic_complete': fields.datetime('Logistic Complete'),
        #other 
        'other_note': fields.text('Other Note'),
        'other_note2': fields.text('Other'),
    }
    
    _defaults = {
        'user_support_id': lambda obj, cr, uid, context: uid,
        'force_production': False,
    }

    def action_button_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        sale_obj = self.pool.get('sale.order').browse(cr, uid, ids[0])
        if sale_obj.partner_id.credit_over_limit:
                raise osv.except_osv('Warning', "Credit %s Over Limit %s." % (sale_obj.partner_id.credit_limit,sale_obj.partner_id.credit_limit+sale_obj.amount_total))
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)

        # redisplay the record as a sales order
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
        view_id = view_ref and view_ref[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

    def action_manager_confirm(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', ids[0], 'order_confirm', cr)

        # redisplay the record as a sales order
        view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'view_order_form')
        view_id = view_ref and view_ref[1] or False,
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'current',
            'nodestroy': True,
        }

    def button_update_price(self, cr, uid, ids, context=None):
        for id in ids:
            data = self.browse(cr, uid, id)
            for line in data.order_line:
                if line.price_unit <> line.price_unit2:
                    line.write({'price_unit': line.price_unit2})
        return True

    def copy(self, cr, uid, ids, default=None, context=None):
        if default is None:
            default = {}
        default = default.copy()
        default['name'] = '/'
        default['message_ids'] = []
        return super(sale_order, self).copy(cr, uid, ids, default, context=context)   
        
    def sradvanced_action_ship_create(self, cr, uid, ids, *args):
        wf_service = netsvc.LocalService("workflow")
        picking_id = False
        move_obj = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        company = self.pool.get('res.users').browse(cr, uid, uid).company_id
        for order in self.browse(cr, uid, ids, context={}):
            if order.requested_date == False or order.date_finished == False:
                raise osv.except_osv(_('Warning'), _("Please input Request Date and Finished Date"))

            for plan in order.plan_ids:
                if not order.force_production and plan.capacity_planned < plan.capacity_loaded + plan.capacity:
                    raise osv.except_osv(_('Warning'), _("Max Capacity please contact Production Manager"))

            proc_ids = []
            output_id = order.shop_id.warehouse_id.lot_output_id.id
            picking_id = False
            seq = 1
            for line in order.order_line:
                proc_id = False
                #orginal
                #date_planned = datetime.now() + relativedelta(days=line.delay or 0.0)
                #date_planned = (date_planned - timedelta(days=company.security_lead)).strftime('%Y-%m-%d %H:%M:%S')
                
                if order.requested_date and order.date_finished:
                    #date_planned = datetime.strptime(order.requested_date, '%Y-%m-%d') + relativedelta(days=1)
                    date_planned = order.date_finished
                else:
                    date_planned = datetime.now() + relativedelta(days=line.delay or 0.0) - relativedelta(days=1)

                if line.state == 'done':
                    continue
                move_id = False
                if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    location_id = order.shop_id.warehouse_id.lot_stock_id.id
                    if not picking_id:
                        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
                        picking_id = self.pool.get('stock.picking').create(cr, uid, {
                            'name': pick_name,
                            'origin': order.name,
                            'type': 'out',
                            'state': 'auto',
                            'move_type': order.picking_policy,
                            'sale_id': order.id,
                            'address_id': order.partner_shipping_id.id,
                            'note': order.note,
                            'invoice_state': '2binvoiced',
                            'company_id': order.company_id.id,
                            #POP-001
                            'ineco_delivery_date': order.date_finished,
                        })
                    move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name': line.name[:64],
                        'picking_id': picking_id,
                        'product_id': line.product_id.id,
                        'date': date_planned,
                        'date_expected': date_planned,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos_qty,
                        'product_uos': (line.product_uos and line.product_uos.id)\
                                or line.product_uom.id,
                        'product_packaging': line.product_packaging.id,
                        'address_id': line.address_allotment_id.id or order.partner_shipping_id.id,
                        'location_id': location_id,
                        'location_dest_id': output_id,
                        'sale_line_id': line.id,
                        'tracking_id': False,
                        'state': 'draft',
                        #'state': 'waiting',
                        'note': line.notes,
                        'company_id': order.company_id.id,
                    })

                #check with addition cost Line
                if line.product_id:
                    if not line.additional_line:
                        proc_id = self.pool.get('procurement.order').create(cr, uid, {
                            'name': line.name,
                            'origin': order.name,
                            'date_planned': date_planned,
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                                    or line.product_uom_qty,
                            'product_uos': (line.product_uos and line.product_uos.id)\
                                    or line.product_uom.id,
                            'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
                            'procure_method': line.type,
                            'move_id': move_id,
                            'property_ids': [(6, 0, [x.id for x in line.property_ids])],
                            'company_id': order.company_id.id,
                        })
                        proc_ids.append(proc_id)
                        self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
                        if order.state == 'shipping_except':
                            for pick in order.picking_ids:
                                for move in pick.move_lines:
                                    if move.state == 'cancel':
                                        mov_ids = move_obj.search(cr, uid, [('state', '=', 'cancel'),('sale_line_id', '=', line.id),('picking_id', '=', pick.id)])
                                        if mov_ids:
                                            for mov in move_obj.browse(cr, uid, mov_ids):
                                                move_obj.write(cr, uid, [move_id], {'product_qty': mov.product_qty, 'product_uos_qty': mov.product_uos_qty})
                                                proc_obj.write(cr, uid, [proc_id], {'product_qty': mov.product_qty, 'product_uos_qty': mov.product_uos_qty})
                    else:
                        #new additional cost for create bom 
                        routing_obj = self.pool.get('mrp.routing')
                        routing_id = routing_obj.create(cr, uid, {
                            'code': order.name,
                            'name': 'Process of '+line.product_id.name_template                            
                        })
                        master_bom_obj = self.pool.get('mrp.bom')
                        master_bom_id = master_bom_obj.create(cr, uid, {
                            'name': line.product_id.name_template ,
                            'product_id': line.product_id.id,
                            'code': order.name,
                            'product_qty': 1,
                            'product_uom': line.product_uom.id,
                            'type': 'normal',
                            'routing_id': routing_id, #map routing to new bom
                        })
                        if order.requested_date:
                            production_date = order.plan_ids[0].date_start
                            #production_date = datetime.strptime(order.requested_date, '%Y-%m-%d')
                        else:
                            production_date = datetime.now() + relativedelta(days=line.product_id.sale_delay) - relativedelta(days=1)
                        hour_total = 0
                        for additional_line in line.additional_line :
                            bom_ids = self.pool.get('mrp.bom').search(cr, uid, [('product_id', '=', additional_line.product_id.id),('routing_id','<>','False')], context=None)
                            bom_obj = self.pool.get('mrp.bom').browse(cr, uid, bom_ids,context=None)                            
                            if bom_obj:
                                #routing_id = bom_obj[0].routing_id.id
                                routing = self.pool.get('mrp.routing').browse(cr, uid, bom_obj[0].routing_id.id, context=None)                                
                                
                                if routing:
                                    for wkline in routing.workcenter_lines:
                                        product_id_new = additional_line.product_id
                                        workcenter_id_new = wkline.workcenter_id
                                        dt_from = datetime.strptime(production_date[:10], '%Y-%m-%d')
                                        dt_to = datetime.strptime(production_date[:10], '%Y-%m-%d')
                                        #print "%s %s" % (dt_from, dt_to)
                                        hour_caps = wkline.workcenter_id.resource_id.calendar_id.ineco_interval_hours_get(dt_from, dt_to )

                                        hour = 0
                                        capacity = None
                                        if workcenter_id_new and product_id_new:
                                            capacity_ids = self.pool.get('ineco.workcenter.capacity').search(cr, uid, [('workcenter_id','=',workcenter_id_new.id),('categ_id','=',product_id_new.categ_id.id)])
                                            if capacity_ids:
                                                capacity = self.pool.get('ineco.workcenter.capacity').browse(cr, uid, capacity_ids)[0]
                                                hour = additional_line.product_qty / capacity.cycle_per_hour or 0.00     
                                                hour_total = (line.product_uom_qty * additional_line.product_qty) / capacity.cycle_per_hour or 0.00   
                                        day = math.floor(hour_total / hour_caps)
                                        #print day, hour, hour_caps, dt_from, dt_to
                                        #print abc
                                        day_sec = hour_total % hour_caps       
                                        loop = 0
                                        workcenter_line_obj = self.pool.get('mrp.routing.workcenter')
                                        while loop < day:                     
                                            if capacity:
                                                cycle_nbr = capacity.cycle_per_hour * (((hour_total - day_sec ) / line.product_uom_qty) / day)
                                            else:
                                                cycle_nbr = 0.0
                                            workcenter_line_id = workcenter_line_obj.create(cr, uid, {
                                                'routing_id': routing_id,
                                                'sequence': (int(wkline.sequence) * 10) + loop,
                                                #'name': wkline.name + "-"+additional_line.product_id.name+"-Day " + str(loop+1) or "",
                                                'name': additional_line.product_id.name_template.replace(u'ค่า','',1)+"-Day " + str(loop+1) or "",                                                
                                                'workcenter_id' : wkline.workcenter_id.id or False,
                                                'cycle_nbr': cycle_nbr,
                                                'hour_nbr': ((hour_total - day_sec ) / line.product_uom_qty) / day , #hour
                                            })
                                            loop += 1
                                        if day_sec:
                                            if capacity:
                                                cycle_nbr = capacity.cycle_per_hour * (day_sec / line.product_uom_qty)
                                            else:
                                                cycle_nbr = 0.0
                                            workcenter_line_id = workcenter_line_obj.create(cr, uid, {
                                                'routing_id': routing_id,
                                                'sequence': (int(wkline.sequence) * 10) + loop,
                                                'name': additional_line.product_id.name_template.replace(u'ค่า','',1)+"-Day " + str(loop+1) or "",                                                
                                                'workcenter_id' : wkline.workcenter_id.id or False,
                                                'cycle_nbr': cycle_nbr,
                                                'hour_nbr': day_sec / line.product_uom_qty , #hour
                                            })
                                            
                            #disable semigoods in new boms
                            if additional_line.product_id.type == 'product' and additional_line.product_id.supply_method == 'buy' and additional_line.product_qty > 0 :                                
                                child_bom_obj = self.pool.get('mrp.bom')
                                child_bom_id = child_bom_obj.create(cr, uid, {
                                    'name': additional_line.product_id.name_template ,
                                    'product_id': additional_line.product_id.id,
                                    'code': order.name,
                                    'product_qty': additional_line.product_qty,
                                    'product_uom': additional_line.product_uom.id,
                                    #'routing_id' : routing_id,
                                    'type': 'normal',
                                    'bom_id': master_bom_id,
                                })
                        mrp_order_obj = self.pool.get('mrp.production')
                        stock_location_ids = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal'),('name','=','Stock')], context=None)
                        stock_location_obj = self.pool.get('stock.location').browse(cr, uid,stock_location_ids,context=None)[0]
                        sticker_note = ''
                        if order.sticker_note:
                            sticker_note = order.sticker_note
                        if line.notes: 
                            sticker_note = sticker_note + line.notes 
                        mrp_order_id = mrp_order_obj.create(cr, uid, {
                            #must change date planned after scheduling
                            'name': order.name+'#'+'%02d' % (seq,),
                            'date_planned' : production_date,
                            'origin': order.name,
                            'product_qty': line.product_uom_qty,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'bom_id': master_bom_id,
                            'location_src_id': stock_location_obj.id,
                            'location_dest_id': stock_location_obj.id,
                            'routing_id': routing_id,
                            'partner_id': order.partner_id.id,
                            'sr_width': line.sr_width,
                            'sr_length': line.sr_length,
                            'sale_target_date': order.requested_date,
                            #POP-002
                            'delivery_date': order.date_finished,
                            'note': sticker_note ,
                            #POP-003
                            'sale_line_id': line.id,
                        })
                        seq = seq + 1
                        #mrp_order_obj.action_confirm(cr, uid, [mrp_order_id])

            val = {}

            #change sale progess on delivery 100%
            if picking_id:                      
                wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)

            for proc_id in proc_ids:
                wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
                        
            if order.state == 'shipping_except':
                val['state'] = 'progress'
                val['shipped'] = False

                if (order.order_policy == 'manual'):
                    for line in order.order_line:
                        if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                            val['state'] = 'manual'
                            break
            self.write(cr, uid, [order.id], val)
        return True

    def action_ship_end(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids, context=context):
            val = {'shipped': False}
            if order.state == 'shipping_except':
                val['state'] = 'progress'
                if (order.order_policy == 'manual'):
                    for line in order.order_line:
                        if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                            val['state'] = 'manual'
                            break
            for line in order.order_line:
                towrite = []
                if line.state == 'exception':
                    towrite.append(line.id)
                if towrite:
                    self.pool.get('sale.order.line').write(cr, uid, towrite, {'state': 'done'}, context=context)
            self.write(cr, uid, [order.id], val)
        return True

    def button_create_costline(self, cr, uid, ids, context=None):  
        start_time = time.time()
        for id in ids:
            saleorder = self.browse(cr, uid, id)
            for line in saleorder.order_line:
                line.button_create_costline()
        print "Finish Time: %02d" % (int(time.time() - start_time))
        return True 
        
    def button_create_schedule_finish(self, cr, uid, ids, context=None):
        for id in ids:
            saleorders = self.pool.get('sale.order').browse(cr, uid, id)
            request_date = saleorders[0].requested_date[:10]
            workcenter_load = {}
            for sale in saleorders:
                for line in sale.order_line:
                    for linework in line.additional_line:
                        qty = linework.product_qty
                        product = linework.product_id
                        product_qty = line.product_uom_qty
                        bom_ids = self.pool.get('mrp.bom').search(cr, uid, [('product_id','=',product.id),('type','=','normal'),('bom_id','=',False)])
                        if bom_ids:
                            bom = self.pool.get('mrp.bom').browse(cr, uid, bom_ids)[0]
                            if bom.routing_id:
                                for wc_line in bom.routing_id.workcenter_lines:
                                    workcenter = wc_line.workcenter_id
                                    wk_caps = workcenter._get_capacity(product, qty*product_qty)
                                    if not workcenter_load.has_key(workcenter.id):
                                        workcenter_load.update({workcenter.id: wk_caps})
                                    else:
                                        new_caps = workcenter_load[workcenter.id] + wk_caps
                                        workcenter_load.update({workcenter.id: new_caps})
                                    #print workcenter_load
            cr.execute( ("delete from sale_order_line_plan where order_id = %d " % id) )
            for workcenter_id, capacity in workcenter_load.iteritems():                    
                workcenter_obj = self.pool.get('mrp.workcenter')
                workcenter_ids = workcenter_obj.browse(cr, uid, [workcenter_id])
                if workcenter_ids:
                    workcenters = workcenter_ids[0]
                    wk_capacities = workcenters._get_capacity_hours(request_date)
                    wk_load = workcenters._get_planned_capacity_hours(request_date)
                    wk_newload = wk_load + capacity
                    obj = self.pool.get('sale.order.line.plan')
                    obj.create(cr, uid, {
                        'order_id': id,
                        'workcenter_id': workcenters.id,
                        'name': workcenters.name,
                        'seq': workcenters.priority,
                        'capacity': capacity,
                        'capacity_planned': wk_capacities,
                        'capacity_loaded': wk_load,
                    })
            cr.execute(("select * from sale_order_line_plan where order_id = %s order by seq desc" % id) )
            plan_ids = map(itemgetter(0), cr.fetchall())
            request_date_new = datetime.strptime(request_date[:10], '%Y-%m-%d')
            if plan_ids:                
                for plan in self.pool.get('sale.order.line.plan').browse(cr, uid, plan_ids):
                    finish_date = request_date_new
                    if plan.capacity_loaded + plan.capacity <= plan.capacity_planned:
                        plan.write({'date_start':request_date_new,'date_finish':finish_date,'capacity_loaded':plan.capacity_loaded + plan.capacity})
                    else:
                        hasChange = False
                        wk_load_sum = 0
                        while (not hasChange) and (request_date_new > datetime.strptime(saleorders[0].date_order[:10], '%Y-%m-%d')):                            
                            request_date = datetime.strftime(request_date_new, '%Y-%m-%d')
                            wk_load = plan.workcenter_id._get_planned_capacity_hours(request_date)
                            wk_capacities = plan.workcenter_id._get_capacity_hours(request_date)
                            wk_load_sum += (wk_capacities - wk_load)
                            #print 'WC:%s, Date:%s, %s' % (plan.workcenter_id.name, request_date_new, wk_load_sum)
                            if plan.capacity <= wk_load_sum:
                                plan.write({'date_start':request_date_new,'date_finish':finish_date,'capacity_loaded':wk_load_sum})
                                hasChange = True
                            else:
                                request_date_new -= timedelta(days=1)
            
        return True

class sale_order_line(osv.osv):

    def _get_foot_square(self, cr, uid, ids, field_name, arg, context=None):
        #cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = (line.sr_width * line.sr_length) / (304.79 * 304.79)
        return res

    def _get_sale_unitprice(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        res = {}
        if context is None:
            context = {}

        #add_obj = self.pool.get('sale.order.line.addtionalcost')
        for line in self.browse(cr, uid, ids, context=context):

            sum_price = 0.0
            for add_line in line.additional_line:
                sum_price = sum_price + add_line.price_subtotal

            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])

            #if price_old < sum_price:
            #    self.pool.get('sale.order.line').write(cr, uid, ids, {'price_unit':sum_price})        
        return res

    def _get_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line.addtionalcost').browse(cr, uid, ids, context=context):
            result[line.order_line_id.id] = True
        return result.keys()

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        #cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'price_unit2': 0.0,
            }
            val1 = 0.0
            if order.additional_line:
                for line in order.additional_line:
                    val1 += line.price_subtotal
            else:
                val1 = order.price_unit
            sum_price = val1
            if order.round_method:
                if order.round_method == 'down':
                    sum_price =  math.floor(sum_price)
                    #self.write(cr, uid, order.id, {'price_unit':math.ceil(sum_price)})
                elif order.round_method == 'no':
                    sum_price =  round(sum_price,2)
                    #self.write(cr, uid, order.id, {'price_unit': math.floor(sum_price)})
                else:
                    sum_price =   math.ceil(sum_price)
                    #self.write(cr, uid, order.id, {'price_unit': round(sum_price,2)})
            else:
                sum_price =   math.ceil(sum_price)

            res[order.id]['price_unit2'] = sum_price
        return res

    def button_dummy(self, cr, uid, ids, context=None):
        for id in ids:
            data = self.browse(cr, uid, id)
            data.write({'price_unit': data.price_unit2})
        return True
    
    _name = "sale.order.line"
    _inherit = "sale.order.line"
    _description="Extension of Sale Order for SR Advance Co.,Ltd."
    _columns = {
        'additional_line': fields.one2many('sale.order.line.addtionalcost', 'order_line_id','Additional Cost'),
        'sr_width': fields.float('Width', digits_compute= dp.get_precision('Sale Price')),
        'sr_length': fields.float('Length', digits_compute= dp.get_precision('Sale Price')),
        'ft2': fields.function(_get_foot_square, method=True, string='FT2', digits_compute= dp.get_precision('Sale Price')),
        'round_method': fields.selection([('up','Round Up'),('no','No Round'),('down','Round Down')],string="Rounding"),
        'line_note': fields.text('Note'),
        'price_unit2': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Price Unit',
            #store={
            #    'sale.order.line': (lambda self, cr, uid, ids, c={}: ids, ['additional_line'], 20),
            #    'sale.order.line.addtionalcost': (_get_line, [], 10),
            #},
            multi='linesums'),
    }
    _defaults = {
        'sr_width': 0.0,
        'sr_length': 0.0,      
    }

    def rounding_change(self, cr, uid, ids, round_method):
        result = {}        
        for order in self.browse(cr, uid, ids):
            result = {
                'price_unit': 0.0,
            }
            val1 = 0.0
            if order.additional_line:
                for line in order.additional_line:
                    val1 += line.price_subtotal
            else:
                val1 = order.price_unit
            sum_price = val1
            if round_method:
                if round_method == 'down':
                    sum_price =  math.floor(sum_price)
                elif round_method == 'no':
                    sum_price =  round(sum_price,2)
                else:
                    sum_price =   math.ceil(sum_price)
            else:
                sum_price =   math.ceil(sum_price)
            result['price_unit'] = sum_price
        return {'value': result}

    def width_lengh_change(self, cr, uid, ids, width, length):
        result = {}        
        if width and length:
            result['product_uom_qty'] = ( width * length ) / (304.79 * 304.79)
            result['product_uos_qty'] = ( width * length ) / (304.79 * 304.79)
        return {'value': result}
    
    def onadditional_change(self, cr, uid, ids, line_ids, context=None):
        if context is None:
            context = {}
        result = {}
        subtotal = 0.0        
        result['product_uom_qty'] = subtotal
        result['product_uos_qty'] = subtotal
        return {'value': result}    

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        context = context or {}
        lang = lang or context.get('lang',False)
        if not  partner_id:
            raise osv.except_osv(_('No Customer Defined !'), _('Before choosing a product,\n select a customer in the sales form.'))
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        context = {'lang': lang, 'partner_id': partner_id}
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
        context_partner = {'lang': lang, 'partner_id': partner_id}

        if not product:
            return {'value': {'th_weight': 0,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product, context=context_partner)

        result['product_uom'] = product_obj and product_obj.uom_id and product_obj.uom_id.id
        
        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        if update_tax: #The quantity only have changed
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n'+product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id
        # get unit price

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg +"\n\n"
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom or result.get('product_uom'),
                        'date': date_order,
                        })[pricelist]
            #if price is False:
            #    warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
            #            "You have to change either the product, the quantity or the pricelist.")

            #    warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            #else:
            #    result.update({'price_unit': price})
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        if partner_id:
            result['round_method'] = partner_obj.browse(cr, uid, partner_id).round_method or 'up'
        else:
            result['round_method'] = 'up'
        
        return {'value': result, 'domain': domain, 'warning': warning}

    
    def sradvance_product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        if not  partner_id:
            raise osv.except_osv(_('No Customer Defined !'), _('You have to select a customer in the sales form !\nPlease set one customer before choosing a product.'))
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')

        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
            
        context = {'lang': lang, 'partner_id': partner_id}

        if not product:
            return {'value': {'th_weight': 0, 'product_packaging': False,
                'product_uos_qty': qty}, 'domain': {'product_uom': [],
                   'product_uos': []}}
        if not date_order:
            date_order = time.strftime('%Y-%m-%d')

        result = {}
        product_obj = product_obj.browse(cr, uid, product, context=context)
        if not packaging and product_obj.packaging:
            packaging = product_obj.packaging[0].id
            result['product_packaging'] = packaging

        if packaging:
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            pack = self.pool.get('product.packaging').browse(cr, uid, packaging, context=context)
            q = product_uom_obj._compute_qty(cr, uid, uom, pack.qty, default_uom)
            if qty and (q and not (qty % q) == 0):
                ean = pack.ean or _('(n/a)')
                qty_pack = pack.qty
                type_ul = pack.ul
                warn_msg = _("You selected a quantity of %d Uval1nits.\n"
                            "But it's not compatible with the selected packaging.\n"
                            "Here is a proposition of quantities according to the packaging:\n\n"
                            "EAN: %s Quantity: %s Type of ul: %s") % \
                                (qty, ean, qty_pack, type_ul.name)
                warning = {
                    'title': _('Picking Information !'),
                    'message': warn_msg
                    }
            result['product_uom_qty'] = qty

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        if product_obj.description_sale:
            result['notes'] = product_obj.description_sale
        fpos = fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position) or False
        if update_tax: #The quantity only have changed
            result['delay'] = (product_obj.sale_delay or 0.0)
            result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, fpos, product_obj.taxes_id)
            result.update({'type': product_obj.procure_method})

        if not flag:
            result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context)[0][1]
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}

        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight        # Round the quantity up

        if not uom2:
            uom2 = product_obj.uom_id

        if not pricelist:
            warning = {
                'title': 'No Pricelist !',
                'message':
                    'You have to select a pricelist or a customer in the sales form !\n'
                    'Please set one before choosing a product.'
                }
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom,
                        'date': date_order,
                        })[pricelist]
            if price is False:
                warning = {
                    'title': 'No valid pricelist line found !',
                    'message':
                        "Couldn't find a pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the pricelist."
                    }
            else:
                result.update({'price_unit': math.ceil(price)})
                
        if partner_id:
            result['round_method'] = partner_obj.browse(cr, uid, partner_id).round_method
        else:
            result['round_method'] = 'up'
            
            
        return {'value': result, 'domain': domain, 'warning': warning}
    
    def button_create_costline(self, cr, uid, ids, context=None):    
        sale_line_obj = self.pool.get('sale.order.line')
        add_obj = self.pool.get('sale.order.line.addtionalcost')
        bom_obj = self.pool.get('mrp.bom')
        for line_id in ids:
            additional_line_ids = []
            line_data = sale_line_obj.browse(cr, uid, line_id,context=context)
            #print line_data.id
            #self.write(cr, uid,{'price_unit':1})
            cr.execute( ("delete from sale_order_line_addtionalcost where order_line_id = %d " % line_data.id) )
            bom_ids = bom_obj.search(cr, uid, [('product_id','=',line_data.product_id.id),('type','=','phantom')])
            sum_price = 0.0
            if bom_ids:
                bom = bom_obj.browse(cr, uid, bom_ids[0])    
                for line in bom.bom_lines:
                    ft2 = 1
                    m2 = 1
                    if line_data.sr_width and line_data.sr_length:
                        ft2 = (line_data.sr_width * line_data.sr_length) / (304.8 * 304.8)
                        m2 = (line_data.sr_width * 2 / 1000) + (line_data.sr_length * 2 / 1000)
                    if line.double_qty:
                        new_qty = '%.2f' % (line.product_qty * 2) or 1.0
                    else:
                        new_qty = '%.2f' % line.product_qty or 1.0
                    if line.product_id.product_use_ft2:
                        if line.double_qty:
                            new_qty = '%.2f' % (ft2 * 2) 
                        else:
                            new_qty = '%.2f' % ft2
                    if line.product_id.product_use_m2:
                        if line.double_qty:
                            new_qty = '%.3f' % (m2 * 2)
                        else:
                            new_qty = '%.3f' % m2
                    product_name = line.product_id.name
                    cost_line_id = add_obj.create(cr, uid, {
                        'order_line_id': line_data.id,
                        'product_id':line.product_id.id,
                        'product_qty': new_qty,
                        'price_unit': line.product_id.lst_price,
                        'product_uom':line.product_uom.id,
                        'name': product_name } )   
                    #new_line = {
                    #    'order_line_id': line_data.id,
                    #    'product_id':line.product_id.id,
                    #    'product_qty': new_qty,
                    #    'price_unit': line.product_id.lst_price,
                    #    'product_uom':line.product_uom.id,
                    #    'name': product_name }
                    #additional_line_ids.append((0,0,new_line))
                    sum_price = sum_price + (float(new_qty) * line.product_id.lst_price) or 0.0
                if line_data.round_method:
                    if line_data.round_method == 'down':
                        sum_price =  math.floor(sum_price)
                        self.write(cr, uid, line_data.id, {'price_unit':math.ceil(sum_price)})
                    elif line_data.round_method == 'no':
                        sum_price =  round(sum_price,2)
                        self.write(cr, uid, line_data.id, {'price_unit': math.floor(sum_price)})
                    else:
                        sum_price =   math.ceil(sum_price)
                        self.write(cr, uid, line_data.id, {'price_unit': round(sum_price,2)})
                else:
                    sum_price =   math.ceil(sum_price)
                    self.write(cr, uid, line_data.id, {'price_unit': math.ceil(sum_price)})
            #line_data.write({'additional_line':additional_line_ids,'price_unit': sum_price})
            #print sum_price
        return {'price_unit': sum_price}

class sale_order_line_plan(osv.osv):
    _name = "sale.order.line.plan"
    _description = "Forcast planing about sale order line addtional."
    _columns = {
        'order_id': fields.many2one('sale.order','Order Reference', ondelete='cascade'),
        'name': fields.char('Description', size=100, required=True, select=True),
        'workcenter_id': fields.many2one('mrp.workcenter', 'Workcenter', ondelete='restrict'),
        'capacity': fields.float('Capacity', digits=(16, 2), readonly=True ),
        'capacity_planned': fields.float('Capacity Planned', digits=(16, 2), readonly=True ),
        'capacity_loaded': fields.float('Capacity Loaded', digits=(16, 2), readonly=True ),
        'date_start': fields.date('Start Date'),
        'date_finish': fields.date('Finish Date'),
        'seq': fields.integer('Sequence'),
    }
    _orderby = 'seq desc'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
