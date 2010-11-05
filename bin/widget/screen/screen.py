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
from lxml import etree
from rpc import RPCProxy
import rpc
import gettext
from datetime import datetime
from dateutil.relativedelta import relativedelta
import gtk
import gobject
from gtk import glade

from widget.model.group import ModelRecordGroup

from widget.view.screen_container import screen_container
from widget.view.list import group_record
import widget_search

import signal_event
import tools
import service
import common
import copy


class Screen(signal_event.signal_event):

    def __init__(self, model_name, view_ids=None, view_type=None,help={},
            parent=None, context=None, views_preload=None, tree_saves=True,
            domain=None, create_new=False, row_activate=None, hastoolbar=False,
            hassubmenu=False,default_get=None, show_search=False, window=None,
            limit=80, readonly=False, auto_search=True, is_wizard=False, search_view=None,win_search=False):
        if view_ids is None:
            view_ids = []
        if view_type is None:
            view_type = ['tree', 'form']
        if views_preload is None:
            views_preload = {}
        if not domain:
            domain = []
        if default_get is None:
            default_get = {}
        if search_view is None:
            search_view = "{}"

        super(Screen, self).__init__()
        self.win_search = win_search
        self.win_search_domain = []
        self.win_search_ids = []
        self.win_search_callback = False
        self.show_search = show_search
        self.auto_search = auto_search
        self.search_count = 0
        self.hastoolbar = hastoolbar
        self.hassubmenu = hassubmenu
        self.default_get=default_get
        self.sort = False
        self.type = None
        self.dummy_cal = False
        if not row_activate:
            self.row_activate = lambda self,screen=None: self.switch_view(screen, 'form')
        else:
            self.row_activate = row_activate
        self.create_new = create_new
        self.name = model_name
        self.domain_init = domain
        self.action_domain = []
        self.action_domain += domain
        self.latest_search = []
        self.views_preload = views_preload
        self.resource = model_name
        self.rpc = RPCProxy(model_name)
        self.context_init = context or {}
        self.context_update()
        self.views = []
        self.fields = {}
        self.view_ids = view_ids
        self.models = None
        self.parent=parent
        self.window=window
        self.is_wizard = is_wizard
        self.search_view = eval(search_view)
        models = ModelRecordGroup(model_name, self.fields, parent=self.parent, context=self.context, is_wizard=is_wizard)
        self.models_set(models)
        self.current_model = None
        self.screen_container = screen_container(self.win_search)
        self.filter_widget = None
        self.widget = self.screen_container.widget_get()
        self.__current_view = 0
        self.tree_saves = tree_saves
        self.limit = limit
        self.old_limit = limit
        self.offset = 0
        self.readonly= readonly
        self.custom_panels = []
        self.view_fields = {} # Used to switch self.fields when the view switchs
        self.sort_domain = []
        self.old_ctx = {}
        self.help_mode = False
        if view_type:
            self.view_to_load = view_type[1:]
            view_id = False
            if view_ids:
                view_id = view_ids.pop(0)
            if view_type[0] in ('tree','graph','calendar'):
                self.screen_container.help = help
                self.help_mode = view_type[0]
            view = self.add_view_id(view_id, view_type[0], help=help)
            self.screen_container.set(view.widget)
        self.display()

    def context_update(self, ctx={}, dmn=[]):
        self.context = self.context_init.copy()
        self.context.update(rpc.session.context)
        self.context.update(ctx)
        self.domain = self.domain_init[:]
        self.domain += dmn


    def readonly_get(self):
        return self._readonly

    def readonly_set(self, value):
        self._readonly = value
        self.models._readonly = value

    readonly = property(readonly_get, readonly_set)

    def search_active(self, active=True, show_search=True):
        if active:
            if not self.filter_widget:
                if not self.search_view:
                    self.search_view = rpc.session.rpc_exec_auth('/object', 'execute',
                            self.name, 'fields_view_get', False, 'search',
                            self.context)
                self.filter_widget = widget_search.form(self.search_view['arch'],
                        self.search_view['fields'], self.name, self.window,
                        self.domain, (self, self.search_filter))
                self.screen_container.add_filter(self.filter_widget.widget,
                        self.search_filter, self.search_clear,
                        self.search_offset_next,
                        self.search_offset_previous,
                        self.execute_action, self.add_custom, self.name, self.limit)

        if active and show_search:
            self.screen_container.show_filter()
        else:
            self.screen_container.hide_filter()


    def update_scroll(self, *args):
        offset = self.offset
        limit = self.screen_container.get_limit()
        if self.screen_container.but_previous:
            if offset<=0:
                self.screen_container.but_previous.set_sensitive(False)
            else:
                self.screen_container.but_previous.set_sensitive(True)
        if self.screen_container.but_next:
            if not limit or offset+limit>=self.search_count:
                self.screen_container.but_next.set_sensitive(False)
            else:
                self.screen_container.but_next.set_sensitive(True)
        if self.win_search:
            self.win_search_callback()

    def search_offset_next(self, *args):
        offset=self.offset
        limit = self.screen_container.get_limit()
        self.offset = offset+limit
        self.search_filter()
        if self.win_search:
            self.win_search_callback()

    def search_offset_previous(self, *args):
        offset=self.offset
        limit = self.screen_container.get_limit()
        self.offset = max(offset-limit,0)
        self.search_filter()
        if self.win_search:
            self.win_search_callback()

    def search_clear(self, *args):
        self.filter_widget.clear()
        if not self.win_search:
            self.screen_container.action_combo.set_active(0)
        self.clear()

    def get_calenderDomain(self, start=None,old_date='',mode='month'):
        args = []
        old_date = old_date.date()
        if not old_date:
            old_date = datetime.today().date()
        if old_date == datetime.today().date():
            if mode =='month':
                start_date = (old_date + relativedelta(months=-1)).strftime('%Y-%m-%d')
                args.append((start, '>',start_date))
                end_date = (old_date + relativedelta(months=+1)).strftime('%Y-%m-%d')
                args.append((start, '<',end_date))

            if mode=='week':
                start_date = (old_date + relativedelta(weeks=-1)).strftime('%Y-%m-%d')
                args.append((start, '>',start_date))
                end_date = (old_date + relativedelta(weeks=+1)).strftime('%Y-%m-%d')
                args.append((start, '<',end_date))

            if mode=='day':
                start_date = (old_date + relativedelta(days=-1)).strftime('%Y-%m-%d')
                args.append((start, '>',start_date))
                end_date = (old_date + relativedelta(days=+1)).strftime('%Y-%m-%d')
                args.append((start, '<',end_date))
        else:
            if mode =='month':
                end_date = (old_date + relativedelta(months=+1)).strftime('%Y-%m-%d')
            if mode=='week':
                end_date = (old_date + relativedelta(weeks=+1)).strftime('%Y-%m-%d')
            if mode=='day':
                end_date = (old_date + relativedelta(days=+1)).strftime('%Y-%m-%d')
            old_date = old_date.strftime('%Y-%m-%d')
            args = [(start,'>',old_date),(start,'<',end_date)]
        return args

    def search_filter(self, *args):
        if not self.auto_search:
            self.auto_search = True
            return
        val = self.filter_widget and self.filter_widget.value or {}
        if self.current_view.view_type == 'graph' and self.current_view.view.key:
            self.domain = self.domain_init[:]
            self.domain += val.get('domain',[]) + self.sort_domain
        else:
            self.context_update(val.get('context',{}), val.get('domain',[]) + self.sort_domain)

        v = self.domain
        if self.win_search:
            v += self.win_search_domain
        limit = self.screen_container.get_limit()
        if self.current_view.view_type == 'calendar':
            start = self.current_view.view.date_start
            old_date = self.current_view.view.date
            mode = self.current_view.view.mode
            calendar_domain = self.get_calenderDomain(start,old_date,mode)
            v += calendar_domain
        filter_keys = []

        for ele in self.domain:
            if isinstance(ele,tuple):
                filter_keys.append(ele[0])

        if self.latest_search != v:
            self.offset = 0
        offset = self.offset
        self.latest_search = v
        if self.context.get('group_by') or \
               self.context.get('group_by_no_leaf') \
               and not self.current_view.view_type == 'graph':
            self.current_view.reload = True
            self.display()
            return True
        ids = rpc.session.rpc_exec_auth('/object', 'execute', self.name, 'search', v, offset, limit, self.sort, self.context)
        self.win_search_ids = ids
        if self.win_search and self.win_search_domain:
            for dom in self.win_search_domain:
                if dom in v:
                    v.remove(dom)
            self.win_search_domain = []
        if len(ids) < limit:
            self.search_count = len(ids)
        else:
            self.search_count = rpc.session.rpc_exec_auth_try('/object', 'execute', self.name, 'search_count', v, self.context)
        self.update_scroll()
        self.clear()
        if self.sort_domain in v:
            v.remove(self.sort_domain)
        self.sort_domain = []
        self.load(ids)
        return True

    def add_custom(self, dynamic_button):
        fields_list = []
        for k,v in self.search_view['fields'].items():
            if v['type'] in ('many2one','text','char','float','integer','date','datetime','selection','many2many','boolean','one2many') and v.get('selectable', False):
                selection = v.get('selection', False)
                fields_list.append([k,v['string'], v['type'], selection])
        if fields_list:
            fields_list.sort(lambda x, y: cmp(x[1], y[1]))
        panel = self.filter_widget.add_custom(self.filter_widget, self.filter_widget.widget, fields_list)
        self.custom_panels.append(panel)

        if len(self.custom_panels)>1:
            self.custom_panels[-1].condition_next.hide()
            self.custom_panels[-2].condition_next.show()

    def execute_action(self, combo):
        flag = combo.get_active_text()
        combo_model = combo.get_model()
        active_id = combo.get_active()
        action_name = active_id != -1 and flag not in ['mf','blk','sh', 'sf'] and combo_model[active_id][2]
        # 'mf' Section manages Filters
        def clear_domain_ctx():
            for key in self.old_ctx.keys():
                if key in self.context_init:
                    del self.context_init[key]
            for domain in self.latest_search:
                if domain in self.domain_init:
                    self.domain_init.remove(domain)
            #append action domain to filter domain
            self.domain_init += self.action_domain
        if flag == 'mf':
            obj = service.LocalService('action.main')
            act={'name':'Manage Filters',
                 'res_model':'ir.filters',
                 'type':'ir.actions.act_window',
                 'view_type':'form',
                 'view_mode':'tree,form',
                 'domain':'[(\'model_id\',\'=\',\''+self.name+'\'),(\'user_id\',\'=\','+str(rpc.session.uid)+')]'}
            ctx = self.context.copy()
            for key in ('group_by','group_by_no_leaf'):
                if key in ctx:
                    del ctx[key]
            value = obj._exec_action(act, {}, ctx)

        if flag in ['blk','mf']:
            self.screen_container.last_active_filter = False
            clear_domain_ctx()
            if flag == 'blk':
                self.search_filter()
            combo.set_active(0)
            return True
        #This section handles shortcut and action creation
        elif flag in ['sh','sf']:
            glade2 = glade.XML(common.terp_path("openerp.glade"),'dia_get_action',gettext.textdomain())
            widget = glade2.get_widget('action_name')
            win = glade2.get_widget('dia_get_action')
            win.set_icon(common.OPENERP_ICON)
            lbl = glade2.get_widget('label157')
            if flag == 'sh':
                win.set_title('Shortcut Entry')
                lbl.set_text('Shortcut Name:')
            else:
                win.set_size_request(300, 165)
                text_entry = glade2.get_widget('action_name')
                lbl.set_text('Filter Name:')
                table =  glade2.get_widget('table8')
                info_lbl = gtk.Label('(Any existing filter with the \nsame name will be replaced)')
                table.attach(info_lbl,1,2,2,3, gtk.FILL, gtk.EXPAND)
                if self.screen_container.last_active_filter:
                    text_entry.set_text(self.screen_container.last_active_filter)
            win.show_all()
            response = win.run()
            # grab a safe copy of the entered text before destroy() to avoid GTK bug https://bugzilla.gnome.org/show_bug.cgi?id=613241
            action_name = widget.get_text()
            win.destroy()
            combo.set_active(0)
            if response == gtk.RESPONSE_OK and action_name:
                filter_domain = self.filter_widget and self.filter_widget.value.get('domain',[])
                filter_context = self.filter_widget and self.filter_widget.value.get('context',{})
                values = {'name':action_name,
                       'model_id':self.name,
                       'user_id':rpc.session.uid
                       }
                if flag == 'sf':
                    domain, context = self.screen_container.get_filter(action_name)
                    for dom in eval(domain):
                        if dom not in filter_domain:
                            filter_domain.append(dom)
                    groupby_list = eval(context).get('group_by',[]) + filter_context.get('group_by',[])
                    filter_context.update(eval(context))
                    if groupby_list:
                        filter_context.update({'group_by':groupby_list})
                    values.update({'domain':str(filter_domain),
                                   'context':str(filter_context),
                                   })
                    action_id = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.filters', 'create_or_replace', values, self.context)
                    self.screen_container.fill_filter_combo(self.name, action_name)
                if flag == 'sh':
                    filter_domain += self.domain_init
                    filter_context.update(self.context_init)
                    values.update({'res_model':self.name,
                                   'domain':str(filter_domain),
                                   'context':str(filter_context),
                                   'search_view_id':self.search_view['view_id'],
                                   'default_user_ids': [[6, 0, [rpc.session.uid]]]})
                    rpc.session.rpc_exec_auth_try('/object', 'execute', 'ir.ui.menu', 'create_shortcut', values, self.context)
        else:
            try:
                self.screen_container.last_active_filter = action_name
                filter_domain = flag and tools.expr_eval(flag)
                clear_domain_ctx()
                if combo.get_active() >= 0:
                    combo_model = combo.get_model()
                    val = combo_model[combo.get_active()][1]
                    if val:
                        self.old_ctx = eval(val)
                        self.context_init.update(self.old_ctx)
                self.domain_init += filter_domain or []
                if isinstance(self.domain_init,type([])):
                    self.search_filter()
                    self.reload()
            except Exception:
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
            offset = int(self.offset)
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
        if isinstance(self.current_model, group_record) and mode != 'graph':
          return
        if mode == 'calendar' and self.dummy_cal:
            mode = 'dummycalendar'
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
            if len(self.view_to_load) and mode in self.view_to_load:
                self.load_view_to_load(mode=mode)
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
            if mode:
                idx = self.view_to_load.index(mode)
                view_id = self.view_ids and self.view_ids.pop(idx) or False
            else:
                idx = 0
                view_id = False
            type = self.view_to_load.pop(idx)
            self.add_view_id(view_id,type)

    def add_view_custom(self, arch, fields, display=False, toolbar={}, submenu={}):
        return self.add_view(arch, fields, display, True, toolbar=toolbar, submenu=submenu)

    def add_view_id(self, view_id, view_type, display=False, help={}, context=None):
        if context is None:
            context = {}
        if view_type in self.views_preload:
            return self.add_view(self.views_preload[view_type]['arch'],
                    self.views_preload[view_type]['fields'], display,
                    toolbar=self.views_preload[view_type].get('toolbar', False),
                    submenu=self.views_preload[view_type].get('submenu', False), help=help,
                    context=context)
        else:
            view = self.rpc.fields_view_get(view_id, view_type, self.context,
                        self.hastoolbar, self.hassubmenu)
            context.update({'view_type' : view_type})
            return self.add_view(view['arch'], view['fields'], display, help=help,
                    toolbar=view.get('toolbar', False), submenu=view.get('submenu', False), context=context)

    def add_view(self, arch, fields, display=False, custom=False, toolbar=None, submenu=None, help={},
            context=None):
        if toolbar is None:
            toolbar = {}
        if submenu is None:
            submenu = {}
        def _parse_fields(node, fields):
            if node.tag =='field':
                attrs = tools.node_attributes(node)
                if attrs.get('widget', False):
                    if attrs['widget']=='one2many_list':
                        attrs['widget']='one2many'
                    attrs['type'] = attrs['widget']
                if attrs.get('selection',[]):
                    attrs['selection'] = eval(attrs['selection'])
                    for att_key, att_val in attrs['selection'].items():
                        for sel in fields[str(attrs['name'])]['selection']:
                            if att_key == sel[0]:
                                sel[1] = att_val
                    attrs['selection'] = fields[str(attrs['name'])]['selection']
                fields[unicode(attrs['name'])].update(attrs)
            for node2 in node:
                _parse_fields(node2, fields)
        root_node = etree.XML(arch)
        _parse_fields(root_node, fields)

        from widget.view.widget_parse import widget_parse
        models = self.models.models
        if self.current_model and (self.current_model not in models):
            models = models + [self.current_model]
        if context and context.get('view_type','') == 'diagram':
            fields = {}
        if custom:
            self.models.add_fields_custom(fields, self.models)
        else:
            self.models.add_fields(fields, self.models, context=context)
        self.fields = self.models.fields

        parser = widget_parse(parent=self.parent, window=self.window)
        view = parser.parse(self, root_node, self.fields, toolbar=toolbar, submenu=submenu, help=help)
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
        model = self.models.model_new(default, self.action_domain, ctx)
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
            self.current_view.reset()

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
            self.current_model.update_context_with_concurrency(ctx)
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
                    m.update_context_with_concurrency(ctx)

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
        limit = self.screen_container.get_limit()
        self.models.load(ids, display=False, context=self.context)
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
            if self.screen_container.help_frame:
                if vt != self.help_mode:
                    self.screen_container.help_frame.hide_all()
                else:
                    self.screen_container.help_frame.show_all()
            self.search_active(
                    active=self.show_search and vt in ('tree', 'graph', 'calendar'),
                    show_search=self.show_search and vt in ('tree', 'graph','calendar'),
            )

    def groupby_next(self):
        if not self.models.models:
             self.current_model = self.models.list_group.lst[0]
        elif self.current_view.store.on_iter_has_child(self.current_model):
                path = self.current_view.store.on_get_path(self.current_model)
                if path == (0,):
                     self.current_view.expand_row(path)
                self.current_model = self.current_view.store.on_iter_children(self.current_model)
        else:
            if self.current_model in self.current_model.list_group.lst:
                idx = self.current_model.list_group.lst.index(self.current_model)
                if idx + 1 >= len(self.current_model.list_group.lst):
                    parent = True
                    while parent:
                        parent = self.current_view.store.on_iter_parent(self.current_model)
                        if parent:
                            self.current_model = parent
                            if self.current_view.store.on_iter_next(parent):
                                break
                    self.current_model = self.current_view.store.on_iter_next(self.current_model)
                    if self.current_model == None:
                        self.current_model = self.current_view.store.on_get_iter \
                                            (self.current_view.store.on_get_path \
                                             (self.current_view.store.get_iter_first()))
                else:
                    idx = (idx+1) % len(self.current_model.list_group.lst)
                    self.current_model = self.current_model.list_group.lst[idx]
        if self.current_model:
            path = self.current_view.store.on_get_path(self.current_model)
            self.current_view.expand_row(path)
        return

    def groupby_prev(self):
        if not self.models.models :
             self.current_model = self.models.list_group.lst[-1]
        else:
             if self.current_model in self.current_model.list_group.lst:
                idx = self.current_model.list_group.lst.index(self.current_model) - 1
                if idx < 0 :
                    parent = self.current_view.store.on_iter_parent(self.current_model)
                    if parent:
                        self.current_model = parent
                else:
                    idx = (idx) % len(self.current_model.list_group.lst)
                    self.current_model = self.current_model.list_group.lst[idx]
        if self.current_model:
            path = self.current_view.store.on_get_path(self.current_model)
            self.current_view.collapse_row(path)
        return

    def display_next(self):
        self.current_view.set_value()
        if self.context.get('group_by') and \
            not self.current_view.view_type == 'form':
            if self.current_model:
                self.groupby_next()
        else:
            if self.current_model in self.models.models:
                idx = self.models.models.index(self.current_model)
                idx = (idx+1) % len(self.models.models)
                self.current_model = self.models.models[idx]
            else:
                self.current_model = len(self.models.models) and self.models.models[0]
        self.check_state()
        self.current_view.set_cursor()

    def display_prev(self):
        self.current_view.set_value()
        if self.context.get('group_by') and \
            not self.current_view.view_type == 'form':
            if self.current_model:
               self.groupby_prev()
        else:
            if self.current_model in self.models.models:
                idx = self.models.models.index(self.current_model)-1
                if idx<0:
                    idx = len(self.models.models)-1
                self.current_model = self.models.models[idx]
            else:
                self.current_model = len(self.models.models) and self.models.models[-1]
        self.check_state()
        self.current_view.set_cursor()

    def check_state(self):
        if not self.type == 'one2many'  \
            and (not self.context.get('group_by') \
                or self.current_view.view_type == 'form'):
            if self.current_model:
                self.current_model.validate_set()
            self.display()
        if self.type == 'one2many':
            self.display()

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

    def make_buttons_readonly(self, value=False):
        # This method has been created because
        # Some times if the user executes an action on an unsaved record in a dialog box
        # the record gets saved in the dialog's Group before going to the particular widgets group
        # and as a result it crashes. So we just set the buttons visible on the
        # dialog box screen to non-sensitive if the model is not saved.
        def process(widget, val):
            for wid in widget:
                if hasattr(wid, 'get_children'):
                    process(wid, val=value)
                if isinstance(wid, gtk.Button) and \
                    not isinstance(wid.parent, (gtk.HBox,gtk.VBox)):
                    wid.set_sensitive(val)
        if value and not self.current_model.id:
            return True
        process(self.widget, value)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

