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

import types
import gettext

import gtk
import gobject
from gtk import glade

import rpc
import win_selection
import win_search
import win_export
import win_import
import win_list

from gtk.gdk import Color

import common
import service
import options
import copy

import gc

from observator import oregistry
from widget.screen import Screen


class form(object):
    def __init__(self, model, res_id=False, domain=None, view_type=None,
            view_ids=None, window=None, context=None, name=False, limit=80,
            auto_refresh=False):
        if not view_type:
            view_type = ['form','tree']
        if domain is None:
            domain = []
        if view_ids is None:
            view_ids = []
        if context is None:
            context = {}

        fields = {}
        self.model = model
        self.window = window
        self.previous_action = None
        self.glade = glade.XML(common.terp_path("openerp.glade"),'win_form_container',gettext.textdomain())
        self.widget = self.glade.get_widget('win_form_container')
        self.widget.show_all()
        self.fields = fields
        self.domain = domain
        self.context = context

        self.screen = Screen(self.model, view_type=view_type,
                context=self.context, view_ids=view_ids, domain=domain,
                hastoolbar=options.options['form.toolbar'], show_search=True,
                window=self.window, limit=limit, readonly=bool(auto_refresh))
        self.screen.signal_connect(self, 'record-message', self._record_message)
        self.screen.widget.show()
        oregistry.add_receiver('misc-message', self._misc_message)

        if not name:
            self.name = self.screen.current_view.title
        else:
            self.name = name
        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(self.screen.widget)
        vp.show()
        self.sw = gtk.ScrolledWindow()
        self.sw.set_shadow_type(gtk.SHADOW_NONE)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.add(vp)
        self.sw.show()

        self.has_backup = False
        self.backup = {}

        self.widget.pack_start(self.sw)
        self.handlers = {
            'but_new': self.sig_new,
            'but_copy': self.sig_copy,
            'but_save': self.sig_save,
            'but_save_as': self.sig_save_as,
            'but_import': self.sig_import,
            'but_print_repeat': self.sig_print_repeat,
            'but_remove': self.sig_remove,
            'but_search': self.sig_search,
            'but_previous': self.sig_previous,
            'but_next': self.sig_next,
            'but_goto_id': self.sig_goto,
            'but_log': self.sig_logs,
            'but_print': self.sig_print,
            'but_reload': self.sig_reload,
            'but_print_html': self.sig_print_html,
            'but_action': self.sig_action,
            'but_switch': self.sig_switch,
            'but_attach': self.sig_attach,
            'but_close': self.sig_close,
        }
        if 'tree' in view_type:
            self.handlers['radio_tree'] = self.sig_switch_tree
        if 'form' in view_type:
            self.handlers['radio_form'] =  self.sig_switch_form
        if 'graph' in view_type:
            self.handlers['radio_graph'] =  self.sig_switch_graph
        if 'calendar' in view_type:
            self.handlers['radio_calendar'] =  self.sig_switch_calendar
        if res_id:
            if isinstance(res_id, (int, long,)):
                res_id = [res_id]
            self.screen.load(res_id)
        else:
            if self.screen.current_view.view_type == 'form':
                self.sig_new(autosave=False)
            if self.screen.current_view.view_type in ('tree', 'graph', 'calendar'):
                self.screen.search_filter()

        if auto_refresh and int(auto_refresh):
            gobject.timeout_add(int(auto_refresh) * 1000, self.sig_reload)

    def sig_switch_form(self, widget=None):
        return self.sig_switch(widget, 'form')

    def sig_switch_tree(self, widget=None):
        return self.sig_switch(widget, 'tree')

    def sig_switch_calendar(self, widget=None):
        return self.sig_switch(widget, 'calendar')

    def sig_switch_graph(self, widget=None):
        return self.sig_switch(widget, 'graph')
    
    def get_resource(self,widget):
        all_ids = rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'search', [])
        get_id = int(widget.get_value())
        if get_id in all_ids:
            current_ids = self.screen.ids_get()
            if get_id in current_ids:
                self.screen.display(get_id)
            else:
                self.screen.load([get_id])    
            self.screen.current_view.set_cursor()
        else:
            common.message(_('Resource ID does not exist for this object!'))    
    
    def get_event(self, widget, event, win):
        if event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter):
            win.destroy()
            self.get_resource(widget)
        
        
    def sig_goto(self, *args):
        if not self.modified_save():
            return
        
        glade2 = glade.XML(common.terp_path("openerp.glade"),'dia_goto_id',gettext.textdomain())
        widget = glade2.get_widget('goto_spinbutton')
        win = glade2.get_widget('dia_goto_id')
        widget.connect('key_press_event',self.get_event,win)
        
        win.set_transient_for(self.window)
        win.show_all()

        response = win.run()
        win.destroy()
        
        if response == gtk.RESPONSE_OK:
            self.get_resource(widget)
            

    def destroy(self):
        oregistry.remove_receiver('misc-message', self._misc_message)
        self.screen.signal_unconnect(self)
        self.screen.destroy()
        del self.screen
        del self.glade
        del self.widget
        self.sw.destroy()
        del self.sw
        gc.collect()

    def ids_get(self):
        return self.screen.ids_get()

    def id_get(self):
        return self.screen.id_get()

    def sig_attach(self, widget=None):
        id = self.id_get()
        if id:
            ctx = self.context.copy()
            ctx.update(rpc.session.context)
            action = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.attachment', 'action_get', ctx)
            action['domain'] = [('res_model', '=', self.model), ('res_id', '=', id)]
            ctx['default_res_model'] = self.model
            ctx['default_res_id'] = id
            obj = service.LocalService('action.main')
            obj._exec_action(action, {}, ctx)
        else:
            self.message_state(_('No record selected ! You can only attach to existing record.'), color='red')
        return True

    def sig_switch(self, widget=None, mode=None):
        if not self.modified_save():
            return
        if mode<>self.screen.current_view.view_type:
            self.screen.switch_view(mode=mode)
            self.sig_reload()
            self.screen.current_view.set_cursor()

    def sig_logs(self, widget=None):
        id = self.id_get()
        if not id:
            self.message_state(_('You have to select a record !'), color='red')
            return False
        res = rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'perm_read', [id])
        message = ''
        for line in res:
            todo = [
                ('id', _('ID')),
                ('create_uid', _('Creation User')),
                ('create_date', _('Creation Date')),
                ('write_uid', _('Latest Modification by')),
                ('write_date', _('Latest Modification Date'))
            ]
            for (key,val) in todo:
                if line[key] and key in ('create_uid','write_uid','uid'):
                    line[key] = line[key][1]
                message+=val+': '+str(line[key] or '/')+'\n'
        common.message(message)
        return True

    def sig_remove(self, widget=None):
        if not self.id_get():
            msg = _('Record is not saved ! \n Do You want to Clear Current Record ?')
        else:
            if self.screen.current_view.view_type == 'form':
                msg = _('Are you sure to remove this record ?')
            else:
                msg = _('Are you sure to remove those records ?')
        if common.sur(msg):
            id = self.screen.remove(unlink=True)
            if not id:
                self.message_state(_('Resources cleared.'), color='darkgreen')
            else:
                self.message_state(_('Resources successfully removed.'), color='darkgreen')
        self.sig_reload()
        
    def sig_import(self, widget=None):
        fields = []
        while(self.screen.view_to_load):
            self.screen.load_view_to_load()
        win = win_import.win_import(self.model, self.screen.fields, fields, parent=self.window,local_context= self.screen.context)
        res = win.go()

    def sig_save_as(self, widget=None):
        fields = []
        while(self.screen.view_to_load):
            self.screen.load_view_to_load()
        win = win_export.win_export(self.model, self.screen.ids_get(), self.screen.fields, fields, parent=self.window, context=self.context)
        res = win.go()

    def sig_new(self, widget=None, autosave=True):
        if autosave:
            if not self.modified_save():
                return
        self.screen.new()
        self.message_state('')

    def sig_copy(self, *args):
        if not self.modified_save():
            return
        res_id = self.id_get()
        ctx = self.context.copy()
        ctx.update(rpc.session.context)
        new_id = rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'copy', res_id, {}, ctx)
        if new_id:
            self.screen.load([new_id])
            self.screen.current_view.set_cursor()
            self.message_state(_('Working now on the duplicated document !'))
        self.sig_reload()
        
    def _form_save(self, auto_continue=True):
        pass

    def sig_save(self, widget=None, sig_new=True, auto_continue=True):
        id = self.screen.save_current()
        if id:
            self.message_state(_('Document Saved.'), color="darkgreen")
        else:
            common.warning(_('Invalid form, correct red fields !'),_('Error !'))
            self.message_state(_('Invalid form, correct red fields !'), color="red")
        return bool(id)

    def sig_previous(self, widget=None):
        if not self.modified_save():
            return
        self.screen.display_prev()
        self.message_state('')

    def sig_next(self, widget=None):
        if not self.modified_save():
            return
        self.screen.display_next()
        self.message_state('')

    def sig_reload(self, test_modified=True):
        if not hasattr(self, 'screen'):
            return False
        if test_modified and self.screen.is_modified():
            res = common.sur_3b(_('This record has been modified\n' \
                    'do you want to save it ?'))
            if res == 'ok':
                self.sig_save()
            elif res == 'ko':
                pass
            else:
                return False
        if self.screen.current_view.view_type == 'form':
            self.screen.cancel_current()
            self.screen.display()
        else:
            id = self.screen.id_get()
            self.screen.search_filter()
            for model in self.screen.models:
                if model.id == id:
                    self.screen.current_model = model
                    self.screen.display()
                    break
        self.message_state('')
        return True

    def sig_action(self, keyword='client_action_multi', previous=False, report_type='pdf', adds={}):
        ids = self.screen.ids_get()
        if self.screen.current_model:
            id = self.screen.current_model.id
        else:
            id = False
        if self.screen.current_view.view_type == 'form':
            id = self.screen.save_current()
            if not id:
                return False
            ids = [id]
        if self.screen.current_view.view_type == 'tree':
            sel_ids = self.screen.current_view.sel_ids_get()
            if sel_ids:
                ids = sel_ids
        if len(ids):
            obj = service.LocalService('action.main')
            if previous and self.previous_action:
                obj._exec_action(self.previous_action[1], {'model':self.screen.resource, 'id': id or False, 'ids':ids, 'report_type': report_type}, self.screen.context)
            else:
                res = obj.exec_keyword(keyword, {'model':self.screen.resource, 'id': id or False, 'ids':ids, 'report_type': report_type}, adds, self.screen.context)
                if res:
                    self.previous_action = res
            self.sig_reload(test_modified=False)
        else:
            self.message_state(_('You must select one or several records !'),color='red')

    def sig_print_repeat(self):
        self.sig_action('client_print_multi', True)

    def sig_print_html(self):
        self.sig_action('client_print_multi', report_type='html')

    def sig_print(self):
        self.sig_action('client_print_multi', adds={_('Print Screen').encode('utf8'): {'report_name':'printscreen.list', 'name':_('Print Screen'), 'type':'ir.actions.report.xml'}})

    def sig_search(self, widget=None):
        if not self.modified_save():
            return
        dom = self.domain
        win = win_search.win_search(self.model, domain=self.domain, context=self.context, parent=self.window)
        res = win.go()
        if res:
            self.screen.clear()
            self.screen.load(res)

    def message_state(self, message, context='message', color=None):
        sb = self.glade.get_widget('stat_state')
        if color is not None:
            message = '<span foreground="%s">%s</span>' % (color, message)
        sb.set_label(message)

    def _record_message(self, screen, signal_data):
        if not signal_data[3]:
            msg = _('No record selected')
        else:
            name = '_'
            if signal_data[0]>=0:
                name = str(signal_data[0]+1)
            name2 = _('New document')
            if signal_data[3]:
                name2 = _('Editing document (id: ')+str(signal_data[3])+')'
            # Total Records should never change    
            tot_count = signal_data[2] < signal_data[1] and  str(signal_data[1]) or str(signal_data[2])
            msg = _('Record: ') + name + ' / ' + str(signal_data[1]) + \
                    _(' of ') + str(tot_count) + ' - ' + name2
        sb = self.glade.get_widget('stat_form')
        cid = sb.get_context_id('message')
        sb.push(cid, msg)

    def _misc_message(self, obj, message, color=None):
        self.message_state(message, color=color)

    def modified_save(self, reload=True):
        if self.screen.is_modified():
            value = common.sur_3b(_('This record has been modified\ndo you want to save it ?'))
            if value == 'ok':
                return self.sig_save()
            elif value == 'ko':
                if reload:
                    self.sig_reload(test_modified=False)
                return True
            else:
                return False
        return True

    def sig_close(self, urgent=False):
        return self.modified_save(reload=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

