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
from gtk import glade
import gobject
import gettext
import common

import rpc

import csv
import cStringIO

import options
import service

#
# TODO: make it works with references
#
def import_csv(csv_data, f, model, fields, context=None):
    fname = csv_data['fname']
    content = file(fname,'rb').read()
    input=cStringIO.StringIO(content)
    input.seek(0)
    data = list(csv.reader(input, quotechar=csv_data['del'] or '"', delimiter=csv_data['sep']))[int(csv_data['skip']):]
    datas = []
    for line in data:
        if not line:
            continue
        datas.append(map(lambda x:x.decode(csv_data['combo']).encode('utf-8'), line))
    if not datas:
        common.warning(_('The file is empty !'), _('Importation !'))
        return False
    try:
        res = rpc.session.rpc_exec_auth('/object', 'execute', model, 'import_data', f, datas, 'init', '', False, context)
    except Exception, e:
        common.warning(str(e), _('XML-RPC error !'))
        return False
    result = res[0]    
    if result>=0:
        if result == 1:
            common.message(_('Imported one object !'))
        else:
            common.message(_('Imported %d objects !') % (result,))
    else:
        d = ''
        for key,val in res[1].items():
            d+= ('\t%s: %s\n' % (str(key),str(val)))
        error = u'Error trying to import this record:\n%s\nError Message:\n%s\n\n%s' % (d,res[2],res[3])
        common.message_box(_('Importation Error !'), unicode(error))
    return True

class win_import(object):
    def __init__(self, model, fields, preload = [], parent=None, local_context=None):
        self.glade = glade.XML(common.terp_path("openerp.glade"), 'win_import',
                gettext.textdomain())
        self.glade.get_widget('import_csv_combo').set_active(0)
        self.win = self.glade.get_widget('win_import')
        self.model = model
        self.fields_data = {}
        self.invert = False
        self.context = local_context or {}
        if parent is None:
            parent = service.LocalService('gui.main').window
        self.win.set_transient_for(parent)
        self.win.set_icon(common.OPENERP_ICON)
        self.parent = parent

        self.glade.get_widget('import_csv_file').set_current_folder(
                options.options['client.default_path'])
        self.view1 = gtk.TreeView()
        self.view1.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.glade.get_widget('import_vp_left').add(self.view1)
        self.view2 = gtk.TreeView()
        self.view2.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.glade.get_widget('import_vp_right').add(self.view2)
        self.view1.set_headers_visible(False)
        self.view2.set_headers_visible(False)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Field name'), cell, text=0, background=2)
        self.view1.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn(_('Field name'), cell, text=0)
        self.view2.append_column(column)

        self.model1 = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.model2 = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)

        for f in preload:
            self.model2.set(self.model2.append(), 0, f[1], 1, f[0])

        self.fields = {}
        self.fields_invert = {}
        def model_populate(fields, prefix_node='', prefix=None, prefix_value='', level=2):
            fields_order = fields.keys()
            fields_order.sort(lambda x,y: -cmp(fields[x].get('string', ''), fields[y].get('string', '')))
            for field in fields_order:
                if (fields[field].get('type','') not in ('reference',)) \
                        and (not fields[field].get('readonly', False) \
                        or not dict(fields[field].get('states', {}).get(
                            'draft', [('readonly', True)])).get('readonly', True)\
                        or not dict(fields[field].get('states', {}).get(
                            field, [('readonly', True)])).get('readonly', True)):
                    self.fields_data[prefix_node+field] = fields[field]
                    st_name = prefix_value+fields[field]['string'] or field
                    node = self.model1.insert(prefix, 0, [st_name, prefix_node+field,
                        (fields[field].get('required', False) and '#ddddff') or 'white'])
                    self.fields[prefix_node+field] = st_name
                    self.fields_invert[st_name] = prefix_node+field
                    if fields[field].get('type','') == 'one2many' and level>0:
                        fields2 = rpc.session.rpc_exec_auth('/object', 'execute', fields[field]['relation'], 'fields_get', False, rpc.session.context)
                        model_populate(fields2, prefix_node+field+'/', node, st_name+'/', level-1)
                    if fields[field].get('type','') in ('many2one' , 'many2many' ) and level>0:
                        #self.fields[field+':id'] = fields[field]['string']
                        #self.fields_invert[fields[field]['string']] = field+':id'
                        model_populate({'id':{'string':'ID'},'db_id':{'string':'Database ID'}}, \
                                       prefix_node+field+':', node, st_name+'/', level-1)
        fields.update({'id':{'string':'ID'},'db_id':{'string':'Database ID'}})
        model_populate(fields)

        #for f in fields:
        #   self.model1.set(self.model1.append(), 1, f, 0, fields[f].get('string', 'unknown'))

        self.view1.set_model(self.model1)
        self.view2.set_model(self.model2)
        self.view1.show_all()
        self.view2.show_all()

        self.glade.signal_connect('on_but_unselect_all_clicked', self.sig_unsel_all)
        self.glade.signal_connect('on_but_select_all_clicked', self.sig_sel_all)
        self.glade.signal_connect('on_but_select_clicked', self.sig_sel)
        self.glade.signal_connect('on_but_unselect_clicked', self.sig_unsel)
        self.glade.signal_connect('on_but_autodetect_clicked', self.sig_autodetect)

    def sig_autodetect(self, widget=None):
        fname= self.glade.get_widget('import_csv_file').get_filename()
        if not fname:
            common.message('You must select an import file first !')
            return True
        csvsep= self.glade.get_widget('import_csv_sep').get_text()
        csvdel= self.glade.get_widget('import_csv_del').get_text()
        csvcode= self.glade.get_widget('import_csv_combo').get_active_text() or 'UTF-8'

        self.glade.get_widget('import_csv_skip').set_value(1)
        try:
            data = csv.reader(file(fname), quotechar=csvdel or '"', delimiter=csvsep)
        except:
            common.warning('Error opening .CSV file', 'Input Error.')
            return True
        self.sig_unsel_all()
        word=''
        try:
            for line in data:
                for word in line:
                    word = word.decode(csvcode)
                    if not csvcode.lower() == 'utf-8':
                        word = word.encode('utf-8')
                    if (word in self.fields):
                        num = self.model2.append()
                        self.model2.set(num, 0, self.fields[word], 1, word)
                    elif word in self.fields_invert:
                        self.invert = True
                        num = self.model2.append()
                        self.model2.set(num, 0, word, 1, word)
                    else:
                        raise Exception(_("You cannot import this field %s, because we cannot auto-detect it"))
                break
        except:
            common.warning('Error processing your first line of the file.\nField %s is unknown !' % (word,), 'Import Error.')
        return True

    def sig_sel_all(self, widget=None):
        self.model2.clear()
        for field in self.fields.keys():
            self.model2.set(self.model2.append(), 0, self.fields[field], 1, field)

    def sig_sel(self, widget=None):
        sel = self.view1.get_selection()
        sel.selected_foreach(self._sig_sel_add)

    def _sig_sel_add(self, store, path, iter):
        num = self.model2.append()
        self.model2.set(num, 0, store.get_value(iter,0), 1, store.get_value(iter,1))

    def sig_unsel(self, widget=None):
        def _sig_sel_del(store, path, iter):
            store.remove(iter)
        (store,paths) = self.view2.get_selection().get_selected_rows()
        for p in paths:
            store.remove(store.get_iter(p))

    def sig_unsel_all(self, widget=None):
        self.model2.clear()

    def go(self):
        while True:
            button = self.win.run()
            if button == gtk.RESPONSE_OK:
                if not len(self.model2):
                    common.warning(_("You have not selected any fields to import"))
                    continue

                fields = []
                fields2 = []
                iter = self.model2.get_iter_root()
                while iter:
                    fields.append(self.model2.get_value(iter, 1))
                    fields2.append(self.model2.get_value(iter, 0))
                    iter = self.model2.iter_next(iter)

                csv = {
                    'fname': self.glade.get_widget('import_csv_file').get_filename(),
                    'sep': self.glade.get_widget('import_csv_sep').get_text(),
                    'del': self.glade.get_widget('import_csv_del').get_text(),
                    'skip': self.glade.get_widget('import_csv_skip').get_value(),
                    'combo': self.glade.get_widget('import_csv_combo').get_active_text() or 'UTF-8'
                }
                self.parent.present()
                self.win.destroy()                
                if csv['fname']:
                    if self.invert:
                        inverted = []
                        for f in fields:  
                            for key, value in self.fields_invert.items():
                                if key.encode('utf8') == f:
                                    inverted.append(value)
                        return import_csv(csv, inverted, self.model, self.fields_invert, context=self.context)
                    else:
                        return import_csv(csv, fields, self.model, self.fields, context=self.context)
                return False
            else:
                self.parent.present()
                self.win.destroy()
                return False


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

