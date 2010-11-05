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

import datetime
import logging
import locale
import os
import time
from dateutil.relativedelta import relativedelta

import rpc

if os.name == 'nt':
    import win32

def expr_eval(string, context=None):
    if context is None:
        context = {}
    context.update(
        uid = rpc.session.uid,
        current_date = time.strftime('%Y-%m-%d'),
        time = time,
        datetime = datetime,
        relativedelta = relativedelta,
    )
    if isinstance(string, basestring):
        string = string.strip()
        if not string:
            return {}
        # sometimes the server returns the active_id  as a string
        string = string.replace("'active_id'","active_id")
        try:
            temp = eval(string, context)
        except Exception, e:
            logging.getLogger('tools.expr_eval').exception(string)
            return {}
        return temp
    else:
        return string

def launch_browser(url):
    import webbrowser
    import sys
    if sys.platform == 'win32':
        webbrowser.open(url.decode('utf-8'))
    else:
        import os
        pid = os.fork()
        if not pid:
            pid = os.fork()
            if not pid:
                webbrowser.open(url)
            sys.exit(0)
        os.wait()

def node_attributes(node):
    attrs = dict(node.attrib)
    if attrs is None:
        return {}
    if 'digits' in attrs and isinstance(attrs['digits'],(str,unicode)):
        attrs['digits'] = eval(attrs['digits'])
    return attrs

#FIXME use spaces
def calc_condition(self,model,con):
    if model and (con[0] in model.mgroup.fields):
        val = model[con[0]].get(model)
        if con[1]=="=" or con[1]=="==":
            if val==con[2]:
                return True
        elif con[1]=="!=" or con[1]=="<>":
            if val!=con[2]:
                return True
        elif con[1]=="<":
            if val<con[2]:
                return True
        elif con[1]==">":
            if val>con[2]:
                return True
        elif con[1]=="<=":
            if val<=con[2]:
                return True
        elif con[1]==">=":
            if val>=con[2]:
                return True
        elif con[1].lower()=="in":
            for cond in con[2]:
                if val == cond:
                    return True
        elif con[1].lower()=="not in":
            for cond in con[2]:
                if val == cond:
                    return False
            return True
        return False

def call_log(fun):
    """Debug decorator
       TODO: Add optionnal execution time
    """
    def f(*args, **kwargs):
        log = logging.getLogger('call_log')
        log.info("call %s with %r, %r:" % (getattr(fun, '__name__', str(fun)), args, kwargs))
        try:
            r = fun(*args, **kwargs)
            log.info(repr(r))
            return r
        except Exception, ex:
            log.exception("Exception: %r" % (ex,))
            raise
    return f

def to_xml(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def human_size(sz):
    """
    Return the size in a human readable format
    """
    if not sz:
        return False
    units = ('bytes', 'Kb', 'Mb', 'Gb')
    s, i = float(sz), 0
    while s >= 1024 and i < len(units)-1:
        s = s / 1024
        i = i + 1
    return "%0.2f %s" % (s, units[i])

def ustr(value, from_encoding='utf-8'):
    """This method is similar to the builtin `str` method, except
    it will return Unicode string.

    @param value: the value to convert

    @rtype: unicode
    @return: unicode string
    """

    if isinstance(value, unicode):
        return value

    if hasattr(value, '__unicode__'):
        return unicode(value)

    if not isinstance(value, str):
        value = str(value)

    return unicode(value, from_encoding)

def locale_format(format, value):
    label_str = locale.format(format, value, True)
    if not locale.getpreferredencoding().lower().startswith('utf'):
        label_str = label_str.replace('\xa0', '\xc2\xa0')
    return label_str

def format_connection_string(login, _passwd, server, port, protocol, dbname):
#def format_connection_string(*args):
#    login, _passwd, server, port, protocol, dbname = args
    DEFAULT_PORT = {
        'http://': 8069,
        'https://': 8069,
        'socket://': 8070,
    }
    result = '%s%s@%s' % (protocol, login, server)
    if port and DEFAULT_PORT.get(protocol) != int(port):
        result += ':%s' % (port,)
    result += '/%s' % (dbname,)
    return result

def str2int(string, default=None):
    assert isinstance(string, basestring)
    try:
        integer = locale.atoi(string)
        return integer
    except:
        if default is not None:
            return default
    raise ValueError("%r does not represent a valid integer value" % (string,))


def str2float(string, default=None):
    assert isinstance(string, basestring)
    try:
        float = locale.atof(string)
        return float
    except:
        if default is not None:
            return default
    raise ValueError("%r does not represent a valid float value" % (string,))

def str2bool(string, default=None):
    """Convert a string representing a boolean into the corresponding boolean

         True  | False
       --------+---------
        'True' | 'False'
        '1'    | '0'
        'on'   | 'off'
        't'    | 'f'

    If string can't be converted and default value is not None, default value
    returned, else a ValueError is raised
    """
    assert isinstance(string, basestring)
    mapping = {
        True: "true t 1 on".split(),
        False: "false f 0 off".split(),
    }
    string = string.lower()
    for value in mapping:
        if string in mapping[value]:
            return value
    if default is not None:
        return default
    raise ValueError("%r does not represent a valid boolean value" % (string,))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
