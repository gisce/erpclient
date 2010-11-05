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

import rpc
import gobject
import gtk

import gettext
import service

class view_tree_sc(object):
    ( COLUMN_RES_ID, COLUMN_NAME, COLUMN_ID ) = range(3)
    def __init__(self, tree, model):
        self.last_iter = None
        self.model = model
        self.tree = tree
        self.tree.connect( 'key-press-event', self.on_key_press_event )
        self.tree.get_selection().set_mode('single')

        self.tree.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, [("shortcuts", 0, 0)], gtk.gdk.ACTION_COPY)
        self.tree.enable_model_drag_dest([("shortcuts", 0, 0)], gtk.gdk.ACTION_COPY)
        self.tree.connect("drag_data_received", self.on_drag_data_received)

        column = gtk.TreeViewColumn (_('ID'), gtk.CellRendererText(), text=0)
        self.tree.append_column(column)
        column.set_visible(False)
        cell = gtk.CellRendererText()
        cell.connect( 'edited', self.on_cell_edited )

        column = gtk.TreeViewColumn (_('Description'), cell, text=1)
        self.tree.append_column(column)
#        self.update()

    def update(self):
        store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
        uid =  rpc.session.uid
        sc = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.ui.view_sc', 'get_sc', uid, self.model, rpc.session.context) or []
        for s in sc:
            num = store.append()
            store.set(num,
              self.COLUMN_RES_ID, s['res_id'],
              self.COLUMN_NAME, s['name'],
              self.COLUMN_ID, s['id']
            )
            self.last_iter = num

        self.tree.set_model(store)
        if self.model == 'ir.ui.menu':
            service.LocalService('gui.main').shortcut_set(sc)

    def remove(self, id):
        self.update()

    def add(self, id):
        self.update()

    def value_get(self, col):
        sel = self.tree.get_selection().get_selected()
        if not sel:
            return None
        (model, iter) = sel
        if not iter:
            return None
        return model.get_value(iter, col)

    def sel_id_get(self):
        res = self.value_get(0)
        res = eval(str(res))
        if res:
            return int(res[0])
        return None

    def serv_update(self, ids, action):
        if (action==2):
            self.update()

    def on_cell_edited(self, cell, path_string, new_text):
        model = self.tree.get_model()
        iter = model.get_iter_from_string(path_string)
        old_text = model.get_value( iter, self.COLUMN_NAME )
        if old_text <> new_text:
            res_id = int( model.get_value( iter, self.COLUMN_ID ) )
            rpc.session.rpc_exec_auth('/object', 'execute', 'ir.ui.view_sc', 'write', res_id, { 'name' : new_text }, rpc.session.context )
            model.set(iter, self.COLUMN_NAME, new_text)

        cell.set_property( 'editable', False )

    def on_key_press_event( self, widget, event ):
        if event.keyval == gtk.keysyms.F2:
            column = self.tree.get_column( self.COLUMN_NAME )
            cell = column.get_cell_renderers()[0]
            cell.set_property( 'editable', True )

            selected_row = widget.get_selection().get_selected()
            if selected_row and selected_row[1]:
                (model, iter) = selected_row
                path = model.get_path( iter )
                self.tree.set_cursor_on_cell( path, column, cell, True )

    def check_sanity(self, model, iter_to_copy, target_iter):
        path_of_iter_to_copy = model.get_path(iter_to_copy)
        path_of_target_iter = model.get_path(target_iter)
        return not ( path_of_target_iter[0:len(path_of_iter_to_copy)] == path_of_iter_to_copy )

    def iter_copy(self, treeview, model, iter_to_copy, target_iter, pos):
        data_column_0 = model.get_value(iter_to_copy, self.COLUMN_RES_ID)
        data_column_1 = model.get_value(iter_to_copy, self.COLUMN_NAME)
        data_column_2 = model.get_value(iter_to_copy, self.COLUMN_ID)
        if (pos == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE) or (pos == gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
            new_iter = model.prepend(None)
        elif pos == gtk.TREE_VIEW_DROP_BEFORE:
            new_iter = model.insert_before(target_iter, None)
        elif pos == gtk.TREE_VIEW_DROP_AFTER:
            new_iter = model.insert_after(target_iter, None)
        else:
            new_iter = model.append()
        model.set_value(new_iter, self.COLUMN_RES_ID, data_column_0)
        model.set_value(new_iter, self.COLUMN_NAME, data_column_1)
        model.set_value(new_iter, self.COLUMN_ID, data_column_2)

    def on_drag_data_received(self, treeview, drag_context, x, y, selection, info, eventtime):
        drop_info = treeview.get_dest_row_at_pos(x,y)
        modified = False
        if drop_info:
            path, pos = drop_info
            model, iter_to_copy = treeview.get_selection().get_selected()
            target_iter = model.get_iter(path)
            if target_iter <> iter_to_copy:
                if self.check_sanity(model, iter_to_copy, target_iter):
                    self.iter_copy(treeview, model, iter_to_copy, target_iter, pos)
                    drag_context.finish(True, True, eventtime)
                    treeview.expand_all()
                    modified = True
                else:
                    drag_context.finish(False, False, eventtime)
            else:
                drag_context.finish(False, False, eventtime)
        else:
            model, iter_to_copy = treeview.get_selection().get_selected()
            if iter_to_copy <> self.last_iter:
                self.iter_copy( treeview, model, iter_to_copy, None, None )
                drag_context.finish(True, True, eventtime)
                modified = True
            else:
                drag_context.finish(False, False, eventtime)

        if modified == True:
            model = treeview.get_model()
            iter = model.get_iter_first()
            counter = 0
            while iter:
                res_id = int(model.get_value( iter, self.COLUMN_ID ))
                rpc.session.rpc_exec_auth('/object', 'execute', 'ir.ui.view_sc', 'write', res_id, { 'sequence' : counter }, rpc.session.context )
                counter = counter + 1
                iter = model.iter_next( iter )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

