# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re
import locale
import gtk
import math
import cgi

import tools
import tools.datetime_util

from rpc import RPCProxy
from editabletree import EditableTreeView
from decoratedtree import DecoratedTreeView
from widget.view import interface

import time
import date_renderer

from widget.view.form_gtk.many2one import dialog as M2ODialog
from modules.gui.window.win_search import win_search
from widget.view.form_gtk.parser import Button

import common
import rpc
import datetime as DT
import service
import gobject
import pango
import pytz

def send_keys(renderer, editable, position, treeview):
    editable.connect('key_press_event', treeview.on_keypressed)
    editable.editing_done_id = editable.connect('editing_done', treeview.on_editing_done)
    if isinstance(editable, gtk.ComboBoxEntry):
        editable.connect('changed', treeview.on_editing_done)

def sort_model(column, treeview):
    model = treeview.get_model()
    model.sort(column.name)

class parser_tree(interface.parser_interface):
    def parse(self, model, root_node, fields):
        dict_widget = {}
        btn_list=[]
        attrs = tools.node_attributes(root_node)
        on_write = attrs.get('on_write', '')
        editable = attrs.get('editable', False)
        if editable:
            treeview = EditableTreeView(editable)
        else:
            treeview = DecoratedTreeView(editable)
        treeview.colors = dict()
        self.treeview = treeview
        for color_spec in attrs.get('colors', '').split(';'):
            if color_spec:
                colour, test = color_spec.split(':')
                treeview.colors[colour] = test
        treeview.set_property('rules-hint', True)
        if not self.title:
            self.title = attrs.get('string', 'Unknown')


        treeview.sequence = False
        for node in root_node.childNodes:
            node_attrs = tools.node_attributes(node)
            if node.localName == 'button':
                cell = Cell('button')(node_attrs['string'])
                cell.attrs=node_attrs
                cell.name=node_attrs['name']
                cell.type=node_attrs.get('type','object')
                cell.context=node_attrs.get('context',{})
                cell.model=model
                treeview.cells[node_attrs['name']] = cell
                col = gtk.TreeViewColumn(None, cell)
                btn_list.append(col)
                cell.set_property('editable',False)
                col._type = 'Button'
                col.name = node_attrs['name']
                
            if node.localName == 'field':
                fname = str(node_attrs['name'])
                if fields[fname]['type'] in ('image', 'binary'):
                    continue    # not showed types
                if fname == 'sequence':
                    treeview.sequence = True
                for boolean_fields in ('readonly', 'required'):
                    if boolean_fields in node_attrs:
                        if node_attrs[boolean_fields] in ('True', 'False'):
                            node_attrs[boolean_fields] = eval(node_attrs[boolean_fields])
                        else:    
                            node_attrs[boolean_fields] = bool(int(node_attrs[boolean_fields]))
                fields[fname].update(node_attrs)
                node_attrs.update(fields[fname])
                cell = Cell(fields[fname]['type'])(fname, treeview, node_attrs,
                        self.window)
                treeview.cells[fname] = cell
                renderer = cell.renderer
                
                write_enable = editable and not node_attrs.get('readonly', False)
                if isinstance(renderer, gtk.CellRendererToggle):
                    renderer.set_property('activatable', write_enable)
                elif isinstance(renderer, (gtk.CellRendererText, gtk.CellRendererCombo, date_renderer.DecoratorRenderer)):
                    renderer.set_property('editable', write_enable)
                if write_enable:
                    renderer.connect_after('editing-started', send_keys, treeview)

                col = gtk.TreeViewColumn(None, renderer)
                col_label = gtk.Label('')
                if fields[fname].get('required', False):
                    col_label.set_markup('<b>%s</b>' % cgi.escape(fields[fname]['string']))
                else:
                    col_label.set_text(fields[fname]['string'])
                col_label.show()
                col.set_widget(col_label)

                col.name = fname
                col._type = fields[fname]['type']
                col.set_cell_data_func(renderer, cell.setter)
                col.set_clickable(True)
                twidth = {
                    'integer': 60,
                    'float': 80,
                    'float_time': 80,
                    'date': 70,
                    'datetime': 120,
                    'selection': 90,
                    'char': 100,
                    'one2many': 50,
                    'many2many': 50,
                    'boolean': 20,
                }
                if 'width' in fields[fname]:
                    width = int(fields[fname]['width'])
                else:
                    width = twidth.get(fields[fname]['type'], 100)
                col.set_min_width(width)
                if not treeview.sequence:
                    col.connect('clicked', sort_model, treeview)
                col.set_resizable(True)
                #col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                visval = eval(str(fields[fname].get('invisible', 'False')), {'context':self.screen.context})
                col.set_visible(not visval)
                n = treeview.append_column(col)
                if 'sum' in fields[fname] and fields[fname]['type'] \
                        in ('integer', 'float', 'float_time'):
                    label = gtk.Label()
                    label.set_use_markup(True)
                    label_str = fields[fname]['sum'] + ': '
                    label_bold = bool(int(fields[fname].get('sum_bold', 0)))
                    if label_bold:
                        label.set_markup('<b>%s</b>' % label_str)
                    else:
                        label.set_markup(label_str)
                    label_sum = gtk.Label()
                    label_sum.set_use_markup(True)
                    dict_widget[n] = (fname, label, label_sum,
                            fields[fname].get('digits', (16,2))[1], label_bold)
        for btn in btn_list:
            treeview.append_column(btn)
        return treeview, dict_widget, [], on_write

class UnsettableColumn(Exception):
    pass

class Cell(object):
    def __new__(self, type):
        klass = CELLTYPES.get(type, CELLTYPES['char'])
        return klass


class Char(object):
    def __init__(self, field_name, treeview=None, attrs=None, window=None):
        self.field_name = field_name
        self.attrs = attrs or {}
        self.renderer = gtk.CellRendererText()
        self.treeview = treeview
        if not window:
            window = service.LocalService('gui.main').window
        self.window = window
    
    def attrs_set(self, model, cell):
        if self.attrs.get('attrs',False):
            attrs_changes = eval(self.attrs.get('attrs',"{}"),{'uid':rpc.session.uid})
            for k,v in attrs_changes.items():
                result = False
                for condition in v:
                    result = tools.calc_condition(self,model,condition)
                model[self.field_name].get_state_attrs(model)[k] = result

    def state_set(self, model, state='draft'):
        ro = model.mgroup._readonly
        field = model[self.field_name]
        state_changes = dict(field.attrs.get('states',{}).get(state,[]))
        if 'readonly' in state_changes:
            field.get_state_attrs(model)['readonly'] = state_changes['readonly'] or ro
        else:
            field.get_state_attrs(model)['readonly'] = field.attrs.get('readonly',False) or ro
        if 'required' in state_changes:
            field.get_state_attrs(model)['required'] = state_changes['required']
        else:
            field.get_state_attrs(model)['required'] = field.attrs.get('required',False)
        if 'value' in state_changes:
            field.set(model, state_changes['value'], test_state=False, modified=True)
                            
    def setter(self, column, cell, store, iter):
        model = store.get_value(iter, 0)
        text = self.get_textual_value(model)
        cell.set_property('text', text)
        if model.value.get('state',False):
            self.state_set(model, model.value.get('state','draft'))
        self.attrs_set(model, cell)
        color = self.get_color(model)
        cell.set_property('foreground', str(color))
        if self.attrs['type'] in ('float', 'integer', 'boolean'):
            align = 1
        else:
            align = 0
        if self.treeview.editable:
            field = model[self.field_name]
            
            #setting the cell property editable or not
            cell.set_property('editable',not field.get_state_attrs(model).get('readonly', False))
                
            if not field.get_state_attrs(model).get('valid', True):
                cell.set_property('background', common.colors.get('invalid', 'white'))
            elif bool(int(field.get_state_attrs(model).get('required', 0))):
                cell.set_property('background', common.colors.get('required', 'white'))
            else:
                cell.set_property('background', None)
                  
        cell.set_property('xalign', align)

    def get_color(self, model):
        to_display = ''
        for color, expr in self.treeview.colors.items():
            if model.expr_eval(expr, check_load=False):
                to_display = color
                break
        return to_display or 'black'

    def open_remote(self, model, create, changed=False, text=None):
        raise NotImplementedError

    def get_textual_value(self, model):
        return model[self.field_name].get_client(model) or ''

    def value_from_text(self, model, text):
        return text

class Int(Char):

    def value_from_text(self, model, text):
        return int(text)

    def get_textual_value(self, model):
        return tools.locale_format('%d', model[self.field_name].get_client(model) or 0)

class Boolean(Int):

    def __init__(self, *args):
        super(Boolean, self).__init__(*args)
        self.renderer = gtk.CellRendererToggle()
        self.renderer.connect('toggled', self._sig_toggled)

    def get_textual_value(self, model):
        return model[self.field_name].get_client(model) or 0

    def setter(self, column, cell, store, iter):
        model = store.get_value(iter, 0)
        value = self.get_textual_value(model)
        cell.set_active(bool(value))
        if model.value.get('state',False):
            self.state_set(model, model.value.get('state','draft'))
        self.attrs_set(model, cell)
        if self.treeview.editable:
            field = model[self.field_name]

            cell.set_property('sensitive',not field.get_state_attrs(model).get('readonly', False))
            
            if field.get_state_attrs(model).get('required', True): 
                cell.set_property('cell-background',common.colors.get('required', 'white'))
            else:
                cell.set_property('cell-background',None)   

    def _sig_toggled(self, renderer, path):
        store = self.treeview.get_model()
        model = store.get_value(store.get_iter(path), 0)
        field = model[self.field_name]
        if not field.get_state_attrs(model).get('readonly', False):
            value = model[self.field_name].get_client(model)
            model[self.field_name].set_client(model, int(not value))
            self.treeview.set_cursor(path)
        return True


class GenericDate(Char):
    def __init__(self, field_name, treeview=None, attrs=None, window=None):
        self.field_name = field_name
        self.attrs = attrs or {}
        self.renderer1 = gtk.CellRendererText()
# TODO: Review this, not always editable
        self.renderer1.set_property('editable', True)
        self.renderer = date_renderer.DecoratorRenderer(self.renderer1, date_renderer.date_callback(treeview), self.display_format)
        self.treeview = treeview
        if not window:
            window = service.LocalService('gui.main').window
        self.window = window

    def get_textual_value(self, model):
        value = model[self.field_name].get_client(model)
        if not value:
            return ''
        try:
            date = DT.datetime.strptime(value[:10], self.server_format)
            return date.strftime(self.display_format)
        except:
            return ''

    def value_from_text(self, model, text):
        dt = self.renderer.date_get(self.renderer.editable)
        res = dt and dt.strftime(self.server_format)
        if res:
            DT.datetime.strptime(res[:10], self.server_format)
        return res

class Date(GenericDate):
    server_format = '%Y-%m-%d'
    display_format = tools.datetime_util.get_date_format()

class Datetime(GenericDate):
    server_format = '%Y-%m-%d %H:%M:%S'
    display_format = tools.datetime_util.get_date_format() + ' %H:%M:%S'

    def get_textual_value(self, model):
        value = model[self.field_name].get_client(model)
        if not value:
            return ''
        date = DT.datetime.strptime(value[:19], self.server_format)

        if rpc.session.context.get('tz'):
            try:
                lzone = pytz.timezone(rpc.session.context['tz'])
                szone = pytz.timezone(rpc.session.timezone)
                sdt = szone.localize(date, is_dst=True)
                date = sdt.astimezone(lzone)
            except pytz.UnknownTimeZoneError:
                # Timezones are sometimes invalid under Windows
                # and hard to figure out, so as a low-risk fix
                # in stable branch we will simply ignore the
                # exception and consider client in server TZ
                # (and sorry about the code duplication as well,
                # this is fixed properly in trunk)
                pass
        if isinstance(date, DT.datetime):
            return date.strftime(self.display_format)
        return time.strftime(self.display_format, date)

    def value_from_text(self, model, text):
        if not text:
            return False
        try:
            date = DT.datetime.strptime(text[:19], self.display_format)
        except ValueError, ex:
            #ValueError: time data '__/__/____ __:__:__' does not match format '%m/%d/%Y %H:%M:%S'
            return False

        if rpc.session.context.get('tz'):
            try:
                lzone = pytz.timezone(rpc.session.context['tz'])
                szone = pytz.timezone(rpc.session.timezone)
                ldt = lzone.localize(date, is_dst=True)
                sdt = ldt.astimezone(szone)
                date = sdt.timetuple()
            except pytz.UnknownTimeZoneError:
                # Timezones are sometimes invalid under Windows
                # and hard to figure out, so as a low-risk fix
                # in stable branch we will simply ignore the
                # exception and consider client in server TZ
                # (and sorry about the code duplication as well,
                # this is fixed properly in trunk)
                pass

        if isinstance(date, DT.datetime):
            return date.strftime(self.server_format)
        return time.strftime(self.server_format, date)

class Float(Char):
    def get_textual_value(self, model):
        interger, digit = self.attrs.get('digits', (16,2) )
        return tools.locale_format('%.' + str(digit) + 'f', model[self.field_name].get_client(model) or 0.0)

    def value_from_text(self, model, text):
        try:
            return locale.atof(text)
        except:
            return 0.0

class FloatTime(Char):
    def get_textual_value(self, model):
        val = model[self.field_name].get_client(model)
        hours = math.floor(abs(val))
        mins = round(abs(val)%1+0.01,2)
        if mins >= 1.0:
            hours = hours + 1
            mins = 0.0
        else:
            mins = mins * 60
        t = '%02d:%02d' % (hours,mins)
        if val<0:
            t = '-'+t
        return t

    def value_from_text(self, model, text):
        try:
            if text and ':' in text:
                return round(int(text.split(':')[0]) + int(text.split(':')[1]) / 60.0,4)
            else:
                return locale.atof(text)
        except:
            pass
        return 0.0

class M2O(Char):

    def value_from_text(self, model, text):
        if not text:
            return False

        relation = model[self.field_name].attrs['relation']
        rpc = RPCProxy(relation)

        domain = model[self.field_name].domain_get(model)
        context = model[self.field_name].context_get(model)

        names = rpc.name_search(text, domain, 'ilike', context)
        if len(names) != 1:
            return self.search_remote(relation, [x[0] for x in names],
                             domain=domain, context=context)[0]
        return names[0]

    def open_remote(self, model, create=True, changed=False, text=None):
        modelfield = model.mgroup.mfields[self.field_name]
        relation = modelfield.attrs['relation']

        domain=modelfield.domain_get(model)
        context=modelfield.context_get(model)
        if create:
            id = None
        elif not changed:
            id = modelfield.get(model)
        else:
            rpc = RPCProxy(relation)

            names = rpc.name_search(text, domain, 'ilike', context)
            if len(names) == 1:
                return True, names[0]
            searched = self.search_remote(relation, [x[0] for x in names], domain=domain, context=context)
            if searched[0]:
                return True, searched
            return False, False
        dia = M2ODialog(relation, id, domain=domain, context=context,
                window=self.window)
        ok, value = dia.run()
        dia.destroy()
        if ok:
            return True, value
        else:
            return False, False

    def search_remote(self, relation, ids=[], domain=[], context={}):
        rpc = RPCProxy(relation)

        win = win_search(relation, sel_multi=False, ids=ids, context=context, domain=domain)
        found = win.go()
        if found:
            return rpc.name_get([found[0]], context)[0]
        else:
            return False, None


class O2M(Char):
    def get_textual_value(self, model):
        return '( '+str(len(model[self.field_name].get_client(model).models)) + ' )'

    def value_from_text(self, model, text):
        raise UnsettableColumn('Can not set column of type o2m')


class M2M(Char):
    def get_textual_value(self, model):
        value = model[self.field_name].get_client(model)
        if value:
            return '(%s)' % len(value)
        else:
            return '(0)'

    def value_from_text(self, model, text):
        if not text:
            return []
        if not (text[0]<>'('):
            return model[self.field_name].get(model)
        relation = model[self.field_name].attrs['relation']
        rpc = RPCProxy(relation)
        domain = model[self.field_name].domain_get(model)
        context = model[self.field_name].context_get(model)
        names = rpc.name_search(text, domain, 'ilike', context)
        ids = [x[0] for x in names]
        win = win_search(relation, sel_multi=True, ids=ids, context=context, domain=domain)
        found = win.go()
        return found or []

    def open_remote(self, model, create=True, changed=False, text=None):
        modelfield = model[self.field_name]
        relation = modelfield.attrs['relation']

        rpc = RPCProxy(relation)
        context = model[self.field_name].context_get(model)
        domain = model[self.field_name].domain_get(model)
        if create:
            if text and len(text) and text[0]<>'(':
                domain.append(('name','=',text))
            ids = rpc.search(domain)
            if ids and len(ids)==1:
                return True, ids
        else:
            ids = model[self.field_name].get_client(model)
        win = win_search(relation, sel_multi=True, ids=ids, context=context, domain=domain)
        found = win.go()
        if found:
            return True, found
        else:
            return False, None

class Selection(Char):

    def __init__(self, *args):
        super(Selection, self).__init__(*args)
        self.renderer = gtk.CellRendererCombo()
        selection_data = gtk.ListStore(str, str)
        for x in self.attrs.get('selection', []):
            selection_data.append(x)
        self.renderer.set_property('model', selection_data)
        self.renderer.set_property('text-column', 1)

    def get_textual_value(self, model):
        selection = dict(model[self.field_name].attrs['selection'])
        return selection.get(model[self.field_name].get(model), '')

    def value_from_text(self, model, text):
        selection = model[self.field_name].attrs['selection']
        text = tools.ustr(text)
        res = False
        for val, txt in selection:
            if txt[:len(text)].lower() == text.lower():
                if len(txt) == len(text):
                    return val
                res = val
        return res


class ProgressBar(object):
    def __init__(self, field_name, treeview=None, attrs=None, window=None):
        self.field_name = field_name
        self.attrs = attrs or {}
        self.renderer = gtk.CellRendererProgress()
        self.treeview = treeview
        if not window:
            window = service.LocalService('gui.main').window
        self.window = window

    def setter(self, column, cell, store, iter):
        model = store.get_value(iter, 0)
        text = self.get_textual_value(model) or 0.0
        cell.set_property('text', '%.2f %%' % (text,))
        if text<0: text = 0.0
        if text>100.0: text = 100.0
        cell.set_property('value', text)

    def open_remote(self, model, create, changed=False, text=None):
        raise NotImplementedError

    def get_textual_value(self, model):
        return model[self.field_name].get_client(model) or ''

    def value_from_text(self, model, text):
        return text


class CellRendererButton(gtk.GenericCellRenderer):
    __gproperties__ = {
            "text": (gobject.TYPE_STRING, None, "Text",
                "Displayed text", gobject.PARAM_READWRITE),
            "editable" : (gobject.TYPE_BOOLEAN, None, None,
                True, gobject.PARAM_READWRITE),
    }
    __gsignals__ = {
            'clicked': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                (gobject.TYPE_STRING, )),
    }
    def __init__(self, text=""):
        self.__gobject_init__()
        self.text = text
        self.border = gtk.Button().border_width
        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self.clicking = False
        self.xalign = 0.0
        self.yalign = 0.5
        self.textborder = 4
#        self.set_property('editable',False)

    def __get_states(self):
        return [e for e in self.attrs.get('states','').split(',') if e]

    def __get_model_state(self, widget, cell_area):
        path = widget.get_path_at_pos(int(cell_area.x),int(cell_area.y))
        modelgrp = widget.get_model()
        model = modelgrp.models[path[0][0]]

        if model and ('state' in model.mgroup.fields):
            state = model['state'].get(model)
        else:
            state = 'draft'
        return state
    
    def __is_visible(self, widget, cell_area):
        states = self.__get_states()
        model_state = self.__get_model_state(widget, cell_area)
        return (not states) or (model_state in states)

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def on_render(self, window, widget, background_area, cell_area,
            expose_area, flags):

        if not self.__is_visible(widget, cell_area):
            return True

        state = gtk.STATE_NORMAL
        shadow = gtk.SHADOW_OUT
        if self.clicking and flags & gtk.CELL_RENDERER_SELECTED:
            state = gtk.STATE_ACTIVE
            shadow = gtk.SHADOW_IN
        widget.style.paint_box(window, state, shadow,
                None, widget, "button",
                cell_area.x, cell_area.y,
                cell_area.width, cell_area.height)
        
        #layout = widget.create_pango_layout('')
        #layout.set_font_description(widget.style.font_desc)
        #w, h = layout.get_size()
        #x = cell_area.x
        #y = int(cell_area.y + (cell_area.height - h / pango.SCALE) / 2)
        #window.draw_layout(widget.style.text_gc[0], x, y, layout)

        layout = widget.create_pango_layout(self.text)
        layout.set_font_description(widget.style.font_desc)
        w, h = layout.get_size()
        x = int(cell_area.x + (cell_area.width - w / pango.SCALE) / 2)
        y = int(cell_area.y + (cell_area.height - h / pango.SCALE) / 2)
        window.draw_layout(widget.style.text_gc[0], x, y, layout)

    def on_get_size(self, widget, cell_area=None):
        width,height=90,18
        if cell_area:
            width = max(width + self.textborder * 2, cell_area.width)
        else:
            width += self.textborder * 2
            height += self.textborder * 2
        if cell_area:
            x = max(int(self.xalign * (cell_area.width - width)), 0)
            y = max(int(self.yalign * (cell_area.height - height)), 0)
        else:
            x, y = 0, 0
        return (x, y, width, height)

    def on_start_editing(self, event, widget, path, background_area,
            cell_area, flags):
        
        if not self.__is_visible(widget, cell_area):
            return
        
        if (event is None) or ((event.type == gtk.gdk.BUTTON_PRESS) \
                or (event.type == gtk.gdk.KEY_PRESS \
                    and event.keyval == gtk.keysyms.space)):
            self.clicking = True
            widget.queue_draw()
            gtk.main_iteration()
            model=widget.screen.current_model
            if widget.screen.current_model.validate():
                id = widget.screen.save_current()
                if not self.attrs.get('confirm',False) or \
                        common.sur(self.attrs['confirm']):
                    button_type = self.attrs.get('type', 'workflow')
                    if button_type == 'workflow':
                        result = rpc.session.rpc_exec_auth('/object', 'exec_workflow',
                                                widget.screen.name,
                                                self.attrs['name'], id)
                        if type(result)==type({}):
                            if result['type']== 'ir.actions.act_window_close':
                                widget.screen.window.destroy()
                            else:
                                datas = {}
                                obj = service.LocalService('action.main')
                                obj._exec_action(result,datas)
                    elif button_type == 'object':
                        if not id:
                            return
                        result = rpc.session.rpc_exec_auth(
                            '/object', 'execute',
                            widget.screen.name,
                            self.attrs['name'],
                            [id], model.context_get()
                        )
                        datas = {}
                        obj = service.LocalService('action.main')
                        obj._exec_action(result,datas,context=widget.screen.context)

                    elif button_type == 'action':
                        obj = service.LocalService('action.main')
                        action_id = int(self.attrs['name'])
                        obj.execute(action_id, {'model':widget.screen.name, 'id': id or False,
                            'ids': id and [id] or [], 'report_type': 'pdf'}, context=widget.screen.context)
                    else:
                        raise Exception, 'Unallowed button type'
                    widget.screen.reload()
            else:
                widget.screen.display()
            self.emit("clicked", path)
            def timeout(self, widget):
                self.clicking = False
                widget.queue_draw()
            gobject.timeout_add(60, timeout, self, widget)
gobject.type_register(CellRendererButton)


CELLTYPES = {
    'char': Char,
    'many2one': M2O,
    'date': Date,
    'one2many': O2M,
    'many2many': M2M,
    'selection': Selection,
    'float': Float,
    'float_time': FloatTime,
    'integer': Int,
    'datetime': Datetime,
    'boolean': Boolean,
    'progressbar': ProgressBar,
    'button': CellRendererButton,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

