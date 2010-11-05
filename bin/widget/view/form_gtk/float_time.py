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

import re
import gettext
import gtk

import math
import locale

import common
import interface
from tools import datetime_util

class float_time(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent=parent, attrs=attrs)

        self.widget = gtk.Entry()
        self.widget.set_max_length(int(attrs.get('size',11)))
        self.widget.set_visibility(not attrs.get('password', False))
        self.widget.set_width_chars(5)
        self.widget.set_property('activates_default', True)

        self.widget.connect('populate-popup', self._menu_open)
        self.widget.connect('activate', self.sig_activate)
        self.widget.connect('focus-in-event', lambda x,y: self._focus_in())
        self.widget.connect('focus-out-event', lambda x,y: self._focus_out())

    def text_to_float(self, text):
        try:
            if text and ':' in text:
                return round(int(text.split(':')[0]) + int(text.split(':')[1]) / 60.0,4)
            else:
                return locale.atof(text)
        except:
            pass
        return 0.0

    def set_value(self, model, model_field):
        v = self.widget.get_text()
        if not v:
            return model_field.set_client(model, 0.0)
        return model_field.set_client(model, self.text_to_float(v))

    def display(self, model, model_field):
        if not model_field:
            self.widget.set_text('00:00')
            return False
        super(float_time, self).display(model, model_field)
        val = model_field.get(model)
        t= datetime_util.float_time_convert(val)
        if val<0:
            t = '-'+t
        self.widget.set_text(t)

    def _readonly_set(self, value):
        self.widget.set_editable(not value)
        self.widget.set_sensitive(not value)

    def grab_focus(self):
        return self.widget.grab_focus()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

