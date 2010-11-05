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
from gtk import glade
import gettext

import common
import wid_int
import rpc
import tools

class reference(wid_int.wid_int):
    def __init__(self, name, parent, attrs={},screen=None):
        wid_int.wid_int.__init__(self, name, parent, attrs, screen)

        self.widget = gtk.combo_box_entry_new_text()
        self.widget.child.set_editable(False)
        self.set_popdown(attrs.get('selection', []))
        if self.default_search:
                self._value_set(str(self.default_search))

    def get_model(self):
        res = self.widget.child.get_text()
        return self._selection.get(res, False)

    def set_popdown(self, selection):
        model = self.widget.get_model()
        model.clear()
        self._selection={}
        lst = []
        for (i,j) in selection:
            name = str(j)
            if type(i)==type(1):
                name+=' ('+str(i)+')'
            lst.append(name)
            self._selection[name]=i
        self.widget.append_text('')
        for l in lst:
            self.widget.append_text(l)
        return lst

    def _value_get(self):
        if self.get_model():
            return {'domain': [(self.name, 'like', self.get_model()+',')]}
        return {}

    def _value_set(self, value):
        if value==False:
            value=''
        for s in self._selection:
            if self._selection[s]==value:
                self.widget.child.set_text(s)
    
         
    def grab_focus(self):
        return self.widget.child.grab_focus()


    value = property(_value_get, _value_set, None, _('The content of the widget or ValueError if not valid'))

    def clear(self, widget=None):
        self.value = ''

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

