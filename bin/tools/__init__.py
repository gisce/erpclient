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
if os.name == 'nt':
    import win32

def expr_eval(string, context={}):
    import rpc
    context['uid'] = rpc.session.uid
    context['current_date'] = time.strftime('%Y-%m-%d')
    context['time'] = time
    if isinstance(string, basestring):
#        return eval(string, context)
        try:
            string  =string.replace("'active_id'","active_id")
            temp = eval(string, context)
        except:
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
    result = {}
    attrs = node.attributes
    if attrs is None:
        return {}
    for i in range(attrs.length):
        result[attrs.item(i).localName] = str(attrs.item(i).nodeValue)
        if attrs.item(i).localName == "digits" and isinstance(attrs.item(i).nodeValue, (str, unicode)):
            result[attrs.item(i).localName] = eval(attrs.item(i).nodeValue)
    return result

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
        print "call %s with %r, %r:" % (getattr(fun, '__name__', str(fun)), args, kwargs),
        try:
            r = fun(*args, **kwargs)
            print repr(r)
            return r
        except Exception, ex:
            print "Exception: %r" % (ex,)
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
    import locale
    label_str = locale.format(format, value, True)
    if not locale.getpreferredencoding().lower().startswith('utf'):
        label_str = label_str.replace('\xa0', '\xc2\xa0')
    return label_str

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
