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

# ------------------------------------------------------------------- #
# Module printer
# ------------------------------------------------------------------- #
#
# Supported formats: pdf
#
# Print or open a previewer
#
import base64
import gc
import platform
import sys
import time
import os

import gtk

import common
import options 


class Printer(object):

    def __init__(self):
        self.openers = {
            'pdf': self._findPDFOpener,
            'html': self._findHTMLOpener,
            'doc': self._findHTMLOpener,
            'xls': self._findHTMLOpener,
            'sxw': self._findSXWOpener,
            'odt': self._findSXWOpener,
            'tiff': self._findPDFOpener,
        }

    def _findInPath(self, progs):
        lstprogs = progs[:]
        found = {}
        path = [dir for dir in os.environ['PATH'].split(':')
                if os.path.isdir(dir)]
        for dir in path:
            content = os.listdir(dir)
            for prog in progs[:]:
                if prog in content:
                    return os.path.join(dir, prog)#prog
                    
                    progs.remove(prog)
                    found[prog] = os.path.join(dir, prog)
        for prog in lstprogs:
            if prog in found:
                return found[prog]
        return ''

    def _findHTMLOpener(self):
        import webbrowser
        def opener(fn):
            webbrowser.open('file://'+fn)
        return opener

    def _opener(self, fnct):
        def opener(fn):
            pid = os.fork()
            if not pid:
                pid = os.fork()
                if not pid:
                    fnct(fn)
                time.sleep(0.1)
                sys.exit(0)
            os.waitpid(pid, 0)
        return opener

    def _findPDFOpener(self):
        if platform.system() == 'Darwin':
            return self._opener(lambda fn: os.system('open ' + fn))
        softpath = options.options['printer.softpath']
        if platform.system() == 'Windows':
            if options.options['printer.preview']:
                if not softpath or (softpath and softpath in ['None','none']):
                    return os.startfile
                else:
                    return lambda fn: os.system(softpath + ' ' + fn)
            else:
                return print_w32_filename
        else:
            if options.options['printer.preview']:
                if not softpath or (softpath and softpath in ['None','none']):
                    prog = self._findInPath(['xdg-open', 'gnome-open', 'see'])
                    return self._opener(lambda fn: os.execv(prog, (os.path.basename(prog), fn)))
                else:
                    return self._opener(lambda fn: os.execv(softpath, (os.path.basename(softpath), fn)))
            else:
                return print_linux_filename
    
    def _findSXWOpener(self):
        if os.name == 'nt':
            return lambda fn: os.startfile(fn)
        else:
            if options.options['printer.softpath_html'] is None:
                prog = self._findInPath(['ooffice', 'ooffice2', 'openoffice', 'soffice'])
                def opener(fn):
                    pid = os.fork()
                    if not pid:
                        pid = os.fork()
                        if not pid:
                            os.execv(prog, (os.path.basename(prog),fn))
                        time.sleep(0.1)
                        sys.exit(0)
                    os.waitpid(pid, 0)
                return opener
            else:
                def opener(fn):
                    pid = os.fork()
                    if not pid:
                        pid = os.fork()
                        if not pid:
                            os.execv(options.options['printer.softpath_html'], (os.path.basename(options.options['printer.softpath_html']),fn))
                        time.sleep(0.1)
                        sys.exit(0)
                    os.waitpid(pid, 0)
                return opener
    def print_file(self, fname, ftype, preview=False):
        app_to_run = None
        try:
            filetypes = eval( options.options['extensions.filetype'] )
            (app, app_print) = filetypes[ftype]
            if options.options['printer.preview'] or preview:
                app_to_run = app
            else:
                app_to_run = app_print
        except:
            pass

        if app_to_run:
            def open_file(cmd, filename):
                cmd = cmd.split()
                found = False
                for i, v in enumerate(cmd):
                    if v == '%s':
                        cmd[i] = filename
                        found = True
                        break
                if not found:
                    cmd.append(filename)

                import subprocess
                subprocess.Popen(cmd)
            open_file(app_to_run, fname)

        else:
            try:
                finderfunc = self.openers.get(ftype,False)
                if not finderfunc:
                    if sys.platform in ['win32', 'nt']:
                        os.startfile(fname)
                    else:
                        finderfunc = self.openers['html']
                        opener = finderfunc()
                        opener(fname)
                else:
                    opener = finderfunc()
                    opener(fname)
                    gc.collect()
            except Exception,e:
                raise Exception(_('Unable to handle %s filetype') % ftype)

printer = Printer()

def print_linux_filename(filename):
    common.message(_('Linux Automatic Printing not implemented.\nUse preview option !'))

def print_w32_filename(filename):
    import win32api
    win32api.ShellExecute (0, "print", filename, None, ".", 0)

def print_data(data):
    if 'result' not in data:
        common.message(_('Error! No Data found. Make sure you have enough data to print!'))
        return 
    if data.get('code','normal')=='zlib':
        import zlib
        content = zlib.decompress(base64.decodestring(data['result']))
    else:
        content = base64.decodestring(data['result'])

    if data['format'] in printer.openers.keys():
        import tempfile
        if data['format']=='html' and os.name=='nt':
            data['format']='doc'
        (fileno, fp_name) = tempfile.mkstemp('.'+data['format'], 'openerp_')
        fp = file(fp_name, 'wb+')
        fp.write(content)
        fp.close()
        os.close(fileno)
        printer.print_file(fp_name, data['format'])
    else:
        fname = common.file_selection(_('Save As...'), filename='report.' + data['format'],
                action=gtk.FILE_CHOOSER_ACTION_SAVE)
        if fname:
            try:
                fp = file(fname,'wb+')
                fp.write(content)
                fp.close()
            except:
                common.message(_('Error writing the file!'))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

