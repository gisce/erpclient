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

import gtk
import sys
import interface


class spinbutton(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)

        adj = gtk.Adjustment(0.0, -sys.maxint, sys.maxint, 1.0, 5.0)
        self.widget = gtk.SpinButton(adj, 1.0, digits=int( attrs.get('digits',(14,2))[1] ) )
        self.widget.set_numeric(True)
        self.widget.set_activates_default(True)
        self.widget.connect('populate-popup', self._menu_open)
        if self.attrs['readonly']:
            self._readonly_set(True)
        self.widget.connect('focus-in-event', lambda x,y: self._focus_in())
        self.widget.connect('focus-out-event', lambda x,y: self._focus_out())
        self.widget.connect('activate', self.sig_activate)

    def set_value(self, model, model_field):
        self.widget.update()
        model_field.set_client(model, self.widget.get_value())

    def display(self, model, model_field):
        if not model_field:
            self.widget.set_value( 0.0 )
            return False
        super(spinbutton, self).display(model, model_field)
        value = model_field.get(model) or 0.0
        self.widget.set_value( float(value) )

    def _readonly_set(self, value):
        self.widget.set_editable(not value)
        self.widget.set_sensitive(not value)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

