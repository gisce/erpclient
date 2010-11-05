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


import interface
import xml.dom.minidom

import form_gtk
import tree_gtk
import graph_gtk
import calendar_gtk
import gantt_gtk

from form import ViewForm
from list import ViewList
from graph import ViewGraph
from calendar import ViewCalendar
from gantt import ViewGantt

parsers = {
    'form' : (form_gtk.parser_form, ViewForm),
    'tree' : (tree_gtk.parser_tree, ViewList),
    'graph': (graph_gtk.parser_graph, ViewGraph),
    'calendar' : (calendar_gtk.parser_calendar, ViewCalendar),
    'gantt' : (gantt_gtk.parser_gantt, ViewGantt),
}

class widget_parse(interface.parser_interface):
    def parse(self, screen, root_node, fields, toolbar={}):
        for node in root_node.childNodes:
            if not node.nodeType == node.ELEMENT_NODE:
                continue
            if node.localName not in parsers:
                raise Exception(_("This type (%s) is not supported by the GTK client !") % node.localName)
            widget_parser, view_parser = parsers[node.localName]
            # Select the parser for the view (form, tree, graph, calendar or gantt)
            widget = widget_parser(self.window, self.parent, self.attrs, screen)
            wid, child, buttons, on_write = widget.parse(screen.resource, node, fields)
            screen.set_on_write(on_write)

            res = view_parser(self.window, screen, wid, child, buttons, toolbar)
            res.title = widget.title
            return res
        raise Exception(_("No valid view found for this object!"))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

