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
import xmlrpclib
import logging
import socket

import tiny_socket

import service
import common
import options
import os

import re
import pytz

CONCURRENCY_CHECK_FIELD = '__last_update'

class rpc_exception(Exception):
    def __init__(self, code, backtrace):

        self.code = code
        self.args = backtrace
        if hasattr(code, 'split'):
            lines = code.split('\n')

            self.type = lines[0].split(' -- ')[0]
            self.message = ''
            if len(lines[0].split(' -- ')) > 1:
                self.message = lines[0].split(' -- ')[1]

            self.data = '\n'.join(lines[2:])
        else:
            self.type = 'error'
            self.message = backtrace
            self.data = backtrace

        self.backtrace = backtrace

        log = logging.getLogger('rpc.exception')
        log.warning('CODE %s: %s' % (str(code), self.message))

class gw_inter(object):
    __slots__ = ('_url', '_db', '_uid', '_passwd', '_sock', '_obj')
    def __init__(self, url, db, uid, passwd, obj='/object'):
        self._url = url
        self._db = db
        self._uid = uid
        self._obj = obj
        self._passwd = passwd
    def exec_auth(method, *args):
        pass
    def execute(method, *args):
        pass

class xmlrpc_gw(gw_inter):
    __slots__ = ('_url', '_db', '_uid', '_passwd', '_sock', '_obj')
    def __init__(self, url, db, uid, passwd, obj='/object'):
        gw_inter.__init__(self, url, db, uid, passwd, obj)
        self._sock = xmlrpclib.ServerProxy(url+obj)
    def exec_auth(self, method, *args):
        logging.getLogger('rpc.request').debug_rpc(str((method, self._db, self._uid, self._passwd, args)))
        res = self.execute(method, self._uid, self._passwd, *args)
        logging.getLogger('rpc.result').debug_rpc_answer(str(res))
        return res

    def __convert(self, result):
        if type(result)==type(u''):
            return result.encode('utf-8')
        elif type(result)==type([]):
            return map(self.__convert, result)
        elif type(result)==type({}):
            newres = {}
            for i in result.keys():
                newres[i] = self.__convert(result[i])
            return newres
        else:
            return result

    def execute(self, method, *args):
        result = getattr(self._sock,method)(self._db, *args)
        return self.__convert(result)

class tinySocket_gw(gw_inter):
    __slots__ = ('_url', '_db', '_uid', '_passwd', '_sock', '_obj')
    def __init__(self, url, db, uid, passwd, obj='/object'):
        gw_inter.__init__(self, url, db, uid, passwd, obj)
        self._sock = tiny_socket.mysocket()
        self._obj = obj[1:]
    def exec_auth(self, method, *args):
        logging.getLogger('rpc.request').debug_rpc(str((method, self._db, self._uid, self._passwd, args)))
        res = self.execute(method, self._uid, self._passwd, *args)
        logging.getLogger('rpc.result').debug_rpc_answer(str(res))
        return res
    def execute(self, method, *args):
        self._sock.connect(self._url)
        self._sock.mysend((self._obj, method, self._db)+args)
        res = self._sock.myreceive()
        self._sock.disconnect()
        return res

class rpc_session(object):
    __slots__ = ('_open', '_url', 'uid', 'uname', '_passwd', '_gw', 'db', 'context', 'timezone')
    def __init__(self):
        self._open = False
        self._url = None
        self._passwd = None
        self.uid = None
        self.context = {}
        self.uname = None
        self._gw = xmlrpc_gw
        self.db = None
        self.timezone = 'utc'

    def rpc_exec(self, obj, method, *args):
        try:
            sock = self._gw(self._url, self.db, self.uid, self._passwd, obj)
            return sock.execute(method, *args)
        except socket.error, e:
            common.message(str(e), title=_('Connection refused !'), type=gtk.MESSAGE_ERROR)
            raise rpc_exception(69, _('Connection refused!'))
        except xmlrpclib.Fault, err:
            raise rpc_exception(err.faultCode, err.faultString)

    def rpc_exec_auth_try(self, obj, method, *args):
        if self._open:
            sock = self._gw(self._url, self.db, self.uid, self._passwd, obj)
            return sock.exec_auth(method, *args)
        else:
            raise rpc_exception(1, 'not logged')

    def rpc_exec_auth_wo(self, obj, method, *args):
        try:
            sock = self._gw(self._url, self.db, self.uid, self._passwd, obj)
            return sock.exec_auth(method, *args)
        except xmlrpclib.Fault, err:
            a = rpc_exception(err.faultCode, err.faultString)
        except tiny_socket.Myexception, err:
            a = rpc_exception(err.faultCode, err.faultString)
        if a.code in ('warning', 'UserError'):
            common.warning(a.data, a.message)
            return None
        raise a

    def rpc_exec_auth(self, obj, method, *args):
        if self._open:
            try:
                sock = self._gw(self._url, self.db, self.uid, self._passwd, obj)
                return sock.exec_auth(method, *args)
            except socket.error, e:
                common.message(_('Unable to reach to OpenERP server !\nYou should check your connection to the network and the OpenERP server.'), _('Connection Error'), type=gtk.MESSAGE_ERROR)
                raise rpc_exception(69, 'Connection refused!')
            except Exception, e:
                if isinstance(e, xmlrpclib.Fault) \
                        or isinstance(e, tiny_socket.Myexception):
                    a = rpc_exception(e.faultCode, e.faultString)
                    if a.type in ('warning','UserError'):
                        if a.message in ('ConcurrencyException') and len(args) > 4:
                            if common.concurrency(args[0], args[2][0], args[4]):
                                if CONCURRENCY_CHECK_FIELD in args[4]:
                                    del args[4][CONCURRENCY_CHECK_FIELD]
                                return self.rpc_exec_auth(obj, method, *args)
                        else:
                            common.warning(a.data, a.message)
                    else:
                        common.error(_('Application Error'), e.faultCode, e.faultString)
                else:
                    common.error(_('Application Error'), _('View details'), str(e))
                #TODO Must propagate the exception?
                raise
        else:
            raise rpc_exception(1, 'not logged')

    def login(self, uname, passwd, url, port, protocol, db):
        _protocol = protocol
        if _protocol == 'http://' or _protocol == 'https://':
            _url = _protocol + url+':'+str(port)+'/xmlrpc'
            _sock = xmlrpclib.ServerProxy(_url+'/common')
            self._gw = xmlrpc_gw
            try:
                res = _sock.login(db or '', uname or '', passwd or '')
            except socket.error,e:
                return -1
            if not res:
                self._open=False
                self.uid=False
                return -2
        else:
            _url = _protocol+url+':'+str(port)
            _sock = tiny_socket.mysocket()
            self._gw = tinySocket_gw
            try:
                _sock.connect(url, int(port))
                _sock.mysend(('common', 'login', db or '', uname or '', passwd or ''))
                res = _sock.myreceive()
                _sock.disconnect()
            except socket.error,e:
                return -1
            if not res:
                self._open=False
                self.uid=False
                return -2
        self._url = _url
        self._open = True
        self.uid = res
        self.uname = uname
        self._passwd = passwd
        self.db = db

        #CHECKME: is this useful? maybe it's used to see if there is no
        # exception raised?
        sock = self._gw(self._url, self.db, self.uid, self._passwd)
        self.context_reload()
        return 1

    def migrate_databases(self, url, password, databases):
        return self.exec_no_except(url, 'db', 'migrate_databases', password, databases)

    def get_available_updates(self, url, password, contract_id, contract_password):
        return self.exec_no_except(url, 'common', 'get_available_updates', password, contract_id, contract_password)

    def get_migration_scripts(self, url, password, contract_id, contract_password):
        return self.exec_no_except(url, 'common', 'get_migration_scripts', password, contract_id, contract_password)

    def about(self, url):
        return self.exec_no_except(url, 'common', 'about')

    def login_message(self, url):
        try:
            return self.exec_no_except(url, 'common', 'login_message')
        except:
            return False

    def list_db(self, url):
        try:
            return self.db_exec_no_except(url, 'list')
        except (xmlrpclib.Fault, tiny_socket.Myexception), e:
            if e.faultCode == 'AccessDenied':
                return None
            raise

    def db_exec_no_except(self, url, method, *args):
        return self.exec_no_except(url, 'db', method, *args)

    def exec_no_except(self, url, resource, method, *args):
        m = re.match('^(http[s]?://|socket://)([\w.\-]+):(\d{1,5})$', url or '')
        if m.group(1) == 'http://' or m.group(1) == 'https://':
            sock = xmlrpclib.ServerProxy(url + '/xmlrpc/' + resource)
            return getattr(sock, method)(*args)
        else:
            sock = tiny_socket.mysocket()
            sock.connect(m.group(2), int(m.group(3)))
            sock.mysend((resource, method)+args)
            res = sock.myreceive()
            sock.disconnect()
            return res

    def db_exec(self, url, method, *args):
        res = False
        try:
            res = self.db_exec_no_except(url, method, *args)
        except socket.error, msg:
            common.warning('Could not contact server!')
        return res

    def context_reload(self):
        self.context = {}
        self.timezone = 'utc'
        self.context = self.rpc_exec_auth('/object', 'execute', 'res.users', 'context_get') or {}
        if 'lang' in self.context:
            import translate
            translate.setlang(self.context['lang'])
            options.options['client.lang']=self.context['lang']
            ids = self.rpc_exec_auth('/object', 'execute', 'res.lang', 'search', [('code', '=', self.context['lang'])])
            if ids:
                l = self.rpc_exec_auth('/object', 'execute', 'res.lang', 'read', ids, ['direction'])
                if l and 'direction' in l[0]:
                    common.DIRECTION = l[0]['direction']
                    import gtk
                    if common.DIRECTION == 'rtl':
                        gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)
                    else:
                        gtk.widget_set_default_direction(gtk.TEXT_DIR_LTR)
        if self.context.get('tz'):
            # FIXME: Timezone handling
            #   rpc_session.timezone contains the server's idea of its timezone (from time.tzname[0]),
            #   which is quite quite unreliable in some cases. We'll fix this in trunk.
            self.timezone = self.rpc_exec_auth('/common', 'timezone_get')
            try:
                pytz.timezone(self.timezone)
            except pytz.UnknownTimeZoneError:
                # Server timezone is not recognized!
                # Time values will be displayed as if located in the server timezone. (nothing we can do)
                pass

    def logged(self):
        return self._open

    def logout(self):
        if self._open :
            self._open = False
            self.uname = None
            self.uid = None
            self._passwd = None

session = rpc_session()


class RPCProxy(object):

    def __init__(self, resource):
        self.resource = resource
        self.__attrs = {}

    def __getattr__(self, name):
        if not name in self.__attrs:
            self.__attrs[name] = RPCFunction(self.resource, name)
        return self.__attrs[name]


class RPCFunction(object):

    def __init__(self, object, func_name):
        self.object = object
        self.func = func_name

    def __call__(self, *args):
        return session.rpc_exec_auth('/object', 'execute', self.object, self.func, *args)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

