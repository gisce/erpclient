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
from copy import deepcopy
import gobject
import gettext
import common
import service

import rpc

from widget.screen import Screen
import widget_search

fields_list_type = {
    'checkbox': gobject.TYPE_BOOLEAN
}

class dialog(object):
    def __init__(self, model, domain=None, context=None, window=None, target=False):
        if domain is None:
            domain = []
        if context is None:
            context = {}

        if not window:
            window = service.LocalService('gui.main').window

        self.dia = gtk.Dialog(_('OpenERP - Link'), window,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT)
        self.window = window
        if not target:
            self.dia.set_property('default-width', 760)
            self.dia.set_property('default-height', 500)
            self.dia.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            self.dia.set_icon(common.OPENERP_ICON)

            self.accel_group = gtk.AccelGroup()
            self.dia.add_accel_group(self.accel_group)

            self.but_cancel = self.dia.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            self.but_cancel.add_accelerator('clicked', self.accel_group, gtk.keysyms.Escape, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

            self.but_ok = self.dia.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            self.but_ok.add_accelerator('clicked', self.accel_group, gtk.keysyms.Return, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_placement(gtk.CORNER_TOP_LEFT)
        scroll.set_shadow_type(gtk.SHADOW_NONE)
        self.dia.vbox.pack_start(scroll, expand=True, fill=True)

        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        scroll.add(vp)
        self.screen = Screen(model, view_ids=None, domain=domain, context=context, window=self.dia, view_type=['form'])
        self.screen.new()
        vp.add(self.screen.widget)

        x,y = self.screen.screen_container.size_get()
        width, height = window.get_size()
        vp.set_size_request(min(width - 20, x + 20),min(height - 60, y + 25))
        self.dia.show_all()
        self.screen.display()

    def run(self, datas={}):
        while True:
            try:
                res = self.dia.run()
                if res == gtk.RESPONSE_OK:
                    if self.screen.current_model.validate() and self.screen.save_current():
                        return self.screen.current_model.id
                    else:
                        self.screen.display()
                        self.screen.current_view.set_cursor()
                else:
                    break
            except Exception:
                # Passing all exceptions, most preferably the one of sql_constraint
                pass
        return False

    def destroy(self):
        self.window.present()
        self.dia.destroy()


class win_search(object):
    def __init__(self, model, sel_multi=True, ids=[], context={}, domain = [], parent=None):
        self.model = model
        self.sel_multi = sel_multi
        self.ids = ids
        self.glade = glade.XML(common.terp_path("openerp.glade"),'win_search',gettext.textdomain())
        self.win = self.glade.get_widget('win_search')
        self.win.set_icon(common.OPENERP_ICON)
        if not parent:
            parent = service.LocalService('gui.main').window
        self.parent = parent
        self.win.set_transient_for(parent)
        self.screen = Screen(model, view_type=['tree'], show_search=True, domain=domain,
                             context=context, parent=self.win, win_search=True)
        self.view = self.screen.current_view
        if self.screen.filter_widget.focusable:
            self.screen.filter_widget.focusable.grab_focus()
        self.title = _('OpenERP Search: %s') % self.screen.name
        self.title_results = _('OpenERP Search: %s (%%d result(s))') % (self.screen.name,)
        self.win.set_title(self.title)
        self.view.unset_editable()
        sel = self.view.widget_tree.get_selection()
        if not sel_multi:
            sel.set_mode('single')
        else:
            sel.set_mode(gtk.SELECTION_MULTIPLE)
        self.view.widget_tree.connect('row_activated', self.sig_activate)
        self.view.widget_tree.connect('button_press_event', self.sig_button)
        self.screen.win_search_callback = self.update_title
        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(self.screen.widget)
        vp.show()
        self.sw = gtk.ScrolledWindow()
        self.sw.set_shadow_type(gtk.SHADOW_NONE)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.add(vp)
        self.sw.show()
        self.wid = self.glade.get_widget('win_search_vbox')
        self.wid.pack_start(self.sw)
        self.wid.show_all()

    def sig_activate(self, treeview, path, column, *args):
        self.view.widget_tree.emit_stop_by_name('row_activated')
        if not self.sel_multi:
            self.win.response(gtk.RESPONSE_OK)
        return False

    def sig_button(self, view, event):
        if event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
            self.win.response(gtk.RESPONSE_OK)
        return False

    def find(self, widget=None, *args):
        self.screen.search_filter()
        self.update_title()

    def update_title(self):
        self.ids = self.screen.win_search_ids
        self.reload()
        self.win.set_title(self.title_results % len(self.ids))

    def reload(self):
        sel = self.view.widget_tree.get_selection()
        if sel.get_mode() == gtk.SELECTION_MULTIPLE:
            sel.select_all()


    def sel_ids_get(self):
        return self.screen.sel_ids_get()

    def destroy(self):
        self.parent.present()
        self.win.destroy()

    def go(self):
        ## This is if the user has set some filters by default with search_default_XXX
        if self.ids:
            self.screen.win_search_domain += [('id','in', self.ids)]
            self.find()
        else:
            self.screen.update_scroll()
        end = False
        while not end:
            button = self.win.run()
            if button == gtk.RESPONSE_OK:
                res = self.sel_ids_get() or self.ids
                end = True
            elif button== gtk.RESPONSE_APPLY:
                self.find()
            else:
                res = None
                end = True
        self.destroy()
        if button == gtk.RESPONSE_ACCEPT:
            dia = dialog(self.model, window=self.parent, domain=self.screen.domain_init ,context=self.screen.context)
            id = dia.run()
            res = id and [id] or None
            dia.destroy()
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
