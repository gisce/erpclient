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
import gobject
import common
from rpc import RPCProxy
import rpc


class screen_container(object):
    def __init__(self, win_search=False):
        self.old_widget = False
        self.sw = gtk.ScrolledWindow()
        self.sw.set_shadow_type(gtk.SHADOW_NONE)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.vp = gtk.Viewport()
        self.vp.set_shadow_type(gtk.SHADOW_NONE)
        self.vbox = gtk.VBox()
        self.last_active_filter = False
        self.vbox.pack_end(self.sw)
        self.filter_vbox = None
        self.button = None
        self.but_previous = None
        self.but_next = None
        self.help_frame = False
        self.help = {}
        self.win_search = win_search
        self.domain = []
        self.context = {}
        self.handler_id = None

    def widget_get(self):
        return self.vbox

    def fill_filter_combo(self, model, action_name = False):
        if self.handler_id:
            self.action_combo.handler_block(self.handler_id)
            self.action_list.clear()
            self.action_combo.handler_unblock(self.handler_id)
        active = False
        my_acts = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.filters', 'get_filters', model)
        filters_list=[['blk','','-- Filters --']]
        sorted_filters = [[act.get('domain',act['id']),act['context'],act['name']] for act in my_acts]
        sorted_filters.sort(lambda x, y: cmp(x[2], y[2]))
        filters_list += sorted_filters
        filters_list += [['blk','','--Actions--'],['sh','','Save as a Shortcut'],['sf','','Save as a Filter'],['mf','','Manage Filters']]
        for index, action in enumerate(filters_list):
            if action[-1] == action_name:
                active = index
            self.action_list.append(action)
        if active:
            self.action_combo.set_active(active)
        else:
            self.action_combo.set_active(0)

    def fill_limit_combo(self):
        self.limit_combo.clear()
        for lim in [[100,'100'],[200,'200'],[500,'500'],[None,'Unlimited']]:
            self.limit_combo.append(lim)
        self.combo.set_active(0)

    def get_filter(self, filter_name):
        def fnct(filterstore, path, iter, filter_name):
            if filterstore.get(iter, 2)[0].lower() == filter_name.lower():
                self.domain, self.context = filterstore.get(iter, 0, 1)
        self.action_list.foreach(fnct, filter_name)
        return str(self.domain),str(self.context)

    def add_filter(self, widget, fnct, clear_fnct, next_fnct, prev_fnct, execute_action=None, add_custom=None, model=None, limit=100):
        self.filter_vbox = gtk.VBox(spacing=1)
        self.filter_vbox.set_border_width(1)
        if self.help and not self.win_search:
            action_tips = common.action_tips(self.help)
            self.help_frame = action_tips.help_frame
            if self.help_frame:
                self.filter_vbox.pack_start(self.help_frame, expand=False, fill=False, padding=3)
        self.filter_vbox.pack_start(widget, expand=True, fill=True)

        hs = gtk.HBox(homogeneous=False, spacing=0)
        hb1 = gtk.HButtonBox()
        hb1.set_layout(gtk.BUTTONBOX_START)

        button_clear = gtk.Button(stock=gtk.STOCK_CLEAR)
        button_clear.connect('clicked', clear_fnct)
        if self.win_search:
            hb3 = hb1
            hs.pack_start(hb3, expand=False, fill=False)
            hb3.pack_start(button_clear, expand=False, fill=False)
        else:
            hb1.set_spacing(5)
            hb2 = gtk.HBox(homogeneous=False, spacing=0)
            hb3 = gtk.HBox(homogeneous=False, spacing=0)
            hs.pack_start(hb1, expand=False, fill=False)
            hs.pack_start(hb2, expand=True, fill=True)
            hs.pack_end(hb3, expand=False, fill=False)

    #Find Clear Buttons
            self.button = gtk.Button(stock=gtk.STOCK_FIND)
            self.button.connect('clicked', fnct)
            self.button.set_property('can_default', True)
            hb1.pack_start(self.button, expand=False, fill=False)
            hb1.pack_start(button_clear, expand=False, fill=False)

    #Action Filter and custom Filter Button
    #actions combo
            self.action_list = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
            self.action_combo = gtk.ComboBox(self.action_list)
            cell = gtk.CellRendererText()
            self.action_combo.pack_start(cell, True)
            self.action_combo.add_attribute(cell, 'text', 2)

            self.fill_filter_combo(model)
            self.action_combo.set_active(0)
            self.handler_id = self.action_combo.connect('changed', execute_action)

    #Custom Filter Button
            img2 = gtk.Image()
            img2.set_from_stock('gtk-add', gtk.ICON_SIZE_BUTTON)
            self.button_dynamic = gtk.Button()
            self.button_dynamic.set_image(img2)
            self.button_dynamic.set_relief(gtk.RELIEF_NONE)
            self.button_dynamic.set_alignment(0.3,0.3)
            self.button_dynamic.connect('clicked', add_custom)

            hb2.pack_start(gtk.Label(''), expand=True, fill=True)
            hb2.pack_start(self.action_combo, expand=False, fill=False)
            hb2.pack_start(self.button_dynamic, expand=False, fill=False)
            hb2.pack_start(gtk.Label(''), expand=True, fill=True)

# Limit combo
        self.limit_combo = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.combo = gtk.ComboBox(self.limit_combo)
        cell = gtk.CellRendererText()
        self.combo.pack_start(cell, True)
        self.combo.add_attribute(cell, 'text', 1)

        self.selection = []
        hb3.pack_start(self.combo, expand=False, fill=False)
        self.fill_limit_combo()
        self.combo.set_active(0)

#Back Forward Buttons

        self.but_previous = gtk.Button()
        icon = gtk.Image()
        icon.set_from_stock('gtk-go-back', gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.but_previous.set_image(icon)
        self.but_previous.set_relief(gtk.RELIEF_NONE)
        self.but_previous.connect('clicked', prev_fnct)

        icon2 = gtk.Image()
        icon2.set_from_stock('gtk-go-forward', gtk.ICON_SIZE_SMALL_TOOLBAR)
        self.but_next = gtk.Button()
        self.but_next.set_image(icon2)
        self.but_next.set_relief(gtk.RELIEF_NONE)
        self.but_next.connect('clicked', next_fnct)
        next_prev_box = hb3
        if self.win_search:
            next_prev_box = gtk.HBox(homogeneous=False, spacing=0)
            hs.pack_start(next_prev_box, expand=False, fill=False)
        next_prev_box.pack_start(gtk.VSeparator(),padding=3, expand=False, fill=False)
        next_prev_box.pack_start(self.but_previous, expand=False, fill=False)
        next_prev_box.pack_start(self.but_next, expand=False, fill=False)
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

    def get_limit(self):
        if hasattr(self,'limit_combo'):
            try:
                return int(self.limit_combo.get_value(self.combo.get_active_iter(), 0))
            except:
                return False
        else:
            return False


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

