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

from widget.view import interface
from tools import node_attributes
import gtk
import gtk.glade
import gettext
import common
import rpc
import xdot
import pydot

def quote_string(s):
    return '"' + s + '"'

class Viewdiagram(object):
    def __init__(self,window, model, node_attr, arrow_attr, attrs, screen):
        self.glade = gtk.glade.XML(common.terp_path("openerp.glade"),'widget_view_diagram', gettext.textdomain())
        self.widget = self.glade.get_widget('widget_view_diagram')
        self.model = model
        self.screen = screen
        self.node = node_attr
        self.arrow = arrow_attr
        self.id = None
        if self.screen.current_model:
            self.id = screen.current_model.id
        self.window = xdot.DotWindow(window,self.widget, self.screen, node_attr, arrow_attr, attrs)
        self.draw_diagram()

    def draw_diagram(self):
        if self.screen.current_model:
            self.id = self.screen.current_model.id
        label = self.arrow.get('label',False)
        graph = pydot.Dot(graph_type='digraph')
        if self.id:
            dict = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.ui.view', 'graph_get',
                                             self.id, self.model, self.node.get('object', False),
                                             self.arrow.get('object', False),self.arrow.get('source', False),
                                             self.arrow.get('destination', False),label,(140, 180), rpc.session.context)
            node_lst = {}
            for node in dict['blank_nodes']:
                dict['nodes'][str(node['id'])] = {'name' : node['name']}

            record_list = rpc.session.rpc_exec_auth('/object', 'execute', self.node.get('object', False),'read', dict['nodes'].keys())
            shapes = {}
            for shape_field in self.node.get('shape','').split(';'):
                if shape_field:
                    shape, field = shape_field.split(':')
                    shapes[shape] = field
            colors = {}
            for color_field in self.node.get('bgcolor','').split(';'):
                if color_field:
                    color, field = color_field.split(':')
                    colors[color] = field

            for record in record_list:
                record['shape'] = 'ellipse'
                for shape, expr in shapes.iteritems():
                    if eval(expr, record):
                        record['shape'] = shape
                record['bgcolor'] = ''
                record['style'] = ''
                for color, expr in colors.iteritems():
                    if eval(expr, record):
                        record['bgcolor'] = color.strip()
                        record['style'] = 'filled'
            for node in dict['nodes'].iteritems():
                record = {}
                for res in record_list:
                    if int(node[0]) == int(res['id']):
                        record = res
                        break
                graph.add_node(pydot.Node(quote_string(node[1]['name']),
                                          style=record['style'],
                                          shape=record['shape'],
                                          color=record['bgcolor'],
                                          URL=quote_string(node[1]['name'] + "_" + node[0]  + "_node"),
                                          ))
                node_lst[node[0]]  = node[1]['name']
            for edge in dict['transitions'].iteritems():
                if len(edge) < 1 or str(edge[1][0]) not in node_lst or str(edge[1][1]) not in node_lst:
                    continue
                graph.add_edge(pydot.Edge(quote_string(node_lst[str(edge[1][0])]),quote_string(node_lst[str(edge[1][1])]),
                                          label=dict['label'].get(edge[0], False)[1] or  None,
                                          URL = quote_string(dict['label'].get(edge[0], '')[1] + "_" + edge[0] + "_edge"),
                                          fontsize='10',
                                          ))
            file =  graph.create_xdot()
            if 'node_parent_field' in dict:
                self.node['parent_field'] = dict['node_parent_field']
            if not dict['nodes']:
                file = """digraph G {}"""
            self.window.set_dotcode(file, id=self.id, graph=graph)

    def display(self):
        self.draw_diagram()
        return False

class parser_diagram(interface.parser_interface):
    def __init__(self, window, parent=None, attrs=None, screen=None):
           super(parser_diagram, self).__init__(window, parent=parent, attrs=attrs,
                    screen=screen)
           self.window = window

    def get_view(self, view_name = ''):
        view_id = rpc.session.rpc_exec_auth('/object', 'execute', "ir.model.data", 'search' ,[('name','=', view_name)])
        view = rpc.session.rpc_exec_auth('/object', 'execute', "ir.model.data", 'read' , view_id, ['res_id'])
        return view and view[0]['res_id']

    def parse(self, model, root_node, fields):
        attrs = node_attributes(root_node)
        self.title = attrs.get('string', 'diagram')
        node_attr = None
        arrow_attr = None
        for node in root_node:
            node_attrs = node_attributes(node)
            node_fields = []
            if node.tag == 'node':
                node_attr = node_attrs
            if node.tag == 'arrow':
                arrow_attr = node_attrs

            if node.tag in ['node','arrow']:
                for child in node:
                    if node_attributes(child) and node_attributes(child).get('name', False):
                        node_fields.append(node_attributes(child)['name'])
                fields = rpc.session.rpc_exec_auth('/object', 'execute', node_attrs.get('object',False),'fields_get',node_fields)

                for key, val in fields.iteritems():
                    fields[key]['name'] = key
                attrs[node.tag] = {'string' :node_attributes(root_node).get('string', False),
                               'views':{'form': {'fields': fields,'arch' : node}}
                               }

        if node_attr.get('form_view_ref', False):
            node_attr['form_view_ref'] = self.get_view(node_attr.get('form_view_ref',''))
        else:
            node_attr['form_view_ref'] = False

        if arrow_attr.get('form_view_ref', False):
            arrow_attr['form_view_ref'] = self.get_view(arrow_attr.get('form_view_ref',''))
        else:
            arrow_attr['form_view_ref'] = False

        view = Viewdiagram(self.window, model, node_attr, arrow_attr, attrs, self.screen)

        return view, {}, [], ''

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

