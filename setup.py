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
import shutil

from stat import ST_MODE

from distutils.file_util import copy_file
from distutils.core import setup
from mydistutils import L10nAppDistribution

has_py2exe = False

SYSTEM_DLLS = [
    'msvcr71.dll',
    'w9xpopen.exe',
    'api-ms-win-core-debug-l1-1-0.dll',
    'api-ms-win-core-delayload-l1-1-0.dll',
    'api-ms-win-core-errorhandling-l1-1-0.dll',
    'api-ms-win-core-errorhandling-l1-1-0.dll',
    'api-ms-win-core-handle-l1-1-0.dll',
    'api-ms-win-core-heap-l1-1-0.dll',
    'api-ms-win-core-interlocked-l1-1-0.dll',
    'api-ms-win-core-io-l1-1-0.dll',
    'api-ms-win-core-localization-l1-1-0.dll',
    'api-ms-win-core-libraryloader-l1-1-0.dll',
    'api-ms-win-core-localregistry-l1-1-0.dll',
    'api-ms-win-core-misc-l1-1-0.dll',
    'api-ms-win-core-processenvironment-l1-1-0.dll',
    'api-ms-win-core-processthreads-l1-1-0.dll',
    'api-ms-win-core-profile-l1-1-0.dll',
    'api-ms-win-security-base-l1-1-0.dll',
    'api-ms-win-core-string-l1-1-0.dll',
    'api-ms-win-core-synch-l1-1-0.dll',
    'api-ms-win-core-sysinfo-l1-1-0.dll',
    'nsi.dll',
    'msimg32.dll',
    'usp10.dll',
    'dnsapi.dll',
    'kernelbase.dll',
    'powrprof.dll'
]

# From http://trac.assembla.com/fpdb/browser/packaging/windows/py2exe_setup.py
def copy_tree(source,destination):
    source = source.replace('\\', '\\\\')
    destination = destination.replace('\\', '\\\\')
    print "*** Copying " + source + " to " + destination + " ***"
    shutil.copytree( source, destination )

def copy_file(source,destination):
    source = source.replace('\\', '\\\\')
    destination = destination.replace('\\', '\\\\')
    print "*** Copying " + source + " to " + destination + " ***"
    shutil.copy( source, destination )

if os.name == 'nt':
    import py2exe
    has_py2exe = True
    dist_dir = "dist"
    if os.path.isdir(dist_dir):
            shutil.rmtree(dist_dir)
    origIsSystemDLL = py2exe.build_exe.isSystemDLL
    
    
    def isSystemDLL(pathname):
        if os.path.basename(pathname).lower() in SYSTEM_DLLS:
            return 1
        if os.path.basename(pathname).lower() in ("msvcp71.dll", "mfc71.dll"
												  "mfc90.dll", "msvcp90.dll",
                                                  "msvcr90.dll"):
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
        mfcdir = 'C:\Python27\Lib\site-packages\pythonwin'
        mfcfiles = [os.path.join(mfcdir, i)
                    for i in ["mfc90.dll", "mfc90u.dll", "mfcm90.dll",
                              "mfcm90u.dll", "Microsoft.VC90.MFC.manifest"]]
        files += [("Microsoft.VC90.MFC", mfcfiles)]
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
        "optimize": 0,
        "bundle_files": 3,
        "dist_dir": 'dist',
        "packages": ["encodings","gtk", "matplotlib", "pytz", "OpenSSL"],
        "includes": "pango,atk,gobject,cairo,atk,pangocairo,matplotlib._path,gio",
        "excludes": ["Tkinter", "tcl85", "tk85", "TKconstants"],
        "dll_excludes": ['msvcr71.dll',
                         'w9xpopen.exe',
                         'API-MS-Win-Core-LocalRegistry-L1-1-0.dll',
                         'API-MS-Win-Core-ProcessThreads-L1-1-0.dll',
                         'API-MS-Win-Security-Base-L1-1-0.dll',
                         'KERNELBASE.dll',
                         'POWRPROF.dll']
    }
}

complementary_arguments = dict()

if sys.platform == 'win32':
	manifest = open('Microsoft.VC90.CRT.manifest').read()
	complementary_arguments['windows'] = [
        {
            'script' : os.path.join('bin', 'openerp-client.py'),
            'icon_resources' : [(1, os.path.join('bin', 'pixmaps', 'openerp-icon.ico'))],
            'other_resources': [(24, 1, manifest)]
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

dest = "dist"
gtk_dir = "C:/Python27/Lib/site-packages/gtk-2.0/runtime/"
while not os.path.exists(gtk_dir):
    print "Enter directory name for GTK (e.g. c:/gtk) : ",     # the comma means no newline
    gtk_dir = sys.stdin.readline().rstrip()
print "*** py2exe build phase complete ***"
copy_file(os.path.join(gtk_dir, 'bin', 'libgdk-win32-2.0-0.dll'), dest )
copy_file(os.path.join(gtk_dir, 'bin', 'libgobject-2.0-0.dll'), dest)
copy_file(os.path.join(gtk_dir, 'bin', 'libcroco-0.6-3.dll'), dest)
copy_file(os.path.join(gtk_dir, 'bin', 'librsvg-2-2.dll'), dest)
copy_file(os.path.join(gtk_dir, 'bin', 'libxml2-2.dll'), dest)
copy_file(os.path.join(gtk_dir, 'bin', 'gdk-pixbuf-query-loaders.exe'), dest)
copy_file(os.path.join('dlls', 'msvcp90.dll'), dest)
copy_file(os.path.join('dlls', 'msvcr90.dll'), dest)
copy_file('Microsoft.VC90.CRT.manifest', dest)
#copy_file('C:\Python27\lib\site-packages\Pythonwin\mfc90.dll', dest)
#copy_file('C:\Python27\lib\site-packages\OpenSSL\LIBEAY32.dll', dest)
#copy_file(' C:\Python27\lib\site-packages\OpenSSL\SSLEAY32.dll', dest)
copy_tree(os.path.join(gtk_dir, 'share', 'icons'), os.path.join(dest, 'share', 'icons'))
copy_tree(os.path.join(gtk_dir, 'share', 'themes'), os.path.join(dest, 'share', 'themes'))
copy_tree(os.path.join(gtk_dir, 'etc', 'gtk-2.0'), os.path.join(dest, 'etc', 'gtk-2.0'))
print "*** Done ***"