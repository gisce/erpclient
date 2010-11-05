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
import gettext
import xmlrpclib

import common
import service
import view_tree
import rpc
import options
import win_export

class tree(object):
    def __init__(self, view, model, res_id=False, domain=[], context={}, help={}, window=None, name=False):
        self.glade = glade.XML(common.terp_path("openerp.glade"),'win_tree_container',gettext.textdomain())
        self.widget = self.glade.get_widget('win_tree_container')
        self.widget.show_all()
        self.model = view['model']
        self.domain2 = domain
        if view.get('field_parent', False):
            self.domain = []
        else:
            self.domain = domain
        self.view = view
        self.window=window

        self.context=context

        self.tree_res = view_tree.view_tree(view, [], res_id, True, context=context)
        self.tree_res.view.connect('row-activated', self.sig_open)

        sel = self.tree_res.view.get_selection()
        sel.connect('changed', self.expand_one)

        if not name:
            self.name = self.tree_res.name
        else:
            self.name = name
        self.vp = self.glade.get_widget('main_tree_sw')

        wid = self.glade.get_widget('widget_vbox')
        wid.show()

        widget_sc = self.glade.get_widget('win_tree_sc')

        widget_sc.connect('row-activated', self.sc_go)
        self.tree_sc = view_tree.view_tree_sc(widget_sc, self.model)
        self.handlers = {
            'but_reload': self.sig_reload,
            'but_switch': self.sig_edit,
            'but_chroot': self.sig_chroot,
            'but_open': self.sig_action,
            'but_action': self.sig_action,
            'but_print': self.sig_print,
            'but_print_html': self.sig_print_html,
            'but_close': self.sig_close,
            'but_save_as': self.sig_save_as,
        }
        dict = {
            'on_but_sc_go_clicked': self.sc_go,
            'on_but_sc_add_clicked': self.sc_add,
            'on_but_sc_del_clicked': self.sc_del,
            'on_but_expand_collapse_clicked': self.expand_collapse_all,
            'on_tbsc_clicked': self.sc_btn,
        }

        self.help = help
        self.help_frame = False
        wid = self.tree_res.widget_get()
        if self.help:
            action_tips = common.action_tips(self.help)
            self.help_frame = action_tips.help_frame
            if self.help_frame:
                vbox = gtk.VBox()
                vbox.pack_start(self.help_frame, expand=False, fill=False, padding=2)
                vbox.pack_end(wid)
                vbox.show_all()
                wid = vbox
        if self.help_frame:
            self.vp.add_with_viewport(wid)
        else:
            self.vp.add(wid)
        self.sig_reload()

        for signal in dict:
            self.glade.signal_connect(signal, dict[signal])
        self.expand = True

    def sig_reload(self, widget=None):
        self.tree_sc.update()
        ids = rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'search', self.domain2)
        if self.tree_res.toolbar:
            icon_name = 'icon'
            wid = self.glade.get_widget('tree_toolbar')
            for w in wid.get_children():
                wid.remove(w)
            c = {}
            c.update(rpc.session.context)
            res_ids = rpc.session.rpc_exec_auth_try('/object', 'execute', self.view['model'], 'read', ids, ['name',icon_name], c)
            rb = None
            for r in res_ids:
                rb = gtk.RadioToolButton(group=rb)
                l = gtk.Label(r['name'])
                rb.set_label_widget(l)

                icon = gtk.Image()
                if icon_name in r:
                    if hasattr(r[icon_name], 'startswith') and r[icon_name].startswith('STOCK_'):
                        icon.set_from_stock(getattr(gtk, r[icon_name]), gtk.ICON_SIZE_BUTTON)
                    else:
                        try:
                            icon.set_from_stock(r[icon_name], gtk.ICON_SIZE_BUTTON)
                        except:
                            pass

                hb = gtk.HBox(spacing=6)
                hb.pack_start(icon)
                hb.pack_start(gtk.Label(r['name']))
                rb.set_icon_widget(hb)
                rb.show_all()
                rb.set_data('id', r['id'])
                rb.connect('clicked', self.menu_main_clicked)
                self.menu_main_clicked(rb)
                wid.insert(rb, -1)
        else:
            self.tree_res.ids = ids
            self.tree_res.reload()
            wid = self.glade.get_widget('widget_vbox')
            wid.hide()

    def menu_main_clicked(self, widget):
        if widget.get_active():
            id = widget.get_data('id')

            ids = rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'read', [id], [self.view['field_parent']])[0][self.view['field_parent']]

            self.tree_res.ids = ids
            self.tree_res.reload()

            self.expand = False
            self.expand_collapse_all( self.glade.get_widget('button7') )

        return False

    def expand_collapse_all(self, widget):
        if self.expand:
            self.tree_res.view.expand_all()
        else:
            self.tree_res.view.collapse_all()
        self.expand = not self.expand
        if self.expand:
            widget.set_stock_id('gtk-goto-bottom')
        else:
            widget.set_stock_id('gtk-goto-top')

    def expand_one(self, selection):
        model,iter = selection.get_selected_rows()
        if iter:
            self.tree_res.view.expand_row(iter[0],False)

    def sig_print_html(self, widget=None, keyword='client_print_multi', id=None):
        self.sig_action(keyword='client_print_multi', report_type='html')

    def sig_print(self, widget=None, keyword='client_print_multi', id=None):
        self.sig_action(keyword='client_print_multi')

    def sig_action(self, widget=None, keyword='tree_but_action', id=None, report_type='pdf', warning=True):
        ids = self.ids_get()

        if not id and ids and len(ids):
            id = ids[0]
        if id:
            ctx = self.context.copy()
            if 'active_ids' in ctx:
                del ctx['active_ids']
            if 'active_id' in ctx:
                del ctx['active_id']
            obj = service.LocalService('action.main')
            return obj.exec_keyword(keyword, {'model':self.model, 'id':id,
                'ids':ids, 'report_type':report_type, 'window': self.window}, context=ctx,
                warning=warning)
        else:
            common.message(_('No resource selected!'))
        return False

    def sig_open(self, widget, iter, path):
        if not self.sig_action(widget, 'tree_but_open', warning=False):
            if self.tree_res.view.row_expanded(iter):
                self.tree_res.view.collapse_row(iter)
            else:
                self.tree_res.view.expand_row(iter, False)


    def sig_remove(self, widget=None):
        ids = self.ids_get()
        if len(ids):
            if common.sur(_('Are you sure you want\nto remove this record?')):
                try:
                    rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'unlink', ids)
                    self.sig_reload()
                except xmlrpclib.Fault, err:
                    common.message(_('Error removing resource!'))

    # TODO: improve with domain expr
    def sig_chroot(self, widget=None):
        ids = self.ids_get()
        if len(ids) and self.domain:
            id = ids[0]
            datas = {'domain_field': self.domain[0][0], 'domain_value': id[0], 'res_id':id[0]}
            obj = service.LocalService('gui.window')
            obj.create(self.view, self.model, id[0], (self.domain[0],id[0]) )
        else:
            common.message(_('Unable to chroot: no tree resource selected'))

    def sig_new(self, widget=None):
        #datas = {'res_model':self.model, 'domain_field': self.domain[0], 'domain_value': self.id_get(), 'res_id':None}
#       domain = self.domain
#       if self.domain:
#           id = self.id_get()
#           if id:
#               domain=(domain[0],id)
        obj = service.LocalService('gui.window')
        obj.create(None, self.model, None, self.domain)

    def sig_edit(self, widget=None):
        id = False
        ids = self.ids_get()
        if ids:
            id = ids[0]
        elif self.tree_res.toolbar:
            wid = self.glade.get_widget('tree_toolbar')
            for w in wid.get_children():
                if w.get_active():
                    id = w.get_data('id')
        if id:
            obj = service.LocalService('gui.window')
            obj.create(None, self.model, id, self.domain)
        else:
            common.message(_('No resource selected!'))

    def domain_id_get(self, tree=False):
        filter = []
        if self.domain and self.view.get('field_parent', False):
            filter = self.domain
        res = rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'search', filter)
        return res

    def sig_printscreen(self, widget=None):
        ids = self.tree_res.ids
        pass

    def sc_btn(self, widget):
        main = service.LocalService('gui.main')
        main.shortcut_edit(widget, self.model)

    def sc_del(self, widget):
        id = self.tree_sc.sel_id_get()
        if id!=None:
            sc_id = int(self.tree_sc.value_get(2))
            rpc.session.rpc_exec_auth('/object', 'execute', 'ir.ui.view_sc', 'unlink', [sc_id])
        self.tree_sc.update()

    def sc_add(self, widget):
        ids = self.tree_res.sel_ids_get()
        if len(ids):
            res = rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'name_get', ids, rpc.session.context)
            for (id,name) in res:
                uid = rpc.session.uid
                rpc.session.rpc_exec_auth('/object', 'execute', 'ir.ui.view_sc', 'create', {'resource':self.model, 'user_id':uid, 'res_id':id, 'name':name})
        self.tree_sc.update()

    def sc_go(self, widget=None, *args):
        id = self.tree_sc.sel_id_get()
        if id!=None:
            self.sig_action(None, 'tree_but_open', id)

    def ids_get(self):
        res = self.tree_res.sel_ids_get()
        return res

    def id_get(self):
        try:
            if hasattr(self, 'search'):
                return self.search[self.search_pos]
            else:
                return None
        except IndexError:
            return None

    def destroy(self):
        pass

    def sig_close(self, urgent=False):
        return True

    def sig_save_as(self, widget=None):
        fields = []
        win = win_export.win_export(self.model, self.tree_res.sel_ids_get(),
                self.tree_res.fields, [], parent=self.window, context=self.context)
        res = win.go()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

