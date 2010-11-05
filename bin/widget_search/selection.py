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
import gobject
import wid_int

class selection(wid_int.wid_int):
    def __init__(self, name, parent, attrs={}):
        wid_int.wid_int.__init__(self, name, parent, attrs)

        self.widget = gtk.combo_box_entry_new_text()
        self.widget.child.set_editable(True)
        self.widget.child.connect('key_press_event', self.sig_key_press)
        self._selection={}
        if 'selection' in attrs:
            self.set_popdown(attrs.get('selection',[]))

    def set_popdown(self, selection):
        self.model = self.widget.get_model()
        self.model.clear()
        self._selection={}
        lst = []
        for (i,j) in selection:
            name = str(j)
            if type(i)==type(1):
                name+=' ('+str(i)+')'
            lst.append(name)
            self._selection[name]=i
        self.widget.append_text('')
        ind = 1
        self.indexes = {}
        for l in lst:
            self.widget.append_text(l)
            self.indexes[l] = ind
            ind += 1
        return lst

    def sig_key_press(self, widget, event):
        completion=gtk.EntryCompletion()
        completion.set_inline_selection(True)
        if (event.type == gtk.gdk.KEY_PRESS) \
            and ((event.state & gtk.gdk.CONTROL_MASK) != 0) \
            and (event.keyval == gtk.keysyms.space):
            self.entry.popup()
        elif not (event.keyval==65362 or event.keyval==65364):
            completion.set_model(self.model)
            widget.set_completion(completion)
            completion.set_text_column(0)

        # Setting the selected  value active on the entry widget while selection is made by keypress
        if self._selection.get(widget.get_text(),''):
            # to let this value count into domain calculation
            self.widget.set_active(self.indexes[widget.get_text()])
    def _value_get(self):
        model = self.widget.get_model()
        index = self.widget.get_active()
        if index>=0:
            res = self._selection.get(model[index][0], False)
            if res:
                return [(self.name,'=',res)]
        return []

    def _value_set(self, value):
        if value==False:
            value=''
        for s in self._selection:
            if self._selection[s]==value:
                self.widget.child.set_text(s)

    def clear(self):
        self.widget.child.set_text('')

    value = property(_value_get, _value_set, None,
      'The content of the widget or ValueError if not valid')

    def _readonly_set(self, value):
        self.widget.set_sensitive(not value)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

