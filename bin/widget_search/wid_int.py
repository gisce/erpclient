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

class wid_int(object):
    def __init__(self, name, parent, attrs={}, call=None):
        self.call = call
        self._value = None
        self.parent = parent
        self.name = name
        self.model = attrs.get('model', None)
        self.attrs = attrs
        self.default_search = False
        if self.attrs.get('name',False):
            if isinstance(call, tuple):
               default_context = call[0].context
            else:
               default_context = call.context
            context_str = 'search_default_' + str(self.attrs['name'])
            self.default_search = default_context.get(context_str,False)

    def clear(self):
        self.value = ''

    def _value_get(self):
        return {'domain': [(self.name,'=',self._value)]}

    def _value_set(self, value):
        self._value = value

    value = property(_value_get, _value_set, None, _('The content of the widget or exception if not valid'))

    def _readonly_set(self, value):
        pass

    def sig_activate(self, fct):
        pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

