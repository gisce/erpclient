# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2008-2009 B2CK, Bertrand Chenal, Cedric Krier (D&D in lists)
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

import gobject
import gtk
import tools
import itertools
import copy
import rpc
from rpc import RPCProxy
import service
import locale
import common
from interface import parser_view
from widget.model.record import ModelRecord

class field_record(object):
    def __init__(self, name):
        self.name = name

    def get_client(self, *args):
        if isinstance(self.name, (list,tuple)):
            return self.name[1]
        return self.name

    def get(self, *args):
        if isinstance(self.name, (list,tuple)):
            return self.name[0]
        return self.name

    def get_state_attrs(self, *args, **argv):
        return {}

    def set_client(self,*args):
        pass

    def set(self,*args):
        pass

class group_record(object):

    def __init__(self, value={}, ctx={}, domain=[], mgroup=None, child = True, sort_order=False):
        self.list_parent = None
        self._children = None
        self.domain = domain
        self.ctx = ctx
        self.value = value
        self.id = False
        self.has_children = child
        self.mgroup = mgroup
        self.field_with_empty_labels = []
        self.sort_order = sort_order

    def getChildren(self):
        if self._children is None:
            self._children = list_record(self.mgroup, parent=self, context=self.ctx, domain=self.domain,sort_order=self.sort_order)
        #self._children.load()
        return self._children

    def setChildren(self, c):
        self._children = c
        return c

    children = property(getChildren, setChildren)

    def expr_eval(self, *args, **argv):
        return True

    def __setitem__(self, attr, val):
        pass

    def __getitem__(self, attr):
        return field_record(self.value.get(attr, ''))

def echo(fn):
    def wrapped(self, *v, **k):
        name = fn.__name__
        res = fn(self, *v, **k)
        return res
    return wrapped


class list_record(object):
    def __init__(self, mgroup, parent=None, context=None, domain=None, sort_order=False):
        self.mgroup = mgroup
        self.mgroup.list_parent = parent
        self.mgroup.list_group = self
        self.parent = parent
        self.context = context or {}
        self.domain = domain
        self.loaded = False
        self.sort_order = sort_order
        self.lst = []
        self.load()

    def add_dummny_record(self, group_field):
        record = { group_field:'This group is now empty ! Please refresh the list.'}
        rec = group_record(record, ctx=self.context, domain=self.domain, mgroup=self.mgroup, child = False)
        self.add(rec)

    def load(self):
        if self.loaded:
            return
        self.loaded = True
        gb = self.context.get('group_by', [])
        no_leaf = self.context.get('group_by_no_leaf', False)
        if gb or no_leaf:
            records = rpc.session.rpc_exec_auth('/object', 'execute', self.mgroup.resource, 'read_group',
                self.context.get('__domain', []) + (self.domain or []), self.mgroup.fields.keys(), gb, 0, False, self.context)
            if not records and self.parent:
                self.add_dummny_record(gb[0])
            else:
                for r in records:
                    child = True
                    __ctx = r.get('__context', {})
                    inner_gb = __ctx.get('group_by', [])
                    if no_leaf and not len(inner_gb):
                        child = False
                    ctx = {'__domain': r.get('__domain', []),'group_by_no_leaf':no_leaf}
                    if not no_leaf:
                        ctx.update({'__field':gb[-1]})
                    ctx.update(__ctx)
                    rec = group_record(r, ctx=ctx, domain=self.domain, mgroup=self.mgroup, child = child,sort_order=self.sort_order)
                    for field in gb:
                        if not rec.value.get(field, False):
                            field_type = self.mgroup.fields.get(field, {}).get('type', False)
                            if field in inner_gb or field_type in ('integer', 'float', 'boolean'):
                                continue
                            rec.value[field] = 'Undefined'
                            rec.field_with_empty_labels.append(field)
                    self.add(rec)
        else:
            if self.context.get('__domain') and not no_leaf:
                ids = rpc.session.rpc_exec_auth('/object', 'execute', self.mgroup.resource, 'search', self.context.get('__domain'), 0, False, self.sort_order)
                if not ids:
                     self.add_dummny_record(self.context['__field'])
                else:
                    self.mgroup.load(ids)
                    res= []
                    for id in ids:
                        res.append(self.mgroup.get_by_id(id))
                    self.add_list(res)
            else:
                if not no_leaf:
                    self.lst = self.mgroup.models
                    for m in self.mgroup.models:
                        m.list_group = self
                        m.list_parent = self.parent
                #self.add_list(self.mgroup.models)

    def add(self, lst):
        lst.list_parent = self.parent
        lst.list_group = self
        self.lst.append(lst)


    def add_list(self, lst):
        for l in lst:
            self.add(l)

    def __getitem__(self, i):
        self.load()
        return self.lst[i]

    def __len__(self):
        self.load()
        return len(self.lst)

class AdaptModelGroup(gtk.GenericTreeModel):
    def __init__(self, model_group, context={}, domain=[], sort_order=False):
        super(AdaptModelGroup, self).__init__()
        self.model_group = model_group
        self.context = context or {}
        self.domain = domain
        self.models = list_record(model_group, context=context, domain=self.domain, sort_order=sort_order)
        self.set_property('leak_references', False)

    def added(self, modellist, position):
        self.models.loaded = False
        path = len(modellist) - 1
        self.emit('row_inserted',path,self.get_iter(path))

    def cancel(self):
        pass

    def move(self, path, position):
        idx = path[0]
        self.model_group.model_move(self.models[idx], position)

    def removed(self, lst, position):
        self.emit('row_deleted', position)
        self.invalidate_iters()

    def append(self, model):
        self.model_group.model_add(model)

    def prepend(self, model):
        self.model_group.model_add(model, 0)

    def remove(self, iter):
        idx = self.get_path(iter)[0]
        self.model_group.model_remove(self.models[idx])
        self.invalidate_iters()

    def saved(self, id):
        return self.model_group.writen(id)

    def __len__(self):
        return len(self.models)

    ## Mandatory GenericTreeModel methods

    def on_get_flags(self):
        if self.context.get('group_by'):
            return gtk.TREE_MODEL_ITERS_PERSIST
        return gtk.TREE_MODEL_LIST_ONLY

    def on_get_n_columns(self):
        return 1

    def on_get_column_type(self, index):
        return gobject.TYPE_PYOBJECT

    def on_get_path(self, iter):
        iter2 = iter
        result = []
        while iter:
            try:
                result.insert(0,iter.list_group.lst.index(iter))
                iter = iter.list_parent
            except:
                return (0,0)
        return tuple(result)

    def on_get_iter(self, path):
        if not isinstance(path,(list, tuple)):
            path = (path,)
        mods = self.models
        for p in path[:-1]:
            mods = mods[p].children
        if path[-1]<len(mods):
            return mods[path[-1]]
        return None

    def on_get_value(self, node, column):
        assert column == 0
        return node

    def on_iter_next(self, node):
        try:
            i = node.list_group.lst.index(node) + 1
            return node.list_group[i]
        except IndexError:
            return None

    def on_iter_has_child(self, node):
        res = getattr(node,'has_children', False)
        return res

    def on_iter_children(self, node):
        res = getattr(node, 'children', [])
        return res and res[0] or []

    def on_iter_n_children(self, node):
        return len(getattr(node, 'children', []))

    def on_iter_nth_child(self, node, n):
        if node is None:
            return self.on_get_iter([n])
        if n<len(getattr(node,'children',[])):
            return getattr(node,'children',[])[n]
        return None

    def on_iter_parent(self, node):
        return node.list_parent

class ViewList(parser_view):
    def __init__(self, window, screen, widget, children=None, buttons=None,
            toolbar=None, submenu=None, help={}):
        super(ViewList, self).__init__(window, screen, widget, children,
                buttons, toolbar, submenu=submenu)
        self.store = None
        self.view_type = 'tree'
        self.model_add_new = True
        self.widget = gtk.VBox()
        self.widget_tree = widget
        scroll = gtk.ScrolledWindow()
        scroll.add(self.widget_tree)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.widget.pack_start(scroll, expand=True, fill=True)
        self.widget_tree.screen = screen
        self.reload = False
        children = dict(sorted(children.items(), lambda x, y: cmp(x[0], y[0])))
        self.children = children
        self.changed_col = []
        self.tree_editable = False
        self.is_editable = widget.editable
        self.columns = self.widget_tree.get_columns()
        if self.widget_tree.sequence:
            self.set_drag_and_drop(True)
        if children:
            hbox = gtk.HBox()
            self.widget.pack_start(hbox, expand=False, fill=False, padding=2)
            for c in children:
                hbox2 = gtk.HBox()
                hbox2.pack_start(children[c][1], expand=True, fill=False)
                hbox2.pack_start(children[c][2], expand=True, fill=False)
                hbox.pack_start(hbox2, expand=False, fill=False, padding=12)
            hbox.show_all()

        self.display()
        self.widget_tree.connect('button_press_event', self.__contextual_menu)
        self.widget_tree.connect_after('row-activated', self.__sig_switch)
        selection = self.widget_tree.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.connect('changed', self.__select_changed)

    def set_drag_and_drop(self,dnd=False):
        if dnd or self.screen.context.get('group_by'):
            self.widget_tree.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                    [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),],
                    gtk.gdk.ACTION_MOVE)
            self.widget_tree.drag_source_set(gtk.gdk.BUTTON1_MASK | gtk.gdk.BUTTON3_MASK,
                    [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),],
                    gtk.gdk.ACTION_MOVE)
            self.widget_tree.enable_model_drag_dest(
                    [('MY_TREE_MODEL_ROW', gtk.TARGET_SAME_WIDGET, 0),],
                    gtk.gdk.ACTION_MOVE)

            self.widget_tree.connect('drag-drop', self.drag_drop)
            self.widget_tree.connect("drag-data-get", self.drag_data_get)
            self.widget_tree.connect('drag-data-received', self.drag_data_received)
            self.widget_tree.connect('drag-data-delete', self.drag_data_delete)
        else:
            self.widget_tree.unset_rows_drag_source()
            self.widget_tree.unset_rows_drag_dest()

    def drag_drop(self, treeview, context, x, y, time):
        treeview.emit_stop_by_name('drag-drop')
        treeview.drag_get_data(context, context.targets[-1], time)
        return True

    def drag_data_get(self, treeview, context, selection, target_id,
            etime):
        treeview.emit_stop_by_name('drag-data-get')
        def _func_sel_get(store, path, iter, data):
            data.append(path)
        data = []
        treeselection = treeview.get_selection()
        treeselection.selected_foreach(_func_sel_get, data)
        data = str(data[0])
        selection.set(selection.target, 8, data)

    def group_by_move(self, model_list, get_id, rec_id, field='sequence'):
        seq_ids = map(lambda x: x[field].get(x), model_list.children.lst)
        set_list = list(set(seq_ids))
        l = model_list.children.lst
        if len(seq_ids) != len(set_list):
            set_list.sort()
            repeat = set_list[-1]
            mod_list = seq_ids[len(set_list):]
            for e in range(len(mod_list)):
                repeat = repeat + 1
                mod_list[e]= repeat
            seq_ids = set_list + mod_list
        else:
            l.insert(rec_id,l[get_id])
            if get_id < rec_id:
                del l[get_id]
            else:
                del l[get_id +1]
        for x in range(len(l)):
            mod = l[x]
            mod[field].set(mod, seq_ids[x], modified=True)
            mod.save()


    def drag_data_received(self, treeview, context, x, y, selection,
            info, etime):
        treeview.emit_stop_by_name('drag-data-received')
        if treeview.sequence:
            for model in self.screen.models.models:
                if model['sequence'].get_state_attrs(
                        model).get('readonly', False):
                    return
        model = treeview.get_model()
        data = eval(selection.data)
        get_id = data[0]
        drop_info = treeview.get_dest_row_at_pos(x, y)

        if drop_info:
            path, position = drop_info
            self.source_group_child = []
            rec_id = model.on_iter_has_child(model.on_get_iter(path)) and path or path[:-1]
            group_by = self.screen.context.get('group_by')
            if group_by:
                if data and path and data[:-1] == path[:-1] \
                            and isinstance(model.on_get_iter(data), ModelRecord):
                    if position in (gtk.TREE_VIEW_DROP_BEFORE,
                        gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                        m_path = path[-1]
                    else:
                        m_path = path[-1] + 1
                    source_models_list = model.on_get_iter(path[:-1])
                    self.group_by_move(source_models_list, data[-1], m_path)
                else:
                    source_group = model.on_get_iter(data)
                    target_group = model.on_get_iter(rec_id)
                    if model.on_iter_has_child(source_group):
                        def process(parent):
                            for child in parent.getChildren().lst:
                                if model.on_iter_has_child(child):
                                    process(child)
                                else:
                                    self.source_group_child.append(child)
                        process(source_group)
                    else:
                        self.source_group_child = [source_group]
                    if self.source_group_child:
                        self.screen.current_model = self.source_group_child[0]
                        target_domain = filter(lambda x: x[0] in group_by, target_group.children.context.get('__domain',[]))
                        val = {}
                        map(lambda x:val.update({x[0]:x[2]}),target_domain)
                        rpc = RPCProxy(self.source_group_child[0].resource)
                        rpc.write(map(lambda x:x.id,self.source_group_child),val)
                        self.reload = True
                        self.screen.reload()
                for expand_path in (data, path):
                    treeview.expand_to_path(expand_path)
            else:
                idx = path[0]
                if position in (gtk.TREE_VIEW_DROP_BEFORE,
                        gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
                    model.move(data, idx)
                    rec_id = idx
                else:
                    model.move(data, idx + 1)
                    rec_id = idx+1
        context.drop_finish(False, etime)
        if treeview.sequence and drop_info and not group_by:
            self.screen.models.set_sequence(get_id, rec_id, field='sequence')

    def drag_data_delete(self, treeview, context):
        treeview.emit_stop_by_name('drag-data-delete')

    def attrs_set(self, model,path):
        if path.attrs.get('attrs',False):
            attrs_changes = eval(path.attrs.get('attrs',"{}"),{'uid':rpc.session.uid})
            for k,v in attrs_changes.items():
                result = True
                for condition in v:
                    result = tools.calc_condition(self,model,condition)
                if result:
                    if k=='invisible':
                        return False
                    elif k=='readonly':
                        return False
        return True


    def copy_by_row(self, model, path, iter, tree_view):
        columns = tree_view.get_columns()
        model = model.get(iter,0)
        copy_row = ""
        title = ""
        for col in columns:
            if col._type != 'Button' and col.name in model[0].value :
                if col._type == 'many2one':
                   copy_row += unicode(model[0].value[col.name] and model[0].value[col.name][1])
                else:
                   copy_row += unicode(model[0].value[col.name])
                copy_row += '\t'
                if not tree_view.copy_table:
                    title += col.get_widget().get_text() + '\t'
        if title:
            tree_view.copy_table += title  + '\n'
        tree_view.copy_table += copy_row + '\n'

    def copy_selection(self, menu, tree_view, tree_selection):
        tree_view.copy_table = ""
        tree_selection.selected_foreach(self.copy_by_row, tree_view)
        tree_view.copy_table
        clipboard = gtk.clipboard_get()
        clipboard.set_text(unicode(tree_view.copy_table))
        clipboard.store()

    def __contextual_menu(self, treeview, event, *args):
        if event.button in [1,3]:
            path = treeview.get_path_at_pos(int(event.x),int(event.y))
            selection = treeview.get_selection()
            if selection.get_mode() == gtk.SELECTION_SINGLE:
                model, iter = selection.get_selected()
            elif selection.get_mode() == gtk.SELECTION_MULTIPLE:
                model, paths = selection.get_selected_rows()
            if (not path) or not path[0]:
                return False
            current_active_model = model.models[path[0][0]]
            groupby = self.screen.context.get('group_by')
            if groupby:
                current_active_model = self.store.on_get_iter(path[0])
            # TODO: add menu cache

            if event.button == 1:
                # first click on button
                if path[1]._type == 'Button':
                    cell_button = path[1].get_cells()[0]
                    if not cell_button.get_property('sensitive'):
                        return
                    # Calling actions
                    attrs_check = self.attrs_set(current_active_model, path[1])
                    states = [e for e in path[1].attrs.get('states','').split(',') if e]
                    if (attrs_check and not states) or \
                            (attrs_check and \
                             current_active_model['state'].get(current_active_model) in states):
                        if self.widget_tree.editable:
                            if current_active_model.validate():
                                id = self.screen.save_current()
                            else:
                               common.warning(_('Invalid form, correct red fields !'), _('Error !') )
                               self.widget_tree.warn('misc-message', _('Invalid form, correct red fields !'), "red")
                               self.screen.display()
                               return False
                        else:
                            id = current_active_model.id
                        current_active_model.get_button_action(self.screen, id, path[1].attrs)
                        self.screen.current_model = None
                        if self.screen.parent and isinstance(self.screen.parent, ModelRecord):
                            self.screen.parent.reload()
                        current_active_model.reload()

            else:
                # Here it goes for right click
                selected_rows = selection.get_selected_rows()
                if len(selected_rows[1])>1:
                    event.state =  gtk.gdk.CONTROL_MASK
                    for row in selected_rows[1]:
                        selection.select_path(row)
                    selection.unselect_path(path[0])

                menu = gtk.Menu()
                item = gtk.ImageMenuItem(_(gtk.STOCK_COPY))
                item.connect('activate',self.copy_selection, treeview, selection)
                item.show()
                menu.append(item)

                if path[1]._type=='many2one':
                    value = current_active_model[path[1].name].get(current_active_model)
                    resrelate = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.values', 'get', 'action', 'client_action_relate', [(self.screen.fields[path[1].name]['relation'], False)], False, rpc.session.context)
                    resrelate = map(lambda x:x[2], resrelate)
                    if resrelate:
                        item = gtk.SeparatorMenuItem()
                        item.show()
                        menu.append(item)
                    for x in resrelate:
                        x['string'] = x['name']
                        item = gtk.ImageMenuItem('... '+x['name'])
                        f = lambda action, value, model: lambda x: self._click_and_relate(action, value, model)
                        item.connect('activate', f(x, value, self.screen.fields[path[1].name]['relation']))
                        item.set_sensitive(bool(value))
                        item.show()
                        menu.append(item)
                menu.popup(None,None,None,event.button,event.time)

    def _click_and_relate(self, action, value, model):
        data={}
        context={}
        act=action.copy()
        if not(value):
            common.message(_('You must select a record to use the relation !'))
            return False
        from widget.screen import Screen
        screen = Screen(model)
        screen.load([value])
        act['domain'] = screen.current_model.expr_eval(act['domain'], check_load=False)
        act['context'] = str(screen.current_model.expr_eval(act['context'], check_load=False))
        obj = service.LocalService('action.main')
        value = obj._exec_action(act, data, context)
        return value

    def signal_record_changed(self, signal, *args):
        if not self.store:
            return
        if signal=='record-added':
            self.store.added(*args)
        elif signal=='record-removed':
            self.store.removed(*args)
        else:
            pass
        self.update_children()

    def cancel(self):
        pass

    def __str__(self):
        return 'ViewList (%s)' % self.screen.resource

    def __getitem__(self, name):
        return None

    def destroy(self):
        self.widget_tree.destroy()
        del self.screen
        del self.widget_tree
        del self.widget

    def __sig_switch(self, treeview, *args):
        if not isinstance(self.screen.current_model, group_record):
            self.screen.row_activate(self.screen)

    def __select_changed(self, tree_sel):
        if tree_sel.get_mode() == gtk.SELECTION_SINGLE:
            model, iter = tree_sel.get_selected()
            if iter:
                path = model.get_path(iter)[0]
                self.screen.current_model = model.on_get_iter(path)
        elif tree_sel.get_mode() == gtk.SELECTION_MULTIPLE:
            model, paths = tree_sel.get_selected_rows()
            if paths:
                iter = model.on_get_iter(paths[0])
                self.screen.current_model = iter
        self.update_children()

    def set_value(self):
        if self.widget_tree.editable:
            self.widget_tree.set_value()

    def reset(self):
        pass

    def set_column_to_default_pos(self, move_col = False, last_grouped_col = False):
        if last_grouped_col:
            prev_col = filter(lambda col: col.name == last_grouped_col, \
                             self.widget_tree.get_columns())[0]
            self.widget_tree.move_column_after(move_col and move_col[0], prev_col)
        else:
            for col in self.columns:
                if col == self.columns[0]:prev_col = None
                self.widget_tree.move_column_after(col, prev_col)
                prev_col = col
        for col in move_col:
            self.changed_col.remove(col)

    def move_colums(self):
        if self.screen.context.get('group_by'):
            groupby = self.screen.context['group_by']
            # This is done to take the order of the columns
            #as order in groupby list
            group_col = []
            for x in groupby:
                group_col += [col for col in self.columns if col.name == x]
                group_col = group_col + filter(lambda x:x.name not in groupby, self.columns)
            for col in group_col:
                if col.name in groupby:
                    if not col in self.changed_col:
                        if not len(self.changed_col):
                            base_col = None
                        else:
                            base_col = self.changed_col[-1]
                        self.changed_col.append(col)
                        self.widget_tree.move_column_after(col, base_col)
                else:
                    if col in self.changed_col:
                        self.set_column_to_default_pos([col], groupby[-1])
        else:
            if self.changed_col:
                remove_col = copy.copy(self.changed_col)
                self.set_column_to_default_pos(remove_col)

    def display(self):
        if self.reload or (not self.widget_tree.get_model()) or self.screen.models<>self.widget_tree.get_model().model_group:
            if self.screen.context.get('group_by'):
                if self.screen.type == 'one2many':
                    self.screen.domain = [('id','in',self.screen.ids_get())]
                self.screen.models.models.clear()
            self.move_colums()
            self.store = AdaptModelGroup(self.screen.models, self.screen.context, self.screen.domain, self.screen.sort)
            if self.store:
                self.widget_tree.set_model(self.store)
        else:
            self.store.invalidate_iters()
        self.set_invisible_attr()
        self.check_editable()
        self.reload = False
        if not self.screen.current_model:
            #
            # Should find a simpler solution to do something like
            #self.widget.set_cursor(None,None,False)
            #
            if self.store:
                self.widget_tree.set_model(self.store)
        self.update_children()

    def update_children(self):
        ids = self.sel_ids_get()
        for c in self.children:
            value = 0.0
            cal_model = self.screen.models.models
            if not cal_model:
                cal_model = self.store.models.lst
            length = len(cal_model)
            if ids:
                length = len(ids)
            for model in cal_model:
                if model.id in ids or model in ids or not ids:
                    if isinstance(model, group_record):
                        value += float(model[self.children[c][0]].get() or 0.0)
                    else:
                        value += float(model.fields_get()[self.children[c][0]].get(model, check_load=False) or 0.0)
            if self.children[c][5] == 'avg' and length:
                value = value/length
            label_str = tools.locale_format('%.' + str(self.children[c][3]) + 'f', value)
            if self.children[c][4]:
                self.children[c][2].set_markup('<b>%s</b>' % label_str)
            else:
                self.children[c][2].set_markup(label_str)

    def set_cursor(self, new=False):
        if self.screen.current_model:
            path = self.store.on_get_path(self.screen.current_model)
            columns = self.widget_tree.get_columns(include_non_visible=False, include_non_editable=False)
            focus_column = len(columns) and columns[0] or None
            self.widget_tree.set_cursor(path, focus_column, new)

    def sel_ids_get(self):
        def _func_sel_get(store, path, iter, ids):
            model = store.on_get_iter(path)
            if isinstance(model, group_record):
                def process(parent):
                    for child in parent.children.lst:
                        if store.on_iter_has_child(child):
                            process(child)
                        else:
                            if child.id:
                                ids.append(child.id)
                process(model)
            else:
                if model.id:
                    ids.append(model.id)
        ids = []
        sel = self.widget_tree.get_selection()
        if sel:
            sel.selected_foreach(_func_sel_get, ids)
        return ids

    def sel_models_get(self):
        def _func_sel_get(store, path, iter, models):
            models.append(store.on_get_iter(path))
        models = []
        sel = self.widget_tree.get_selection()
        sel.selected_foreach(_func_sel_get, models)
        return models

    def on_change(self, callback):
        self.set_value()
        self.screen.on_change(callback)

    def expand_row(self, path, open_all = False):
        self.widget_tree.expand_row(path, open_all)

    def collapse_row(self, path):
        self.widget_tree.collapse_row(path)

    def unset_editable(self):
        self.set_editable(False)

    def check_editable(self):
        if self.screen.context.get('group_by'):
            if self.widget_tree.editable: # Treeview is editable in groupby unset editable
                self.set_editable(False)
        elif self.is_editable or self.screen.context.get('set_editable',False):#Treeview editable by default or set_editable in context
            self.set_editable(self.is_editable or "bottom")
        else:
            self.set_editable(False)

    def set_editable(self, value=True):
        from tree_gtk.parser import send_keys
        from tree_gtk import date_renderer
        self.widget_tree.editable = value
        for col in self.widget_tree.get_columns():
            for renderer in col.get_cell_renderers():
                if isinstance(renderer, gtk.CellRendererToggle):
                    renderer.set_property('activatable', value)
                elif not isinstance(renderer, gtk.CellRendererProgress) and not isinstance(renderer, gtk.CellRendererPixbuf):
                    old_value = renderer.get_property('editable')
                    renderer.set_property('editable', value and old_value)
                if value in ('top','bottom'):
                    if col in self.widget_tree.handlers:
                        if self.widget_tree.handlers[col]:
                            renderer.disconnect(self.widget_tree.handlers[col])
                    self.widget_tree.handlers[col] = renderer.connect_after('editing-started', send_keys, self.widget_tree)


    def set_invisible_attr(self):
        for col in self.widget_tree.get_columns():
            if col._type == 'datetime':
                col.set_max_width(145)
                if self.screen.context.get('group_by'):
                    col.set_max_width(180)
            value = eval(str(self.widget_tree.cells[col.name].attrs.get('invisible', 'False')),\
                           {'context':self.screen.context})
            if col.name in self.screen.context.get('group_by',[]):
                value = False
            col.set_visible(not value)
