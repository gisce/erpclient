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

import gettext

import gtk
from gtk import glade

import rpc

import common
import win_search
import copy
import service
from widget.screen import Screen

import form

import options
import translate


class win_preference(object):
    def __init__(self, parent=None):
        self.glade = glade.XML(common.terp_path("openerp.glade"),'win_preference', gettext.textdomain())
        self.win = self.glade.get_widget('win_preference')
        self.win.set_icon(common.OPENERP_ICON)
        if not parent:
            parent = service.LocalService('gui.main').window
        self.win.set_transient_for(parent)
        self.parent = parent

        action_id = rpc.session.rpc_exec_auth('/object', 'execute', 'res.users', 'action_get', {})
        action = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.actions.act_window', 'read', [action_id], False, rpc.session.context)[0]

        view_ids=[]
        if action.get('views', []):
            view_ids=[x[0] for x in action['views']]
        elif action.get('view_id', False):
            view_ids=[action['view_id'][0]]

        self.screen = Screen('res.users', view_type=[], window=parent)
        self.screen.add_view_id(view_ids[0], 'form', display=True)
        self.screen.load([rpc.session.uid])
        self.screen.display(rpc.session.uid)

        vbox = self.glade.get_widget('preference_vbox')
        vbox.pack_start(self.screen.widget)

        self.win.set_title(_('Preference'))
        self.win.show_all()

    def run(self, datas={}):
        lang = rpc.session.context.get('lang', 'en_US')
        res = self.win.run()
        if res==gtk.RESPONSE_OK:
            rpc.session.rpc_exec_auth('/object', 'execute', 'res.users', 'write', [rpc.session.uid], self.screen.get())
            rpc.session.context_reload()
            new_lang = rpc.session.context.get('lang', 'en_US')
            if lang != new_lang:
                common.message(_("The default language of the interface has been modified, do not forget to restart " \
                                 "the client to have the interface in your language"),
                               _("Default language modified !"), parent=self.win)
        self.parent.present()
        self.win.destroy()
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

