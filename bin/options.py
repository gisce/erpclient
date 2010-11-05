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

import ConfigParser
import optparse
import os
import sys
import gtk
import gettext
import release

def get_home_dir():
    """Return the closest possible equivalent to a 'home' directory.
    For Posix systems, this is $HOME, and on NT it's $HOMEDRIVE\$HOMEPATH.
    Currently only Posix and NT are implemented, a HomeDirError exception is
    raised for all other OSes. """

    if os.name == 'posix':
        return os.path.expanduser('~')
    elif os.name == 'nt':
        try:
            return os.path.join(os.environ['HOMEDRIVE'],os.environ['HOMEPATH'])
        except:
            try:
                import _winreg as wreg
                key = wreg.OpenKey(wreg.HKEY_CURRENT_USER, "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                homedir = wreg.QueryValueEx(key,'Personal')[0]
                key.Close()
                return homedir
            except:
                return 'C:\\'
    elif os.name == 'dos':
        return 'C:\\'
    else:
        return '.'

class configmanager(object):
    
    def __get_prefix(self):
        if self.__prefix is None:
            f = os.path.normpath(__file__)
            sitepackages_prefix = os.path.join('lib', 'python%s' % sys.version[:3], 'site-packages', release.name, os.path.basename(f))
            home_prefix = os.path.join('lib', 'python', release.name, os.path.basename(f))
            
            for p in [sitepackages_prefix, home_prefix]:
                if f.endswith(p):
                    self.__prefix = f[:-len(p)]
                    break
            if self.__prefix is None:
                self.__prefix = sys.prefix 

        return self.__prefix            

    def __init__(self,fname=None):
        self.__prefix = None
        self.options = {
            'login.login': 'demo',
            'login.server': 'localhost',
            'login.port': '8070',
            'login.protocol': 'socket://',
            'login.db': 'terp',
            'client.toolbar': 'both',
            'client.theme': 'none',
            'path.share': os.path.join(self.__get_prefix(), 'share', release.name),
            'path.pixmaps': os.path.join(self.__get_prefix(), 'share', 'pixmaps', release.name),
            'tip.autostart': False,
            'tip.position': 0,
            'survey.position': 0,
            'form.autosave': False,
            'printer.preview': True,
            'printer.softpath': 'none',
            'printer.softpath_html': 'none',
            'printer.path': 'none',
            'logging.level': 'INFO',
            'logging.output': 'stdout',
            'client.default_path': os.path.expanduser('~'),
            'support.recipient': 'support@openerp.com',
            'support.support_id' : '',
            'form.toolbar': True,
            'client.form_tab': 'top',
            'client.form_tab_orientation': 0,
            'client.lang': False,
            'client.filetype': {},
            'help.index': 'http://doc.openerp.com/',
            'help.context': 'http://doc.openerp.com/index.php?model=%(model)s&lang=%(lang)s',
            'client.timeout': 300,
        }
        loglevels = ('critical', 'error', 'warning', 'info', 'debug', 'debug_rpc', 'debug_rpc_answer', 'notset')
        parser = optparse.OptionParser(version=_("OpenERP Client %s" % openerp_version))
        parser.add_option("-c", "--config", dest="config",help=_("specify alternate config file"))
        parser.add_option("-v", "--verbose", dest="log_level", action='store_const', const="debug", help=_("Enable basic debugging. Alias for '--log-level=debug'"))
        parser.add_option("-l", "--log-level", dest="log_level", type='choice', choices=loglevels, default='error', help=_("specify the log level: %s") % ", ".join(loglevels))
        parser.add_option("-u", "--user", dest="login", help=_("specify the user login"))
        parser.add_option("-p", "--port", dest="port", help=_("specify the server port"))
        parser.add_option("-s", "--server", dest="server", help=_("specify the server ip/name"))
        (opt, args) = parser.parse_args()

        self.rcfile = self._get_rcfile(fname, opt.config)
        self.load()

        self.options['logging.level'] = opt.log_level

        for arg in ('login', 'port', 'server'):
            if getattr(opt, arg):
                self.options['login.'+arg] = getattr(opt, arg)

    def _get_rcfile(self, fname, optconfigfile):
        rcfile = fname or optconfigfile or os.environ.get('OPENERPRC') or os.path.join(get_home_dir(), '.openerprc')
        if not os.path.exists(rcfile):
            import logging
            log = logging.getLogger('common.options')
            additional_info = ""
            if optconfigfile:
                additional_info = " Be sure to specify an absolute path name if you are using the '-c' command line switch"
            log.warn('Config file %s does not exist !%s'% (rcfile, additional_info ))
        return os.path.abspath(rcfile)

    def save(self, fname = None):
        try:
            p = ConfigParser.ConfigParser()
            sections = {}
            for o in self.options.keys():
                if not len(o.split('.'))==2:
                    continue
                osection,oname = o.split('.')
                if not p.has_section(osection):
                    p.add_section(osection)
                p.set(osection,oname,self.options[o])
            p.write(file(self.rcfile,'wb'))
        except:
            import logging
            log = logging.getLogger('common.options')
            log.warn('Unable to write config file %s !'% (self.rcfile,))
        return True


    def load(self, fname=None):
        try:
            self.rcexist = False
            if not os.path.isfile(self.rcfile):
                self.save()
                return False
            self.rcexist = True

            p = ConfigParser.RawConfigParser()
            p.read([self.rcfile])
            for section in p.sections():
                for (name,value) in p.items(section):
                    if value=='True' or value=='true':
                        value = True
                    if value=='False' or value=='false':
                        value = False
                    if value=='None' or value=='none':
                        value = None
                    self.options[section+'.'+name] = value
        except Exception, e:
            import logging
            log = logging.getLogger('common.options')
            log.warn('Unable to read config file %s !'% (self.rcfile,))
        return True

    def __setitem__(self, key, value):
        self.options[key]=value

    def __getitem__(self, key):
        return self.options[key]

    def get(self, key, default_value = None):
        return self.options.get(key, default_value)

options = configmanager()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

