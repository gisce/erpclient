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

import gtk
import sys
import interface


class spinint(interface.widget_interface):

    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)

        adj = gtk.Adjustment(0.0, -sys.maxint, sys.maxint, 1.0, 5.0)
        self.widget = gtk.SpinButton(adj, 1, digits=0)
        self.widget.set_numeric(True)
        self.widget.set_width_chars(5)
        self.widget.set_activates_default(True)
        self.widget.connect('button_press_event', self._menu_open)
        if self.attrs['readonly']:
            self._readonly_set(True)
        self.widget.connect('focus-in-event', lambda x,y: self._focus_in())
        self.widget.connect('focus-out-event', lambda x,y: self._focus_out())
        self.widget.connect('activate', self.sig_activate)

    def set_value(self, model, model_field):
        self.widget.update()
        model_field.set_client(model, self.widget.get_value_as_int())

    def display(self, model, model_field):
        if not model_field:
            self.widget.set_value(0)
            return False
        super(spinint, self).display(model, model_field)
        value = model_field.get(model)
        if isinstance(value, int):
            self.widget.set_value(value)
        elif isinstance(value, float):
            self.widget.set_value(int(value))
        else:
            self.widget.set_value(0)

    def _readonly_set(self, value):
        interface.widget_interface._readonly_set(self, value)
        self.widget.set_editable(not value)
        self.widget.set_sensitive(not value)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

