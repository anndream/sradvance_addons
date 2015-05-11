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

#
# 30-01-2012    POP-001        Add Note Field in mrp.production.
# 13-02-2012    POP-002        Add Delivery Date in Production.
# 21-05-2012    POP-003        Add Delivery Date In Workcenter Line
# 21-05-2012    POP-004        Add Finish Product By 1 When Tracking Done

from datetime import datetime
from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import netsvc
import time
from openerp import tools
import os
from PyQRNative import *
import urllib
import re

image_level = 5

class ineco_mrp_production_tracking(osv.osv):

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return []
        def _name_get(d):
            name = d.get('name','')
            code = d.get('id',False)
            if code:
                name = '[%s] %s' % (code,name)

            return (d['id'], name)

        result = []
        for data in self.browse(cr, user, ids, context=context):
            mydict = {
                      'id': data.id,
                      'name': data.name,
                      }
            result.append(_name_get(mydict))
        return result

    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args=[]
        searchValue = False
        searchList = False
        if name:
            if isinstance(name, int):
                searchValue = name
            elif isinstance(name, unicode) or isinstance(name, str):
                if name.find('ineco') != -1:
                    searchList = name.split(':')
                    if len(searchList) > 0:
                        searchValue = int(searchList[1])
                else:
                    searchValue = int(name)
            
            ids = self.search(cr, user, [('id','=',searchValue)]+ args, limit=limit, context=context)
            if not len(ids):
                if not isinstance(searchValue, int):
                    ids = self.search(cr, user, [('id',operator,searchValue)]+ args, limit=limit, context=context)
                ids += self.search(cr, user, [('name',operator,searchValue)]+ args, limit=limit, context=context)
            if not len(ids):
                ptrn=re.compile('(\[(.*?)\])')
                res = ptrn.search(searchValue)
                if res:
                    ids = self.search(cr, user, [('id','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

    def _get_date_planned(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            date_planned = False
            last_planned = False
            for workcenter in line.tracking_lines:
                if not workcenter.date_finished and not date_planned:
                    date_planned = workcenter.date_planned
                last_planned = workcenter.date_planned
            res[line.id] = date_planned or last_planned
        return res

    def _get_date_finished(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            date_finished = False
            for workcenter in line.tracking_lines:
                date_finished = workcenter.date_finished
            res[line.id] = date_finished
        return res
    
    def _get_next_workcenter(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            next_workcenter = ""
            for workcenter in line.tracking_lines:
                if not next_workcenter:    
                    if not workcenter.date_finished:
                        next_workcenter = workcenter.workcenter_id.name
            res[line.id] = next_workcenter
        return res
    
    def _progress_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cursor, user, ids, context=context):
            complete_qty = 0
            max_qty = len(line.tracking_lines)
            #print max_qty
            for workcenter in line.tracking_lines:
                if workcenter.date_finished:
                    complete_qty += 1
            res[line.id] = min(100.0, complete_qty * 100 / (max_qty or 1.00))
        return res

    def _id_get(self, cr, uid, ids, field_names, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for id in ids:
            res[id] = id
        return res

    def _id_search(self, cr, uid, obj, name, args, context=None):
        ids = set()
        for cond in args:
            amount = cond[2]
            if isinstance(cond[2],(list,tuple)):
                if cond[1] in ['in','not in']:
                    amount = tuple(cond[2])
                else:
                    continue
            else:
                if cond[1] in ['=like', 'like', 'not like', 'ilike', 'not ilike', 'in', 'not in', 'child_of']:
                    continue

            cr.execute("select id from ineco_mrp_production_tracking where id %s %%s" % (cond[1]),(amount,))
            res_ids = set(id[0] for id in cr.fetchall())
            ids = ids and (ids & res_ids) or res_ids
        if ids:
            return [('id', 'in', tuple(ids))]
        return [('id', '=', '0')]
    
    _name = "ineco.mrp.production.tracking"
    _description = "Tracking production in production line"
    _orderby = 'production_id, number'
    _columns = {
        'name': fields.char('Description',size=250,required=True),
        'production_id': fields.many2one('mrp.production','Production Order',ondelete='cascade',required=True),
        'product_id': fields.many2one('product.product','Product',required=True, ondelete='restrict'),
        'origin': fields.char('Origin', size=100),
        'uom_id': fields.many2one('product.uom','UOM',required=True, ondelete='restrict'),
        'number': fields.integer('Sequence',),
        'date_planned': fields.function(_get_date_planned, method=True, string="Date Planned", type="datetime"),
        'date_finished': fields.function(_get_date_finished, method=True, string="Date Finished", type="datetime"),
        'workcenter_id': fields.function(_get_next_workcenter, method=True, string='Next Workcenter', type='string'),
        'tracking_lines': fields.one2many('ineco.mrp.production.tracking.line','tracking_id','Tracking Lines'),
        'progress_rate': fields.function(_progress_rate, method=True, string="Progress", type="float"),
        'image_url': fields.char('Image URL', size=240),
        'note': fields.char('Note', size=100),
        'date_target': fields.date('Sale Target Date'),
        'date_delivery': fields.date('Delivery Date'),
        'tracking_id': fields.function(_id_get, fnct_search=_id_search, method=True, string='Tracking ID', type="integer"),
    }
    _defaults = {
        'name': '/',
    }
        
    def create(self, cr, uid, vals, context=None):
        id = super(ineco_mrp_production_tracking, self).create(cr, uid, vals, context)

        dir = "/var/www/images/"+self._name
        if not os.path.exists(dir):
            os.makedirs(dir)
        image_url = ""
        qr = QRCode(image_level, QRErrorCorrectLevel.L)
        data = []
        data.append(self._name)
        data.append(str(id))
        qr.addData('tracking:'+str(id)+':'+self._name)
        qr.make()
        
        #import ast
        #ast.literal_eval(str(data))
        
        im = qr.makeImage()
        im.save(dir+'/'+str(id),'png')
        
        image_url = "http://localhost/images/"+self._name+"/"+str(id)
        super(ineco_mrp_production_tracking, self).write(cr, uid, id, {'image_url':image_url})
        
        return id
    
    def gen_qrcode(self, cr, uid, ids, context=None):
        
        for tracking in self.browse(cr, uid, ids):
        
            dir = "/var/www/images/"+self._name
            if not os.path.exists(dir):
                os.makedirs(dir)
                
            image_url = ""
            qr = QRCode(image_level, QRErrorCorrectLevel.L)
            data = []
            data.append(self._name)
            data.append(str(tracking.id))
            qr.addData('tracking:'+str(tracking.id)+':'+self._name)
            qr.make()
            
            im = qr.makeImage()
            im.save(dir+'/'+str(tracking.id),'png')
            
            image_url = "http://localhost/images/"+self._name+"/"+str(tracking.id)
            tracking.write({'image_url': image_url})

        return True

    def unlink(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        dir = "/var/www/images/"+self._name+'/'+str(id)+'.png'
        os.remove(dir)       
        return super(ineco_mrp_production_tracking, self).write(cr, uid, ids, vals, context=context)
    
    def act_done(self, cr, uid, ids, context=None):
        #prod_obj = self.pool.get('mrp.production')
        #for tracking in self.browse(cr, uid, ids):
        #    for production in self.pool.get('mrp.production').browse(cr, uid, [tracking.production_id.id] ):
                #POP-004
        #        prod_obj.action_produce(cr, uid, production.id, 1, "consume_produce", context)
        #    print "Production Done"
        return True

class ineco_mrp_production_tracking_line(osv.osv):
    
    _name = "ineco.mrp.production.tracking.line"
    _description = "Tracking production in production line"
    _orderby = 'tracking_id, number'
    _columns = {
        'name': fields.char('Description',size=250,required=True),
        'tracking_id': fields.many2one('ineco.mrp.production.tracking','Tracking',ondelete='cascade',required=True),
        'product_id': fields.many2one('product.product','Product',required=True, ondelete='restrict'),
        'uom_id': fields.many2one('product.uom','UOM',required=True, ondelete='restrict'),
        'workcenter_id': fields.many2one('mrp.workcenter','Workcenter',required=True, ondelete='restrict'),
        'number': fields.integer('Sequence'),
        'date_planned': fields.datetime('Date Planned'),
        'date_finished': fields.datetime('Date Finished'),
        'user_id': fields.many2one('res.users', 'User', readondate_finishedly=True, ondelete='restrict'),
        'state': fields.selection([('draft','Open'), ('done','Done'),('cancel','Cancel')], 'State', readonly=True),
        'image_url': fields.char('Image URL', size=240),
    }
    _defaults = {
        'name': '/',
        'user_id': lambda s, cr, u, c: u,
        'state': 'draft'
    }
    
    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done','date_finished':time.strftime('%Y-%m-%d %H:%M:%S')})
        for line in self.browse(cr, uid, ids):
            for track in self.pool.get('ineco.mrp.production.tracking').browse(cr, uid, [line.tracking_id.id] ):
                #print track.name, track.progress_rate
                if track.progress_rate == 100:
                    track.act_done()
        return True
    
    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft','date_finished':False})
        return True 
    
    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cancel','date_finished': False})
        return True 

    def create(self, cr, uid, vals, context=None):
        id = super(ineco_mrp_production_tracking_line, self).create(cr, uid, vals, context)

        dir = "/var/www/images/"+self._name
        if not os.path.exists(dir):
            os.makedirs(dir)
        image_url = ""
        qr = QRCode(image_level, QRErrorCorrectLevel.L)
        data = []
        data.append(self._name)
        data.append(str(id))
        qr.addData('tracking:'+str(id)+':'+self._name)
        qr.make()
        
        #import ast
        #ast.literal_eval(str(data))
        
        im = qr.makeImage()
        im.save(dir+'/'+str(id),'png')
        
        image_url = dir+"/"+str(id)+".png"
        super(ineco_mrp_production_tracking_line, self).write(cr, uid, id, {'image_url':image_url})
        
        return id
    
    def unlink(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        dir = "/var/www/images/"+self._name+'/'+str(id)+'.png'
        os.remove(dir)       
        return super(ineco_mrp_production_tracking_line, self).write(cr, uid, ids, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if ('date_finished' in vals):
            if vals.get('date_finished'):           
                all_complete_qty = 0      
                for line in self.browse(cr, uid, ids):
                    complete_qty = 0
                    for track in self.pool.get('ineco.mrp.production.tracking').browse(cr, uid, [line.tracking_id.id] ):
                        max_qty = len(track.tracking_lines)
                        prod_id = track.production_id.id
                        for workcenter in track.tracking_lines:
                            if workcenter.id == line.id:
                                complete_qty += 1
                            if workcenter.date_finished:
                                complete_qty += 1
                        percent = min(100.0, complete_qty * 100 / (max_qty or 1.00))
                        if percent >= 99.99:
                            all_complete_qty += 1
                    for production in self.pool.get('mrp.production').browse(cr, uid, [prod_id] ):
                        max_prod_qty = len(production.tracking_lines)
                        for track in production.tracking_lines:
                            if track.progress_rate >= 99.99:
                                all_complete_qty += 1
                    track_percent = min(100.0, all_complete_qty * 100 / (max_prod_qty or 1.00))
                    #Full Production will -> stock
                    #if track_percent >= 99.99:
                    #     track.act_done()
        return super(ineco_mrp_production_tracking_line, self).write(cr, uid, ids, vals, context)   


class mrp_production(osv.osv):
    _name = "mrp.production"
    _inherit = "mrp.production"
    _description = "Generate Tracking Product"

    _columns = {
        'tracking_lines': fields.one2many('ineco.mrp.production.tracking','production_id','Tracking Lines'),
        'partner_id': fields.many2one('res.partner', 'Customer', ondelete="restrict"),
        'sr_width': fields.float('Width', digits=(10,2)),
        'sr_length': fields.float('Length', digits=(10,2)),
        'sale_target_date': fields.date('Sale Target Date'),
        #POP-002
        'delivery_date': fields.date('Delivery Date'),
        #POP-001
        'note': fields.char('Note', size=100),
        'sale_line_id': fields.many2one('sale.order.line', 'Sale Line'),
    }

#Disable BOM/Routing When MO Confirm <- Delivery Finish
#    def wait_action_confirm(self, cr, uid, ids, context=None):
#        result = super(mrp_production, self).action_confirm(cr, uid, ids)
#        for po in self.browse(cr, uid, ids):
#            if po.bom_id:
#                self.pool.get('mrp.bom').write(cr, uid, po.bom_id.id,{'active':False})
#                self.pool.get('mrp.routing').write(cr, uid, po.routing_id.id,{'active':False})
#        return result 

    def action_compute(self, cr, uid, ids, properties=None, context=None):
        start_time = time.time()
        result = super(mrp_production, self).action_compute(cr, uid, ids)
        for po in self.browse(cr, uid, ids):
            cr.execute("""
                delete from ineco_mrp_production_tracking_line
                where id in (
                select b.id from ineco_mrp_production_tracking a
                left join ineco_mrp_production_tracking_line b on b.tracking_id = a.id
                where a.production_id = %d)            
            """ % po.id)
            cr.execute( ("delete from ineco_mrp_production_tracking where production_id = %d " % po.id) )
            qty = 1 
            #context = {}
            product_name = po.product_id.name
            while qty <= int(po.product_qty):
                tracking_id = self.pool.get('ineco.mrp.production.tracking').create(cr, uid,  {
                    'name': 'Seq '+str(qty)+'. '+po.name+'-'+product_name,
                    'production_id': po.id,
                    'origin': po.origin, 
                    'product_id': po.product_id.id,
                    'uom_id': po.product_id.uom_id.id,
                    'number': qty,
                    'date_planned': po.date_planned,
                    'note': po.note,
                    'date_target': po.sale_target_date,
                    'date_delivery': po.delivery_date,
                })                
                print "Tracking %02d Seconds" % int(time.time() - start_time)
                wclids = []
                for wcl in po.workcenter_lines:
                    #found_ids = self.pool.get('ineco.mrp.production.tracking.line').search(cr, uid, [('tracking_id','=',tracking_id),('workcenter_id','=',wcl.workcenter_id.id)])
                    #if not found_ids:
                    dup_ids = self.pool.get('ineco.mrp.production.tracking.line').search(cr, uid, [('tracking_id','=',tracking_id),('workcenter_id','=',wcl.workcenter_id.id)])
                    if not dup_ids:
                        self.pool.get('ineco.mrp.production.tracking.line').create(cr, uid,  {
                            'name': 'Seq '+str(qty)+'. '+po.name+'-'+product_name,
                            'tracking_id': tracking_id,
                            'product_id': po.product_id.id,
                            'uom_id': po.product_id.uom_id.id,
                            'workcenter_id': wcl.workcenter_id.id,
                            'number': wcl.sequence,
                            'date_planned': wcl.date_planned,
                        })
                        wclids.append(wcl.id)
                    #POP-003
                    #wcl.write({'sale_target_date':po.sale_target_date,'date_delivery': po.delivery_date})
                qty += 1
            if wclids:
                self.pool.get('mrp.production.workcenter.line').write(cr, uid, wclids, {'sale_target_date':po.sale_target_date,'date_delivery': po.delivery_date})
            cr.commit()
        print "Finish %02d Seconds" % int(time.time() - start_time)
        return result 

class mrp_bom(osv.osv):
    
    _name = "mrp.bom"
    _inherit = "mrp.bom"
    _description = "Change Default Routing"
    
    _columns = {
        'double_qty': fields.boolean('Double Quantity'),
    }
    
    def onchange_product_id(self, cr, uid, ids, product_id, name, context=None):
        """ Changes UoM and name if product_id changes.
        @param name: Name of the field
        @param product_id: Changed product_id
        @return:  Dictionary of changed values
        """
        if product_id:
            prod = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            v = {'product_uom': prod.uom_id.id}
            if not name:
                v['name'] = prod.name
            bom_ids = self.pool.get('mrp.bom').search(cr, uid, [('product_id','=',product_id),('bom_id','=',False)])
            if bom_ids:
                bom = self.pool.get('mrp.bom').browse(cr, uid, bom_ids[0])
                if bom.routing_id:
                    v['routing_id'] = bom.routing_id.id
            return {'value': v}
        return {}

class ineco_mrp_production_tracking_fixed(osv.osv):
    
    def _get_product(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.tracking_id.product_id.name or ""
        return res

    def _get_origin(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.tracking_id.origin or ""
        return res

    def _get_length(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for fix in self.browse(cr, uid, ids, context=context):
            res[fix.id] = fix.tracking_id.production_id.sr_width or 0.0
        return res

    def _get_width(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for fix in self.browse(cr, uid, ids, context=context):
            res[fix.id] = fix.tracking_id.production_id.sr_length or 0.0
        return res
    
    _name = "ineco.mrp.production.tracking.fixed"
    _description = "Fix Tracking"
    _columns = {
        'name': fields.char('Description',size=250,required=True),
        'date_planned': fields.datetime('Date Fixed'),
        'workcenter_id': fields.many2one('mrp.workcenter','Workcenter',required=True, ondelete='restrict'),
        'tracking_id': fields.many2one('ineco.mrp.production.tracking','Tracking',ondelete='cascade',required=True),
        'user_id': fields.many2one('res.users', 'User', readondate_finishedly=True, ondelete='restrict'),
        'product_id': fields.function(_get_product, method=True, string="Product", type="string"),
        'origin': fields.function(_get_origin, method=True, string="Origin", type="string"),
        'product_length': fields.function(_get_length, method=True, store=True, string="Length", type="float"),
        'product_width': fields.function(_get_width, method=True, store=True, string="Width", type="float"),        
    }
    _defaults = {
        'user_id': lambda s, cr, u, c: u,
        'date_planned': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals.update({'date_planned': time.strftime('%Y-%m-%d %H:%M:%S'), 'user_id':uid})
        return super(ineco_mrp_production_tracking_fixed, self).create(cr, uid, vals, context=context) 

#POP-003
class mrp_production_workcenter_line(osv.osv):
    _name="mrp.production.workcenter.line"
    _inherit = "mrp.production.workcenter.line"
    _description = "Add Delivery Date in Operation"
    _columns = {
        'sale_target_date': fields.date('Sale Target Date'),
        'date_delivery': fields.date('Delivery Date'),
    }

class ineco_mrp_production_barcode(osv.osv):

    def _default_workcenter(self, cr, uid, context=None):
        if context is None:
            context = {}
        barcode_ids = self.pool.get('ineco.mrp.production.barcode').search(cr, uid, [('user_id','=',uid)], limit=1)
        workcenter_id = False
        if barcode_ids:
            barcode = self.pool.get('ineco.mrp.production.barcode').browse(cr, uid, barcode_ids)[0]
            workcenter_id = barcode.workcenter_id.id or False
        return workcenter_id
    
    _name = "ineco.mrp.production.barcode"
    _description = "Barcode Production Operation"
    _columns = {
        'name': fields.char('Description', size=250),
        'workcenter_id': fields.many2one('mrp.workcenter','Workcenter', ondelete='restrict'),
        'tracking_id': fields.many2one('ineco.mrp.production.tracking','Tracking',ondelete='cascade',required=True),
        'user_id': fields.many2one('res.users', 'User', ondelete='restrict'),
        'date_finished': fields.datetime('Date Finish'),
    }
    _defaults = {
        'user_id': lambda s, cr, u, c: u,
        'workcenter_id': _default_workcenter,
        'date_finished': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    _order = "date_finished desc"

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        vals.update({'date_finished': time.strftime('%Y-%m-%d %H:%M:%S'),'user_id':uid})
        workcenter_id = vals['workcenter_id']
        tracking_id = vals['tracking_id']
        line_ids = self.pool.get('ineco.mrp.production.tracking.line').search(cr, uid, [('tracking_id','=',tracking_id),('workcenter_id','=',workcenter_id)])
        if line_ids:
            line = self.pool.get('ineco.mrp.production.tracking.line').browse(cr, uid, line_ids)[0]
            if line.state <> 'done':
                line.action_done()
            line.write({'user_id':uid})
        return super(ineco_mrp_production_barcode, self).create(cr, uid, vals, context=context) 
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        vals.update({'date_finished': time.strftime('%Y-%m-%d %H:%M:%S') , 'user_id': uid})
        return super(ineco_mrp_production_barcode, self).write(cr, uid, ids, vals, context=context)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
