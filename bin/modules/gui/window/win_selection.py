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
from gtk import glade
import gettext
import common

from view_tree import parse
import gobject
import rpc

fields_list_type = {
    'checkbox': gobject.TYPE_BOOLEAN
}

#
# Should be replaced by win_browse
#

class win_selection_class(object):
    def __init__(self, ids, model, view=None):
        self.glade = glade.XML(common.terp_path("openerp.glade"), "win_selection",gettext.textdomain())
        self.win = self.glade.get_widget('win_selection')
        self.win.set_icon(common.OPENERP_ICON)
        self.parent = service.LocalService('gui.main').window
        self.win.set_transient_for(parent)

        self.ids = ids
        self.view = self.glade.get_widget('win_sel_tree')
        self.view.get_selection().set_mode('single')
        if view==None:
            fields = { 'name': {'type': 'char', 'string':_('Name')} }
            xml = '''<?xml version="1.0"?>
<tree string="%s">
    <field name="name" string="%s"></field>
</tree>''' % (_('Ressource Name'), _('Names'))
        else:
            fields = None
            xml = None

        p = parse.parse(fields)
        p.parse(xml, self.view)
        self.view.set_expander_column(self.view.get_column(1))
        self.fields_order = p.fields_order

        types=[ gobject.TYPE_STRING ]
        for x in self.fields_order:
            types.append( fields_list_type.get(fields[x]['type'], gobject.TYPE_STRING))
        self.model = gtk.ListStore(*types)

        if view==None:
            res_ids = rpc.session.rpc_exec_auth('/object', 'execute', model, 'name_get', self.ids, rpc.session.context)
            for res in res_ids:
                num = self.model.append()
                self.model.set(num, 0, res[0], 1, res[1])
        else:
            pass # Todo

        self.view.set_model(self.model)
        self.view.show_all()

    def id_name_get(self):
        id = self.value_get(0)
        if id:
            return (id, self.value_get(1))
        return None

    def value_get(self, col):
        sel = self.view.get_selection().get_selected()
        if sel==None:
            return None
        (model, iter) = sel
        return model.get_value(iter, col)

    def go(self):
        button = self.win.run()
        if button==gtk.RESPONSE_OK:
            res = self.id_name_get()
        else:
            res=None
        self.parent.present()
        self.win.destroy()
        return res

def win_selection_h(from_resource, ids, model, view=None):
    return win_selection(ids, model, view)

def win_selection(ids, model, view=None):
    if len(ids)==1:
        return rpc.session.rpc_exec_auth('/object', 'execute', model, 'name_get', ids, rpc.session.context)[0]
    win = win_selection_class(ids, model, view)
    res = win.go()
    return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

