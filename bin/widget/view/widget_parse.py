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


import interface
from lxml import etree

import form_gtk
import tree_gtk
import graph_gtk
import calendar_gtk
import gantt_gtk
import diagram_gtk

from form import ViewForm
from list import ViewList
from graph import ViewGraph
from calendar import ViewCalendar
from diagram import ViewDiagram
from gantt import ViewGantt

parsers = {
    'form' : (form_gtk.parser_form, ViewForm),
    'tree' : (tree_gtk.parser_tree, ViewList),
    'graph': (graph_gtk.parser_graph, ViewGraph),
    'calendar' : (calendar_gtk.parser_calendar, ViewCalendar),
    'gantt' : (gantt_gtk.parser_gantt, ViewGantt),
    'diagram' : (diagram_gtk.parser_diagram, ViewDiagram),
}

class widget_parse(interface.parser_interface):
    def parse(self, screen, node, fields, toolbar={}, submenu={}, help={}):
        if node is not None:
            if node.tag not in parsers:
                raise Exception(_("This type (%s) is not supported by the GTK client !") % node.tag)
            widget_parser, view_parser = parsers[node.tag]
            # Select the parser for the view (form, tree, graph, calendar or gantt)
            widget = widget_parser(self.window, self.parent, self.attrs, screen)
            wid, child, buttons, on_write = widget.parse(screen.resource, node, fields)
            if isinstance(wid, calendar_gtk.EmptyCalendar):
                view_parser = calendar_gtk.DummyViewCalendar
            screen.set_on_write(on_write)
            res = view_parser(self.window, screen, wid, child, buttons, toolbar, submenu, help=help)
            res.title = widget.title
            return res
        raise Exception(_("No valid view found for this object!"))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

