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
import rpc
import wid_int
import tools
import common

class char(wid_int.wid_int):
    def __init__(self, name, parent, attrs={}, screen=None):
        wid_int.wid_int.__init__(self, name, parent, attrs, screen)
        self.attrs = attrs
        self.widget = gtk.Entry()
        if attrs.get('type') == 'char':
            self.widget.set_max_length(int(attrs.get('size',16)))
        self.widget.set_width_chars(15)
        self.widget.set_property('activates_default', True)
        if self.default_search:
            model = self.attrs.get('relation', '')
            if attrs.get('type','') == 'many2one' and model:
                try:
                    value = rpc.session.rpc_exec_auth('/object', 'execute', model, 'name_get', self.default_search)
                except rpc.rpc_exception, e:
                    common.error(_('Error: ')+str(e.type), e.message, e.data)
                    value = []
                self.default_search = value and value[0] and value[0][1] or ''
            self.widget.set_text(self.default_search or '')

    def _value_get(self):
        s = self.widget.get_text()
        domain = []
        context = {}
        if s:
            if self.attrs.get('filter_domain'):
                domain = tools.expr_eval(self.attrs['filter_domain'], {'self': s})
            else:
                domain = [(self.name,self.attrs.get('comparator','ilike'),s)]
            context = tools.expr_eval(self.attrs.get('context',"{}"), {'self': s})
        return {
            'domain':domain,
            'context': context
        }

    def _value_set(self, value):
        self.widget.set_text(value)

    value = property(_value_get, _value_set, None, _('The content of the widget or ValueError if not valid'))

    def clear(self):
        self.value = ''

    def grab_focus(self):
        self.widget.grab_focus()
        
    def _readonly_set(self, value):
        self.widget.set_editable(not value)
        self.widget.set_sensitive(not value)

    def sig_activate(self, fct):
        self.widget.connect_after('activate', fct)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

