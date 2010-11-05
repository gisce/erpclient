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

import gobject
import gtk
import tools

import gettext

import copy

import wid_common
import common

from widget.screen import Screen
import interface
import service
import rpc
from pager import pager
from modules.gui.window.win_search import win_search
from widget.view.form_gtk.many2one import dialog

class many2many(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)

        self.widget = gtk.VBox(homogeneous=False, spacing=1)

        hb = gtk.HBox(homogeneous=False, spacing=3)
        self.wid_text = gtk.Entry()
        self.wid_text.set_property('width_chars', 13)
        self.wid_text.connect('activate', self._sig_activate)
        self.wid_text.connect('populate-popup', self._menu_open)
        hb.pack_start(self.wid_text, expand=True, fill=True)

        hb.pack_start(gtk.VSeparator(), padding=2, expand=False, fill=False)

        self.wid_but_add = gtk.Button(stock='gtk-add')
        self.wid_but_add.set_relief(gtk.RELIEF_HALF)
        self.wid_but_add.set_focus_on_click(True)
        self.wid_but_add.connect('clicked', self._sig_add)
        hb.pack_start(self.wid_but_add, padding=3, expand=False, fill=False)

        self.wid_but_remove = gtk.Button(stock='gtk-remove')
        self.wid_but_remove.set_relief(gtk.RELIEF_HALF)
        self.wid_but_remove.set_focus_on_click(True)
        self.wid_but_remove.connect('clicked', self._sig_remove)
        hb.pack_start(self.wid_but_remove, expand=False, fill=False)

        hb.pack_start(gtk.VSeparator(), expand=False, fill=True)

        self.context = tools.expr_eval(attrs.get('context',"{}"))

        self.screen = Screen(attrs['relation'], view_type=['tree'],
                views_preload=attrs.get('views', {}),
                row_activate=self.row_activate,
                limit=pager.DEFAULT_LIMIT, context=self.context)
        self.screen.signal_connect(self, 'record-message', self._sig_label)
        self.screen.type = 'many2many'
        self.model = None
        self.model_field = None
        self.name = attrs['name']
        self.pager = pager(object=self, relation=attrs['relation'], screen=self.screen)

        # Button Previous Page
        self.eb_prev_page = self.pager.create_event_box(_('Previous Page'), self._sig_prev_page, 'gtk-goto-first')
        hb.pack_start(self.eb_prev_page, expand=False, fill=False)

        # Button Previous Record
        self.eb_pre = self.pager.create_event_box(_('Previous Record'), self._sig_previous, 'gtk-go-back')
        hb.pack_start(self.eb_pre, expand=False, fill=False)

        # Record display
        self.label = gtk.Label('(0,0)')
        hb.pack_start(self.label, expand=False, fill=False)

        # Button Next
        self.eb_next = self.pager.create_event_box(_('Next Record'), self._sig_next, 'gtk-go-forward')
        hb.pack_start(self.eb_next, expand=False, fill=False)

        # Button Next Page
        self.eb_next_page = self.pager.create_event_box(_('Next Page'), self._sig_next_page, 'gtk-goto-last')
        hb.pack_start(self.eb_next_page, expand=False, fill=False)

        hb.pack_start(gtk.VSeparator(), expand=False, fill=True)

        # LIMIT COMBO
        self.cb = self.pager.create_combo_box(_('Choose Limit'), self.limit_changed)
        hb.pack_start(self.cb, expand=False, fill=False)

        self.widget.pack_start(hb, expand=False, fill=False)
        self.widget.pack_start(gtk.HSeparator(), expand=False, fill=True)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_placement(gtk.CORNER_TOP_LEFT)
        scroll.set_shadow_type(gtk.SHADOW_NONE)

        scroll.add_with_viewport(self.screen.widget)
        self.widget.pack_start(scroll, expand=True, fill=True)

    def row_activate(self, screen):
        gui_window = service.LocalService('gui.window')
        domain = self._view.modelfield.domain_get(self._view.model)
        dia = dialog(screen.name, id=screen.id_get(), attrs=self.attrs, domain=domain, window=screen.window,context=screen.context,target=False, view_type=['form'])
        if dia.dia.get_has_separator():
            dia.dia.set_has_separator(False)
        ok, value = dia.run()
        if ok:
            screen.current_model.validate_set()
            screen.current_view.set_value()
        dia.destroy()

    def destroy(self):
        self.screen.destroy()
        self.widget.destroy()
        del self.widget

    def _menu_sig_default(self, obj):
        res = rpc.session.rpc_exec_auth('/object', 'execute', self.attrs['model'], 'default_get', [self.name])
        self.value = res.get(self.name, False)

    def _sig_add(self, *args):
        domain = self._view.modelfield.domain_get(self._view.model)
        context = self._view.modelfield.context_get(self._view.model)

        records = rpc.session.rpc_exec_auth('/object', 'execute',
                                        self.attrs['relation'], 'name_search',
                                        self.wid_text.get_text(), domain, 'ilike', context)
        ids = [oid for oid, _ in records]
        self.wid_text.set_text('')
        win = win_search(self.attrs['relation'], sel_multi=True, ids=ids, context=context, domain=domain, parent=self._window)
        ids = win.go()

        if ids == None:
            ids = []
        if self.name in self.model.pager_cache:
            self.model.pager_cache[self.name] = list(set(self.model.pager_cache[self.name] + ids))
        else:
            self.model.pager_cache[self.name] = ids
        self.model.is_m2m_modified = True
        self._focus_out()
        self.pager.reset_pager()
        self.pager.search_count()

    def _sig_remove(self, *args):
        remove_ids = self.screen.current_view.sel_ids_get()
        if not remove_ids:
           return
        for oid in remove_ids:
            if oid in self.model.pager_cache[self.name]:
                self.model.pager_cache[self.name].remove(oid)
        self.model.is_m2m_modified = True
        self.screen.remove()
        self.screen.display()
        self._focus_out()
        self.pager.reset_pager()
        self.pager.search_count()

    def _sig_activate(self, *args):
        self._sig_add()

    def _readonly_set(self, ro):
        self.wid_text.set_editable(not ro)
        self.wid_text.set_sensitive(not ro)
        self.wid_but_remove.set_sensitive(not ro)
        self.wid_but_add.set_sensitive(not ro)

    def limit_changed(self,*args):
        self.pager.limit_changed()


    def _sig_prev_page(self, *args):
        self.pager.prev_page()

    def _sig_next_page(self, *args):
        self.pager.next_page()

    def _sig_next(self, *args):
        _, event = args
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.pager.next_record()


    def _sig_previous(self, *args):
        _, event = args
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.pager.prev_record()

    def _sig_label(self, screen, signal_data):
        name = '_'
        if signal_data[0] >= 0:
            name = str(signal_data[0] + 1)
        line = '(%s/%s of %s)' % (name, signal_data[1], signal_data[2])
        self.label.set_text(line)

    def display(self, model, model_field):
        self.model = model
        self.model_field = model_field
        super(many2many, self).display(model, model_field)
        ids = []
        if model_field:
            ids = model_field.get_client(model)
            self.model.pager_cache.setdefault(model_field.name, model.value[model_field.name] or [])
            self.pager.search_count()
        self.screen.clear()
        self.screen.load(ids)
        self.screen.display()
        self.pager.set_sensitivity()
        return True

    def set_value(self, model, model_field):
        self.model.pager_cache.setdefault(model_field.name, model.value[model_field.name] or [])
        if self.name in model.pager_cache:
            model_field.set_client(model, model.pager_cache[self.name])

    def grab_focus(self):
        return self.wid_text.grab_focus()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

