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

import os
import gettext
import gobject
import gtk
import gtk.glade

import service
import common
import options

class win_extension(object):
    def __init__(self, parent=None):
        glade = gtk.glade.XML(common.terp_path('openerp.glade'), 'win_extension', gettext.textdomain())
        self.win = glade.get_widget('win_extension')
        self.win.set_icon(common.OPENERP_ICON)
        model = gtk.ListStore( str, str, str )

        self.treeview = glade.get_widget('treeview_extension')
        self.treeview.set_model(model)

        for index, text in enumerate(['Extension', 'Application', 'Print Processor']):
            renderer = gtk.CellRendererText()
            renderer.set_property( 'editable', True )
            renderer.connect( 'edited', self._on_cell_renderer_edited )
            column = gtk.TreeViewColumn( text, renderer, text=index )
            column.set_resizable( True )
            self.treeview.append_column( column )

        dict = {
            'on_button5_clicked' : self._sig_add,
            'on_button6_clicked' : self._sig_remove,
        }

        for signal in dict:
            glade.signal_connect( signal, dict[signal] )

        self.load_from_file()

    def load_from_file(self):
        try:
            filetypes = eval(options.options['extensions.filetype'][:])
            for ext, (app, app_print) in filetypes.items():
                self.add_to_model( ext, app, app_print )
        except Exception, ex:
            pass

    def save_to_file(self):
        value = dict( [ [ ext, ( app, printable ) ] for ext, app, printable in self.treeview.get_model() ] )
        options.options['extensions.filetype'] = str(value)
        options.options.save()

    def add_to_model( self, extension, application, printable ):
        model = self.treeview.get_model()
        iter = model.append()
        model.set( iter, 0, extension, 1, application, 2, printable )
        return model.get_path( iter )

    def _sig_add( self, button, data = None ):
        path = self.add_to_model( '', '', '' )
        self.treeview.set_cursor( path, self.treeview.get_column(0), True )

    def _sig_remove( self, button, data = None ):
        selection = self.treeview.get_selection()
        model, iter = selection.get_selected()

        if iter:
            path = model.get_path(iter)
            model.remove( iter )
            selection.select_path( path )

            if not selection.path_is_selected( path ):
                row = path[0]-1
                if row >= 0:
                    selection.select_path((row,))

    def _on_cell_renderer_edited( self, cell, path_string, new_text ):
        model = self.treeview.get_model()
        iter = model.get_iter_from_string(path_string)

        (path,column) = self.treeview.get_cursor()

        column_id = self.treeview.get_columns().index(column)

        old_text = model.get_value( iter, column_id )

        if column_id == 0:
            old_text = old_text.lower()
            new_text = new_text.lower()

        if old_text <> new_text:
            if column_id == 0:
                if new_text in [ ext for ext, app, app_print in model ]:
                    common.warning(_('This extension is already defined'), 'Extension Manager')
                    return
                else:
                    model.set(iter, column_id, new_text)
            else:
                model.set(iter, column_id, new_text)

    def run(self):
        res = self.win.run()
        if res == -5:
            self.save_to_file()
        self.win.destroy()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
