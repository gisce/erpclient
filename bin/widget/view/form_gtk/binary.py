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

import os
import sys
import tempfile
import time
from datetime import datetime
import base64

import gtk
import gettext

import rpc
import interface
import common
import options
import printer


class wid_binary(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)

        self.widget = gtk.HBox(spacing=3)
        self.wid_text = gtk.Entry()
        #self.wid_text.set_property('activates_default', True)
        self.wid_text.set_property('editable', False)
        self.widget.pack_start(self.wid_text, expand=True, fill=True)

        self.filters = attrs.get('filters', None)
        if self.filters:
            self.filters = self.filters.split(',')

        class binButton(gtk.Button):
            def __init__(self, stock, title, long=True):
                assert stock is not None
                super(binButton, self).__init__()

                box = gtk.HBox()
                box.set_spacing(2)

                img = gtk.Image()
                img.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
                box.pack_start(img, expand=False, fill=False)

                if long:
                    label = gtk.Label(title)
                    label.set_use_underline(False)
                    box.pack_end(label, expand=False, fill=False)
                else:
                    self.set_relief(gtk.RELIEF_NONE)
                    if gtk.pygtk_version >= (2, 12, 0):
                        self.set_property('tooltip-text', title)

                self.add(box)

        self.but_select = binButton('terp-folder-orange', _('Select'), True)
        self.but_select.connect('clicked', self.sig_select)
        self.widget.pack_start(self.but_select, expand=False, fill=False)

        self.but_exec = binButton('terp-folder-blue', _('Open'), True)
        self.but_exec.connect('clicked', self.sig_execute)
        self.widget.pack_start(self.but_exec, expand=False, fill=False)

        self.but_save_as = binButton('gtk-save-as', _('Save As'), True)
        self.but_save_as.connect('clicked', self.sig_save_as)
        self.widget.pack_start(self.but_save_as, expand=False, fill=False)

        self.but_remove = binButton('gtk-clear', _('Clear'), True)
        self.but_remove.connect('clicked', self.sig_remove)
        self.widget.pack_start(self.but_remove, expand=False, fill=False)

        self.model_field = False
        self.has_filename = attrs.get('filename')
        self.data_field_name = attrs.get('name')
        self.__ro = False

    def _readonly_set(self, value):
        self.__ro = value
        if value:
            self.but_select.hide()
            self.but_remove.hide()
        else:
            self.but_select.show()
            self.but_remove.show()

    def _get_filename(self):
        return self._view.model.value.get(self.has_filename) \
               or self._view.model.value.get('name', self.data_field_name) \
               or datetime.now().strftime('%c')

    def sig_execute(self,widget=None):
        try:
            filename = self._get_filename()
            if filename:
                data = self._view.model.value.get(self.data_field_name)
                if not data:
                    data = self._view.model.get(self.data_field_name)[self.data_field_name]
                    if not data:
                        raise Exception(_("Unable to read the file data"))

                ext = os.path.splitext(filename)[1][1:]
                (fileno, fp_name) = tempfile.mkstemp('.'+ext, 'openerp_')

                os.write(fileno, base64.decodestring(data))
                os.close(fileno)

                printer.printer.print_file(fp_name, ext, preview=True)
        except Exception, ex:
            common.message(_('Error reading the file: %s') % str(ex))
            raise

    def sig_select(self, widget=None):
        try:
            # Add the filename from the field with the filename attribute in the view
            filters = []
            if not self.filters:
                filter_file = gtk.FileFilter()
                filter_file.set_name(_('All Files'))
                filter_file.add_pattern('*')
                filters.append(filter_file)
            else:
                for pat in self.filters:
                    filter_file = gtk.FileFilter()
                    filter_file.set_name(str(pat))
                    filter_file.add_pattern(pat)
                    filters.append(filter_file)

            filename = common.file_selection(_('Select a file...'), parent=self._window,filters=filters)
            if filename:
                self.model_field.set_client(self._view.model, base64.encodestring(file(filename, 'rb').read()))
                if self.has_filename:
                    self._view.model.set({self.has_filename: os.path.basename(filename)}, modified=True)
                self._view.display(self._view.model)
        except Exception, ex:
            common.message(_('Error reading the file: %s') % str(ex))

    def sig_save_as(self, widget=None):
        try:
            data = self._view.model.value.get(self.data_field_name)
            if not data:
                data = self._view.model.get(self.data_field_name)[self.data_field_name]
                if not data:
                    raise Exception(_("Unable to read the file data"))

            # Add the filename from the field with the filename attribute in the view
            filename = common.file_selection(
                _('Save As...'),
                parent=self._window,
                action=gtk.FILE_CHOOSER_ACTION_SAVE,
                filename=self._get_filename()
            )
            if filename:
                fp = file(filename,'wb+')
                fp.write(base64.decodestring(data))
                fp.close()
        except Exception, ex:
            common.message(_('Error writing the file: %s') % str(ex))

    def sig_remove(self, widget=None):
        self.model_field.set_client(self._view.model, False)
        if self.has_filename:
            self._view.model.set({self.has_filename: False}, modified=True)
        self.display(self._view.model, False)

    def display(self, model, model_field):
        def btn_activate(state):
            self.but_exec.set_sensitive(state)
            self.but_save_as.set_sensitive(state)
            self.but_remove.set_sensitive((not self.__ro) and state)

        if not model_field:
            self.wid_text.set_text('')
            btn_activate(False)
            return False
        super(wid_binary, self).display(model, model_field)
        self.model_field = model_field
        disp_text = model_field.get_client(model)

        self.wid_text.set_text(disp_text and str(disp_text) or '')
        btn_activate(bool(disp_text))
        return True

    def set_value(self, model, model_field):
        return

    def _color_widget(self):
        return self.wid_text

    def grab_focus(self):
        return self.wid_text.grab_focus()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

