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

import gobject
import gtk
from interface import parser_view

class ViewGraph(parser_view):

    def __init__(self, window, screen, widget, children=None, buttons=None,
            toolbar=None):
        super(ViewGraph, self).__init__(window, screen, widget, children,
                buttons, toolbar)
        self.view_type = 'graph'
        self.model_add_new = False
        self.view = widget
        self.widget = widget.widget
        self.widget.screen = screen

    def cancel(self):
        pass

    def __str__(self):
        return 'ViewGraph (%s)' % self.screen.resource

    def __getitem__(self, name):
        return None

    def destroy(self):
        self.widget.destroy()
        del self.screen
        del self.widget

    def set_value(self):
        pass

    def reset(self):
        pass

    def display(self):
        self.view.display(self.screen.models)
        return None

    def signal_record_changed(self, *args):
        pass

    def sel_ids_get(self):
        return []

    def on_change(self, callback):
        pass

    def unset_editable(self):
        pass

    def set_cursor(self, new=False):
        pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

