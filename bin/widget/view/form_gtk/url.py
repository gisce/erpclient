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

import gettext
import gtk

import common
import interface
import tools

class url(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent=parent, attrs=attrs)

        self.widget = gtk.HBox(homogeneous=False)

        self.entry = gtk.Entry()
        self.entry.set_max_length(int(attrs.get('size',16)))
        self.entry.set_visibility(not attrs.get('password', False))
        self.entry.set_width_chars(5)
        self.entry.set_property('activates_default', True)
        self.entry.connect('populate-popup', self._menu_open)
        self.entry.connect('activate', self.sig_activate)
        self.entry.connect('focus-in-event', lambda x,y: self._focus_in())
        self.entry.connect('focus-out-event', lambda x,y: self._focus_out())
        self.widget.pack_start(self.entry, expand=True, fill=True)

        self.button = gtk.Button()
        img = gtk.Image()
        if attrs.get('widget',False) == 'email':
            img.set_from_stock('terp-mail-message-new', gtk.ICON_SIZE_BUTTON)
        else:
            img.set_from_stock('gtk-jump-to', gtk.ICON_SIZE_BUTTON)
        self.button.set_image(img)
        self.button.set_size_request(30,30)
        self.button.set_relief(gtk.RELIEF_NONE)
        self.button.set_tooltip_text(_('Open this resource'))
        self.button.connect('clicked', self.button_clicked)
        self.button.set_alignment(0.5, 0.5)
        self.button.set_property('can-focus', False)
        self.widget.pack_start(self.button, expand=False, fill=False)


    def set_value(self, model,model_field):
        return model_field.set_client(model, self.entry.get_text() or False)

    def display(self, model, model_field):
        if not model_field:
            self.entry.set_text('')
            return False
        super(url, self).display(model, model_field)
        self.entry.set_text(model_field.get(model) or '')

    def _readonly_set(self, value):
        self.entry.set_editable(not value)
        self.entry.set_sensitive(not value)

    def button_clicked(self, widget):
        value = self.entry.get_text()
        if value:
            tools.launch_browser(value)

    def _color_widget(self):
        return self.entry

class email(url):
    def button_clicked(self, widget):
        value = self.entry.get_text()
        if value:
            tools.launch_browser('mailto:%s' % value)

class callto(url):
    def button_clicked(self, widget):
        value = self.entry.get_text()
        if value:
            tools.launch_browser('callto:%s' % value)

class sip(url):
    def button_clicked(self, widget):
        value = self.entry.get_text()
        if value:
            tools.launch_browser('sip:%s' % value)

class uri(url):

    def __init__(self, window, parent, model, attrs=None):
        super(uri, self).__init__(window, parent, model, attrs=attrs)

        self.but_new = gtk.Button()
        img_new = gtk.Image()
        img_new.set_from_stock('gtk-find', gtk.ICON_SIZE_BUTTON)
        self.but_new.set_image(img_new)
        self.but_new.set_relief(gtk.RELIEF_NONE)
        self.but_new.connect('clicked', self.sig_new)
        self.widget.pack_start(self.but_new, expand=False, fill=False)
        self.model_field = None

    def sig_new(self, widget=None):
        filename = common.file_selection(_('Open...'),
                parent=self._window)
        if filename:
            self.model_field.set_client(self._view.model, filename)

    def display(self, model, model_field):
        self.model_field = model_field
        return super(uri, self).display(model, model_field)

    def button_clicked(self, widget):
        value = self.entry.get_text()
        common.open_file(value, self._window)




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

