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
import tools
import gtk


class EmptyCalendar(object):
    def __init__(self, model):
        self.widget = gtk.Label(
            _('Calendar View Error !')+'\n\n'+
            _('You must intall the library python-hippocanvas to use calendars.'))

    def display(self, models):
        pass


class parser_calendar(interface.parser_interface):
    def parse(self, model, root_node, fields):
        attrs = tools.node_attributes(root_node)
        self.title = attrs.get('string', 'Unknown')

        on_write = ''

        view = EmptyCalendar(model)

        return view, {}, [], on_write

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

