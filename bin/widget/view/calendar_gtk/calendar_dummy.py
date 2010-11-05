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

from widget.view.interface import parser_view

class DummyViewCalendar(parser_view):

    def __init__(self, window, screen, widget, children=None, buttons=None,
            toolbar=None, submenu=None, help=None):
        super(DummyViewCalendar, self).__init__(window, screen, widget, children,
                buttons, toolbar, submenu)
        self.view_type = 'dummycalendar'
        self.view = widget
        self.widget = widget.widget
        screen.dummy_cal = True
        self.view.screen = screen


    def cancel(self):
        pass

    def __str__(self):
        pass

    def __getitem__(self, name):
        return None

    def destroy(self):
        pass

    def set_value(self):
        pass

    def reset(self):
        pass

    def reset(self):
        pass

    def display(self):
        pass

    def signal_record_changed(self, *args):
        pass

    def sel_ids_get(self):
        pass

    def on_change(self, callback):
        pass

    def unset_editable(self):
        pass

    def set_cursor(self, new=False):
        pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

