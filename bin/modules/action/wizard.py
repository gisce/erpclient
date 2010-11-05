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
import copy

import service
import rpc
import common
import thread
import time

from widget.screen import Screen


class dialog(object):
    def __init__(self, arch, fields, state, name, parent=None):
        buttons = []
        self.states=[]
        default=-1
        if not parent:
            parent = service.LocalService('gui.main').window
        self.dia = gtk.Dialog('OpenERP', parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        for x in state:
            but = gtk.Button(x[1])
            but.show()
            if len(x) >= 3:
                icon = gtk.Image()
                icon.set_from_stock(x[2], gtk.ICON_SIZE_BUTTON)
                but.set_image(icon)
            self.dia.add_action_widget(but, len(self.states))
            if len(x) >= 4 and x[3]:
                but.set_flags(gtk.CAN_DEFAULT)
                default = len(self.states)
            self.states.append(x[0])
        if default >= 0:
            self.dia.set_default_response(default)

        val = {}
        for f in fields:
            if 'value' in fields[f]:
                val[f] = fields[f]['value']

        self.screen = Screen('wizard.'+name, view_type=[], window=self.dia, is_wizard=True)
        self.screen.new(default=False)
        self.screen.add_view_custom(arch, fields, display=True)
        self.screen.current_model.set(val)

        x,y = self.screen.screen_container.size_get()
        width, height = parent.get_size()
        self.screen.widget.set_size_request(min(width - 20, x + 20),
                min(height - 60, y + 25))
        self.screen.widget.show()

        self.dia.vbox.pack_start(self.screen.widget)
        self.dia.set_title(self.screen.current_view.title)
        self.dia.show()

    def run(self, datas={}):
        while True:
            res = self.dia.run()
            self.screen.current_view.set_value()
            if self.screen.current_model.validate() or (res<0) or (self.states[res]=='end'):
                break
            self.screen.display()
        if res<len(self.states) and res>=0:
            datas.update(self.screen.get())
            self.dia.destroy()
            return (self.states[res], datas)
        else:
            self.dia.destroy()
            return False

def execute(action, datas, state='init', parent=None, context=None):
    if context is None:
        context = {}
    if not 'form' in datas:
        datas['form'] = {}
    wiz_id = rpc.session.rpc_exec_auth('/wizard', 'create', action)

    while state!='end':
        class wizard_progress(object):
            def __init__(self, parent=None):
                self.res = None
                self.error = False
                self.parent = parent
                self.exception = None

            def run(self):
                def go(wiz_id, datas, state):
                    ctx = context.copy()
                    ctx.update(rpc.session.context)
                    try:
                        self.res = rpc.session.rpc_exec_auth_try('/wizard', 'execute', wiz_id, datas, state, ctx)
                    except Exception, e:
                        self.error = True
                        self.res = False
                        self.exception = e
                        return True
                    if not self.res:
                        self.error = True
                    return True

                thread.start_new_thread(go, (wiz_id, datas, state))

                i = 0
                win = None
                pb = None
                while (not self.res) and (not self.error):
                    time.sleep(0.1)
                    i += 1
                    if i > 10:
                        if not win or not pb:
                            win = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
                            win.set_title(_('OpenERP Computing'))
                            win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
                            vbox = gtk.VBox(False, 0)
                            hbox = gtk.HBox(False, 13)
                            hbox.set_border_width(10)
                            img = gtk.Image()
                            img.set_from_stock('gtk-dialog-info', gtk.ICON_SIZE_DIALOG)
                            hbox.pack_start(img, expand=True, fill=False)
                            vbox2 = gtk.VBox(False, 0)
                            label = gtk.Label()
                            label.set_markup('<b>'+_('Operation in progress')+'</b>')
                            label.set_alignment(0.0, 0.5)
                            vbox2.pack_start(label, expand=True, fill=False)
                            vbox2.pack_start(gtk.HSeparator(), expand=True, fill=True)
                            vbox2.pack_start(gtk.Label(_("Please wait,\nthis operation may take a while...")), expand=True, fill=False)
                            hbox.pack_start(vbox2, expand=True, fill=True)
                            vbox.pack_start(hbox)
                            pb = gtk.ProgressBar()
                            pb.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
                            vbox.pack_start(pb, expand=True, fill=False)
                            win.add(vbox)
                            if not self.parent:
                                self.parent = service.LocalService('gui.main').window
                            win.set_transient_for(self.parent)
                            win.show_all()
                        pb.pulse()
                        gtk.main_iteration()
                if win:
                    win.destroy()
                    gtk.main_iteration()
                if self.exception:
                    import xmlrpclib
                    import socket
                    from rpc import rpc_exception, CONCURRENCY_CHECK_FIELD
                    import tiny_socket
                    try:
                        raise self.exception
                    except socket.error, e:
                        common.message(str(e), title=_('Connection refused !'), type=gtk.MESSAGE_ERROR)
                    except xmlrpclib.Fault, err:
                        a = rpc_exception(err.faultCode, err.faultString)
                        if a.type in ('warning', 'UserError'):
                            if a.message in ('ConcurrencyException') and len(args) > 4:
                                if common.concurrency(args[0], args[2][0], args[4]):
                                    if CONCURRENCY_CHECK_FIELD in args[4]:
                                        del args[4][CONCURRENCY_CHECK_FIELD]
                                    return self.rpc_exec_auth(obj, method, *args)
                            else:
                                common.warning(a.data, a.message)
                        else:
                            common.error(_('Application Error'), err.faultCode, err.faultString)
                    except tiny_socket.Myexception, err:
                        a = rpc_exception(err.faultCode, err.faultString)
                        if a.type in ('warning', 'UserError'):
                            common.warning(a.data, a.message)
                        else:
                            common.error(_('Application Error'), err.faultCode, err.faultString)
                    except Exception, e:
                        common.error(_('Application Error'), _('View details'), str(e))
                return self.res

        wp = wizard_progress(parent)
        res = wp.run()
        if not res:
            return False

        if 'datas' in res:
            datas['form'].update( res['datas'] )
        if res['type']=='form':
            dia = dialog(res['arch'], res['fields'], res['state'], action, parent)
            dia.screen.current_model.set( datas['form'] )
            res = dia.run(datas['form'])
            if not res:
                break
            (state, new_data) = res
            for d in new_data:
                if new_data[d]==None:
                    del new_data[d]
            datas['form'].update(new_data)
            del new_data
        elif res['type']=='action':
            obj = service.LocalService('action.main')
            obj._exec_action(res['action'],datas)
            state = res['state']
        elif res['type']=='print':
            obj = service.LocalService('action.main')
            datas['report_id'] = res.get('report_id', False)
            if res.get('get_id_from_action', False):
                backup_ids = datas['ids']
                datas['ids'] = datas['form']['ids']
                win = obj.exec_report(res['report'], datas)
                datas['ids'] = backup_ids
            else:
                win = obj.exec_report(res['report'], datas)
            state = res['state']
        elif res['type']=='state':
            state = res['state']
        #common.error('Wizard Error:'+ str(e.type), e.message, e.data)
        #state = 'end'


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

