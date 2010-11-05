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

import re
import time
import common
import rpc
from rpc import RPCProxy
from rpc import CONCURRENCY_CHECK_FIELD
import field
import signal_event
import gtk
import gettext
import service
from gtk import glade
import tools
from field import O2MField

class EvalEnvironment(object):
    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, item):
        if item=='parent' and self.parent.parent:
            return EvalEnvironment(self.parent.parent)
        if item=="current_date":
            return time.strftime('%Y-%m-%d')
        if item=="time":
            return time
        return self.parent.get(includeid=True)[item]


class ModelRecord(signal_event.signal_event):
    def __init__(self, resource, id, group=None, parent=None, new=False, list_parent=None):
        super(ModelRecord, self).__init__()
        self.resource = str(resource)
        self.rpc = RPCProxy(self.resource)
        self.id = id
        self.list_parent = list_parent
        self._loaded = False
        self.parent = parent
        self.mgroup = group
        self.value = {}
        self.state_attrs = {}
        self.modified = False
        self.modified_fields = {}
        self.pager_cache = {}
        self.is_m2m_modified = False
        self._concurrency_check_data = False
        for key, val in self.mgroup.mfields.items():
            self.value[key] = val.create(self)
            if (new and val.attrs['type']=='one2many') and (val.attrs.get('mode', 'tree,form').startswith('form')):
                mod = self.value[key].model_new()
                self.value[key].model_add(mod)

    def __getitem__(self, name):
        return self.mgroup.mfields.get(name, False)

    def __repr__(self):
        return '<ModelRecord %s@%s>' % (self.id, self.resource)

    def is_modified(self):
        return self.modified

    def is_wizard(self):
        return self.mgroup.is_wizard

    def fields_get(self):
        return self.mgroup.mfields

    def _check_load(self):
        if not self._loaded:
            self.reload()
            return True
        return False

    def update_context_with_concurrency(self, context):
        if self.id and self.is_modified():
            context.setdefault(CONCURRENCY_CHECK_FIELD, {})["%s,%s" % (self.resource, self.id)] = self._concurrency_check_data
        for name, field in self.mgroup.mfields.items():
            if isinstance(field, O2MField):
                v = self.value[field.name]
                from itertools import chain
                for m in chain(v.models, v.models_removed):
                    m.update_context_with_concurrency(context)

    def get(self, get_readonly=True, includeid=False, check_load=True, get_modifiedonly=False):
        if check_load:
            self._check_load()
        value = []
        for name, field in self.mgroup.mfields.items():
            if (get_readonly or not field.get_state_attrs(self).get('readonly', False)) \
                and (not get_modifiedonly or (field.name in self.modified_fields or isinstance(field, O2MField))):
                    value.append((name, field.get(self, readonly=get_readonly,
                        modified=get_modifiedonly)))
        value = dict(value)
        if includeid:
            value['id'] = self.id
        return value

    def cancel(self):
        self._loaded = False
        self.reload()

    def failed_validation(self):
        invalid_fields = self.rpc.get_invalid_fields()
        for item in invalid_fields:
           if item in self.mgroup.mfields:
               self.mgroup.mfields[item].get_state_attrs(self)['valid'] = False

    def save(self, reload=True):
        self._check_load()
        try:
            if not self.id:
                value = self.get(get_readonly=False)
                self.id = self.rpc.create(value, self.context_get())
            else:
                if not self.is_modified():
                    return self.id
                value = self.get(get_readonly=False, get_modifiedonly=True)
                context = self.context_get().copy()
                self.update_context_with_concurrency(context)
                res = self.rpc.write([self.id], value, context)
                #if type(res) in (int, long):
                #    self.id = res
        except Exception, e:
            if hasattr(e, 'faultCode') and e.faultCode.find('ValidateError')>-1:
                self.failed_validation()
                return False
            pass

        self._loaded = False
        if reload:
            self.reload()
        else:
            # just reload the CONCURRENCY_CHECK_FIELD
            self._reload([CONCURRENCY_CHECK_FIELD])
        return self.id

    def default_get(self, domain=[], context={}):
        if len(self.mgroup.fields):
            val = self.rpc.default_get(self.mgroup.fields.keys(), context)
            for d in domain:
                if d[0] in self.mgroup.fields:
                    if d[1] == '=':
                        if d[2]:
                            value = d[2]
                            # domain containing fields like M2M/O2M should return values as list
                            if self.mgroup.fields[d[0]].get('type', '') in ('many2many','one2many'):
                                if not isinstance(d[2], (bool,list)):
                                    value = [d[2]]
                            val[d[0]] = value
                    if d[1] == 'in' and len(d[2]) == 1:
                        val[d[0]] = d[2][0]
            self.set_default(val)

    def name_get(self):
        name = self.rpc.name_get([self.id], rpc.session.context)[0]
        return name

    def validate_set(self):
        change = self._check_load()
        for fname in self.mgroup.mfields:
            field = self.mgroup.mfields[fname]
            change = change or not field.get_state_attrs(self).get('valid', True)
            field.get_state_attrs(self)['valid'] = True
        if change:
            self.signal('record-changed')
        self.reload()
        return change

    def validate(self):
        self._check_load()
        ok = True
        for fname in self.mgroup.mfields:
            if not self.mgroup.mfields[fname].validate(self):
                ok = False
        return ok

    def _get_invalid_fields(self):
        res = []
        for fname, field in self.mgroup.mfields.items():
            if not field.get_state_attrs(self).get('valid', True):
                res.append((fname, field.attrs['string']))
        return dict(res)
    invalid_fields = property(_get_invalid_fields)

    def context_get(self):
        return self.mgroup.context

    def get_default(self):
        self._check_load()
        value = dict([(name, field.get_default(self))
                      for name, field in self.mgroup.mfields.items()])
        return value

    def set_default(self, val):
        fields_with_on_change = {}
        for fieldname, value in val.items():
            if fieldname not in self.mgroup.mfields:
                continue
            # Fields with on_change should be processed last otherwise
            # we might override the values the on_change() sets with
            # the next defaults. There's still a possible issue with
            # the order in which we process the defaults of the fields
            # with on_change() in case they cascade, but that's fixable
            # normally in the view a single clean on_change on the first
            # field.
            if self.mgroup.mfields[fieldname].attrs.get('on_change',False):
                fields_with_on_change[fieldname] = value
            else:
                self.mgroup.mfields[fieldname].set_default(self, value)
        for field, value in fields_with_on_change.items():
            self.mgroup.mfields[field].set_default(self, value)
        self._loaded = True
        self.signal('record-changed')

    def set(self, val, modified=False, signal=True):
        later = {}
        for fieldname, value in val.items():
            if fieldname == CONCURRENCY_CHECK_FIELD:
                self._concurrency_check_data = value
            if fieldname not in self.mgroup.mfields:
                continue
            if isinstance(self.mgroup.mfields[fieldname], field.O2MField):
                 self.pager_cache[fieldname] = value
                 later[fieldname] = value
                 continue
            if isinstance(self.mgroup.mfields[fieldname], field.M2MField):
                self.pager_cache[fieldname] = value

            self.mgroup.mfields[fieldname].set(self, value, modified=modified)

        for fieldname, value in later.items():
            self.mgroup.mfields[fieldname].set(self, value, modified=modified)
        self._loaded = True
        self.modified = modified
        if not self.modified:
            self.modified_fields = {}
        if signal:
            self.signal('record-changed')

    def reload(self):
        return self._reload(self.mgroup.mfields.keys() + [CONCURRENCY_CHECK_FIELD])

    def _reload(self, fields):
        if not self.id:
            return
        c = rpc.session.context.copy()
        c.update(self.context_get())
        c['bin_size'] = True
        res = self.rpc.read([self.id], fields, c)
        if res:
            value = res[0]
            if self.parent:
                self.set(value,signal=False)
            else:
                self.set(value)


    def expr_eval(self, dom, check_load=True):
        if not isinstance(dom, basestring):
            return dom
        if check_load:
            self._check_load()
        d = {}
        for name, mfield in self.mgroup.mfields.items():
            d[name] = mfield.get(self, check_load=check_load)

        d['current_date'] = time.strftime('%Y-%m-%d')
        d['time'] = time
        d['context'] = self.context_get()
        d['active_id'] = self.id
        if self.parent:
            d['parent'] = EvalEnvironment(self.parent)
        val = tools.expr_eval(dom, d)
        return val

    #XXX Shoud use changes of attributes (ro, ...)
    def on_change(self, callback):
        match = re.match('^(.*?)\((.*)\)$', callback)
        if not match:
            raise Exception, 'ERROR: Wrong on_change trigger: %s' % callback
        func_name = match.group(1)
        arg_names = [n.strip() for n in match.group(2).split(',') if n.strip()]
        args = [self.expr_eval(arg) for arg in arg_names]
        ids = self.id and [self.id] or []
        response = getattr(self.rpc, func_name)(ids, *args)
        if response:
            self.set(response.get('value', {}), modified=True)
            if 'domain' in response:
                for fieldname, value in response['domain'].items():
                    if fieldname not in self.mgroup.mfields:
                        continue
                    self.mgroup.mfields[fieldname].attrs['domain'] = value
            if 'context' in response:
                value = response.get('context', {})
                self.mgroup.context = value

            warning=response.get('warning', {})
            if warning:
                common.warning(warning['message'], warning['title'])
        self.signal('record-changed')

    def on_change_attrs(self, callback):
        self.signal('attrs-changed')

    def cond_default(self, field, value):
        if field in self.mgroup.mfields:
            if self.mgroup.mfields[field].attrs.get('change_default', False):
                ir = RPCProxy('ir.values')
                values = ir.get('default', '%s=%s' % (field, value),
                                [(self.resource, False)], False, {})
                data = {}
                for index, fname, value in values:
                    data[fname] = value
                self.set_default(data)

    # Performing button clicks on both forms of view: list and form.
    def get_button_action(self, screen, id=None, attrs={}):

        """Arguments:
        screen : Screen to be worked upon
        id     : Id of the record for which the button is clicked
        attrs  : Button Attributes
        """
        if not id:
            id = self.id
        if not attrs.get('confirm', False) or common.sur(attrs['confirm']):
            button_type = attrs.get('type', 'workflow')
            obj = service.LocalService('action.main')

            if button_type == 'workflow':
                result = rpc.session.rpc_exec_auth('/object', 'exec_workflow',
                                                   self.resource, attrs['name'], self.id)
                if type(result)==type({}):
                    if result['type']== 'ir.actions.act_window_close':
                        screen.window.destroy()
                    else:
                        datas = {'ids':[id], 'id':id}
                        obj._exec_action(result, datas)
                elif type([]) == type(result):
                    datas = {'ids':[id]}
                    for rs in result:
                        obj._exec_action(rs, datas)

            elif button_type == 'object':
                if not self.id:
                    return
                context = self.context_get()
                if 'context' in attrs:
                    context.update(self.expr_eval(attrs['context'], check_load=False))
                result = rpc.session.rpc_exec_auth('/object', 'execute',
                                                   self.resource,attrs['name'], [id], context)
                if isinstance(result, dict):
                    if not result.get('nodestroy', False):
                        screen.window.destroy()
                    obj._exec_action(result, {}, context=context)

            elif button_type == 'action':
                action_id = int(attrs['name'])
                context = screen.context.copy()
                if 'context' in attrs:
                    context.update(self.expr_eval(attrs['context'], check_load=False))
                datas = {'model':self.resource,
                         'id': id or False,
                         'ids': id and [id] or [],
                         'report_type': 'pdf'
                         }
                obj.execute(action_id, datas, context=context)
            else:
                raise Exception, 'Unallowed button type'
            if screen.current_model and screen.current_view.view_type != 'tree':
                screen.reload()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

