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

import os
import copy
import time
import base64
import datetime
import service
import rpc
import wizard
import printer
import common
import tools
import options
from widget.view.form_gtk.many2one import dialog
from lxml import etree

class main(service.Service):
    def __init__(self, name='action.main'):
        service.Service.__init__(self, name)

    def exec_report(self, name, data, context={}):
        datas = data.copy()
        ids = datas['ids']
        del datas['ids']
        if not ids:
            ids =  rpc.session.rpc_exec_auth('/object', 'execute', datas['model'], 'search', datas.get('_domain',[]))
            if ids == []:
                common.message(_('Nothing to print!'))
                return False
            datas['id'] = ids[0]
        ctx = rpc.session.context.copy()
        ctx.update(context)
        report_id = rpc.session.rpc_exec_auth('/report', 'report', name, ids, datas, ctx)
        state = False
        attempt = 0
        max_attemps = int(options.options.get('client.timeout') or 0)
        while not state:
            val = rpc.session.rpc_exec_auth('/report', 'report_get', report_id)
            if not val:
                return False
            state = val['state']
            if not state:
                time.sleep(1)
                attempt += 1
            if attempt>max_attemps:
                common.message(_('Printing aborted, too long delay !'))
                return False
        printer.print_data(val)
        return True

    def execute(self, act_id, datas, type=None, context={}):
        act_id = int(act_id)
        ctx = rpc.session.context.copy()
        ctx.update(context)
        if type is None:
            res = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.actions.actions', 'read', int(act_id), ['type'], ctx)
            if not (res and len(res)):
                raise Exception, 'ActionNotFound'
            type=res['type']

        res = rpc.session.rpc_exec_auth('/object', 'execute', type, 'read', act_id, False, ctx)
        self._exec_action(res,datas,context)

    def _exec_action(self, action, datas, context={}):
        if isinstance(action, bool) or 'type' not in action:
            return
        # Updating the context : Adding the context of action in order to use it on Views called from buttons
        if datas.get('id',False):
            context.update( {'active_id': datas.get('id',False), 'active_ids': datas.get('ids',[]), 'active_model': datas.get('model',False)})
        context.update(tools.expr_eval(action.get('context','{}'), context.copy()))
        if action['type'] in ['ir.actions.act_window', 'ir.actions.submenu']:
            for key in ('res_id', 'res_model', 'view_type', 'view_mode',
                    'limit', 'auto_refresh', 'search_view', 'auto_search', 'search_view_id'):
                datas[key] = action.get(key, datas.get(key, None))

            datas['auto_search'] = action.get('auto_search', True)
            if not datas['search_view'] and datas['search_view_id']:
                 datas['search_view'] = str(rpc.session.rpc_exec_auth('/object', 'execute', datas['res_model'], 'fields_view_get', datas['search_view_id'], 'search', context))

            if datas['limit'] is None or datas['limit'] == 0:
                datas['limit'] = 80

            view_ids=False
            if action.get('views', []):
                if isinstance(action['views'],list):
                    view_ids=[x[0] for x in action['views']]
                    datas['view_mode']=",".join([x[1] for x in action['views']])
                else:
#                    view_ids=[(action['view_type']=='tree') and 1 or False,(action['view_type']=='form') and 1 or False]
                    if action.get('view_id', False):
                        view_ids=[action['view_id'][0]]
            elif action.get('view_id', False):
                view_ids=[action['view_id'][0]]

            if not action.get('domain', False):
                action['domain']='[]'
            domain_ctx = context.copy()
            domain_ctx['time'] = time
            domain_ctx['datetime'] = datetime
            domain = tools.expr_eval(action['domain'], domain_ctx)
            help = {}
            if action.get('display_menu_tip', False):
                msg = action.get('help', False)
                title = action.get('name', False)
                if msg and len(msg):
                    help['msg'] =  msg
                    help['title'] = title or ''
            if datas.get('domain', False):
                domain.append(datas['domain'])
            if action.get('target', False)=='new':
                dia = dialog(datas['res_model'], id=datas.get('res_id',None), window=datas.get('window',None), domain=domain, context=context, view_ids=view_ids,target=True, view_type=datas.get('view_mode', 'tree').split(','))
                if dia.dia.get_has_separator():
                    dia.dia.set_has_separator(False)
                dia.run()
                dia.destroy()
            else:
                obj = service.LocalService('gui.window')
                obj.create(view_ids, datas['res_model'], datas['res_id'], domain,
                        action['view_type'], datas.get('window',None), context,
                        datas['view_mode'], name=action.get('name', False), help=help,
                        limit=datas['limit'], auto_refresh=datas['auto_refresh'], auto_search = datas['auto_search'], search_view = datas['search_view'])

        elif action['type']=='ir.actions.server':
            res = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.actions.server', 'run', [action['id']], context)
            if res:
                if not isinstance(res, list):
                    res = [res]
                for r in res:
                    self._exec_action(r, datas, context)

        elif action['type']=='ir.actions.wizard':
            win=None
            if 'window' in datas:
                win=datas['window']
                del datas['window']
            wizard.execute(action['wiz_name'], datas, parent=win, context=context)

        elif action['type']=='ir.actions.report.custom':
            if 'window' in datas:
                win=datas['window']
                del datas['window']
            datas['report_id'] = action['report_id']
            self.exec_report('custom', datas, context)

        elif action['type']=='ir.actions.report.xml':
            if 'window' in datas:
                win=datas['window']
                del datas['window']
            if not datas:
                datas = action.get('datas',[])
            self.exec_report(action['report_name'], datas, context)

        elif action['type']=='ir.actions.act_url':
            tools.launch_browser(action.get('url',''))

    def exec_keyword(self, keyword, data={}, adds={}, context={}, warning=True):
        actions = None
        if 'id' in data:
            try:
                id = data.get('id', False)
                actions = rpc.session.rpc_exec_auth('/object', 'execute',
                        'ir.values', 'get', 'action', keyword,
                        [(data['model'], id)], False, rpc.session.context)
                actions = map(lambda x: x[2], actions)
            except rpc.rpc_exception, e:
#               common.error(_('Error: ')+str(e.type), e.message, e.data)
                return False
        keyact = {}
        for action in actions:
            action_name = action.get('name') or ''
            keyact[action_name.encode('utf8')] = action
        keyact.update(adds)
        res = common.selection(_('Select your action'), keyact)
        if res:
            (name,action) = res
            context.update(rpc.session.context)
            self._exec_action(action, data, context=context)
            return (name, action)
        return False

main()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

