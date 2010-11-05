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
import gobject

import time
import datetime as DT
import copy
import math
import locale
import gettext

from xml.parsers import expat

import options
import rpc
import parse
import pytz

import tools
import tools.datetime_util

DT_FORMAT = '%Y-%m-%d'
DHM_FORMAT = '%Y-%m-%d %H:%M:%S'
LDFMT = tools.datetime_util.get_date_format()

# BUG: ids = []
#
# Tree struct:  [ id, values, childs, childs_id ]
#
#    values: [...]
#    childs: [ tree_struct ]
#            [] for no childs
#            None for undevelopped (with childs!)
#        assert: no childs => []
#
# Node struct: [list of (pos, list) ]
#
class view_tree_model(gtk.GenericTreeModel, gtk.TreeSortable):
    def __init__(self, ids, view, fields, fields_type, context={}, pixbufs={}, treeview=None):
        gtk.GenericTreeModel.__init__(self)
        self.fields = fields
        self.fields_type = fields_type
        self.view = view
        self.roots = ids
        self.context = context
        self.tree = self._node_process(self.roots)
        self.pixbufs = pixbufs
        self.treeview = treeview

    def _read(self, ids, fields):
        c = {}
        c.update(rpc.session.context)
        c.update(self.context)
        try:
            res_ids = rpc.session.rpc_exec_auth_try('/object', 'execute',
                    self.view['model'], 'read', ids, fields, c)
        except:
            res_ids = []
            for id in ids:
                val = {'id': id}
                for f in fields:
                    if self.fields_type[f]['type'] in ('one2many','many2many'):
                        val[f] = []
                    else:
                        val[f] = ''
                res_ids.append(val)
        for field in self.fields:
            if self.fields_type[field]['type'] in ('date',):
                display_format = LDFMT
                for x in res_ids:
                    if x[field]:
                        date = time.strptime(x[field], DT_FORMAT)
                        x[field] = time.strftime(display_format, date)
            if self.fields_type[field]['type'] in ('datetime',):
                display_format = LDFMT + ' %H:%M:%S'
                for x in res_ids:
                    if x[field]:
                        date = time.strptime(x[field], DHM_FORMAT)
                        if rpc.session.context.get('tz'):
                            try:
                                lzone = pytz.timezone(rpc.session.context['tz'])
                                szone = pytz.timezone(rpc.session.timezone)
                                dt = DT.datetime(date[0], date[1], date[2],
                                        date[3], date[4], date[5], date[6])
                                sdt = szone.localize(dt, is_dst=True)
                                ldt = sdt.astimezone(lzone)
                                date = ldt.timetuple()
                            except pytz.UnknownTimeZoneError:
                                # Timezones are sometimes invalid under Windows
                                # and hard to figure out, so as a low-risk fix
                                # in stable branch we will simply ignore the
                                # exception and consider client in server TZ
                                # (and sorry about the code duplication as well,
                                # this is fixed properly in trunk)
                                pass
                        x[field] = time.strftime(display_format, date)

            if self.fields_type[field]['type'] in ('one2one','many2one'):
                for x in res_ids:
                    if x[field]:
                        x[field] = x[field][1]

            if self.fields_type[field]['type'] in ('selection'):
                for x in res_ids:
                    if x[field]:
                        x[field] = dict(self.fields_type[field]['selection']
                                ).get(x[field],'')
            if self.fields_type[field]['type'] in ('float',):
                interger, digit = self.fields_type[field].get('digits', (16,2))
                for x in res_ids:
                    x[field] = tools.locale_format('%.' + str(digit) + 'f', x[field] or 0.0)
            if self.fields_type[field]['type'] in ('float_time',):
                for x in res_ids:
                    hours = math.floor(abs(x[field]))
                    mins = round(abs(x[field]) % 1 + 0.01, 2)
                    if mins >= 1.0:
                        hours = hours + 1
                        mins = 0.0
                    else:
                        mins = mins * 60
                    val = '%02d:%02d' % (hours,mins)
                    if x[field] < 0:
                        val = '-' + val
                    x[field] = val
        return res_ids

    def _node_process(self, ids):
        tree = []
        if self.view.get('field_parent', False):
            res = self._read(ids, self.fields+[self.view['field_parent']])
            for x in res:
                tree.append( [ x['id'], None, [], x[self.view['field_parent']] ] )
                tree[-1][1] = [ x[ y ] for y in self.fields]
                if len(x[self.view['field_parent']]):
                    tree[-1][2] = None
        else:
            res = self._read(ids, self.fields)
            for x in res:
                tree.append( [ x['id'],  [ x[y] for y in self.fields], [] ])
        return tree

    def _node_expand(self, node):
        node[2] = self._node_process(node[3])
        del node[3]

    def on_get_flags(self):
        return 0

    def on_get_n_columns(self):
        return len(self.fields)+1

    def on_get_column_type(self, index):
        if index in self.pixbufs:
            return gtk.gdk.Pixbuf
        return fields_list_type.get(self.fields_type[self.fields[index-1]]['type'],
                gobject.TYPE_STRING)

    def on_get_path(self, node):
        '''returns the tree path (a tuple of indices)'''
        return tuple([ x[0] for x in node ])

    def on_get_iter(self, path):
        '''returns the node corresponding to the given path.'''
        node = []
        tree = self.tree
        if self.tree==[]:
            return None
        for x in path:
            node.append( (x, tree) )
            tree = tree[x][2]
        return node

    def on_get_value(self, node, column):
        (n, list) = node[-1]
        if column:
            value = list[n][1][column-1]
        else:
            value = list[n][0]
            
        if value==None or (value==False and type(value)==bool):
            res = ''
        else:
            res = value
        if (column in self.pixbufs) and res:
            if res.startswith('STOCK_'):
                res = getattr(gtk, res)
            return self.treeview.render_icon(stock_id=res, size=gtk.ICON_SIZE_MENU, detail=None)
        return res

    def on_iter_next(self, node):
        '''returns the next node at this level of the tree'''
        node = node[:]
        (n, list) = node[-1]
        if n<len(list)-1:
            node[-1] = (n+1, list)
            return node
        return None

    def on_iter_children(self, node):
        '''returns the first child of this node'''
        if node==None:                    # added
            return [ (0, self.tree) ]     # added
        node = node[:]
        (n, list) = node[-1]                 
        if list[n][2]==None:
            self._node_expand(list[n])
        if list[n][2]==[]:
            return None
        node.append( (0, list[n][2]) )
        return node

    def on_iter_has_child(self, node):
        '''returns true if this node has children'''
        (n, list) = node[-1]
        return list[n][2]!=[]

    def on_iter_n_children(self, node):
        '''returns the number of children of this node'''
        if node==None:                    # changed
            return len(self.tree)         # changed
        (n, list) = node[-1]
        if list[n][2]==None:
            self._node_expand(list[n])
        return len(list[n][2])

    def on_iter_nth_child(self, node, child):
        '''returns the nth child of this node'''
        if node==None:
            if child<len(self.tree):
                return [ (child, self.tree) ]
            return None
        else:
            (n, list) = node[-1]
            if list[n][2]==None:
                self._node_expand(list[n])
            if child<len(list[n][2]):
                node = node[:]
                node.append( (child, list[n][2]) )
                return node
            return None

    def on_iter_parent(self, node):
        '''returns the parent of this node'''
        if node==None:
            return None
        return node[:-1]

    def cus_refresh(self):
        tree = self.tree
        tree[0][2] = None

    def _cus_row_find(self, ids_res):
        tree = self.tree
        try:
            ids = ids_res[:]
            while len(ids)>0:
                if ids[-1] in self.roots:
                    ids.pop()
                    break
                ids.pop()
            path = []
            while ids!=[]:
                path.append(0)
                val = ids.pop()
                i = iter(tree)
                while True:
                    node = i.next()
                    if node[0]==val:
                        break
                    path[-1]+=1
                if (node[2]==None) and (ids!=[]):
                    return None
                tree = node[2]
            return (tuple(path), node)
        except:
            return None

class view_tree(object):
    def __init__(self, view_info, ids, res_id=None, sel_multi=False, context={}):
        self.view = gtk.TreeView()
        self.view.set_headers_visible(True)
        self.context = {}
        self.context.update(rpc.session.context)
        self.context.update(context)
        self.fields = rpc.session.rpc_exec_auth('/object', 'execute', view_info['model'], 'fields_get', False, self.context)
        p = parse.parse(self.fields)
        p.parse(view_info['arch'], self.view)
        self.toolbar = p.toolbar
        self.pixbufs = p.pixbufs
        self.name = p.title
        self.sel_multi = sel_multi

        if sel_multi:
            self.view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        else:
            self.view.get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.view.set_expander_column(self.view.get_column(1))
        self.view.set_enable_search(False)
        self.view.get_column(0).set_visible(False)

        self.ids=ids
        self.view_info = view_info
        self.fields_order = p.fields_order
        self.model = None
        self.reload()

        self.view.show_all()
        self.search=[]
        self.next=0

    def reload(self):
        del self.model
        self.context.update(rpc.session.context)
        self.model = view_tree_model(self.ids, self.view_info, self.fields_order, self.fields, context=self.context, pixbufs=self.pixbufs, treeview=self.view)
        self.view.set_model(self.model)

    def widget_get(self):
        return self.view

    def sel_ids_get(self):
        sel = self.view.get_selection()
        if not sel:
            return None
        sel = sel.get_selected_rows()
        if not sel:
            return []
        (model, iters) = sel
        return map(lambda x: int(model.get_value(model.get_iter(x), 0)), iters)
        
    def sel_id_get(self):
        sel = self.view.get_selection().get_selected()
        if sel==None:
            return None
        (model, iter) = sel
        if not iter:
            return None
        res = model.get_value(iter, 0)
        if res!=None:
            return int(res)
        return res

    def value_get(self, col):
        sel = self.view.get_selection().get_selected_rows()
        if sel==None:
            return None
        (model, iter) = sel
        if not iter:
            return None
        return model.get_value(iter, col)

    def go(self, id):
        return
        ids = com_rpc.xrpc.exec_auth('res_path_get', id, self.root)
        if not len(ids):
            raise Exception, 'IdNotFound'
        self.view.collapse_all()
        model = self.view.get_model()
        iter = model.get_iter_root()
        while len(ids)>0:
            if ids[-1]==model.root:
                break
            ids.pop()
        if ids!=[]:
            ids.pop()
            while ids!=[]:
                val = ids.pop()
                while True:
                    if int(model.get_value(iter,0))==val:
                        self.view.expand_row( model.get_path(iter), False)
                        break
                    if not model.iter_next(iter):
                        raise Exception, 'IdNotFound'
                if ids!=[]:
                    iter = model.iter_children(iter)
            self.view.get_selection().select_iter(iter)

fields_list_type = {
    'checkbox': gobject.TYPE_BOOLEAN,
    'integer': gobject.TYPE_INT,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

