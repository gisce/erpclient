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

import os
from base64 import encodestring, decodestring

import pygtk
pygtk.require('2.0')
import gtk

import common
import interface
import tempfile
import urllib

NOIMAGE = file(common.terp_path_pixmaps("noimage.png"), 'rb').read()

class image_wid(interface.widget_interface):

    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent=parent, attrs=attrs)

        self._value = ''
        self.attrs = attrs
        self.height = int(attrs.get('img_height', 100))
        self.width = int(attrs.get('img_width', 300))

        self.widget = gtk.VBox(spacing=3)
        self.event = gtk.EventBox()
        self.event.drag_dest_set(gtk.DEST_DEFAULT_ALL, [
            ('text/plain', 0, 0),
            ('text/uri-list', 0, 1),
            ("image/x-xpixmap", 0, 2)], gtk.gdk.ACTION_MOVE)
        self.event.connect('drag_motion', self.drag_motion)
        self.event.connect('drag_data_received', self.drag_data_received)

        self.is_readonly = False

        self.image = gtk.Image()
        self.event.add(self.image)
        self.widget.pack_start(self.event, expand=True, fill=True)

        self.alignment = gtk.Alignment(xalign=0.5, yalign=0.5)
        self.hbox = gtk.HBox(spacing=3)
        self.but_add = gtk.Button()
        img_add = gtk.Image()
        img_add.set_from_stock('gtk-open', gtk.ICON_SIZE_BUTTON)
        self.but_add.set_image(img_add)
        self.but_add.set_relief(gtk.RELIEF_NONE)
        self.but_add.connect('clicked', self.sig_add)
        self.but_add.set_tooltip_text(_('Set Image'))
        self.hbox.pack_start(self.but_add, expand=False, fill=False)

        self.but_save_as = gtk.Button()
        img_save_as = gtk.Image()
        img_save_as.set_from_stock('gtk-save', gtk.ICON_SIZE_BUTTON)
        self.but_save_as.set_image(img_save_as)
        self.but_save_as.set_relief(gtk.RELIEF_NONE)
        self.but_save_as.connect('clicked', self.sig_save_as)
        self.but_save_as.set_tooltip_text(_('Save As'))
        self.hbox.pack_start(self.but_save_as, expand=False, fill=False)

        self.but_remove = gtk.Button()
        img_remove = gtk.Image()
        img_remove.set_from_stock('gtk-clear', gtk.ICON_SIZE_BUTTON)
        self.but_remove.set_image(img_remove)
        self.but_remove.set_relief(gtk.RELIEF_NONE)
        self.but_remove.connect('clicked', self.sig_remove)
        self.but_remove.set_tooltip_text(_('Clear'))
        self.hbox.pack_start(self.but_remove, expand=False, fill=False)

        self.alignment.add(self.hbox)
        self.widget.pack_start(self.alignment, expand=False, fill=False)

        self.update_img()
        self._old_model = False

    def sig_add(self, widget):
        filter_all = gtk.FileFilter()
        filter_all.set_name(_('All files'))
        filter_all.add_pattern("*")

        filter_image = gtk.FileFilter()
        filter_image.set_name(_('Images'))
        for mime in ("image/png", "image/jpeg", "image/gif"):
            filter_image.add_mime_type(mime)
        for pat in ("*.png", "*.jpg", "*.gif", "*.tif", "*.xpm"):
            filter_image.add_pattern(pat)

        filename = common.file_selection(_('Open...'), parent=self._window, preview=True,
                filters=[filter_image, filter_all])
        if filename:
            self._value = encodestring(file(filename, 'rb').read())
            self.update_img()

    def sig_save_as(self, widget):
        if not self._value:
            common.warning('There is no image!',_('Warning'))
        else:
            filename = common.file_selection(_('Save As...'), parent=self._window,
                    action=gtk.FILE_CHOOSER_ACTION_SAVE)
            if filename:
                file(filename, 'wb').write(decodestring(self._value))
    
    def sig_remove(self, widget):
        self._value = ''
        self.set_value(self._view.model, self._view.model.mgroup.mfields[self.attrs['name']])
        self.update_img()

    def drag_motion(self, widget, context, x, y, timestamp):
        if self.is_readonly:
            return False
        context.drag_status(gtk.gdk.ACTION_COPY, timestamp)
        return True

    def drag_data_received(self, widget, context, x, y, selection, info, timestamp):
        if self.is_readonly:
            return
        if info == 0:
            uri = selection.get_text().split('\n')[0]
            if uri:
                self._value = encodestring(urllib.urlopen(uri).read())
            self.update_img()
        elif info == 1:
            uri = selection.data.split('\r\n')[0]
            if uri:
                self._value = encodestring(urllib.urlopen(uri).read())
            self.update_img()
        elif info == 2:
            data = selection.get_pixbuf()
            if data:
                self._value = encodestring(data)
                self.update_img()

    def update_img(self):
        if not self._value:
            data = NOIMAGE
        else:
            data = decodestring(self._value)

        pixbuf = None
        for type in ('jpeg', 'gif', 'png', 'bmp'):
            loader = gtk.gdk.PixbufLoader(type)
            try:
                loader.write(data, len(data))
            except:
                continue
            pixbuf = loader.get_pixbuf()
            if pixbuf:
                break
        if not pixbuf:
            loader = gtk.gdk.PixbufLoader('png')
            loader.write(NOIMAGE, len(NOIMAGE))
            pixbuf = loader.get_pixbuf()

        loader.close()

        img_height = pixbuf.get_height()
        if img_height > self.height:
            height = self.height
        else:
            height = img_height

        img_width = pixbuf.get_width()
        if img_width > self.width:
            width = self.width
        else:
            width = img_width

        if (img_width / width) < (img_height / height):
            width = float(img_width) / float(img_height) * float(height)
        else:
            height = float(img_height) / float(img_width) * float(width)

        scaled = pixbuf.scale_simple(int(width), int(height), gtk.gdk.INTERP_BILINEAR)
        self.image.set_from_pixbuf(scaled)

    def display(self, model, model_field):
        if not model_field:
            return False
        if (self._old_model != model) or not self._value:
            self._value = model_field.get(model)
        super(image_wid, self).display(model, model_field)
        self.update_img()
        self._old_model = model

    def set_value(self, model, model_field):
        return model_field.set_client(model, self._value or False)

    def _readonly_set(self, value):
        self.but_add.set_sensitive(not value)
        self.but_save_as.set_sensitive(not value)
        self.but_remove.set_sensitive(not value)
        self.is_readonly = value
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

