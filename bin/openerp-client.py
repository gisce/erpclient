#!/usr/bin/env python
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

"""
OpenERP - Client
OpenERP is an ERP+CRM program for small and medium businesses.

The whole source code is distributed under the terms of the
GNU Public Licence.

(c) 2003-TODAY, Fabien Pinckaers - Tiny sprl
"""
import sys
import os
import release
__author__ = release.author
__version__ = release.version

import __builtin__
__builtin__.__dict__['openerp_version'] = __version__

import logging
arguments = {}
if sys.platform == 'win32':
    arguments['filename'] = os.path.join(os.environ['USERPROFILE'], 'openerp-client.log')

logging.basicConfig(**arguments)

from distutils.sysconfig import get_python_lib
terp_path = os.path.join(get_python_lib(), 'openerp-client')
sys.path.append(terp_path)

if os.name == 'nt':
    sys.path.insert(0, os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'GTK\\bin'))
    sys.path.insert(0, os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'GTK\\lib'))
    os.environ['PATH'] = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'GTK\\lib') + ";" + os.environ['PATH']
    os.environ['PATH'] = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'GTK\\bin') + ";" + os.environ['PATH']

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade

#gtk.gdk.threads_init() # causes the GTK client to block everything.

import locale
import gettext

import atk
import gtk._gtk
import pango

if os.name == 'nt':
    sys.path.insert(0, os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])))
    os.environ['PATH'] = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0])) + ";" + os.environ['PATH']

import translate
translate.setlang()

import options

# On first run, client won't have a language option,
# so try with the LANG environ, or fallback to english
client_lang = options.options['client.lang']
if not client_lang:
    client_lang = os.environ.get('LANG', '').split('.')[0]

translate.setlang(client_lang)


# add new log levels below DEBUG
logging.DEBUG_RPC = logging.DEBUG - 1
logging.addLevelName(logging.DEBUG_RPC, 'DEBUG_RPC')
logging.Logger.debug_rpc = lambda self, msg, *args, **kwargs: self.log(logging.DEBUG_RPC, msg, *args, **kwargs)

logging.DEBUG_RPC_ANSWER = logging.DEBUG - 2
logging.addLevelName(logging.DEBUG_RPC_ANSWER, 'DEBUG_RPC_ANSWER')
logging.Logger.debug_rpc_answer = lambda self, msg, *args, **kwargs: self.log(logging.DEBUG_RPC_ANSWER, msg, *args, **kwargs)

logging.getLogger().setLevel(getattr(logging, options.options['logging.level'].upper()))



import modules
import common

items = [('terp-flag', '_Translation', gtk.gdk.CONTROL_MASK, ord('t'), '')]
gtk.stock_add (items)

factory = gtk.IconFactory ()
factory.add_default ()

pix_file = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'icons')
if not os.path.isdir(pix_file):
    pix_file = os.path.join(options.options['path.pixmaps'],'icons')

for fname in os.listdir(pix_file):
    ffname = os.path.join(pix_file,fname)
    if not os.path.isfile(ffname):
        continue
    iname = os.path.splitext(fname)[0]
    try:
        pixbuf = gtk.gdk.pixbuf_new_from_file(ffname)
    except:
        pixbuf = None
        continue
    if pixbuf:
        icon_set = gtk.IconSet (pixbuf)
        factory.add('terp-'+iname, icon_set)

try:
    win = modules.gui.main.terp_main()
    if options.options.rcexist:
        win.sig_login()
    if os.name == 'nt':
        from tools.win32 import get_systemfont_style
        gtk.rc_parse_string(get_systemfont_style())
    gtk.main()
except KeyboardInterrupt, e:
    log = logging.getLogger('common')
    log.info(_('Closing OpenERP, KeyboardInterrupt'))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

