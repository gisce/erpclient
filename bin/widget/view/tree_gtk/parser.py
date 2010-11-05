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


import re
import locale
import gtk
import math
import cgi


import tools
import tools.datetime_util

from rpc import RPCProxy
from editabletree import EditableTreeView
from widget.view import interface
from widget.view.list import group_record
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

def send_keys(renderer, editable, position, treeview):
    editable.connect('key_press_event', treeview.on_keypressed, renderer.get_property('text'))
    editable.set_data('renderer', renderer)
    editable.editing_done_id = editable.connect('editing_done', treeview.on_editing_done)
    if isinstance(editable, gtk.ComboBoxEntry):
        editable.connect('changed', treeview.on_editing_done)

def sort_model(column, screen):
    unsaved_model =  [x for x in screen.models if x.id == None or x.modified]
    if unsaved_model:
        res =  common.message(_('You have unsaved record(s) !  \n\nPlease Save them before sorting !'))
        return res
    group_by = screen.context.get('group_by',[])
    group_by_no_leaf = screen.context.get('group_by_no_leaf')
    if column.name in group_by or group_by_no_leaf:
        return True
    screen.current_view.set_drag_and_drop(column.name == 'sequence')
    if screen.sort == column.name:
        screen.sort = column.name+' desc'
    else:
        screen.sort = column.name
    screen.offset = 0
    if screen.type in ('many2many','one2many'):
        screen.sort_domain = [('id','in',screen.ids_get())]
    screen.search_filter()
    if group_by:
        screen.current_view.widget_tree.expand_all()


class parser_tree(interface.parser_interface):

    def parse(self, model, root_node, fields):
        dict_widget = {}
        attrs = tools.node_attributes(root_node)
        on_write = attrs.get('on_write', '')
        editable = attrs.get('editable', False)
        treeview = EditableTreeView(editable)
        treeview.colors = dict()
        self.treeview = treeview

        for color_spec in attrs.get('colors', '').split(';'):
            if color_spec:
                colour, test = color_spec.split(':')
                treeview.colors.setdefault(colour,[])
                treeview.colors[colour].append(test)
        if not self.title:
            self.title = attrs.get('string', 'Unknown')
        treeview.set_property('rules-hint', True)
        treeview.sequence = False
        treeview.connect("motion-notify-event", treeview.set_tooltip)
        treeview.connect('key-press-event', treeview.on_tree_key_press)

        for node in root_node:
            node_attrs = tools.node_attributes(node)

            if node.tag == 'button':
                cell = Cell('button')(node_attrs['string'], treeview, node_attrs)
                cell.name = node_attrs['name']
                cell.attrs = node_attrs
                cell.type = node_attrs.get('type','object')
                cell.context = node_attrs.get('context',{})
                cell.model = model
                treeview.cells[node_attrs['name']] = cell
                col = gtk.TreeViewColumn(None, cell.renderer)
                col.set_clickable(True)
                col.set_cell_data_func(cell.renderer, cell.setter)
                col.name = node_attrs['name']
                col.attrs = node_attrs
                col._type = 'Button'
                col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                col.tooltip = node_attrs['string']
                if node_attrs.get('help',False):
                    col.tooltip = node_attrs['string'] +':\n' + node_attrs['help']
                col.set_fixed_width(20)
                visval = eval(str(node_attrs.get('invisible', 'False')), {'context':self.screen.context})
                col.set_visible(not visval)
                treeview.append_column(col)

            if node.tag == 'field':
                handler_id = False
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

                if fields[fname]['type'] == 'selection':
                    if fields[fname].get('selection',[]):
                        node_attrs['selection'] = fields[fname]['selection']
                fields[fname].update(node_attrs)
                node_attrs.update(fields[fname])
                node_attrs['editable'] = editable
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
                    handler_id = renderer.connect_after('editing-started', send_keys, treeview)

                col = gtk.TreeViewColumn(None, renderer)
                treeview.handlers[col] = handler_id
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
                    'integer': (60, 170),
                    'float': (80, 300),
                    'float_time': (80,150),
                    'date': (70, False),
                    'datetime': (145, 145),
                    'selection': (90, 250),
                    'char': (100, False),
                    'one2many': (50, False),
                    'many2many': (50, False),
                    'boolean': (20, 80),
                    'progressbar':(150, 200)
                }

                if col._type not in twidth:
                    col.set_expand(True)
                else:
                    if 'width' in fields[fname]:
                        min_width = max_width = int(fields[fname]['width'])
                    else:
                        min_width, max_width = twidth[col._type]

                    col.set_min_width(min_width)
                    if max_width:
                        col.set_max_width(max_width)

                col.connect('clicked', sort_model, self.screen)
                col.set_resizable(True)
                #col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                visval = eval(str(fields[fname].get('invisible', 'False')), {'context':self.screen.context})
                col.set_visible(not visval)
                n = treeview.append_column(col)
                calculate = ''
                if 'sum' in node_attrs.keys():
                    calculate = 'sum'
                elif 'avg' in node_attrs.keys():
                    calculate = 'avg'

                if calculate and fields[fname]['type'] \
                        in ('integer', 'float', 'float_time'):
                    label = gtk.Label()
                    label.set_use_markup(True)
                    label_str = fields[fname][calculate] + ': '
                    label_bold = bool(int(fields[fname].get('bold', 0)))
                    if label_bold:
                        label.set_markup('<b>%s</b>' % label_str)
                    else:
                        label.set_markup(label_str)
                    label_sum = gtk.Label()
                    label_sum.set_use_markup(True)
                    dict_widget[n] = (fname, label, label_sum,
                            fields[fname].get('digits', (16,2))[1], label_bold, calculate)
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
        if isinstance(model,group_record):
            return
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
        align = 0
        if self.attrs['type'] in ('float', 'integer', 'boolean'):
            align = 1
        gb = self.treeview.screen.context.get('group_by')
        cell.set_property('font-desc', None)
        cell.set_property('background', None)
        cell.set_property('xalign', align)
        if isinstance(model, group_record) and gb:
            cell.set_property('foreground', 'black')
            font = pango.FontDescription('Times New Roman bold 10')
            if self.field_name in model.field_with_empty_labels:
                cell.set_property('foreground', '#AAAAAA')
                font = pango.FontDescription('italic 10')
            cell.set_property('font-desc', font)
        elif self.treeview.editable:
            field = model[self.field_name]
            cell.set_property('editable',not field.get_state_attrs(model).get('readonly', False))
            self.set_color(cell, model)

    def set_color(self, cell, model, group_by = False):
        field = model[self.field_name]
        cell.set_property('background', None)
        if not field.get_state_attrs(model).get('valid', True):
            cell.set_property('background', common.colors.get('invalid', 'white'))
        elif bool(int(field.get_state_attrs(model).get('required', 0))):
            cell.set_property('background', common.colors.get('required', 'white'))


    def get_color(self, model):
        to_display = False
        try:
            for color, expr in self.treeview.colors.iteritems():
                to_display = False
                for cond in expr:
                    if model.expr_eval(cond, check_load=False):
                        to_display = color
                        break
                if to_display:
                    break
        except Exception:
            # we can still continue if we can't get the color..
            pass
        return to_display or 'black'

    def open_remote(self, model, create, changed=False, text=None):
        raise NotImplementedError

    def get_textual_value(self, model):
        return model[self.field_name].get_client(model) or ''

    def value_from_text(self, model, text):
        return text

class Int(Char):

    def value_from_text(self, model, text):
        return tools.str2int(text)

    def get_textual_value(self, model):
        return tools.locale_format('%d', int(model[self.field_name].get_client(model) or 0))

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
            if self.treeview.screen.context.get('group_by'):
                return value
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
        return tools.datetime_util.server_to_local_timestamp(value[:19],
                self.server_format, self.display_format)

    def value_from_text(self, model, text):
        if not text:
            return False
        return tools.datetime_util.local_to_server_timestamp(text[:19],
                self.display_format, self.server_format)

class Float(Char):
    def get_textual_value(self, model):
        interger, digit = self.attrs.get('digits', (16,2) )
        return tools.locale_format('%.' + str(digit) + 'f', model[self.field_name].get_client(model) or 0.0)

    def value_from_text(self, model, text):
        return tools.str2float(text)

class FloatTime(Char):
    def get_textual_value(self, model):
        val = model[self.field_name].get_client(model) or 0
        t= tools.datetime_util.float_time_convert(val)
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
        selection = dict(self.attrs['selection'])
        return selection.get(model[self.field_name].get(model), '')

    def value_from_text(self, model, text):
        selection = self.attrs['selection']
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
        self.editable = attrs.get('editable',False)
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

class CellRendererButton(object):
    def __init__(self, field_name, treeview=None, attrs=None, window=None):
        self.field_name = field_name
        self.attrs = attrs or {}
        self.treeview = treeview
        self.renderer = gtk.CellRendererPixbuf()
        self.window = window or service.LocalService('gui.main').window
#        self.renderer.set_property('stock-id', self.attrs.get('icon','gtk-help'))

    def __get_states(self):
        return [e for e in self.attrs.get('states','').split(',') if e]

    def __get_model_state(self, widget, cell_area):
        path = widget.get_path_at_pos(int(cell_area.x),int(cell_area.y))
        if not path:
            return False
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

    def attrs_set(self, model):
        if self.attrs.get('attrs',False):
            attrs_changes = eval(self.attrs.get('attrs',"{}"),{'uid':rpc.session.uid})
            for k,v in attrs_changes.items():
                result = False
                for condition in v:
                    result = tools.calc_condition(self,model,condition)
                if result:
                    if k == 'invisible':
                        return 'hide'
                    elif k == 'readonly':
                        return True
        return False

    def setter(self, column, cell, store, iter):
        #TODO
        model = store.get_value(iter, 0)
        if not isinstance(model, group_record) \
               and model.parent and not model.id:
            cell.set_property('stock-id', self.attrs.get('icon','gtk-help'))
            cell.set_property("sensitive", False)
        else:
            current_state = self.get_textual_value(model, 'draft')
            tv = column.get_tree_view()
            valid_states = self.__get_states() or []
            ## This changes the icon according to states or attrs: to not show /hide the icon
            attrs_check = self.attrs_set(model)
            if valid_states and current_state not in valid_states \
                                or isinstance(model, group_record) or attrs_check == 'hide':
                cell.set_property('stock-id', None)
            else:
                cell.set_property('stock-id', self.attrs.get('icon','gtk-help'))
                cell.set_property("sensitive", not attrs_check)

    def open_remote(self, model, create, changed=False, text=None):
        raise NotImplementedError

    def get_textual_value(self, model, default=False):
        if model['state']:
            return model['state'].get_client(model)
        return default

    def value_from_text(self, model, text):
        return 0
#gobject.type_register(CellRendererButton)

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

