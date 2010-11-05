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
import pygtk
pygtk.require('2.0')

import gtk
from xml.parsers import expat
import rpc
import wid_int
import tools
from lxml import etree
import uuid

class _container(object):
    def __init__(self, max_width):
        self.cont = []
        self.max_width = max_width
        self.width = {}
        self.count = 0
        self.col=[]
        self.flag = True
    def new(self, col=8):
        self.col.append(col)
        table = gtk.Table(1, col)
        table.set_homogeneous(False)
        table.set_col_spacings(0)
        table.set_row_spacings(0)
        table.set_border_width(0)
        self.cont.append( (table, 1, 0) )
    def get(self):
        return self.cont[-1][0]
    def pop(self):
        (table, x, y) = self.cont.pop()
        if self.cont and self.flag:
            self.flag = False
            tab = []
            tab = [cont[0] for cont in self.cont]
            table_new =  tab + [table]
            return table_new
        self.col.pop()
        return table
    def newline(self,new_table):
        (table, x, y) = self.cont[-1]
        if x>0:
            self.cont[-1] = (table, 1, y+1)
        if new_table:
            self.new(col=4)
#           table= gtk.Table(1, 8)
#        table.resize(y+1,self.col[-1])

    def wid_add(self, widget, colspan=1, name=None, expand=False, xoptions=False, ypadding=0, help=False, rowspan=1):
        self.count += 1
        (table, x, y) = self.cont[-1]
        if name:
            vbox = gtk.VBox(homogeneous=False, spacing=2)
            label = gtk.Label(name)
            label.set_alignment(0.0, 0.0)
            if help:
                try:
                    vbox.set_tooltip_markup('<span foreground=\"darkred\"><b>'+tools.to_xml(name)+'</b></span>\n'+tools.to_xml(help))
                except:
                    pass
                label.set_markup("<sup><span foreground=\"darkgreen\">?</span></sup>"+tools.to_xml(name))
            vbox.pack_start(label, expand=False)
            vbox.pack_start(widget, expand=expand, fill=False)
            wid = vbox
            wid.set_border_width(2)
        else:
            wid = widget
            if help:
                try:
                    wid.set_tooltip_markup('<span foreground=\"darkred\"></span>'+tools.to_xml(help))
                except:
                    pass

        yopt = False
        if expand:
            yopt = yopt | gtk.EXPAND |gtk.FILL
        if not xoptions:
            xoptions = gtk.FILL|gtk.EXPAND
        table.attach(wid, x, x+colspan, y, y+rowspan, yoptions=yopt, xoptions=xoptions, ypadding=ypadding, xpadding=0)
        self.cont[-1] = (table, x+colspan, y)
        wid_list = table.get_children()
        wid_list.reverse()
        table.set_focus_chain(wid_list)
        return wid

class parse(object):
    def __init__(self, parent, fields, model, col=6):
        self.fields = fields
        self.name_lst = []
        self.name_lst1 = []

        all_fields = rpc.session.rpc_exec_auth('/object', 'execute', model, 'fields_get')
        if len(fields) != len(all_fields):
            common_fields = [f for f in all_fields if f in fields]
            for f in common_fields:
                del all_fields[f]
            field_dict = all_fields

            self.fields.update(field_dict)
            self.name_lst1=[('field',(field_dict[x])) for x in field_dict]
        self.parent = parent
        self.model = model
        self.col = col
        self.focusable = None
        self.add_widget_end = []

    def custom_remove(self, button, custom_panel):
        custom_panel.destroy()
        return True

    def _psr_end(self, name):
        pass
    def _psr_char(self, char):
        pass

    def dummy_start(self,name,attrs):
            flag=False
            if name =='field' and 'name' in attrs:
                    for i in range (0,len(self.name_lst)):
                       if 'name' in self.name_lst[i][1]:
                           if self.name_lst[i][1]['name']==attrs['name']:
                               flag=True
                               if 'select' in attrs:
                                   self.name_lst[i]=(name,attrs)
                    if not flag:
                        self.name_lst.append((name,attrs))
            else:
                self.name_lst.append((name,attrs))

    def parse_filter(self, xml_data, max_width, root_node, call=None):
        psr = expat.ParserCreate()
        psr.StartElementHandler = self.dummy_start
        psr.EndElementHandler = self._psr_end
        psr.CharacterDataHandler = self._psr_char
        self.notebooks = []
        dict_widget = {}
        psr.Parse(xml_data)
        self.name_lst += self.name_lst1

        container = _container(max_width)
        attrs = tools.node_attributes(root_node)
        container.new()
        self.container = container

        for node in root_node:
            attrs = tools.node_attributes(node)
            if attrs.get('invisible', False):
                visval = eval(attrs['invisible'], {'context':call[0].context})
                if visval:
                    continue
            if node.tag =='field':
                field_name = str(attrs['name'])
                field_dic = self.fields[field_name]
                type = attrs.get('widget', field_dic['type'])
                field_dic.update(attrs)
                field_dic['model'] = self.model
                if type not in widgets_type:
                    continue
                widget_act = widgets_type[type][0](field_name, self.parent, field_dic, screen=call[0])
                if 'string' in field_dic:
                    label = field_dic['string']+' :'
                else:
                    label = None
                if not self.focusable:
                    self.focusable = widget_act.widget

                mywidget = widget_act.widget
                if node is not None and len(node):
                    mywidget = gtk.HBox(homogeneous=False, spacing=0)
                    mywidget.pack_start(widget_act.widget,expand=True,fill=True)
                    for node_child in node:
                        attrs_child = tools.node_attributes(node_child)
                        if attrs_child.get('invisible', False):
                            visval = eval(attrs_child['invisible'], {'context':call[0].context})
                            if visval:
                                continue
                        if node_child.tag == 'filter':
                            widget_child = widgets_type['filter'][0]('', self.parent, attrs_child, call)
                            mywidget.pack_start(widget_child.widget)
                            dict_widget[str(attrs['name']) + str(uuid.uuid1())] = (widget_child, mywidget, 1)
                        elif node_child.tag == 'separator':
                            if attrs_child.get('orientation','vertical') == 'horizontal':
                                sep = gtk.HSeparator()
                                sep.set_size_request(30,5)
                                mywidget.pack_start(sep,False,True,5)
                            else:
                                sep = gtk.VSeparator()
                                sep.set_size_request(3,40)
                                mywidget.pack_start(sep,False,False,5)
#                    mywidget.pack_start(widget_act.widget,expand=False,fill=False)
                xoptions = gtk.SHRINK
                wid = container.wid_add(mywidget, 1,label, int(self.fields[str(attrs['name'])].get('expand',0)),xoptions=xoptions)
                dict_widget[str(attrs['name'])] = (widget_act, wid, 1)

            elif node.tag == 'filter':
                name = str(attrs.get('string','filter'))
                widget_act = filter.filter(name, self.parent, attrs, call)
                help = attrs.get('help', False) or name
                wid = container.wid_add(widget_act.butt, xoptions=gtk.SHRINK, help=help)
                dict_widget[name + str(uuid.uuid1())] = (widget_act, widget_act, 1)

            elif node.tag == 'separator':
                if attrs.get('orientation','vertical') == 'horizontal':
                    sep_box = gtk.VBox(homogeneous=False, spacing=0)
                    sep = gtk.HSeparator()
                    sep.set_size_request(30,5)
                    sep_box.pack_start(gtk.Label(''),expand=False,fill=False)
                    sep_box.pack_start(sep,False,True,5)
                else:
                    sep_box = gtk.HBox(homogeneous=False, spacing=0)
                    sep = gtk.VSeparator()
                    sep.set_size_request(3,45)
                    sep_box.pack_start(sep,False,False,5)
                wid = container.wid_add(sep_box,xoptions=gtk.SHRINK)
                wid.show()
            elif node.tag=='newline':
                container.newline(node.getparent() is not None and node.getparent().tag == 'group')

            elif node.tag=='group':
                if attrs.get('invisible', False):
                    continue
                if attrs.get('expand', False):
                    attrs['expand'] = tools.expr_eval(attrs.get('expand',False),{'context':call[0].context})
                    frame = gtk.Expander(attrs.get('string', None))
                    frame.set_expanded(bool(attrs['expand']))
                else:
                    frame = gtk.Frame(attrs.get('string', None))
                    if not attrs.get('string', None):
                        frame.set_shadow_type(gtk.SHADOW_NONE)
                frame.attrs = attrs
                frame.set_border_width(0)
                container.wid_add(frame, colspan=1, expand=int(attrs.get('expand',0)), ypadding=0)
                container.new()
                widget, widgets = self.parse_filter(xml_data, max_width, node, call= call)
                dict_widget.update(widgets)
                if isinstance(widget, list):
                    tb = gtk.Table(1, 1, True)
                    row = 1
                    for table in widget:
                        tb.attach(table, 0, 1, row-1, row)
                        row +=1
                    frame.add(tb)
                else:
                    frame.add(widget)
                if not attrs.get('string', None):
                    container.get().set_border_width(0)
                container.pop()
        self.widget = container.pop()
        self.container = container
        return self.widget, dict_widget

class form(wid_int.wid_int):
    def __init__(self, xml_arch, fields, model=None, parent=None, domain=[], call=None, col=6):
        wid_int.wid_int.__init__(self, 'Form', parent)
        xml_arch = self.xml_process(xml_arch)
        root_node = etree.XML(xml_arch)
        assert root_node.tag == 'search'
        parser = parse(parent, fields, model=model, col=col)
        self.parent = parent
        self.fields = fields
        self.model = model
        self.parser = parser
        self.call = call
        self.custom_widgets = {}
        #get the size of the window and the limite / decalage Hbox element
        ww, hw = 640,800
        if self.parent:
            ww, hw = self.parent.size_request()
        self.groupby = []
        self.widget, self.widgets = parser.parse_filter(xml_arch, ww, root_node, call=call)
        self.rows = 4
        self.focusable = parser.focusable
        self.id=None
        self.widget.show_all()
        self.name="" #parser.title
        self.show()
        for x in self.widgets.values():
            x[0].sig_activate(self.sig_activate)

    def xml_process(self,xml_arch):
        root = etree.fromstring(xml_arch)
        group =  etree.Element("group")
        em_list = []
        for element in root.iterchildren():
            if element.tag == "group":
                em_list.append(element)
            elif element.tag == "newline":
                if group.getchildren():
                    em_list.append(group)
                em_list.append(element)
                group =  etree.Element("group")
            else:
                group.append(element)
        if group.getchildren():
            em_list.append(group)

        search =  etree.Element("search")
        for element in em_list:
            search.append(element)
        return etree.tostring(search)

    def clear(self, *args):
        for panel in self.custom_widgets:
            self.custom_widgets[panel][0].widget.destroy()
        self.custom_widgets = {}
        self.id = None
        for x in self.widgets.values():
            x[0].clear()

    def show(self):
        for w, widget, value in  self.widgets.values():
            if w.attrs.get('default_focus'):
                w.grab_focus()
            if value >= 2:
                widget.show()
        self._hide=False

    def hide(self):
        for w, widget, value in  self.widgets.values():
            if value >= 2:
                widget.hide()
        self._hide=True

    def remove_custom(self, button, panel):
        button.parent.destroy()
        # Removing the Destroyed widget from Domain calculation
        for element in self.custom_widgets.keys():
            if self.custom_widgets[element][0] == panel:
                del self.custom_widgets[element]
                break
        return True

    def add_custom(self, widget, table, fields):
        new_table = gtk.Table(1,1,False)
        panel = widgets_type['custom_filter'][0]('', self.parent,{'fields':fields},call=self.remove_custom)
        x =  self.rows
        new_table.attach(panel.widget,0, 1, x, x+1, xoptions=gtk.FILL, yoptions=gtk.FILL , ypadding=2, xpadding=0)
        panelx = 'panel' + str(x)
        panel.sig_activate(self.sig_activate)
        self.custom_widgets[panelx] = (panel, new_table, 1)
        table.attach(new_table, 1, 9, x, x+1)
        self.rows += 1
        table.show_all()
        return panel

    def toggle(self, widget, event=None):
        pass

    def sig_activate(self, *args):
        if self.call:
            obj,fct = self.call
            fct(obj)

    def _value_get(self):
        domain = []
        context = {}

        for x in self.widgets.values() + self.custom_widgets.values():
            domain += x[0].value.get('domain',[])
            ctx = x[0].value.get('context',{})
            ctx_groupby = ctx.pop('group_by', False)
            ctx_remove_group = ctx.pop('remove_group',False)
            if ctx_groupby:
                if not isinstance(ctx_groupby, list):
                    ctx_groupby = [ctx_groupby]
                [self.groupby.append(x) for x in ctx_groupby if x not in self.groupby]
            elif ctx_remove_group:
                if not isinstance(ctx_remove_group, list):
                    ctx_remove_group = [ctx_remove_group]
                [self.groupby.remove(x) for x in ctx_remove_group if x in self.groupby]
            context.update(ctx)
        if self.groupby:
            context.update({'group_by':self.groupby})
        if domain:
            if len(domain)>1 and domain[-2] in ['&','|']:
                if len(domain) == 2:
                    domain = [domain[1]]
                else:
                    res1 = domain[:-2]
                    res2 = domain[-1:]
                    domain = res1 + res2
        return {'domain':domain, 'context':context}

    def _value_set(self, value):
        for x in value:
            if x in self.widgets:
                self.widgets[x][0].value = value[x]
            if x in self.custom_widgets:
                self.custom_widgets[x][0].value = value[x]

    value = property(_value_get, _value_set, None, _('The content of the form or exception if not valid'))

import calendar
import spinbutton
import spinint
import selection
import char
import checkbox
import reference
import filter
import custom_filter

widgets_type = {
    'date': (calendar.calendar, 2),
    'datetime': (calendar.datetime, 2),
    'float': (spinbutton.spinbutton, 2),
    'float_time': (spinbutton.spinbutton, 2),
    'integer': (spinint.spinint, 2),
    'selection': (selection.selection, 2),
    'char': (char.char, 2),
    'boolean': (checkbox.checkbox, 2),
    'reference': (reference.reference, 2),
    'text': (char.char, 2),
    'text_wiki':(char.char, 2),
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
    'filter' : (filter.filter,1),
    'custom_filter' : (custom_filter.custom_filter,6)
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
