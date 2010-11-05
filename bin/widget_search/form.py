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

import pygtk
pygtk.require('2.0')

import gtk
from xml.parsers import expat

import sys
import wid_int
import gettext

class _container(object):
    def __init__(self, max_width):
        self.cont = []
        self.max_width = max_width
        self.width = {}
        self.count = 0
    def new(self, col=8):
        self.col = col+1
        table = gtk.Table(1, col)
        table.set_homogeneous(False)
        table.set_col_spacings(3)
        table.set_row_spacings(0)
        table.set_border_width(1)
        self.cont.append( (table, 1, 0) )
    def get(self):
        return self.cont[-1][0]
    def pop(self):
        (table, x, y) = self.cont.pop()
        return table
    def newline(self):
        (table, x, y) = self.cont[-1]
        if x>0:
            self.cont[-1] = (table, 1, y+1)
        table.resize(y+1,self.col)
    def wid_add(self, widget, l=1, name=None, expand=False, ypadding=0):
        self.count += 1
        (table, x, y) = self.cont[-1]
        if l>self.col:
            l=self.col
        if l+x>self.col:
            self.newline()
            (table, x, y) = self.cont[-1]
        if name:
            vbox = gtk.VBox(homogeneous=False, spacing=1)
            label = gtk.Label(name)
            label.set_alignment(0.0, 0.5)
            vbox.pack_start(label, expand=False)
            vbox.pack_start(widget, expand=expand, fill=True)
            wid = vbox
        else:
            wid = widget
        yopt = False
        if expand:
            yopt = yopt | gtk.EXPAND |gtk.FILL
        table.attach(wid, x, x+l, y, y+1, yoptions=yopt, xoptions=gtk.FILL|gtk.EXPAND, ypadding=ypadding, xpadding=5)
        self.cont[-1] = (table, x+l, y)
        width, height=750, 550
        if widget:
            (width, height) = widget.size_request()
        self.width[('%d.%d') % (x,y)] = width
        return wid

class parse(object):
    def __init__(self, parent, fields, model=''):
        self.fields = fields
        self.parent = parent
        self.model = model
        self.col = 8
        self.focusable = None
        self.add_widget_end = []
        self.name_lst=[]

    def dummy_start(self,name,attrs):
            flag=False
            if name =='field' and attrs.has_key('name'):
                    for i in range (0,len(self.name_lst)):
                       if 'name' in self.name_lst[i][1]:
                           if self.name_lst[i][1]['name']==attrs['name']:
                               flag=True
                               if attrs.has_key('select'):
                                   self.name_lst[i]=(name,attrs)
                    if not flag:
                        self.name_lst.append((name,attrs))
            else:
                self.name_lst.append((name,attrs))


    def _psr_start(self, name, attrs):

        if name in ('form','tree'):
            self.title = attrs.get('string','Form')
            self.container.new(self.col)
        elif name=='field':
            val  = attrs.get('select', False) or self.fields[unicode(attrs['name'])].get('select', False)
            if val:
                if int(val) <= 1:
                    self.add_widget(name, attrs, val)
                else:
                    self.add_widget_end.append((name, attrs, val))

    def add_widget(self, name, attrs, val):
        type = attrs.get('widget', self.fields[str(attrs['name'])]['type'])
        self.fields[str(attrs['name'])].update(attrs)
        self.fields[str(attrs['name'])]['model']=self.model
        if type not in widgets_type:
            return False
        widget_act = widgets_type[type][0](str(attrs['name']), self.parent, self.fields[attrs['name']])
        if 'string' in self.fields[str(attrs['name'])]:
            label = self.fields[str(attrs['name'])]['string']+' :'
        else:
            label = None
        size = widgets_type[type][1]
        if not self.focusable:
            self.focusable = widget_act.widget
        wid = self.container.wid_add(widget_act.widget, size, label, int(self.fields[str(attrs['name'])].get('expand',0)))
        if int(val) <= 1:
            wid.show()
        self.dict_widget[str(attrs['name'])] = (widget_act, wid, int(val))

    def add_parameters(self):

        hb_param=gtk.HBox(spacing=3)
        hb_param.pack_start(gtk.Label(_('Limit :')), expand=False, fill=False)

        self.spin_limit = gtk.SpinButton(climb_rate=1, digits=0)
        self.spin_limit.set_numeric(False)
        self.spin_limit.set_adjustment(gtk.Adjustment(value=80, lower=1, upper=sys.maxint, step_incr=10, page_incr=100))
        self.spin_limit.set_property('visible', True)

        hb_param.pack_start(self.spin_limit, expand=False, fill=False)

        hb_param.pack_start(gtk.Label(_('Offset :')), expand=False, fill=False)

        self.spin_offset = gtk.SpinButton(climb_rate=1,digits=0)
        self.spin_offset.set_numeric(False)
        self.spin_offset.set_adjustment(gtk.Adjustment(value=0, lower=0, upper=sys.maxint, step_incr=80, page_incr=100))

        hb_param.pack_start(self.spin_offset, expand=False, fill=False)

        return hb_param

    def _psr_end(self, name):
        pass
    def _psr_char(self, char):
        pass
    def parse(self, xml_data, max_width):
        psr = expat.ParserCreate()
        psr.StartElementHandler = self.dummy_start
        psr.EndElementHandler = self._psr_end
        psr.CharacterDataHandler = self._psr_char
        self.notebooks=[]
        self.container=_container(max_width)

        self.dict_widget={}
        psr.Parse(xml_data)
        for i in self.name_lst:
            self._psr_start(i[0],i[1])
        for i in self.add_widget_end:
            self.add_widget(*i)
        self.add_widget_end=[]

        self.button_param = gtk.Button()
        img = gtk.Image()
        img.set_from_stock('gtk-add', gtk.ICON_SIZE_BUTTON)
        self.button_param.set_image(img)
        self.button_param.set_relief(gtk.RELIEF_NONE)
        self.button_param.set_alignment(0.5, 0.5)
        table = self.container.get()
        table.attach(self.button_param, 0, 1, 0, 1, yoptions=gtk.FILL, xoptions=gtk.FILL, ypadding=2, xpadding=0)

        self.hb_param = self.container.wid_add(self.add_parameters(), l=8, name=_('Parameters :'))


        self.widget =self.container.pop()
        return self.dict_widget

class form(wid_int.wid_int):
    def __init__(self, xml, fields, model=None, parent=None, domain=[], call=None):
        wid_int.wid_int.__init__(self, 'Form', parent)
        parser = parse(parent, fields, model=model)
        self.parent=parent
        self.fields=fields
        self.model = model

        self.parser=parser
        self.call=call

        #get the size of the window and the limite / decalage Hbox element
        ww, hw = 640,800
        if self.parent:
            ww, hw = self.parent.size_request()
        self.widgets = parser.parse(xml, ww)
        self.widget = parser.widget
        #self.widget = parser.widget
        self.widget.show_all()
        self.hb_param = parser.hb_param
        self.button_param = parser.button_param
        self.button_param.connect('clicked', self.toggle)
        self.spin_limit = parser.spin_limit
        self.spin_limit.connect('value-changed', self.limit_changed)
        self.spin_limit.set_activates_default(True)
        self.spin_offset = parser.spin_offset
        self.spin_offset.set_activates_default(True)
        self.focusable = parser.focusable
        self.id=None
        self.name=parser.title
        self.hide()
        value={}
        for x in domain:
            if x[0] in self.widgets:
                if x[1] == '=':
                    self.widgets[x[0]][0]._readonly_set(True)
        for x in self.widgets.values():
            x[0].sig_activate(self.sig_activate)
        self.spin_limit.connect_after('activate', self.sig_activate)
        self.spin_offset.connect_after('activate', self.sig_activate)

    def clear(self, *args):
        self.id=None
        for x in self.widgets.values():
            x[0].clear()

    def show(self):
        for w, widget, value in  self.widgets.values():
            if value >= 2:
                widget.show()
        self.hb_param.show()
        self._hide=False

    def hide(self):
        for w, widget, value in  self.widgets.values():
            if value >= 2:
                widget.hide()
        self.hb_param.hide()
        self._hide=True

    def toggle(self, widget, event=None):
        img = gtk.Image()
        if self._hide:
            self.show()
            img.set_from_stock('gtk-remove', gtk.ICON_SIZE_BUTTON)
            widget.set_image(img)
        else:
            self.hide()
            img.set_from_stock('gtk-add', gtk.ICON_SIZE_BUTTON)
            widget.set_image(img)

    def limit_changed(self, widget):
        self.spin_offset.set_increments(step=self.spin_limit.get_value(), page=100)

    def set_limit(self, value):
        return self.spin_limit.set_value(value)

    def get_limit(self):
        return self.spin_limit.get_value()

    def set_offset(self, val):
        self.spin_offset.set_value(val)

    def get_offset(self):
        return self.spin_offset.get_value()

    def sig_activate(self, *args):
        if self.call:
            obj,fct = self.call
            fct(obj)

    def _value_get(self):
        res = []
        for x in self.widgets:
            res+=self.widgets[x][0].value
        return res

    def _value_set(self, value):
        for x in value:
            if x in self.widgets:
                self.widgets[x][0].value = value[x]

    value = property(_value_get, _value_set, None, _('The content of the form or exception if not valid'))

import calendar
import spinbutton
import spinint
import selection
import char
import checkbox
import reference

widgets_type = {
    'date': (calendar.calendar, 2),
    'datetime': (calendar.calendar, 2),
    'float': (spinbutton.spinbutton, 2),
    'integer': (spinint.spinint, 2),
    'selection': (selection.selection, 2),
    'many2one_selection': (selection.selection, 2),
    'char': (char.char, 2),
    'boolean': (checkbox.checkbox, 2),
    'reference': (reference.reference, 2),
    'text': (char.char, 2),
    'email': (char.char, 2),
    'url': (char.char, 2),
    'many2one': (char.char, 2),
    'one2many': (char.char, 2),
    'one2many_form': (char.char, 2),
    'one2many_list': (char.char, 2),
    'many2many_edit': (char.char, 2),
    'many2many': (char.char, 2),
    'callto': (char.char, 2),
    'sip': (char.char, 2),
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

