# -*- coding: utf-8 -*-
##############################################################################
#    
#   This file is part of Gnomolicious.
#
#   Gnomolicious is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   Gnomolicious is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Gnomolicious; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#   (C) 2003, 2005 Terje RÃžsten <terjeros@phys.ntnu.no>, Nicolas Ãvrard     
#
##############################################################################


import sys
import os
import os.path
import re
import glob
import commands
import types
import msgfmt

from distutils.core import Command
from distutils.command.build import build
from distutils.command.install import install
from distutils.command.install_data import install_data
from distutils.dep_util import newer
from distutils.dist import Distribution
from distutils.core import setup

try:
    from dsextras import BuildExt
except ImportError:
    try:
        from gtk.dsextras import BuildExt
    except ImportError:
        sys.exit('Error: Can not find dsextras or gtk.dsextras')

# get python short version
py_short_version = '%s.%s' % sys.version_info[:2]


class l10napp_build(build):

    def has_po_files(self):
        return self.distribution.has_po_files()

    sub_commands = []
    sub_commands.append(('build_conf', None))
    sub_commands.extend(build.sub_commands)
    sub_commands.append(('build_mo', has_po_files))

class l10napp_install(install):

    def has_po_files(self):
        return self.distribution.has_po_files()

    def run(self):
        # create startup script
        # start_script = "#!/bin/sh\ncd %s\nexec %s ./openerp-client.py $@\n" % (opj(self.install_libbase, "openerp-client"), sys.executable)
        opj = os.path.join
        openerp_site_packages = opj('/usr', 'lib', 'python%s' % py_short_version, 'site-packages', 'openerp-client')
        start_script = "#!/bin/sh\ncd %s\nexec %s ./openerp-client.py $@\n" % (openerp_site_packages, sys.executable)
        # write script
        f = open('openerp-client', 'w')
        f.write(start_script)
        f.close()
        install.run(self)

    sub_commands = []
    sub_commands.extend(install.sub_commands)
    sub_commands.append(('install_mo', has_po_files))

class build_conf(Command):

    description = 'update conf file'

    user_options = []

    def initialize_options(self):
        self.prefix = None

    def finalize_options(self):
        self.set_undefined_options('install', ('prefix', 'prefix'))

    def run(self):
        self.announce('Building files from templates')

class build_mo(Command):

    description = 'build binary message catalog'

    user_options = [
        ('build-base=', 'b', 'directory to build to')]

    def initialize_options(self):
        self.build_base = None
        self.translations = self.distribution.translations
        self.force = None
    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('force', 'force'))
    def run(self):
        self.announce('Building binary message catalog')
        if self.distribution.has_po_files():
            for mo, po in self.translations:
                dest = os.path.normpath(self.build_base + '/' + mo)
                self.mkpath(os.path.dirname(dest))
                if not self.force and not newer(po, dest):
                    self.announce("not building %s (up-to-date)" % dest)
                else:
                    msgfmt.make(po, dest)

class install_mo(install_data):

    description = 'install generated binary message catalog'

    def initialize_options(self):
        install_data.initialize_options(self)
        self.translations = self.distribution.translations
        self.has_po_files = self.distribution.has_po_files
        self.install_dir = None
        self.build_dir = None
        self.skip_build = None
        self.outfiles = []
        
    def finalize_options(self):
        install_data.finalize_options(self)
        self.set_undefined_options('build_mo', ('build_base', 'build_dir'))
        self.set_undefined_options('install',
                                   ('install_data', 'install_dir'),
                                   ('skip_build', 'skip_build'))
    def run(self):
        if not self.skip_build:
            self.run_command('build_mo')
        if self.has_po_files():
            for mo, po in self.translations:
                src = os.path.normpath(self.build_dir + '/' + mo)
                if not os.path.isabs(mo):
                    dest =  os.path.normpath(self.install_dir + '/' + mo)
                elif self.root:
                    dest = self.root + mo
                else:
                    dest = mo
                self.mkpath(os.path.dirname(dest))
                (out, _) = self.copy_file(src, dest)
                self.outfiles.append(out)

    def get_outputs (self):
        return self.outfiles

    def get_inputs (self):
        return [ po for mo, po in self.translations ]

class L10nAppDistribution(Distribution):
    def __init__(self, attrs = None):
        self.modules_check = 0
        self.gconf = 1
        self.msg_sources = None
        self.translations = []
        self.name = attrs.get('name')
        Distribution.__init__(self, attrs)
        self.cmdclass = {
            'install' : l10napp_install,
            'install_mo' : install_mo,
            'build' : l10napp_build,
            'build_mo' : build_mo,
            'build_conf' : build_conf,
            'build_ext': BuildExt,
            }

    def has_po_files(self):
        return len(self.translations) > 0
    
def setup(**kwds):
    from distutils.core import setup
    kwds['distclass'] = L10nAppDistribution
    setup(**kwds)

# vim:expandtab:tw=80
