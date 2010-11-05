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

import copy
import gtk
import wid_common

import rpc
import common

_attrs_boolean = {
    'required': False,
    'readonly': False
}

class widget_interface(object):
    def __init__(self, window, parent=None, view=None, attrs=None):
        if attrs is None:
            attrs = {}
        self.parent = parent
        self._window = window
        self._view = None
        self.attrs = attrs
        for key,val in _attrs_boolean.items():
            self.attrs[key] = attrs.get(key, False) not in ('False', '0', False)
        self.default_readonly = self.attrs.get('readonly', False)
        self._menu_entries = [
            (_('Set to default value'), lambda x: self._menu_sig_default_get(), 1),
            (_('Set as default'), lambda x: self._menu_sig_default_set(), 1),
        ]

    def destroy(self):
        pass

    def _menu_sig_default_get(self):
        try:
            if self._view.modelfield.get_state_attrs(self._view.model).get('readonly', False):
                return False
            model = self._view.modelfield.parent.resource
            res = rpc.session.rpc_exec_auth_try('/object', 'execute', model, 'default_get', [self.attrs['name']])
            self._view.modelfield.set(self._view.model, res.get(self.attrs['name'], False), modified=True)
            self.display(self._view.model, self._view.modelfield)
        except:
            common.warning('You can not set to the default value here !', 'Operation not permited')
            return False

    def sig_activate(self, widget=None):
        # emulate a focus_out so that the onchange is called if needed
        self._focus_out()

    def _readonly_set(self, ro):
        pass

    def _color_widget(self):
        return self.widget

    def color_set(self, name):
        widget = self._color_widget()
        map = widget.get_colormap()
        colour = map.alloc_color(common.colors.get(name,'white'))
        widget.modify_bg(gtk.STATE_ACTIVE, colour)
        widget.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        widget.modify_base(gtk.STATE_NORMAL, colour)
        widget.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        widget.modify_text(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse("black"))

    def _menu_sig_default_set(self):
        deps = []
        wid = self._view.view_form.widgets
        for wname, wview in self._view.view_form.widgets.items():
            if wview.modelfield.attrs.get('change_default', False):
                value = wview.modelfield.get(self._view.model)
                deps.append((wname, wname, value, value))
        value = self._view.modelfield.get_default(self._view.model)
        model = self._view.modelfield.parent.resource
        wid_common.field_pref_set(self._view.widget_name,
                self.attrs.get('string', self._view.widget_name), model,
                value, deps, window=self._window)

    def _menu_open(self, obj, event):
        if event.button == 3:
            menu = gtk.Menu()
            for stock_id,callback,sensitivity in self._menu_entries:
                if stock_id:
                    item = gtk.ImageMenuItem(stock_id)
                    if callback:
                        item.connect("activate",callback)
                    item.set_sensitive(sensitivity)
                else:
                    item=gtk.SeparatorMenuItem()
                item.show()
                menu.append(item)
            menu.popup(None,None,None,event.button,event.time)
            return True

    def _focus_in(self):
        pass

    def _focus_out(self):
        if not self._view.modelfield:
            return False
        self.set_value(self._view.model, self._view.modelfield)

    def display(self, model, modelfield):
        if not modelfield:
            self._readonly_set(self.attrs.get('readonly', False))
            return
        self._readonly_set(modelfield.get_state_attrs(model).get('readonly', False))
        if modelfield.get_state_attrs(model).get('readonly', False):
            self.color_set('readonly')
        elif not modelfield.get_state_attrs(model).get('valid', True):
            self.color_set('invalid')
        elif modelfield.get_state_attrs(model).get('required', False):
            self.color_set('required')
        else:
            self.color_set('normal')

    def sig_changed(self):
        if self.attrs.get('on_change',False):
            self._view.view_form.screen.on_change(self.attrs['on_change'])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

