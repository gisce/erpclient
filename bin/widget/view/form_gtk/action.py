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
from gtk import glade

import gettext
import common
import wid_common

import interface
from widget.screen import Screen

import rpc
import tools
import time
from modules.gui.window.win_search import win_search
import service
import datetime

class action(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)

        self.act_id=attrs['name']
        res = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.actions.actions', 'read', [self.act_id], ['type'], rpc.session.context)
        if not res:
            raise Exception, 'ActionNotFound'
        type=res[0]['type']
        self.action = rpc.session.rpc_exec_auth('/object', 'execute', type, 'read', [self.act_id], False, rpc.session.context)[0]
        if 'view_mode' in attrs:
            self.action['view_mode'] = attrs['view_mode']

        if self.action['type']=='ir.actions.act_window':
            if not self.action.get('domain', False):
                self.action['domain']='[]'
            self.context = {'active_id': False, 'active_ids': []}
            self.context.update(eval(self.action.get('context', '{}'), self.context.copy()))
            a = self.context.copy()
            a['time'] = time
            a['datetime'] = datetime
            self.domain = tools.expr_eval(self.action['domain'], a)

            view_id = []
            if self.action['view_id']:
                view_id = [self.action['view_id'][0]]
            if self.action['view_type']=='form':
                mode = (self.action['view_mode'] or 'form,tree').split(',')
                self.screen = Screen(self.action['res_model'], view_type=mode, context=self.context, view_ids = view_id, domain=self.domain)
                self.win_gl = glade.XML(common.terp_path("openerp.glade"), 'widget_paned', gettext.textdomain())

                self.win_gl.signal_connect('on_switch_button_press_event', self._sig_switch)
                self.win_gl.signal_connect('on_search_button_press_event', self._sig_search)
                self.win_gl.signal_connect('on_open_button_press_event', self._sig_open)
                label=self.win_gl.get_widget('widget_paned_lab')
                label.set_text(attrs.get('string', self.screen.current_view.title))
                vbox=self.win_gl.get_widget('widget_paned_vbox')
                vbox.add(self.screen.widget)
                self.widget=self.win_gl.get_widget('widget_paned')
                self.widget.set_size_request(int(attrs.get('width', -1)), int(attrs.get('height', -1)))
            elif self.action['view_type']=='tree':
                pass #TODO

    def _sig_switch(self, *args):
        self.screen.switch_view()

    def _sig_search(self, *args):
        win = win_search(self.action['res_model'], domain=self.domain, context=self.context)
        res = win.go()
        if res:
            self.screen.clear()
            self.screen.load(res)

    def _sig_open(self, *args):
        obj = service.LocalService('action.main')
        obj.execute(self.act_id, {})

    def set_value(self, mode, model_field):
        self.screen.current_view.set_value()
        return True

    def display(self, model, model_field):
        res_id = rpc.session.rpc_exec_auth('/object', 'execute',
                self.action['res_model'], 'search', self.domain, 0,
                self.action.get('limit', 80),False,self.context)
        self.screen.clear()
        self.screen.load(res_id)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

