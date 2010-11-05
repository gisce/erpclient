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

import interface

class checkbox(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)
        self.widget = gtk.CheckButton()
        self.widget.connect('focus-in-event', lambda x,y: self._focus_in())
        self.widget.connect('focus-out-event', lambda x,y: self._focus_out())
        self.widget.connect('button_press_event', self._menu_open)
        self.widget.connect('clicked',self._toggled)
        self.widget.connect('key_press_event', lambda x,y: self._focus_out())

    def _readonly_set(self, value):
        self.widget.set_sensitive(not value)
        
    def _toggled(self, button):
        self._focus_out()
        self._focus_in()
        
    def set_value(self, model, model_field):
        model_field.set_client(model, int(self.widget.get_active()))
     
    def display(self, model, model_field):
        if not model_field:
            self.widget.set_active(False)
            return False
        super(checkbox, self).display(model, model_field)
        self.widget.set_active(bool(model_field.get(model)))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

