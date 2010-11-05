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
import interface

class progressbar(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)
        self.widget = gtk.ProgressBar()

    def display(self, model, model_field):
        if not model_field:
            self.widget.set_text("/")
            self.widget.set_fraction(0.0)
            return False

        super(progressbar, self).display(model, model_field)
        value = model_field.get(model) or 0.0
        self.widget.set_text('%.2f %%' % (value,) )
        if value<=0.0:
            value = 0.0
        if value>=100.0:
            value = 100.0
        self.widget.set_fraction(value / 100.0)

    def set_value(self, *args, **argv):
        pass

