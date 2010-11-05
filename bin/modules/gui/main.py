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

import time
import os
import gettext
import urlparse

import gobject
import gtk
from gtk import glade
from pango import parse_markup
import translate

import rpc

import service
import options
import common

from window import win_preference, win_extension
import tools
import re
import xmlrpclib
import base64

RESERVED_KEYWORDS=['absolute', 'action', 'all', 'alter', 'analyse', 'analyze', 'and', 'any', 'as', 'asc', 'authorization', 'between', 'binary', 'both',
            'case', 'cast', 'check', 'collate', 'column','constraint', 'create', 'cross', 'current_date', 'current_time', 'current_timestamp',
            'current_user','default', 'deferrable', 'desc', 'distinct', 'do', 'else', 'end', 'except', 'false', 'for', 'foreign', 'freeze',
            'from', 'full', 'grant', 'group', 'having', 'ilike', 'in', 'initially','inner', 'intersect', 'into', 'is', 'isnull', 'join', 'leading',
            'left', 'like', 'limit', 'localtime', 'localtimestamp', 'natural', 'new', 'not', 'notnull', 'null', 'off', 'offset', 'old',
             'on', 'only', 'or', 'order', 'outer', 'overlaps', 'placing', 'primary', 'references', 'right','select', 'session_user', 'similar',
             'some', 'sysid', 'table', 'then', 'to', 'trailing', 'true', 'union', 'unique', 'user', 'using', 'verbose', 'when', 'where']

def check_ssl():
    try:
        from OpenSSL import SSL
        import socket

        return hasattr(socket, 'ssl')
    except:
        return False

class StockButton(gtk.Button):
    def __init__(self, label, stock):
        gtk.Button.__init__(self, label)
        self.icon = gtk.Image()
        self.icon.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
        self.set_image(self.icon)

class DatabaseDialog(gtk.Dialog):
    def __init__(self, label, parent):
        gtk.Dialog.__init__(
            self, label, parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
             gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        )

        self.set_icon(common.OPENERP_ICON)
        self.set_default_response(gtk.RESPONSE_ACCEPT)
        self.set_response_sensitive(gtk.RESPONSE_ACCEPT, False)

        self.table = gtk.Table(3, 2, False)
        self.table.set_row_spacings(5)
        self.table.set_col_spacings(5)

        self.messageLabel = gtk.Label('<b>'+_('Could not connect to server !')+'</b>')
        self.messageLabel.set_use_markup(True)
        self.messageLabel.hide()

        lbl = gtk.Label(_("Server:"))
        lbl.set_alignment(1.0, 0.5)
        self.table.attach(lbl, 0, 1, 0, 1)
        hbox = gtk.HBox(spacing=5)
        self.serverEntry = gtk.Entry()
        self.serverEntry.connect('changed', self.on_server_entry_changed, self.messageLabel)
        self.serverEntry.set_text(self.default_server_url())
        self.serverEntry.set_sensitive(False)

        hbox.pack_start(self.serverEntry, False, False)

        but_server = StockButton(_("Change"), gtk.STOCK_NETWORK)
        but_server.connect_after('clicked', lambda *a: _server_ask(self.serverEntry, parent))
        hbox.pack_start(but_server, False, False)
        self.table.attach(hbox, 1, 2, 0, 1)

        self.table.attach(self.messageLabel, 0, 2, 1, 2)

        lbl = gtk.Label(_("Super Administrator Password:"))
        lbl.set_alignment(1.0, 0.5)
        self.table.attach(lbl, 0, 1, 2, 3)
        self.adminPwdEntry = gtk.Entry()
        self.adminPwdEntry.set_visibility(False)
        self.table.attach(self.adminPwdEntry, 1, 2, 2, 3)

        self.vbox.add(self.table)

    def run(self):
        self.show_all()
        self.messageLabel.hide()
        res = super(DatabaseDialog, self).run()

        if res == gtk.RESPONSE_ACCEPT:
            self.run_thread()

        self.destroy()

    def on_server_entry_changed(self, entry, message):
        try:
            rpc.session.about(entry.get_text())
            self.clear_screen()
            self.on_server_entry_changed_after(entry)
            self.set_response_sensitive(gtk.RESPONSE_ACCEPT, True)
        except Exception, ex:
            self.clear_screen()
            message.show()

    def default_server_url(self):
        return "%(protocol)s%(host)s:%(port)d" % {
            'protocol' : options.options['login.protocol'],
            'host' : options.options['login.server'],
            'port' : int(options.options['login.port']),
        }

    def run_thread(self):
        import thread
        self.result = None
        self.error = False
        self.exception = None

        def go():
            try:
                self.on_response_accept()
                self.result = True
            except Exception, e:
                self.result = True
                self.exception = e
            return True

        thread.start_new_thread(go, ())

        i = 0
        win = None
        pb = None
        while not self.result:
            time.sleep(0.1)
            i += 1

            if i > 10:
                if not win or not pb:
                    win = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
                    win.set_title(_('OpenERP Computing'))
                    win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
                    win.set_modal(True) 
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
                    win.set_transient_for(self)
                    win.show_all()
                pb.pulse()
                gtk.main_iteration()
        if win:
            win.destroy()
            gtk.main_iteration()

        if self.exception:
            import xmlrpclib
            import socket
            import tiny_socket
            from rpc import rpc_exception
            try:
                raise self.exception
            except socket.error, e:
                common.message(str(e), title=_('Connection refused !'), type=gtk.MESSAGE_ERROR)
            except (tiny_socket.Myexception, xmlrpclib.Fault), err:
                a = rpc_exception(err.faultCode, err.faultString)
                if a.type in ('warning', 'UserError'):
                    common.warning(a.data, a.message)
                elif a.type == 'AccessDenied':
                    common.warning('Bad Super Administrator Password', self.get_title())
                else:
                    common.error(_('Application Error'), err.faultCode, err.faultString, disconnected_mode=True)
            except Exception, e:
                import sys
                import traceback
                tb = sys.exc_info()
                tb_s = "".join(traceback.format_exception(*tb))
                common.error(_('Application Error'), str(e), tb_s, disconnected_mode=True)
        else:
            if hasattr(self, 'message') and self.message:
                common.message(self.message, self.get_title())

    def on_response_accept(self):
        pass

    def on_server_entry_changed_after(self, entry):
        pass

    def clear_screen(self):
        self.messageLabel.hide()

class RetrieveMigrationScriptDialog(DatabaseDialog):
    def __init__(self, parent):
        DatabaseDialog.__init__(self, _("Migration Scripts"), parent)
        self.table.resize(5, 2)

        lbl = gtk.Label(_("Contract ID:"))
        lbl.set_alignment(1.0, 0.5)
        self.table.attach(lbl, 0, 1, 3, 4)
        self.contractIdEntry = gtk.Entry()
        self.table.attach(self.contractIdEntry, 1, 2, 3, 4)

        lbl = gtk.Label(_("Contract Password:"))
        lbl.set_alignment(1.0, 0.5)
        self.table.attach(lbl, 0, 1, 4, 5)
        self.contractPwdEntry = gtk.Entry()
        self.contractPwdEntry.set_visibility(False)
        self.table.attach(self.contractPwdEntry, 1, 2, 4, 5)

    def on_response_accept(self):
        au = rpc.session.get_available_updates(
            self.serverEntry.get_text(),
            self.adminPwdEntry.get_text(),
            self.contractIdEntry.get_text(),
            self.contractPwdEntry.get_text(),
        )
        if not au:
            self.message = _("You already have the latest version")
            return

        au = ["%s: %s" % (k, v) for k, v in au.items()]
        au.sort()
        au.insert(0, _("The following updates are available:"))
        msg = "\n * ".join(au)
        if not common.sur(msg):
            return

        # The OpenERP server fetchs the migration scripts
        rpc.session.get_migration_scripts(
            self.serverEntry.get_text(),
            self.adminPwdEntry.get_text(),
            self.contractIdEntry.get_text(),
            self.contractPwdEntry.get_text(),
        )
        self.message = _("You can now migrate your databases.")

class MigrationDatabaseDialog(DatabaseDialog):
    def __init__(self, parent):
        self.model = gtk.ListStore(bool, str)
        DatabaseDialog.__init__(self, _("Migrate Database"), parent)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        treeview = gtk.TreeView(self.model)
        treeview.set_rules_hint(True)
        treeview.set_size_request(300, 380)

        # Add the boolean column (apply)
        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self._on_toggle_renderer__toggled, 0)
        col = gtk.TreeViewColumn("Apply", renderer, active=0)
        treeview.append_column(col)

        # Add the text column (database name)
        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn("Database", renderer, text=1)
        treeview.append_column(col)
        sw.add(treeview)
        self.table.attach(sw, 0, 2, 3, 4)

    def on_response_accept(self):
        databases = [ item[1] for item in self.model if bool(item[0]) ]
        if databases:
            rpc.session.migrate_databases(self.serverEntry.get_text(), 
                                          self.adminPwdEntry.get_text(), 
                                          databases)
            if len(databases) == 1:
                self.message = _("Your database has been upgraded.")
            else:
                self.message = _("Your databases have been upgraded.")
        else:
            self.message = "You have not selected a database"

    def _on_toggle_renderer__toggled(self, renderer, path, col_index):
        row = self.model[path]
        row[col_index] = not row[col_index]

    def clear_screen(self):
        super(MigrationDatabaseDialog, self).clear_screen()
        self.model.clear()

    def on_server_entry_changed_after(self, entry):
        self.clear_screen()
        try:
            result = rpc.session.list_db(entry.get_text())
        except:
            return
        if result:
            for db_num, db_name in enumerate(result):
                self.model.set( self.model.append(), 0, False, 1, db_name)

def _get_db_name_from_url(url):
    if not url:
        return ''
    url = url.split('://', 1)[1].rsplit(':', 1)[0]
    if '.' in url:
        import socket
        try:
            socket.inet_aton(url)
        except socket.error:
            return url.split('.', 1)[0]
    return ''

def _refresh_dblist(db_widget, entry_db, label, butconnect, url, dbtoload=None):
    if not dbtoload:
        dbtoload = options.options['login.db'] or ''
        if not dbtoload:
            dbtoload = _get_db_name_from_url(url)

    label.hide()

    liststore = db_widget.get_model()
    liststore.clear()
    try:
        result = rpc.session.list_db(url)
    except:
        label.set_label('<b>'+_('Could not connect to server !')+'</b>')
        db_widget.hide()
        entry_db.hide()
        label.show()
        if butconnect:
            butconnect.set_sensitive(False)
        return False

    if result is None:
        entry_db.show()
        entry_db.set_text(dbtoload)
        entry_db.grab_focus()
        db_widget.hide()
        if butconnect:
            butconnect.set_sensitive(True)
    else:
        entry_db.hide()

        if not result:
            label.set_label('<b>'+_('No database found, you must create one !')+'</b>')
            label.show()
            db_widget.hide()
            if butconnect:
                butconnect.set_sensitive(False)
        else:
            db_widget.show()
            index = 0
            for db_num, db_name in enumerate(result):
                liststore.append([db_name])
                if db_name == dbtoload:
                    index = db_num
            db_widget.set_active(index)
            if butconnect:
                butconnect.set_sensitive(True)

    lm = rpc.session.login_message(url)
    if lm:
        try:
            parse_markup(lm)
        except:
            pass
        else:
            label.set_label(lm)
            label.show()

    return True


def _refresh_langlist(lang_widget, url):
    liststore = lang_widget.get_model()
    liststore.clear()
    lang_list = rpc.session.db_exec_no_except(url, 'list_lang')
    lang_list.append( ('en_US','English') )
    for key,val in lang_list:
        liststore.insert(0, (val,key))
    lang = rpc.session.context.get('lang', options.options.get('client.lang', 'en_US'))
    lang_widget.set_active(0)
    for idx, item in enumerate(lang_widget.get_model()):
        if item[1] == lang:
            lang_widget.set_active(idx)
            break
    return lang_list

def _server_ask(server_widget, parent=None):
    result = False
    win_gl = glade.XML(common.terp_path("openerp.glade"),"win_server",gettext.textdomain())
    win = win_gl.get_widget('win_server')
    if not parent:
        parent = service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(common.OPENERP_ICON)
    win.show_all()
    win.set_default_response(gtk.RESPONSE_OK)
    host_widget = win_gl.get_widget('ent_host')
    port_widget = win_gl.get_widget('ent_port')
    protocol_widget = win_gl.get_widget('protocol')

    protocol = {
        'XML-RPC': 'http://',
        'NET-RPC (faster)': 'socket://',
    }

    if check_ssl():
        protocol['XML-RPC secure'] ='https://'

    listprotocol = gtk.ListStore(str)
    protocol_widget.set_model(listprotocol)

    m = re.match('^(http[s]?://|socket://)([\w.-]+):(\d{1,5})$', server_widget.get_text())
    if m:
        host_widget.set_text(m.group(2))
        port_widget.set_text(m.group(3))

    index = 0
    i = 0
    for p in protocol:
        listprotocol.append([p])
        if m and protocol[p] == m.group(1):
            index = i
        i += 1
    protocol_widget.set_active(index)

    res = win.run()
    if res == gtk.RESPONSE_OK:
        protocol = protocol[protocol_widget.get_active_text()]
        url = '%s%s:%s' % (protocol, host_widget.get_text(), port_widget.get_text())
        server_widget.set_text(url)
        result = url
    parent.present()
    win.destroy()
    return result


class db_login(object):
    def __init__(self):
        self.win_gl = glade.XML(common.terp_path("openerp.glade"),"win_login",gettext.textdomain())

    def refreshlist(self, widget, db_widget, entry_db, label, url, butconnect=False):

        def check_server_version(url):
            try:
                import release
                full_server_version = rpc.session.db_exec_no_except(url, 'server_version')
                server_version = full_server_version.split('.')
                client_version = release.version.split('.')
                return (server_version[:2] == client_version[:2], full_server_version, release.version)
            except:
                # the server doesn't understand the request. It's mean that it's an old version of the server
                return (False, _('Unknown'), release.version)

        if _refresh_dblist(db_widget, entry_db, label, butconnect, url):
            is_same_version, server_version, client_version = check_server_version(url)
            if not is_same_version:
                common.warning(_('The versions of the server (%s) and the client (%s) missmatch. The client may not work properly. Use it at your own risks.') % (server_version, client_version,))

    def refreshlist_ask(self,widget, server_widget, db_widget, entry_db, label, butconnect = False, url=False, parent=None):
        url = _server_ask(server_widget, parent) or url
        return self.refreshlist(widget, db_widget, entry_db, label, url, butconnect)

    def run(self, dbname=None, parent=None):
        uid = 0
        win = self.win_gl.get_widget('win_login')
        if not parent:
            parent = service.LocalService('gui.main').window
        win.set_transient_for(parent)
        win.set_icon(common.OPENERP_ICON)
        win.show_all()
        img = self.win_gl.get_widget('image_tinyerp')
        img.set_from_file(common.terp_path_pixmaps('openerp.png'))
        login = self.win_gl.get_widget('ent_login')
        passwd = self.win_gl.get_widget('ent_passwd')
        server_widget = self.win_gl.get_widget('ent_server')
        but_connect = self.win_gl.get_widget('button_connect')
        combo_db = self.win_gl.get_widget('combo_db')
        entry_db = self.win_gl.get_widget('ent_db')
        change_button = self.win_gl.get_widget('but_server')
        label = self.win_gl.get_widget('combo_label')
        label.hide()

        host = options.options['login.server']
        port = options.options['login.port']
        protocol = options.options['login.protocol']

        url = '%s%s:%s' % (protocol, host, port)
        server_widget.set_text(url)
        login.set_text(options.options['login.login'])

        # construct the list of available db and select the last one used
        liststore = gtk.ListStore(str)
        combo_db.set_model(liststore)
        cell = gtk.CellRendererText()
        combo_db.pack_start(cell, True)
        combo_db.add_attribute(cell, 'text', 0)

        res = self.refreshlist(None, combo_db, entry_db, label, url, but_connect)
        change_button.connect_after('clicked', self.refreshlist_ask, server_widget, combo_db, entry_db, label, but_connect, url, win)

        if dbname:
            iter = liststore.get_iter_root()
            while iter:
                if liststore.get_value(iter, 0)==dbname:
                    combo_db.set_active_iter(iter)
                    break
                iter = liststore.iter_next(iter)

        res = win.run()
        m = re.match('^(http[s]?://|socket://)([\w.\-]+):(\d{1,5})$', server_widget.get_text() or '')
        if m:
            if combo_db.flags() & gtk.VISIBLE:
                dbname = combo_db.get_active_text()
            else:
                dbname = entry_db.get_text()

            options.options['login.server'] = m.group(2)
            options.options['login.login'] = login.get_text()
            options.options['login.port'] = m.group(3)
            options.options['login.protocol'] = m.group(1)
            options.options['login.db'] = dbname
            result = (login.get_text(), passwd.get_text(), m.group(2), m.group(3), m.group(1), dbname)
        else:
            parent.present()
            win.destroy()
            raise Exception('QueryCanceled')
        if res <> gtk.RESPONSE_OK:
            parent.present()
            win.destroy()
            raise Exception('QueryCanceled')
        parent.present()
        win.destroy()
        return result

class db_create(object):
    def set_sensitive(self, sensitive):
        self.dialog.get_widget('button_db_ok').set_sensitive(False)
        return sensitive

    def server_change(self, widget=None, parent=None):
        url = _server_ask(self.server_widget)
        if self.lang_widget and url:
            _refresh_langlist(self.lang_widget, url)
        return url

    def __init__(self, sig_login, terp_main):
        self.dialog = glade.XML(common.terp_path("openerp.glade"), "win_createdb", gettext.textdomain())
        self.sig_login = sig_login
        self.terp_main = terp_main

    def entry_changed(self, *args):
        up1 = self.dialog.get_widget('ent_user_pass1').get_text()
        up2 = self.dialog.get_widget('ent_user_pass2').get_text()
        self.dialog.get_widget('button_db_ok').set_sensitive(bool(up1 and (up1==up2)))

    def run(self, parent=None):
        win = self.dialog.get_widget('win_createdb')
        self.dialog.signal_connect('on_ent_user_pass1_changed', self.entry_changed)
        self.dialog.signal_connect('on_ent_user_pass2_changed', self.entry_changed)
        win.set_default_response(gtk.RESPONSE_OK)
        if not parent:
            parent = service.LocalService('gui.main').window
        win.set_transient_for(parent)
        win.show_all()
        lang_dict = {}
        pass_widget = self.dialog.get_widget('ent_password_new')
        self.server_widget = self.dialog.get_widget('ent_server_new')
        change_button = self.dialog.get_widget('but_server_new')
        self.lang_widget = self.dialog.get_widget('db_create_combo')
        self.db_widget = self.dialog.get_widget('ent_db_new')
        demo_widget = self.dialog.get_widget('check_demo')
        demo_widget.set_active(True)

        change_button.connect_after('clicked', self.server_change, win)
        protocol = options.options['login.protocol']
        url = '%s%s:%s' % (protocol, options.options['login.server'], options.options['login.port'])

        self.server_widget.set_text(url)
        liststore = gtk.ListStore(str, str)
        self.lang_widget.set_model(liststore)
        try:
            _refresh_langlist(self.lang_widget, url)
        except:
            self.set_sensitive(False)

        while True:
            res = win.run()
            db_name = self.db_widget.get_text().lower()
            if (res==gtk.RESPONSE_OK) and (db_name in RESERVED_KEYWORDS):
                common.warning(_("Sorry,'" +db_name + "' cannot be the name of the database,it's a Reserved Keyword."), _('Bad database name !'), parent=parent)
                continue
            if (res==gtk.RESPONSE_OK) and ((not db_name) or (not re.match('^[a-zA-Z0-9][a-zA-Z0-9_]+$', db_name))):
                common.warning(_('The database name must contain only normal characters or "_".\nYou must avoid all accents, space or special characters.'), _('Bad database name !'), parent=parent)

            else:
                break
        demo_data = demo_widget.get_active()

        langidx = self.lang_widget.get_active_iter()
        langreal = langidx and self.lang_widget.get_model().get_value(langidx,1)
        passwd = pass_widget.get_text()
        user_pass = self.dialog.get_widget('ent_user_pass1').get_text()
        url = self.server_widget.get_text()
        m = re.match('^(http[s]?://|socket://)([\w.\-]+):(\d{1,5})$', url or '')
        if m:
            options.options['login.server'] = m.group(2)
            options.options['login.port'] = m.group(3)
            options.options['login.protocol'] = m.group(1)
            options.options['login.db'] = db_name
        parent.present()
        win.destroy()

        if res == gtk.RESPONSE_OK:
            try:
                id=rpc.session.db_exec(url, 'list')
                if db_name in id:
                    raise Exception('DbExist')
                id = rpc.session.db_exec(url, 'create', passwd, db_name, demo_data, langreal, user_pass)
                win = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
                win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
                win.set_title(_('OpenERP Database Installation'))
                vbox = gtk.VBox(False, 0)
                hbox = gtk.HBox(False, 13)
                hbox.set_border_width(10)
                img = gtk.Image()
                img.set_from_stock('gtk-dialog-info', gtk.ICON_SIZE_DIALOG)
                hbox.pack_start(img, expand=True, fill=False)
                vbox2 = gtk.VBox(False, 0)
                label = gtk.Label()
                label.set_markup(_('<b>Operation in progress</b>'))
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
                if not parent:
                    parent = service.LocalService('gui.main').window
                win.set_transient_for(parent)
                win.show_all()
                self.timer = gobject.timeout_add(1000, self.progress_timeout, pb, url, passwd, id, win, db_name, parent)
                self.terp_main.glade.get_widget('but_menu').set_sensitive(True)
                self.terp_main.glade.get_widget('user').set_sensitive(True)
                self.terp_main.glade.get_widget('form').set_sensitive(True)
                self.terp_main.glade.get_widget('plugins').set_sensitive(True)

            except Exception, e:
                if e.args == ('DbExist',):
                    common.warning(_("Could not create database."),_('Database already exists !'))
                elif (getattr(e,'faultCode',False)=='AccessDenied') or str(e)=='AccessDenied':
                    common.warning(_('Bad database administrator password !'), _("Could not create database."))
                else:
                    common.warning(_("Could not create database."),_('Error during database creation !'))

    def progress_timeout(self, pbar, url, passwd, id, win, dbname, parent=None):
        try:
            progress,users = rpc.session.db_exec_no_except(url, 'get_progress', passwd, id)
        except:
            win.destroy()
            common.warning(_("The server crashed during installation.\nWe suggest you to drop this database."),_("Error during database creation !"))
            return False

        pbar.pulse()
        if progress == 1.0:
            win.destroy()

            pwdlst = '\n'.join(map(lambda x: '    - %s: %s / %s' % (x['name'],x['login'],x['password']), users))
            dialog = glade.XML(common.terp_path("openerp.glade"), "dia_dbcreate_ok", gettext.textdomain())
            win = dialog.get_widget('dia_dbcreate_ok')
            if not parent:
                parent = service.LocalService('gui.main').window
            win.set_transient_for(parent)
            win.show_all()
            buffer = dialog.get_widget('dia_tv').get_buffer()

            buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
            iter_start = buffer.get_start_iter()
            buffer.insert(iter_start, _('The following users have been installed on your database:')+'\n\n'+ pwdlst + '\n\n'+_('You can now connect to the database as an administrator.'))
            res = win.run()
            parent.present()
            win.destroy()

            if res == gtk.RESPONSE_OK:
                m = re.match('^(http[s]?://|socket://)([\w.]+):(\d{1,5})$', url)
                ok = False
                for x in users:
                    if x['login']=='admin' and m:
                        res = [x['login'], x['password']]
                        res.append( m.group(2) )
                        res.append( m.group(3) )
                        res.append( m.group(1) )
                        res.append( dbname )
                        log_response = rpc.session.login(*res)
                        if log_response == 1:
                            options.options['login.login'] = x['login']
                            id = self.terp_main.sig_win_menu(quiet=False)
                            ok = True
                            break
                if not ok:
                    self.sig_login(dbname=dbname)
            return False
        return True

    def process(self):
        return False


class terp_main(service.Service):
    def __init__(self, name='gui.main', audience='gui.*'):
        service.Service.__init__(self, name, audience)
        self.exportMethod(self.win_add)

        self._handler_ok = True
        self.glade = glade.XML(common.terp_path("openerp.glade"),"win_main",gettext.textdomain())
        self.status_bar_main = self.glade.get_widget('hbox_status_main')
        self.status_bar_main.show()
        self.toolbar = self.glade.get_widget('main_toolbar')
        self.sb_requests = self.glade.get_widget('sb_requests')
        self.sb_username = self.glade.get_widget('sb_user_name')
        self.sb_servername = self.glade.get_widget('sb_user_server')
        id = self.sb_servername.get_context_id('message')
        self.sb_servername.push(id, _('Press Ctrl+O to login'))
        self.secure_img = self.glade.get_widget('secure_img')
        self.secure_img.hide()

        window = self.glade.get_widget('win_main')
        window.connect("destroy", self.sig_quit)
        window.connect("delete_event", self.sig_delete)
        self.window = window
        self.window.set_icon(common.OPENERP_ICON)

        self.notebook = gtk.Notebook()
        self.notebook.set_scrollable(True)
        self.sig_id = self.notebook.connect_after('switch-page', self._sig_page_changed)
        if gtk.pygtk_version >= (2, 10, 0):
            self.notebook.connect('page-reordered', self._sig_page_reordered)
        vbox = self.glade.get_widget('vbox_main')
        vbox.pack_start(self.notebook, expand=True, fill=True)

        self.shortcut_menu = self.glade.get_widget('shortcut')

        #
        # Default Notebook
        #

        self.notebook.show()
        self.pages = []
        self.current_page = 0
        self.last_page = 0

        callbacks_dict = {
            'on_login_activate': self.sig_login,
            'on_logout_activate': self.sig_logout,
            'on_win_next_activate': self.sig_win_next,
            'on_win_prev_activate': self.sig_win_prev,
            'on_plugin_execute_activate': self.sig_plugin_execute,
            'on_quit_activate': self.sig_close,
            'on_but_menu_clicked': self.sig_win_menu,
            'on_win_new_activate': self.sig_win_menu,
            'on_win_home_activate': self.sig_home_new,
            'on_win_close_activate': self.sig_win_close,
            'on_support_activate': common.support,
            'on_preference_activate': self.sig_user_preferences,
            'on_read_requests_activate': self.sig_request_open,
            'on_send_request_activate': self.sig_request_new,
            'on_request_wait_activate': self.sig_request_wait,
            'on_opt_save_activate': lambda x: options.options.save(),
            'on_menubar_icons_activate': lambda x: self.sig_menubar('icons'),
            'on_menubar_text_activate': lambda x: self.sig_menubar('text'),
            'on_menubar_both_activate': lambda x: self.sig_menubar('both'),
            'on_opt_form_tab_top_activate': lambda x: self.sig_form_tab('top'),
            'on_opt_form_tab_left_activate': lambda x: self.sig_form_tab('left'),
            'on_opt_form_tab_right_activate': lambda x: self.sig_form_tab('right'),
            'on_opt_form_tab_bottom_activate': lambda x: self.sig_form_tab('bottom'),
            'on_opt_form_tab_orientation_horizontal_activate': lambda x: self.sig_form_tab_orientation(0),
            'on_opt_form_tab_orientation_vertical_activate': lambda x: self.sig_form_tab_orientation(90),
            'on_help_index_activate': self.sig_help_index,
            'on_help_contextual_activate': self.sig_help_context,
            'on_help_licence_activate': self.sig_licence,
            'on_about_activate': self.sig_about,
            'on_shortcuts_activate' : self.sig_shortcuts,
            'on_db_new_activate': self.sig_db_new,
            'on_db_restore_activate': self.sig_db_restore,
            'on_db_backup_activate': self.sig_db_dump,
            'on_db_drop_activate': self.sig_db_drop,
            'on_admin_password_activate': self.sig_db_password,
            'on_extension_manager_activate': self.sig_extension_manager,
            'on_db_migrate_retrieve_script_activate': self.sig_db_migrate_retrieve_script,
            'on_db_migrate_activate' : self.sig_db_migrate,
        }

        self.glade.signal_autoconnect(callbacks_dict)

        self.buttons = {}
        for button in ('but_new', 'but_save', 'but_remove', 'but_search', 'but_previous', 'but_next', 'but_action', 'but_open', 'but_print', 'but_close', 'but_reload', 'but_switch','but_attach',
                       'radio_tree','radio_form','radio_graph','radio_calendar', 'radio_gantt'):
            self.glade.signal_connect('on_'+button+'_clicked', self._sig_child_call, button)
            self.buttons[button]=self.glade.get_widget(button)

        menus = {
            'form_del': 'but_remove',
            'form_new': 'but_new',
            'form_copy': 'but_copy',
            'form_reload': 'but_reload',
            'form_log': 'but_log',
            'form_open': 'but_open',
            'form_search': 'but_search',
            'form_previous': 'but_previous',
            'form_next': 'but_next',
            'form_save': 'but_save',
            'goto_id': 'but_goto_id',
            'form_print': 'but_print',
            'form_print_html': 'but_print_html',
            'form_save_as': 'but_save_as',
            'form_import': 'but_import',
            'form_filter': 'but_filter',
            'form_repeat': 'but_print_repeat'
        }
        for menu in menus:
            self.glade.signal_connect('on_'+menu+'_activate', self._sig_child_call, menus[menu])

        spool = service.LocalService('spool')
        spool.subscribe('gui.window', self.win_add)


        # we now create the icon for the attachment button when there are attachments
        self.__img_no_attachments = gtk.Image()
        pxbf = self.window.render_icon(self.buttons['but_attach'].get_stock_id(), self.toolbar.get_icon_size())
        self.__img_no_attachments.set_from_pixbuf(pxbf)
        self.__img_no_attachments.show()

        pxbf = pxbf.copy()
        w, h = pxbf.get_width(), pxbf.get_height()
        overlay = self.window.render_icon(gtk.STOCK_APPLY, gtk.ICON_SIZE_MENU)
        ow, oh = overlay.get_width(), overlay.get_height()
        overlay.composite(pxbf,
                        0, h - oh,
                        ow, oh,
                        0, h - oh,
                        1.0, 1.0,
                        gtk.gdk.INTERP_NEAREST,
                        255)

        self.__img_attachments = gtk.Image()
        self.__img_attachments.set_from_pixbuf(pxbf)
        self.__img_attachments.show()

        self.sb_set()

        settings = gtk.settings_get_default()
        settings.set_long_property('gtk-button-images', 1, 'OpenERP:gui.main')

        def fnc_menuitem(menuitem, opt_name):
            options.options[opt_name] = menuitem.get_active()
        dict = {
            'on_opt_print_preview_activate': (fnc_menuitem, 'printer.preview', 'opt_print_preview'),
            'on_opt_form_toolbar_activate': (fnc_menuitem, 'form.toolbar', 'opt_form_toolbar'),
        }
        self.glade.get_widget('menubar_'+(options.options['client.toolbar'] or 'both')).set_active(True)
        self.sig_menubar(options.options['client.toolbar'] or 'both')
        self.glade.get_widget('opt_form_tab_'+(options.options['client.form_tab'] or 'left')).set_active(True)
        self.sig_form_tab(options.options['client.form_tab'] or 'left')
        self.glade.get_widget('opt_form_tab_orientation_'+(str(options.options['client.form_tab_orientation']) or '0')).set_active(True)
        self.sig_form_tab_orientation(options.options['client.form_tab_orientation'] or 0)
        for signal in dict:
            self.glade.signal_connect(signal, dict[signal][0], dict[signal][1])
            self.glade.get_widget(dict[signal][2]).set_active(int(bool(options.options[dict[signal][1]])))

        # Adding a timer the check to requests
        gobject.timeout_add(15 * 60 * 1000, self.request_set)


    def shortcut_edit(self, widget, model='ir.ui.menu'):
        obj = service.LocalService('gui.window')
        domain = [('user_id', '=', rpc.session.uid), ('resource', '=', model)]
        obj.create(False, 'ir.ui.view_sc', res_id=None, domain=domain, view_type='form', mode='tree,form')

    def shortcut_set(self, sc=None):
        def _action_shortcut(widget, action):
            if action:
                ctx = rpc.session.context.copy()
                obj = service.LocalService('action.main')
                obj.exec_keyword('tree_but_open', {'model': 'ir.ui.menu', 'id': action[0],
                    'ids': [action[0]], 'report_type': 'pdf', 'window': self.window}, context=ctx)

        if sc is None:
            uid = rpc.session.uid
            sc = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.ui.view_sc', 'get_sc', uid, 'ir.ui.menu', rpc.session.context) or []

        menu = gtk.Menu()
        for s in sc:
            menuitem = gtk.MenuItem(s['name'])
            menuitem.connect('activate', _action_shortcut, s['res_id'])
            menu.add(menuitem)

        menu.add(gtk.SeparatorMenuItem())
        menuitem = gtk.MenuItem(_('Edit'))
        menuitem.connect('activate', self.shortcut_edit)
        menu.add(menuitem)

        menu.show_all()
        self.shortcut_menu.set_submenu(menu)
        self.shortcut_menu.set_sensitive(True)

    def shortcut_unset(self):
        menu = gtk.Menu()
        menu.show_all()
        self.shortcut_menu.set_submenu(menu)
        self.shortcut_menu.set_sensitive(False)

    def sig_menubar(self, option):
        options.options['client.toolbar'] = option
        if option=='both':
            self.toolbar.set_style(gtk.TOOLBAR_BOTH)
        elif option=='text':
            self.toolbar.set_style(gtk.TOOLBAR_TEXT)
        elif option=='icons':
            self.toolbar.set_style(gtk.TOOLBAR_ICONS)

    def sig_form_tab(self, option):
        options.options['client.form_tab'] = option

    def sig_form_tab_orientation(self, option):
        options.options['client.form_tab_orientation'] = option

    def sig_win_next(self, args):
        pn = self.notebook.get_current_page()
        if pn == len(self.pages)-1:
            pn = -1
        self.notebook.set_current_page(pn+1)

    def sig_win_prev(self, args):
        pn = self.notebook.get_current_page()
        self.notebook.set_current_page(pn-1)

    def sig_user_preferences(self, *args):
        win =win_preference.win_preference(parent=self.window)
        win.run()
        return True

    def sig_win_close(self, *args):
        page_num = None
        if len(args) >= 2:
            page_num = self.notebook.page_num(args[1])
        self._sig_child_call(args[0], 'but_close', page_num)

    def sig_request_new(self, args=None):
        obj = service.LocalService('gui.window')
        try:
            return obj.create(None, 'res.request', False,
                    [('act_from', '=', rpc.session.uid)], 'form',
                    mode='form,tree', window=self.window,
                    context={'active_test': False})
        except:
            return False

    def sig_request_open(self, args=None):
        ids,ids2 = self.request_set()
        obj = service.LocalService('gui.window')
        try:
            return obj.create(False, 'res.request', ids,
                    [('act_to', '=', rpc.session.uid), ('active', '=', True)],
                    'form', mode='tree,form', window=self.window,
                    context={'active_test': False})
        except:
            return False

    def sig_request_wait(self, args=None):
        ids,ids2 = self.request_set()
        obj = service.LocalService('gui.window')
        try:
            return obj.create(False, 'res.request', ids,
                    [('act_from', '=', rpc.session.uid),
                        ('state', '=', 'waiting'), ('active', '=', True)],
                    'form', mode='tree,form', window=self.window,
                    context={'active_test': False})
        except:
            return False

    def request_set(self):
        try:
            uid = rpc.session.uid
            ids,ids2 = rpc.session.rpc_exec_auth_try('/object', 'execute',
                    'res.request', 'request_get')
            if len(ids):
                message = _('%s request(s)') % len(ids)
            else:
                message = _('No request')
            if len(ids2):
                message += _(' - %s request(s) sended') % len(ids2)
            id = self.sb_requests.get_context_id('message')
            self.sb_requests.push(id, message)
            return (ids,ids2)
        except:
            return ([],[])

    def sig_login(self, widget=None, dbname=False):
        RES_OK = 1
        RES_BAD_PASSWORD = -2
        RES_CNX_ERROR = -1
        try:
            log_response = RES_BAD_PASSWORD
            res = None
            while log_response == RES_BAD_PASSWORD:
                try:
                    l = db_login()
                    res = l.run(dbname=dbname, parent=self.window)
                except Exception, e:
                    if e.args == ('QueryCanceled',):
                        return False
                    raise
                service.LocalService('gui.main').window.present()
                self.sig_logout(widget)
                log_response = rpc.session.login(*res)
                if log_response == RES_OK:
                    options.options.save()
                    id = self.sig_win_menu(quiet=False)
                    if id:
                        self.sig_home_new(quiet=True, except_id=id)
                    if res[4] == 'https://':
                        self.secure_img.show()
                    else:
                        self.secure_img.hide()
                    self.request_set()
                elif log_response == RES_CNX_ERROR:
                    common.message(_('Connection error !\nUnable to connect to the server !'))
                elif log_response == RES_BAD_PASSWORD:
                    common.message(_('Authentication error !\nBad Username or Password !'))
        except rpc.rpc_exception:
            rpc.session.logout()
            raise
        self.glade.get_widget('but_menu').set_sensitive(True)
        self.glade.get_widget('user').set_sensitive(True)
        self.glade.get_widget('form').set_sensitive(True)
        self.glade.get_widget('plugins').set_sensitive(True)
        return True

    def sig_logout(self, widget):
        res = True
        while res:
            wid = self._wid_get()
            if wid:
                if 'but_close' in wid.handlers:
                    res = wid.handlers['but_close']()
                if not res:
                    return False
                res = self._win_del()
            else:
                res = False
        id = self.sb_requests.get_context_id('message')
        self.sb_requests.push(id, '')
        id = self.sb_username.get_context_id('message')
        self.sb_username.push(id, _('Not logged !'))
        id = self.sb_servername.get_context_id('message')
        self.sb_servername.push(id, _('Press Ctrl+O to login'))
        self.secure_img.hide()
        self.shortcut_unset()
        self.glade.get_widget('but_menu').set_sensitive(False)
        self.glade.get_widget('user').set_sensitive(False)
        self.glade.get_widget('form').set_sensitive(False)
        self.glade.get_widget('plugins').set_sensitive(False)
        rpc.session.logout()
        return True

    def sig_help_index(self, widget):
        tools.launch_browser(options.options['help.index'])

    def sig_help_context(self, widget):
        model = self._wid_get().model
        l = rpc.session.context.get('lang','en_US')
        getvar = {
            'model': model,
            'lang': l,
        }
        tools.launch_browser(options.options['help.context'] % getvar)

    def sig_licence(self, widget):
        dialog = glade.XML(common.terp_path("openerp.glade"), "win_licence", gettext.textdomain())
        dialog.signal_connect("on_but_ok_pressed", lambda obj: dialog.get_widget('win_licence').destroy())

        win = dialog.get_widget('win_licence')
        win.set_transient_for(self.window)
        win.show_all()

    def sig_about(self, widget):
        about = glade.XML(common.terp_path("openerp.glade"), "win_about", gettext.textdomain())
        buffer = about.get_widget('textview2').get_buffer()
        about_txt = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        buffer.set_text(about_txt % openerp_version)
        about.signal_connect("on_but_ok_pressed", lambda obj: about.get_widget('win_about').destroy())

        win = about.get_widget('win_about')
        win.set_transient_for(self.window)
        win.show_all()

    def sig_shortcuts(self, widget):
        shortcuts_win = glade.XML(common.terp_path('openerp.glade'), 'shortcuts_dia', gettext.textdomain())
        shortcuts_win.signal_connect("on_but_ok_pressed", lambda obj: shortcuts_win.get_widget('shortcuts_dia').destroy())

        win = shortcuts_win.get_widget('shortcuts_dia')
        win.set_transient_for(self.window)
        win.show_all()

    def sig_win_menu(self, widget=None, quiet=True):
        for p in range(len(self.pages)):
            if self.pages[p].model=='ir.ui.menu':
                self.notebook.set_current_page(p)
                return True
        res = self.sig_win_new(widget, type='menu_id', quiet=quiet)
        if not res:
            return self.sig_win_new(widget, type='action_id', quiet=quiet)
        return res

    def sig_win_new(self, widget=None, type='menu_id', quiet=True, except_id=False):
        try:
            act_id = rpc.session.rpc_exec_auth('/object', 'execute', 'res.users',
                    'read', [rpc.session.uid], [type,'name'], rpc.session.context)
        except:
            return False
        id = self.sb_username.get_context_id('message')
        self.sb_username.push(id, act_id[0]['name'] or '')
        id = self.sb_servername.get_context_id('message')
        data = urlparse.urlsplit(rpc.session._url)
        self.sb_servername.push(id, data[0]+':'+(data[1] and '//'+data[1] \
                or data[2])+' ['+options.options['login.db']+']')
        if not act_id[0][type]:
            if quiet:
                return False
            common.warning(_("You can not log into the system !\nAsk the administrator to verify\nyou have an action defined for your user."),'Access Denied !')
            rpc.session.logout()
            return False
        act_id = act_id[0][type][0]
        if except_id and act_id == except_id:
            return act_id
        obj = service.LocalService('action.main')
        win = obj.execute(act_id, {'window':self.window})
        try:
            user = rpc.session.rpc_exec_auth_wo('/object', 'execute', 'res.users',
                    'read', [rpc.session.uid], [type,'name'], rpc.session.context)
            if user[0][type]:
                act_id = user[0][type][0]
        except:
            pass
        return act_id

    def sig_home_new(self, widget=None, quiet=True, except_id=False):
        return self.sig_win_new(widget, type='action_id', quiet=quiet,
                except_id=except_id)

    def sig_plugin_execute(self, widget):
        import plugins
        pn = self.notebook.get_current_page()
        datas = {'model': self.pages[pn].model, 'ids':self.pages[pn].ids_get(), 'id' : self.pages[pn].id_get()}
        plugins.execute(datas)

    def sig_quit(self, widget):
        options.options.save()
        gtk.main_quit()

    def sig_close(self, widget):
        if common.sur(_("Do you really want to quit ?"), parent=self.window):
            if not self.sig_logout(widget):
                return False
            options.options.save()
            gtk.main_quit()

    def sig_delete(self, widget, event, data=None):
        if common.sur(_("Do you really want to quit ?"), parent=self.window):
            if not self.sig_logout(widget):
                return True
            return False
        return True

    def win_add(self, win, datas):
        self.pages.append(win)
        box = gtk.HBox(False, 0)

        # Draw the close button on the right 
        closebtn = gtk.Button()
        image = gtk.Image()
        image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        w, h = image.size_request()

        closebtn.set_image(image)
        closebtn.set_relief(gtk.RELIEF_NONE)
        closebtn.set_size_request(w + 8, h + 4)
        closebtn.unset_flags(gtk.CAN_FOCUS)

        box.pack_start(gtk.Label(win.name), True, True)
        box.pack_end(closebtn, False, False)

        self.notebook.append_page(win.widget, box)
        if hasattr(self.notebook, 'set_tab_reorderable' ):
            # since pygtk 2.10
            self.notebook.set_tab_reorderable(win.widget, True)

        closebtn.connect("clicked", self.sig_win_close,win.widget)
        pagenum = self.notebook.page_num(win.widget)
        pagenum = self.notebook.page_num(image)

        box.show_all()

        self.notebook.set_tab_label_packing(image, True, True, gtk.PACK_START)
        self.notebook.set_tab_label(image, box)
        image.show_all()
        self.notebook.set_current_page(-1)

    def message(self, message):
        id = self.status_bar.get_context_id('message')
        self.status_bar.push(id, message)

    def __attachment_callback(self, view, objid):
        current_view = self._wid_get()
        current_id = current_view and current_view.id_get()
        if current_view == view and objid == current_id:
            cpt = None
            if objid and view.screen.current_view.view_type == 'form':
                cpt = rpc.session.rpc_exec_auth('/object', 'execute',
                                                'ir.attachment', 'search_count',
                                                [('res_model', '=', view.model), ('res_id', '=', objid)])
            if cpt:
                self.buttons['but_attach'].set_icon_widget(self.__img_attachments)
                self.buttons['but_attach'].set_label(_('Attachments (%d)') % cpt)


    def _update_attachment_button(self, view = None):
        """
        Update the attachment icon for display the number of attachments
        """
        if not view:
            view = self._wid_get()

        id = view and view.id_get()
        gobject.timeout_add(1500, self.__attachment_callback, view, id)
        self.buttons['but_attach'].set_icon_widget(self.__img_no_attachments)
        self.buttons['but_attach'].set_label(_('Attachments'))


    def sb_set(self, view=None):
        if not view:
            view = self._wid_get()
        if view and hasattr(view, 'screen'):
            self._handler_ok = False
            self.glade.get_widget('radio_'+view.screen.current_view.view_type).set_active(True)
            self._handler_ok = True
        self._update_attachment_button(view)
        for x in self.buttons:
            if self.buttons[x]:
                self.buttons[x].set_sensitive(view and (x in view.handlers))

    def _win_del(self,page_num=None):
        if page_num is not None:
            pn = page_num
        else:
            pn = self.notebook.get_current_page()
        if pn != -1:
            self.notebook.disconnect(self.sig_id)
            page = self.pages.pop(pn)
            self.notebook.remove_page(pn)
            self.sig_id = self.notebook.connect_after('switch-page', self._sig_page_changed)
            self.sb_set()

            #page.destroy()
            #del page
        return self.notebook.get_current_page() != -1

    def _wid_get(self,page_num=None):
        if page_num is not None:
            pn = page_num
        else:
            pn = self.notebook.get_current_page()
        if pn == -1:
            return False
        return self.pages[pn]

    def _sig_child_call(self, widget, button_name, *args):
        page_num = None
        if len(args):
            page_num = args[0]
        if not self._handler_ok:
            return
        wid = self._wid_get(page_num)
        if wid:
            res = True
            if button_name.startswith('radio_'):
                act = self.glade.get_widget(button_name).get_active()
                if not act: return False

            if button_name in wid.handlers:
                res = wid.handlers[button_name]()
                # for those buttons, we refresh the attachment button.
                # for the "switch view" button, the action has already
                # been called by the Screen object of the view (wid)
                if button_name in ('but_new', 'but_remove', 'but_search', \
                                    'but_previous', 'but_next', 'but_open', \
                                    'but_close', 'but_reload', 'but_attach', 'but_goto_id'):
                    self._update_attachment_button(wid)
            if button_name=='but_close' and res:
                self._win_del(page_num)

    def _sig_page_changed(self, widget=None, *args):
        self.last_page = self.current_page
        self.current_page = self.notebook.get_current_page()
        self.sb_set()

    def _sig_page_reordered(self, notebook, child, page_num, user_param=None):
        widget = self.pages[self.current_page]
        self.pages.remove(widget)
        self.pages.insert(page_num, widget)
        self.current_page = page_num

    def sig_db_new(self, widget):
        if not self.sig_logout(widget):
            return False
        dia = db_create(self.sig_login, self)
        res = dia.run(self.window)
        if res:
            options.options.save()
        return res

    def sig_db_drop(self, widget):
        if not self.sig_logout(widget):
            return False
        url, db_name, passwd = self._choose_db_select(_('Delete a database'))
        if not db_name:
            return

        try:
            rpc.session.db_exec(url, 'drop', passwd, db_name)
            common.message(_("Database dropped successfully !"), parent=self.window)
        except Exception, e:
            if (getattr(e,'faultCode',False)=='AccessDenied') or str(e)=='AccessDenied':
                common.warning(_('Bad database administrator password !'),_("Could not drop database."), parent=self.window)
            else:
                common.warning(_("Couldn't drop database"), parent=self.window)

    def sig_db_restore(self, widget):
        filename = common.file_selection(_('Open...'), parent=self.window, preview=False)
        if not filename:
            return

        url, db_name, passwd = self._choose_db_ent()
        if db_name:
            try:
                f = file(filename, 'rb')
                data_b64 = base64.encodestring(f.read())
                f.close()
                res = rpc.session.db_exec(url, 'restore', passwd, db_name, data_b64)
                if res:
                    common.message(_("Database restored successfully !"), parent=self.window)
            except Exception,e:
                if (getattr(e,'faultCode',False)=='AccessDenied') or str(e)=='AccessDenied':
                    common.warning(_('Bad database administrator password !'),_("Could not restore database."), parent=self.window)
                else:
                    common.warning(_("Couldn't restore database"), parent=self.window)

    def sig_db_migrate_retrieve_script(self, widget):
        RetrieveMigrationScriptDialog(self.window).run()

    def sig_db_migrate(self, widget):
        MigrationDatabaseDialog(self.window).run()

    def sig_extension_manager(self,widget):
        win = win_extension.win_extension(self.window)
        win.run()

    def sig_db_password(self, widget):
        dialog = glade.XML(common.terp_path("openerp.glade"), "dia_passwd_change",
                gettext.textdomain())
        win = dialog.get_widget('dia_passwd_change')
        win.set_icon(common.OPENERP_ICON)
        win.set_transient_for(self.window)
        win.show_all()
        server_widget = dialog.get_widget('ent_server2')
        old_pass_widget = dialog.get_widget('old_passwd')
        new_pass_widget = dialog.get_widget('new_passwd')
        new_pass2_widget = dialog.get_widget('new_passwd2')
        change_button = dialog.get_widget('but_server_change1')
        change_button.connect_after('clicked', lambda a,b: _server_ask(b, win), server_widget)

        host = options.options['login.server']
        port = options.options['login.port']
        protocol = options.options['login.protocol']
        url = '%s%s:%s' % (protocol, host, port)
        server_widget.set_text(url)

        res = win.run()
        if res == gtk.RESPONSE_OK:
            url = server_widget.get_text()
            old_passwd = old_pass_widget.get_text()
            new_passwd = new_pass_widget.get_text()
            new_passwd2 = new_pass2_widget.get_text()
            if new_passwd != new_passwd2:
                common.warning(_("Confirmation password does not match " \
                        "new password, operation cancelled!"),
                        _("Validation Error."), parent=win)
            else:
                try:
                    rpc.session.db_exec(url, 'change_admin_password',
                            old_passwd, new_passwd)
                except Exception,e:
                    if ('faultCode' in dir(e) and e.faultCode=="AccessDenied") \
                            or str(e)=='AccessDenied':
                        common.warning(_("Could not change the Super Admin password."),
                                _('Bad password provided !'), parent=win)
                    else:
                        common.warning(_("Error, password not changed."),
                                parent=win)
        self.window.present()
        win.destroy()

    def sig_db_dump(self, widget):
        url, db_name, passwd = self._choose_db_select(_('Backup a database'))
        if not db_name:
            return
        filename = common.file_selection(_('Save As...'),
                action=gtk.FILE_CHOOSER_ACTION_SAVE, parent=self.window, preview=False)

        if filename:
            try:
                dump_b64 = rpc.session.db_exec(url, 'dump', passwd, db_name)
                dump = base64.decodestring(dump_b64)
                f = file(filename, 'wb')
                f.write(dump)
                f.close()
                common.message(_("Database backed up successfully !"), parent=self.window)
            except Exception,e:
                if getattr(e,'faultCode',False)=='AccessDenied':
                    common.warning(_('Bad database administrator password !'), _("Could not backup the database."),parent=self.window)
                else:
                    common.warning(_("Couldn't backup database."), parent=self.window)

    def _choose_db_select(self, title=_("Backup a database")):

        def refreshlist_ask(widget, server_widget, db_widget, entry_db, label, parent=None):
            url = _server_ask(server_widget, parent)
            if not url:
                return None
            _refresh_dblist(db_widget, entry_db, label, False, url)

        dialog = glade.XML(common.terp_path("openerp.glade"), "win_db_select",
                gettext.textdomain())
        win = dialog.get_widget('win_db_select')
        win.set_icon(common.OPENERP_ICON)
        win.set_default_response(gtk.RESPONSE_OK)
        win.set_transient_for(self.window)
        win.show_all()

        pass_widget = dialog.get_widget('ent_passwd_select')
        server_widget = dialog.get_widget('ent_server_select')
        db_widget = dialog.get_widget('combo_db_select')
        entry_db = dialog.get_widget('entry_db_select')
        label = dialog.get_widget('label_db_select')


        dialog.get_widget('db_select_label').set_markup('<b>'+title+'</b>')

        protocol = options.options['login.protocol']
        url = '%s%s:%s' % (protocol, options.options['login.server'], options.options['login.port'])
        server_widget.set_text(url)

        liststore = gtk.ListStore(str)
        db_widget.set_model(liststore)

        _refresh_dblist(db_widget, entry_db, label, False, url)
        change_button = dialog.get_widget('but_server_select')
        change_button.connect_after('clicked', refreshlist_ask, server_widget, db_widget, entry_db, label, win)

        cell = gtk.CellRendererText()
        db_widget.pack_start(cell, True)
        db_widget.add_attribute(cell, 'text', 0)

        res = win.run()

        db = False
        url = False
        passwd = False
        if res == gtk.RESPONSE_OK:
            db = db_widget.get_active_text()
            url = server_widget.get_text()
            passwd = pass_widget.get_text()
        self.window.present()
        win.destroy()
        return (url,db,passwd)

    def _choose_db_ent(self):
        dialog = glade.XML(common.terp_path("openerp.glade"), "win_db_ent",
                gettext.textdomain())
        win = dialog.get_widget('win_db_ent')
        win.set_icon(common.OPENERP_ICON)
        win.set_transient_for(self.window)
        win.show_all()

        db_widget = dialog.get_widget('ent_db')
        widget_pass = dialog.get_widget('ent_password')
        widget_url = dialog.get_widget('ent_server1')

        protocol = options.options['login.protocol']
        url = '%s%s:%s' % (protocol, options.options['login.server'],
                options.options['login.port'])
        widget_url.set_text(url)

        change_button = dialog.get_widget('but_server_change')
        change_button.connect_after('clicked', lambda a,b: _server_ask(b, win),
                widget_url)

        res = win.run()

        db = False
        passwd = False
        url = False
        if res == gtk.RESPONSE_OK:
            db = db_widget.get_text()
            url = widget_url.get_text()
            passwd = widget_pass.get_text()
        self.window.present()
        win.destroy()
        return url, db, passwd


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

