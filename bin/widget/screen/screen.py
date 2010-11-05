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
import xml.dom.minidom

from rpc import RPCProxy
import rpc

from widget.model.group import ModelRecordGroup

from widget.view.screen_container import screen_container
import widget_search

import signal_event
import tools
import service
import copy


class Screen(signal_event.signal_event):

    def __init__(self, model_name, view_ids=None, view_type=None,
            parent=None, context=None, views_preload=None, tree_saves=True,
            domain=None, create_new=False, row_activate=None, hastoolbar=False,
            default_get=None, show_search=False, window=None, limit=80,
            readonly=False, is_wizard=False):
        if view_ids is None:
            view_ids = []
        if view_type is None:
            view_type = ['tree', 'form']
        if context is None:
            context = {}
        if views_preload is None:
            views_preload = {}
        if domain is None:
            domain = []
        if default_get is None:
            default_get = {}

        super(Screen, self).__init__()

        self.show_search = show_search
        self.search_count = 0
        self.hastoolbar = hastoolbar
        self.default_get=default_get
        if not row_activate:
            self.row_activate = lambda self,screen=None: self.switch_view(screen, 'form')
        else:
            self.row_activate = row_activate
        self.create_new = create_new
        self.name = model_name
        self.domain = domain
        self.latest_search = []
        self.views_preload = views_preload
        self.resource = model_name
        self.rpc = RPCProxy(model_name)
        self.context = context
        self.context.update(rpc.session.context)
        self.views = []
        self.fields = {}
        self.view_ids = view_ids
        self.models = None
        self.parent=parent
        self.window=window
        self.is_wizard = is_wizard
        models = ModelRecordGroup(model_name, self.fields, parent=self.parent, context=self.context, is_wizard=is_wizard)
        self.models_set(models)
        self.current_model = None
        self.screen_container = screen_container()
        self.filter_widget = None
        self.widget = self.screen_container.widget_get()
        self.__current_view = 0
        self.tree_saves = tree_saves
        self.limit = limit
        self.readonly= readonly
        self.view_fields = {} # Used to switch self.fields when the view switchs

        if view_type:
            self.view_to_load = view_type[1:]
            view_id = False
            if view_ids:
                view_id = view_ids.pop(0)
            view = self.add_view_id(view_id, view_type[0])
            self.screen_container.set(view.widget)
        self.display()


    def readonly_get(self):
        return self._readonly

    def readonly_set(self, value):
        self._readonly = value
        self.models._readonly = value

    readonly = property(readonly_get, readonly_set)

    def search_active(self, active=True, show_search=True):

        if active:
            if not self.filter_widget:
                view_form = rpc.session.rpc_exec_auth('/object', 'execute',
                        self.name, 'fields_view_get', False, 'form',
                        self.context)
                view_tree = rpc.session.rpc_exec_auth('/object', 'execute',
                        self.name, 'fields_view_get', False, 'tree',
                        self.context)
                dom = xml.dom.minidom.parseString(view_tree['arch'])
                child_node=dom.childNodes[0].childNodes
                arch=''
                for i in range(1,len(child_node)):
                    arch += child_node[i].toxml()
                #Generic case when we need to remove the last occurance of </form> from form view    
                view_form['arch'] = view_form['arch'][0:view_form['arch'].rfind('</form>')]
                #Special case when form is replaced,we need to remove </form>
                find_form = view_form['arch'].rfind('</form>')
                if find_form > 0:
                    view_form['arch'] = view_form['arch'][0:find_form]

                view_form['arch'] = view_form['arch'] + arch + '\n</form>'
                view_form['fields'].update(view_tree['fields'])
                self.filter_widget = widget_search.form(view_form['arch'],
                        view_form['fields'], self.name, self.window,
                        self.domain, (self, self.search_filter))
                self.screen_container.add_filter(self.filter_widget.widget,
                        self.search_filter, self.search_clear,
                        self.search_offset_next,
                        self.search_offset_previous)
                self.filter_widget.set_limit(self.limit)
                
        if active and show_search:
            self.screen_container.show_filter()
        else:
            self.screen_container.hide_filter()

    def update_scroll(self, *args):
        offset=self.filter_widget.get_offset()
        limit=self.filter_widget.get_limit()
        if offset<=0:
            self.screen_container.but_previous.set_sensitive(False)
        else:
            self.screen_container.but_previous.set_sensitive(True)

        if offset+limit>=self.search_count:
            self.screen_container.but_next.set_sensitive(False)
        else:
            self.screen_container.but_next.set_sensitive(True)

    def search_offset_next(self, *args):
        offset=self.filter_widget.get_offset()
        limit=self.filter_widget.get_limit()
        self.filter_widget.set_offset(offset+limit)
        self.search_filter()

    def search_offset_previous(self, *args):
        offset=self.filter_widget.get_offset()
        limit=self.filter_widget.get_limit()
        self.filter_widget.set_offset(max(offset-limit,0))
        self.search_filter()

    def search_clear(self, *args):
        self.filter_widget.clear()
        self.clear()

    def search_filter(self, *args):
        v = self.filter_widget.value
        filter_keys = [ key for key, _, _ in v]

        for element in self.domain:
            if not isinstance(element,tuple): # Filtering '|' symbol
                v.append(element)
            else:
                (key, op, value) = element
                if key not in filter_keys and not (key=='active' and self.context.get('active_test', False)):
                    v.append((key, op, value))

#        v.extend((key, op, value) for key, op, value in domain if key not in filter_keys and not (key=='active' and self.context.get('active_test', False)))

        if self.latest_search != v:
            self.filter_widget.set_offset(0)
        limit=self.filter_widget.get_limit()
        offset=self.filter_widget.get_offset()
        self.latest_search = v
        ids = rpc.session.rpc_exec_auth('/object', 'execute', self.name, 'search', v, offset, limit, 0, self.context)
        if len(ids) < limit:
            self.search_count = len(ids)
        else:
            self.search_count = rpc.session.rpc_exec_auth_try('/object', 'execute', self.name, 'search_count', v, self.context)

        self.update_scroll()

        self.clear()
        self.load(ids)
        return True

    def models_set(self, models):
        import time
        c = time.time()
        if self.models:
            self.models.signal_unconnect(self.models)
        self.models = models
        self.parent = models.parent
        if len(models.models):
            self.current_model = models.models[0]
        else:
            self.current_model = None
        self.models.signal_connect(self, 'record-cleared', self._record_cleared)
        self.models.signal_connect(self, 'record-changed', self._record_changed)
        self.models.signal_connect(self, 'model-changed', self._model_changed)
        models.add_fields(self.fields, models)
        self.fields.update(models.fields)
        models.is_wizard = self.is_wizard

    def _record_cleared(self, model_group, signal, *args):
        for view in self.views:
            view.reload = True

    def _record_changed(self, model_group, signal, *args):
        try:
            for view in self.views:
                view.signal_record_changed(signal[0], model_group.models, signal[1], *args)
        except:
            pass        

    def _model_changed(self, model_group, model):
        if (not model) or (model==self.current_model):
            self.display()

    def _get_current_model(self):
        return self.__current_model

    #
    # Check more or less fields than in the screen !
    #
    def _set_current_model(self, value):
        self.__current_model = value
        try:
            offset = int(self.filter_widget.get_offset())
        except:
            offset = 0
        try:
            pos = self.models.models.index(value)
        except:
            pos = -1
        self.signal('record-message', (pos + offset,
            len(self.models.models or []) + offset,
            self.search_count,
            value and value.id))
        return True
    current_model = property(_get_current_model, _set_current_model)

    def destroy(self):
        for view in self.views:
            view.destroy()
            del view
        #del self.current_model
        self.models.signal_unconnect(self)
        del self.models
        del self.views

    # mode: False = next view, value = open this view
    def switch_view(self, screen=None, mode=False):
        self.current_view.set_value()
        self.fields = {}
        if self.current_model and self.current_model not in self.models.models:
            self.current_model = None
        if mode:
            ok = False
            for vid in range(len(self.views)):
                if self.views[vid].view_type==mode:
                    self.__current_view = vid
                    ok = True
                    break
            while not ok and len(self.view_to_load):
                self.load_view_to_load()
                if self.current_view.view_type==mode:
                    ok = True
            for vid in range(len(self.views)):
                if self.views[vid].view_type==mode:
                    self.__current_view = vid
                    ok = True
                    break
            if not ok:
                self.__current_view = len(self.views) - 1
        else:
            if len(self.view_to_load):
                self.load_view_to_load()
                self.__current_view = len(self.views) - 1
            else:
                self.__current_view = (self.__current_view + 1) % len(self.views)
        
        self.fields = self.view_fields.get(self.__current_view, self.fields) # Switch the fields
        # TODO: maybe add_fields_custom is needed instead of add_fields on some cases
        self.models.add_fields(self.fields, self.models) # Switch the model fields too
        
        widget = self.current_view.widget
        self.screen_container.set(self.current_view.widget)
        if self.current_model:
            self.current_model.validate_set()
        elif self.current_view.view_type=='form':
            self.new()
        self.display()
        self.current_view.set_cursor()

        main = service.LocalService('gui.main')
        if main:
            main.sb_set()

        # TODO: set True or False accoring to the type

    def load_view_to_load(self, mode=False):
        if len(self.view_to_load):
            if self.view_ids:
                view_id = self.view_ids.pop(0)
                view_type = self.view_to_load.pop(0)
            else:
                view_id = False
                view_type = self.view_to_load.pop(0)
            self.add_view_id(view_id, view_type)

    def add_view_custom(self, arch, fields, display=False, toolbar={}):
        return self.add_view(arch, fields, display, True, toolbar=toolbar)

    def add_view_id(self, view_id, view_type, display=False, context=None):
        if view_type in self.views_preload:
            return self.add_view(self.views_preload[view_type]['arch'],
                    self.views_preload[view_type]['fields'], display,
                    toolbar=self.views_preload[view_type].get('toolbar', False),
                    context=context)
        else:
            view = self.rpc.fields_view_get(view_id, view_type, self.context,
                    self.hastoolbar)
            return self.add_view(view['arch'], view['fields'], display,
                    toolbar=view.get('toolbar', False), context=context)

    def add_view(self, arch, fields, display=False, custom=False, toolbar=None,
            context=None):
        if toolbar is None:
            toolbar = {}
        def _parse_fields(node, fields):
            if node.nodeType == node.ELEMENT_NODE:
                if node.localName=='field':
                    attrs = tools.node_attributes(node)
                    if attrs.get('widget', False):
                        if attrs['widget']=='one2many_list':
                            attrs['widget']='one2many'
                        attrs['type'] = attrs['widget']
                    fields[unicode(attrs['name'])].update(attrs)
            for node2 in node.childNodes:
                _parse_fields(node2, fields)
        dom = xml.dom.minidom.parseString(arch)
        _parse_fields(dom, fields)
        for dom in self.domain:
            if dom[0] in fields:
                field_dom = str(fields[dom[0]].setdefault('domain',
                        []))
                fields[dom[0]]['domain'] = field_dom[:1] + \
                        str(('id', dom[1], dom[2])) + ',' + field_dom[1:]

        from widget.view.widget_parse import widget_parse
        models = self.models.models
        if self.current_model and (self.current_model not in models):
            models = models + [self.current_model]
        if custom:
            self.models.add_fields_custom(fields, self.models)
        else:
            self.models.add_fields(fields, self.models, context=context)
        self.fields = self.models.fields

        parser = widget_parse(parent=self.parent, window=self.window)
        dom = xml.dom.minidom.parseString(arch)
        view = parser.parse(self, dom, self.fields, toolbar=toolbar)
        if view:
            self.views.append(view)

        if display:
            self.__current_view = len(self.views) - 1
            self.current_view.display()
            self.screen_container.set(view.widget)
        
        # Store the fields for this view (we will use them when switching views)
        self.view_fields[len(self.views)-1] = copy.deepcopy(self.fields)

        return view

    def editable_get(self):
        if hasattr(self.current_view, 'widget_tree'):
            return self.current_view.widget_tree.editable
        else:
            return False

    def new(self, default=True, context={}):
        if self.current_view and self.current_view.view_type == 'tree' \
                and not self.current_view.widget_tree.editable:
            self.switch_view(mode='form')
        ctx = self.context.copy()
        ctx.update(context)
        model = self.models.model_new(default, self.domain, ctx)
        if (not self.current_view) or self.current_view.model_add_new or self.create_new:
            self.models.model_add(model, self.new_model_position())
        self.current_model = model
        self.current_model.validate_set()
        self.display()
        if self.current_view:
            self.current_view.set_cursor(new=True)
        return self.current_model

    def new_model_position(self):
        position = -1
        if self.current_view and self.current_view.view_type =='tree' \
                and self.current_view.widget_tree.editable == 'top':
            position = 0
        return position

    def set_on_write(self, func_name):
        self.models.on_write = func_name

    def cancel_current(self):
        if self.current_model:
            self.current_model.cancel()
        if self.current_view:
            self.current_view.cancel()

    def save_current(self):
        if not self.current_model:
            return False
        self.current_view.set_value()
        id = False
        if self.current_model.validate():
            id = self.current_model.save(reload=True)
            self.models.writen(id)
            if not id:
                self.current_view.display()
        else:
            self.current_view.display()
            self.current_view.set_cursor()
            return False
        if self.current_view.view_type == 'tree':
            for model in self.models.models:
                if model.is_modified():
                    if model.validate():
                        id = model.save(reload=True)
                        self.models.writen(id)
                    else:
                        self.current_model = model
                        self.display()
                        self.current_view.set_cursor()
                        return False
            self.display()
            self.current_view.set_cursor()
        if self.current_model not in self.models:
            self.models.model_add(self.current_model)
        return id

    def _getCurrentView(self):
        if not len(self.views):
            return None
        return self.views[self.__current_view]
    current_view = property(_getCurrentView)

    def get(self):
        if not self.current_model:
            return None
        self.current_view.set_value()
        return self.current_model.get()

    def is_modified(self):
        if not self.current_model:
            return False
        self.current_view.set_value()
        if self.current_view.view_type != 'tree':
            return self.current_model.is_modified()
        else:
            for model in self.models.models:
                if model.is_modified():
                    return True
        return False

    def reload(self):
        self.current_model.reload()
        if self.parent:
            self.parent.reload()
        self.display()

    def remove(self, unlink = False):
        id = False
        if self.current_view.view_type == 'form' and self.current_model:
            id = self.current_model.id
            
            idx = self.models.models.index(self.current_model)
            if not id:
                lst=[]
                self.models.models.remove(self.models.models[idx])
                self.current_model=None
                if self.models.models:
                    idx = min(idx, len(self.models.models)-1)
                    self.current_model = self.models.models[idx]
                self.display()
                self.current_view.set_cursor()
                return False

            ctx = self.current_model.context_get().copy()
            self.current_model.update_context_with_concurrency_check_data(ctx)
            if unlink and id:
                if not self.rpc.unlink([id], ctx):
                    return False

            self.models.remove(self.current_model)
            if self.models.models:
                idx = min(idx, len(self.models.models)-1)
                self.current_model = self.models.models[idx]
            else:
                self.current_model = None
            self.display()
            self.current_view.set_cursor()
        if self.current_view.view_type == 'tree':
            ids = self.current_view.sel_ids_get()
            
            ctx = self.models.context.copy()
            for m in self.models:
                if m.id in ids:
                    m.update_context_with_concurrency_check_data(ctx)

            if unlink and ids:
                if not self.rpc.unlink(ids, ctx):
                    return False
            for model in self.current_view.sel_models_get():
                self.models.remove(model)
            self.current_model = None
            self.display()
            self.current_view.set_cursor()
            id = ids
        return id

    def load(self, ids):
        if not isinstance(ids,list):
            ids = [ids]
        self.models.load(ids, display=False)
        self.current_view.reset()
        if ids:
            self.display(ids[0])
        else:
            self.current_model = None
            self.display()

    def display(self, res_id=None):
        if res_id:
            self.current_model = self.models[res_id]
        if self.views:
            self.current_view.display()
            self.current_view.widget.set_sensitive(bool(self.models.models or (self.current_view.view_type!='form') or self.current_model))
            vt = self.current_view.view_type
            self.search_active(
                    active=self.show_search and vt in ('tree', 'graph', 'calendar'),
                    show_search=self.show_search and vt in ('tree', 'graph'),
            )

    def display_next(self):
        self.current_view.set_value()
        if self.current_model in self.models.models:
            idx = self.models.models.index(self.current_model)
            idx = (idx+1) % len(self.models.models)
            self.current_model = self.models.models[idx]
        else:
            self.current_model = len(self.models.models) and self.models.models[0]
        if self.current_model:
            self.current_model.validate_set()
        self.display()
        self.current_view.set_cursor()

    def display_prev(self):
        self.current_view.set_value()
        if self.current_model in self.models.models:
            idx = self.models.models.index(self.current_model)-1
            if idx<0:
                idx = len(self.models.models)-1
            self.current_model = self.models.models[idx]
        else:
            self.current_model = len(self.models.models) and self.models.models[-1]

        if self.current_model:
            self.current_model.validate_set()
        self.display()
        self.current_view.set_cursor()

    def sel_ids_get(self):
        return self.current_view.sel_ids_get()

    def id_get(self):
        if not self.current_model:
            return False
        return self.current_model.id

    def ids_get(self):
        return [x.id for x in self.models if x.id]

    def clear(self):
        self.models.clear()

    def on_change(self, callback):
        self.current_model.on_change(callback)
        self.display()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

