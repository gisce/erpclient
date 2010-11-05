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
import base64
import interface
import common

NOIMAGE = file(common.terp_path_pixmaps("noimage.png"), 'rb').read()

class wid_picture(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)

        self.widget = gtk.VBox(homogeneous=False)
        self.wid_picture = gtk.Image()
        self.widget.pack_start(self.wid_picture, expand=True, fill=True)

        self._value=False

    def set_value(self, model, model_field):
        model_field.set( model, self._value )

    def display(self, model, model_field):
        if not model_field:
            return False
        super(wid_picture, self).display(model, model_field)
        value = model_field.get(model)
        self._value = value

        if (isinstance(value, tuple) or isinstance(value,list)) and len(value)==2:
            type, data = value
        else:
            type, data = None, value

        self.wid_picture.set_from_pixbuf(None)
        self.wid_picture.set_from_stock('', gtk.ICON_SIZE_MENU)
        if data:
            if type == 'stock':
                stock, size = data
                if stock.startswith('STOCK_'):
                    stock = getattr(gtk, stock) or ''
                size = getattr(gtk, size)
                self.wid_picture.set_from_stock(stock, size)
            else:
                pixbuf = None
                if value:
                    data = base64.decodestring(data)
                    for ext in [type, 'jpeg', 'gif', 'png', 'bmp']:
                        loader = None
                        try:
                            loader = gtk.gdk.PixbufLoader(ext)
                            loader.write(data, len(data))
                        except:
                            if loader is not None:
                                loader.close()
                            continue
                        pixbuf = loader.get_pixbuf()
                        if pixbuf:
                            break

                if not pixbuf:
                    loader = gtk.gdk.PixbufLoader('png')
                    loader.write(NOIMAGE, len(NOIMAGE))
                    pixbuf = loader.get_pixbuf()

                loader.close()

                self.wid_picture.set_from_pixbuf(pixbuf)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

