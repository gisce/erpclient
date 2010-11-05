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
import locale
import options


class textbox(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)

        self.widget = gtk.ScrolledWindow()
        self.widget.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.widget.set_shadow_type(gtk.SHADOW_NONE)
        self.widget.set_size_request(-1, 80)

        self.tv = gtk.TextView()
        self.tv.set_wrap_mode(gtk.WRAP_WORD)
        self.tv.connect('populate-popup', self._menu_open)
        self.tv.set_accepts_tab(False)
        self.tv.connect('focus-out-event', lambda x,y: self._focus_out())
        if not attrs.get('readonly'):
            if options.options['client.form_text_spellcheck']:
                try:
                    import gtkspell
                    gtkspell.Spell(self.tv).set_language(locale.getlocale()[0])
                except:
                    # No word list may not be found for the language
                    pass
        self.widget.add(self.tv)
        self.widget.show_all()

    def _readonly_set(self, value):
        interface.widget_interface._readonly_set(self, value)
        self.tv.set_editable(not value)
        #Commenting following line in order to make text field lines selectable
#        self.tv.set_sensitive(not value)

    def _color_widget(self):
        return self.tv
    
    def grab_focus(self):
        return self.tv.grab_focus()    

    def set_value(self, model, model_field):
        buffer = self.tv.get_buffer()
        iter_start = buffer.get_start_iter()
        iter_end = buffer.get_end_iter()
        current_text = buffer.get_text(iter_start,iter_end,False)
        model_field.set_client(model, current_text or False)

    def display(self, model, model_field):
        super(textbox, self).display(model, model_field)
        value = model_field and model_field.get(model)
        if not value:
            value=''
        buffer = self.tv.get_buffer()
        buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
        iter_start = buffer.get_start_iter()
        buffer.insert(iter_start, value)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

