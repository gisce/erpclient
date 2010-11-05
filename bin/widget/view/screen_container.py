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
from gtk import glade

class screen_container(object):
    def __init__(self):
        self.old_widget = False
        self.sw = gtk.ScrolledWindow()
        self.sw.set_shadow_type(gtk.SHADOW_NONE)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vp = gtk.Viewport()
        self.vp.set_shadow_type(gtk.SHADOW_NONE)
        self.vbox = gtk.VBox()
        self.vbox.pack_end(self.sw)
        self.filter_vbox = None
        self.button = None

    def widget_get(self):
        return self.vbox

    def add_filter(self, widget, fnct, clear_fnct, next_fnct, prev_fnct):
        self.filter_vbox = gtk.VBox(spacing=1)
        self.filter_vbox.set_border_width(1)

        self.filter_vbox.pack_start(widget, expand=True, fill=True)

        hb2 = gtk.HButtonBox()
        hb2.set_spacing(5)
        hb2.set_layout(gtk.BUTTONBOX_START)
        hb = gtk.HButtonBox()
        hb.set_spacing(5)
        hb.set_layout(gtk.BUTTONBOX_END)
        hs = gtk.HBox()
        hs.pack_start(hb2)
        hs.pack_start(hb)

        self.but_previous = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.but_previous.connect('clicked', prev_fnct)
        self.but_next = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.but_next.connect('clicked', next_fnct)
        hb2.pack_start(self.but_previous, expand=False, fill=False)
        hb2.pack_start(self.but_next, expand=False, fill=False)

        button_clear = gtk.Button(stock=gtk.STOCK_CLEAR)
        button_clear.connect('clicked', clear_fnct)
        hb.pack_start(button_clear, expand=False, fill=False)

        self.button = gtk.Button(stock=gtk.STOCK_FIND)
        self.button.connect('clicked', fnct)
        self.button.set_property('can_default', True)

        hb.pack_start(self.button, expand=False, fill=False)
        hb.show_all()
        hb2.show_all()

        hs.show_all()
        self.filter_vbox.pack_start(hs, expand=False, fill=False)
        hs = gtk.HSeparator()
        hs.show()
        self.filter_vbox.pack_start(hs, expand=True, fill=False)
        self.vbox.pack_start(self.filter_vbox, expand=False, fill=True)

    def show_filter(self):
        if self.filter_vbox:
            self.filter_vbox.show()
            # TODO find a way to put button has default action
            #self.button.set_property('has_default', True)

    def hide_filter(self):
        if self.filter_vbox:
            self.filter_vbox.hide()

    def set(self, widget):
        if self.vp.get_child():
            self.vp.remove(self.vp.get_child())
        if self.sw.get_child():
            self.sw.remove(self.sw.get_child())
        if not isinstance(widget, gtk.TreeView):
            self.vp.add(widget)
            widget = self.vp
        self.sw.add(widget)
        self.sw.show_all()

    def size_get(self):
        return self.sw.get_child().size_request()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

