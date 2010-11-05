#!/usr/bin/env python
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

# setup from TinyERP
#   taken from straw http://www.nongnu.org/straw/index.html
#   taken from gnomolicious http://www.nongnu.org/gnomolicious/
#   adapted by Nicolas Évrard <nicoe@altern.org>

import imp
import sys
import os
import glob

from stat import ST_MODE

from distutils.file_util import copy_file
from distutils.core import setup
from mydistutils import L10nAppDistribution

has_py2exe = False
if os.name == 'nt':
    import py2exe
    has_py2exe = True

    origIsSystemDLL = py2exe.build_exe.isSystemDLL
    def isSystemDLL(pathname):
        if os.path.basename(pathname).lower() in ("msvcp71.dll", "mfc71.dll"):
                return 0
        return origIsSystemDLL(pathname)
    py2exe.build_exe.isSystemDLL = isSystemDLL

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "bin"))

opj = os.path.join

execfile(opj('bin', 'release.py'))

if sys.argv[1] == 'bdist_rpm':
    version = version.split('-')[0]


# get python short version
py_short_version = '%s.%s' % sys.version_info[:2]

required_modules = [('gtk', 'gtk python bindings'),
                    ('gtk.glade', 'glade python bindings'),
                    ('mx.DateTime', 'date and time handling routines for Python')]

def check_modules():
    ok = True
    for modname, desc in required_modules:
        try:
            exec('import %s' % modname)
        except ImportError:
            ok = False
            print 'Error: python module %s (%s) is required' % (modname, desc)

    if not ok:
        sys.exit(1)

def data_files():
    '''Build list of data files to be installed'''
    files = []
    if os.name == 'nt':
        import matplotlib
        datafiles = matplotlib.get_py2exe_datafiles()
        if isinstance(datafiles, list):
            files.extend(datafiles)
        else:
            files.append(datafiles)
        os.chdir('bin')
        for (dp, dn, names) in os.walk('share\\locale'):
            files.append((dp, map(lambda x: opj('bin', dp, x), names)))
        os.chdir('..')
        files.append((".",["bin\\openerp.glade", 'bin\\dia_survey.glade', "bin\\win_error.glade", 'bin\\tipoftheday.txt', 'doc\\README.txt']))
        files.append(("pixmaps", glob.glob("bin\\pixmaps\\*.*")))
        files.append(("po", glob.glob("bin\\po\\*.*")))
        files.append(("icons", glob.glob("bin\\icons\\*.png")))
        files.append(("share\\locale", glob.glob("bin\\share\\locale\\*.*")))
    else:
        files.append((opj('share','man','man1',''),['man/openerp-client.1']))
        files.append((opj('share','doc', 'openerp-client-%s' % version), [f for
            f in glob.glob('doc/*') if os.path.isfile(f)]))
        files.append((opj('share', 'pixmaps', 'openerp-client'),
            glob.glob('bin/pixmaps/*.png')))
        files.append((opj('share', 'pixmaps', 'openerp-client', 'icons'),
            glob.glob('bin/icons/*.png')))
        files.append((opj('share', 'openerp-client'), ['bin/openerp.glade', 'bin/tipoftheday.txt',
                                                       'bin/win_error.glade', 'bin/dia_survey.glade']))
    return files

included_plugins = ['workflow_print']

f = file('openerp-client','w')
start_script = """#!/bin/sh\necho "OpenERP Setup - The content of this file is generated at the install stage" """
f.write(start_script)
f.close()

def find_plugins():
    for plugin in included_plugins:
        path=opj('bin', 'plugins', plugin)
        for dirpath, dirnames, filenames in os.walk(path):
            if '__init__.py' in filenames:
                modname = dirpath.replace(os.path.sep, '.')
                yield modname.replace('bin', 'openerp-client', 1)

def translations():
    trans = []
    dest = 'share/locale/%s/LC_MESSAGES/%s.mo'
    for po in glob.glob('bin/po/*.po'):
        lang = os.path.splitext(os.path.basename(po))[0]
        trans.append((dest % (lang, name), po))
    return trans

check_modules()

if os.name <> 'nt' and sys.argv[1] == 'build_po':
    os.system('(cd bin ; find . -name \*.py && find . -name \*.glade | xargs xgettext -o po/%s.pot)' % name)
    for file in ([ os.path.join('bin', 'po', fname) for fname in os.listdir('bin/po') ]):
        if os.path.isfile(file):
            os.system('msgmerge --update --backup=off %s bin/po/%s.pot' % (file, name))
    sys.exit()

options = {
    "py2exe": {
        "compressed": 1,
        "optimize": 1,
        "dist_dir": 'dist',
        "packages": ["encodings","gtk", "matplotlib", "pytz", "OpenSSL"],
        "includes": "pango,atk,gobject,cairo,atk,pangocairo,matplotlib._path",
        "excludes": ["Tkinter", "tcl", "TKconstants"],
        "dll_excludes": [
            "iconv.dll","intl.dll","libatk-1.0-0.dll",
            "libgdk_pixbuf-2.0-0.dll","libgdk-win32-2.0-0.dll",
            "libglib-2.0-0.dll","libgmodule-2.0-0.dll",
            "libgobject-2.0-0.dll","libgthread-2.0-0.dll",
            "libgtk-win32-2.0-0.dll","libpango-1.0-0.dll",
            "libpangowin32-1.0-0.dll",
            "wxmsw26uh_vc.dll",
        ],
    }
}

complementary_arguments = dict()

if sys.platform == 'win32':
    complementary_arguments['windows'] = [
        {
            'script' : os.path.join('bin', 'openerp-client.py'),
            'icon_resources' : [(1, os.path.join('bin', 'pixmaps', 'openerp-icon.ico'))],
        }
    ]

setup(name             = name,
      version          = version,
      description      = description,
      long_description = long_desc,
      url              = url,
      author           = author,
      author_email     = author_email,
      classifiers      = filter(None, classifiers.splitlines()),
      license          = license,
      data_files       = data_files(),
      translations     = translations(),
      scripts          = ['openerp-client'],
      packages         = ['openerp-client', 
                          'openerp-client.common', 
                          'openerp-client.modules', 
                          'openerp-client.modules.action',
                          'openerp-client.modules.gui',
                          'openerp-client.modules.gui.window',
                          'openerp-client.modules.gui.window.view_sel',
                          'openerp-client.modules.gui.window.view_tree',
                          'openerp-client.modules.spool',
                          'openerp-client.printer', 
                          'openerp-client.tools',
                          'openerp-client.tinygraph',
                          'openerp-client.widget',
                          'openerp-client.widget.model',
                          'openerp-client.widget.screen',
                          'openerp-client.widget.view',
                          'openerp-client.widget.view.form_gtk',
                          'openerp-client.widget.view.tree_gtk',
                          'openerp-client.widget.view.graph_gtk',
                          'openerp-client.widget.view.calendar_gtk',
                          'openerp-client.widget.view.gantt_gtk',
                          'openerp-client.widget_search',
                          'openerp-client.SpiffGtkWidgets',
                          'openerp-client.SpiffGtkWidgets.Calendar',
                          'openerp-client.plugins'] + list(find_plugins()),
      package_dir      = {'openerp-client': 'bin'},
      distclass = os.name <> 'nt' and L10nAppDistribution or None,
      #extras_required={
      #    'timezone' : ['pytz'],
      #},
      options = options,
      **complementary_arguments
      )

if has_py2exe:
    # Sometime between pytz-2008a and pytz-2008i common_timezones started to
    # include only names of zones with a corresponding data file in zoneinfo.
    # pytz installs the zoneinfo directory tree in the same directory
    # as the pytz/__init__.py file. These data files are loaded using
    # pkg_resources.resource_stream. py2exe does not copy this to library.zip so
    # resource_stream can't find the files and common_timezones is empty when
    # read in the py2exe executable.
    # This manually copies zoneinfo into the zip. See also
    # http://code.google.com/p/googletransitdatafeed/issues/detail?id=121
    import pytz
    import zipfile
    import tempfile
    import shutil
    # Make sure the layout of pytz hasn't changed
    assert (pytz.__file__.endswith('__init__.pyc') or
          pytz.__file__.endswith('__init__.py')), pytz.__file__

    temp_dir = None
    pytz_dir = os.path.dirname(pytz.__file__)
    zoneinfo_dir = os.path.join(pytz_dir, 'zoneinfo')
    if not os.path.exists(zoneinfo_dir):
        egg = os.path.dirname(pytz_dir)

        if zipfile.is_zipfile(egg):
            temp_dir = tempfile.mkdtemp()
            zoneinfo_dir = os.path.join(temp_dir, 'pytz', 'zoneinfo')
            os.makedirs(zoneinfo_dir)

            archive = zipfile.ZipFile(egg)
            for filename in archive.namelist():
                if filename.startswith('pytz/zoneinfo/'):
                    file_path = os.path.join(temp_dir, filename)
                    destination = file_path.replace('/', os.sep)
                    if not file_path.endswith('/'):
                        try:
                            os.makedirs(os.path.dirname(destination))
                        except os.error:
                            pass
                        fp = file(destination, 'w')
                        fp.write(archive.read(filename))
                        fp.close()
            archive.close()

    # '..\\Lib\\pytz\\__init__.py' -> '..\\Lib'
    disk_basedir = os.path.dirname(os.path.dirname(zoneinfo_dir))
    zipfile_path = os.path.join(options['py2exe']['dist_dir'], 'library.zip')
    z = zipfile.ZipFile(zipfile_path, 'a')
    for absdir, directories, filenames in os.walk(zoneinfo_dir):
        zip_dir = absdir[len(disk_basedir):]
        for f in filenames:
            z.write(os.path.join(absdir, f), os.path.join(zip_dir, f))
    z.close()

    if temp_dir is not None:
        shutil.rmtree(temp_dir)

