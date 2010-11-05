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

import common
import interface
import gtk
import gobject

import gettext

class selection(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)

        self.widget = gtk.HBox(spacing=3)
        self.entry = gtk.ComboBoxEntry()
        self.child = self.entry.get_child()
        self.child.set_property('activates_default', True)
        self.child.connect('changed', self.sig_changed)
        self.child.connect('populate-popup', self._menu_open)
        self.child.connect('key_press_event', self.sig_key_press)
        self.child.connect('activate', self.sig_activate)
        self.child.connect_after('focus-out-event', self.sig_activate)
        self.entry.set_size_request(int(attrs.get('size', -1)), -1)
        self.widget.pack_start(self.entry, expand=True, fill=True)

        # the dropdown button is not focusable by a tab
        self.widget.set_focus_chain([self.child])
        self.ok = True
        self._selection={}

        self.set_popdown(attrs.get('selection', []))

    def set_popdown(self, selection):
        self.model = gtk.ListStore(gobject.TYPE_STRING)
        self._selection={}
        lst = []
        for (value, name) in selection:
            name = str(name)
            lst.append(name)
            self._selection[name] = value
            i = self.model.append()
            self.model.set(i, 0, name)
        self.entry.set_model(self.model)
        self.entry.set_text_column(0)
        return lst

    def _readonly_set(self, value):
        interface.widget_interface._readonly_set(self, value)
        self.entry.set_sensitive(not value)

    def value_get(self):
        res = self.child.get_text()
        return self._selection.get(res, False)

    def sig_key_press(self, widget, event):
        # allow showing available entries by hitting "ctrl+space"
        completion=gtk.EntryCompletion()
        if hasattr(completion, 'set_inline_selection'):
            completion.set_inline_selection(True)
        if (event.type == gtk.gdk.KEY_PRESS) \
            and ((event.state & gtk.gdk.CONTROL_MASK) != 0) \
            and (event.keyval == gtk.keysyms.space):
            self.entry.popup()
        elif not (event.keyval == gtk.keysyms.Up or event.keyval == gtk.keysyms.Down):
            completion.set_match_func(self.match_func,widget)
            completion.set_model(self.model)
            widget.set_completion(completion)
            completion.set_text_column(0)
    
    def match_func(self, completion, key, iter, widget):
         model = completion.get_model()
         return model[iter][0].lower().find(widget.get_text().lower()) >= 0 and True or False
     
    def sig_activate(self, *args):
        text = self.child.get_text()
        value = False
        if text:
            for txt, val in self._selection.items():
                if not val:
                    continue
                if txt[:len(text)].lower() == text.lower():
                    value = val
                    if len(txt) == len(text):
                        break
        self._view.modelfield.set_client(self._view.model, value, force_change=True)
        self.display(self._view.model, self._view.modelfield)


    def set_value(self, model, model_field):
        model_field.set_client(model, self.value_get())

    def _menu_sig_default_set(self):
        self.set_value(self._view.model, self._view.modelfield)
        super(selection, self)._menu_sig_default_set()

    def display(self, model, model_field):
        self.ok = False
        if not model_field:
            self.child.set_text('')
            self.ok = True
            return False
        super(selection, self).display(model, model_field)
        value = model_field.get(model)
        if not value:
            self.child.set_text('')
        else:
            found = False
            for long_text, sel_value in self._selection.items():
                if sel_value == value:
                    self.child.set_text(long_text)
                    found = True
                    break
        self.ok = True

    def sig_changed(self, *args):
        if self.ok:
            self._focus_out()

    def _color_widget(self):
        return self.child

    def grab_focus(self):
        return self.entry.grab_focus()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

