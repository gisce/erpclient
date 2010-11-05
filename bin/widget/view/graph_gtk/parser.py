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

import locale
import gtk
import tools

from rpc import RPCProxy
from widget.view import interface

class EmptyGraph(object):
    def __init__(self, model, axis, fields, axis_data={}, attrs={}):
        self.widget = gtk.Image()

    def display(self, models):
        pass

class parser_graph(interface.parser_interface):
    def parse(self, model, root_node, fields):
        attrs = tools.node_attributes(root_node)
        self.title = attrs.get('string', 'Unknown')

        on_write = '' #attrs.get('on_write', '')

        axis = []
        axis_data = {}
        for node in root_node:
            node_attrs = tools.node_attributes(node)
            if node.tag == 'field':
                axis.append(str(node_attrs['name']))
                axis_data[str(node_attrs['name'])] = node_attrs

        #
        # TODO: parse root_node to fill in axis
        #

        try:
            import graph
            view = graph.ViewGraph(model, axis, fields, axis_data, attrs)
        except Exception, e:
            import common
            import traceback
            import sys
            tb_s = reduce(lambda x, y: x + y, traceback.format_exception(
                sys.exc_type, sys.exc_value, sys.exc_traceback))
            common.error('Graph', _('Can not generate graph !'), details=tb_s,
                    parent=self.window)
            view = EmptyGraph(model, axis, fields, axis_data, attrs)
        return view, {}, [], on_write




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

