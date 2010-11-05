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
import os
import gtk
from gtk import glade

import common
import rpc
import service
import options
from form_gtk.action import action
from form_gtk.parser import Button
from interface import parser_view
import tools

class ViewWidget(object):
    def __init__(self, parent, widget, widget_name):
        self.view_form = parent
        self.widget = widget
        self.widget._view = self
        self.widget_name = widget_name

    def display(self, model, state='draft'):
        if not model:
            self.widget.display(model, False)
            return False
        modelfield = model.mgroup.mfields.get(self.widget_name, False)
        if modelfield:
            modelfield.state_set(model, state)
            if modelfield.attrs.get('attrs',False):
                modelfield.attrs_set(model)
            if hasattr(self.widget,'screen') and self.widget.screen.type in ('one2many','many2many'):
                self.widget.pager.reset_pager()
            self.widget.display(model, modelfield)
        elif isinstance(self.widget, action):
            self.widget.display(model, False)

    def reset(self, model):
        modelfield = False
        if model:
            modelfield = model.mgroup.mfields.get(self.widget_name, False)
            if modelfield and 'valid' in modelfield.get_state_attrs(model):
                modelfield.get_state_attrs(model)['valid'] = True
        self.display(model, modelfield)

    def set_value(self, model):
        if self.widget_name in model.mgroup.mfields:
            self.widget.set_value(model, model.mgroup.mfields[self.widget_name])

    def _get_model(self):
        return self.view_form.screen.current_model

    model = property(_get_model)

    def _get_modelfield(self):
        if self.model:
            return self.model.mgroup.mfields[self.widget_name]

    modelfield = property(_get_modelfield)

class ViewForm(parser_view):
    def __init__(self, window, screen, widget, children=None, state_aware_widgets=None, toolbar=None, submenu=None, help={}):
        super(ViewForm, self).__init__(window, screen, widget, children, state_aware_widgets, toolbar, submenu)
        self.view_type = 'form'
        self.model_add_new = False
        self.prev = 0
        self.flag=False
        self.current = 0
        for w in self.state_aware_widgets:
            if isinstance(w.widget, Button):
                w.widget.form = self
        self.widgets = dict([(name, ViewWidget(self, widget, name)) for name, widget in children.items()])
        sm_vbox = False
        self.help = help
        self.help_frame = False
        if self.help:
            action_tips = common.action_tips(self.help)
            self.help_frame = action_tips.help_frame
            if self.help_frame:
                vbox = gtk.VBox()
                vbox.pack_start(self.help_frame, expand=False, fill=False, padding=2)
                vbox.pack_end(self.widget)
                vbox.show_all()
                self.widget = vbox
        if submenu:
            expander = gtk.Expander("Submenus")
            sm_vbox = gtk.VBox()
            sm_hbox = gtk.HBox()
            sm_eb = gtk.EventBox()
            sm_eb.add(sm_hbox)
            sm_eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("gray"))
            expander.add(sm_eb)
            for sub in eval(submenu):
                sbutton = gtk.Button()
                icon = gtk.Image()
                file_path = os.path.realpath("icons")
                iname = sub.get('icon', 'terp-marketing').split('-')[1]
                pixbuf = gtk.gdk.pixbuf_new_from_file(file_path + '/' + iname + '.png')
                icon_set = gtk.IconSet(pixbuf)
                icon.set_from_icon_set(icon_set, gtk.ICON_SIZE_BUTTON)
                lbl = gtk.Label(sub.get('name', 'Undefined'))
                lbl.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
                hb = gtk.HBox(False, 5)
                hb.pack_start(icon, False, False)
                hb.pack_start(lbl, False, False)
                sbutton.add(hb)
                sm_hbox.pack_start(sbutton, False, False, 0)
                def _action_submenu(but, action):
                    act_id = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.model.data', 'search', [('name','=',action['action_id'])])
                    res_model = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.model.data', 'read', act_id, ['res_id'])
                    data = {}
                    context = self.screen.context
                    act = action.copy()
                    self.screen.save_current()
                    id = self.screen.current_model and self.screen.current_model.id
                    if not (id):
                        common.message(_('You must save this record to use the relate button !'))
                        return False
                    self.screen.display()
                    obj = service.LocalService('action.main')
                    if not res_model:
                        common.message(_('Action not defined !'))
                        return None
                    res = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.actions.act_window', 'read', res_model[0]['res_id'], False)
                    res['domain'] = self.screen.current_model.expr_eval(res['domain'], check_load=False)
                    res['context'] = str(self.screen.current_model.expr_eval(res['context'], check_load=False))
                    value = obj._exec_action(res, data, context)
                    self.screen.reload()
                    return value
                sbutton.connect('clicked', _action_submenu, sub)
            sm_vbox.pack_start(expander, False, False, 1)
            sm_vbox.pack_end(self.widget, True, True, 0)

        if toolbar:
            hb = gtk.HBox()
            if sm_vbox:
                hb.pack_start(sm_vbox)
            else:
                hb.pack_start(self.widget)
            tb = gtk.VBox()
            eb = gtk.EventBox()
            hb.pack_start(eb, False, False)
            eb.add(tb)
            eb.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("lightgrey"))
            self.widget = hb
            sep = False
            for icontype in ('print', 'action', 'relate'):
                if icontype in ('action','relate') and sep:
                    tb.pack_start(gtk.HSeparator(), False, False, 2)
                    sep = False
                for tool in toolbar[icontype]:
                    iconstock = {
                        'print': gtk.STOCK_PRINT,
                        'action': gtk.STOCK_EXECUTE,
                        'relate': gtk.STOCK_JUMP_TO,
                    }.get(icontype, gtk.STOCK_ABOUT)
                    icon = gtk.Image()
                    icon.set_from_stock(iconstock, gtk.ICON_SIZE_BUTTON)
                    lbl = gtk.Label(tool['string'])
                    lbl.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
                    hb = gtk.HBox(False, 5)
                    hb.pack_start(icon, False, False)
                    hb.pack_start(lbl, False, False)

                    tbutton = gtk.Button()
                    tbutton.add(hb)
                    tbutton.set_relief(gtk.RELIEF_NONE)
                    tb.pack_start(tbutton, False, False, 2)

                    def _action(button, action, type):
                        data = {}
                        context = self.screen.context
                        if 'group_by' in context:
                            del context['group_by']
                        act = action.copy()
                        if type in ('print', 'action'):
                            self.screen.save_current()
                            id = self.screen.current_model and self.screen.current_model.id
                            if not (id):
                                common.message(_('You must save this record to use the relate button !'))
                                return False
                            self.screen.display()
                            data = {
                                'model': self.screen.name,
                                'id': id,
                                'ids': [id],
                                'report_type': act.get('report_type', 'pdf'),
                            }
                        if type == 'relate':
                            id = self.screen.current_model and self.screen.current_model.id
                            if not (id):
                                common.message(_('You must select a record to use the relate button !'))
                                return False
                            if act.get('domain',False):
                                act['domain'] = self.screen.current_model.expr_eval(act['domain'], check_load=False)
                            if act.get('context',False):
                                act['context'] = str(self.screen.current_model.expr_eval(act['context'], check_load=False))
                            data = {
                                'model': self.screen.name,
                                'id': id,
                                'ids': [id],
                            }
                        obj = service.LocalService('action.main')
                        value = obj._exec_action(act, data, context)
                        if type in ('print', 'action'):
                            self.screen.reload()
                        return value

                    def _translate_label(self, event, tool, window):
                        if event.button != 3:
                            return False
                        def callback(self, tool, window):
                            lang_ids = rpc.session.rpc_exec_auth('/object',
                                    'execute', 'res.lang', 'search',
                                    [('translatable', '=', '1')])
                            if not lang_ids:
                                common.message(_('No other language available!'),
                                        parent=window)
                                return False
                            langs = rpc.session.rpc_exec_auth('/object',
                                    'execute', 'res.lang', 'read', lang_ids,
                                    ['code', 'name'])

                            win = gtk.Dialog(_('Add Translation'), window,
                                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
                            win.vbox.set_spacing(5)
                            win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
                            win.set_icon(common.OPENERP_ICON)
                            vbox = gtk.VBox(spacing=5)

                            entries_list = []
                            for lang in langs:
                                code = lang['code']
                                val = rpc.session.rpc_exec_auth('/object',
                                        'execute', tool['type'], 'read',
                                        [tool['id']], ['name'], {'lang': code})
                                val = val[0]
                                label = gtk.Label(lang['name'])
                                entry = gtk.Entry()
                                entry.set_text(val['name'])
                                entries_list.append((code, entry))
                                hbox = gtk.HBox(homogeneous=True)
                                hbox.pack_start(label, expand=False, fill=False)
                                hbox.pack_start(entry, expand=True, fill=True)
                                vbox.pack_start(hbox, expand=False, fill=True)
                            vp = gtk.Viewport()
                            vp.set_shadow_type(gtk.SHADOW_NONE)
                            vp.add(vbox)
                            sv = gtk.ScrolledWindow()
                            sv.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                            sv.set_shadow_type(gtk.SHADOW_NONE)
                            sv.add(vp)
                            win.vbox.add(sv)
                            win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
                            win.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
                            win.resize(400,200)
                            win.show_all()
                            res = win.run()
                            if res == gtk.RESPONSE_OK:
                                to_save = map(lambda x: (x[0],
                                    x[1].get_text()), entries_list)
                                while to_save:
                                    code, val = to_save.pop()
                                    rpc.session.rpc_exec_auth('/object',
                                            'execute', tool['type'],
                                            'write', [tool['id']],
                                            {'name': val}, {'lang': code})
                            window.present()
                            win.destroy()
                            return res
                        menu = gtk.Menu()
                        item = gtk.ImageMenuItem(_('Translate label'))
                        item.connect("activate", callback, tool, window)
                        item.set_sensitive(1)
                        item.show()
                        menu.append(item)
                        menu.popup(None,None,None,event.button,event.time)
                        return True
                    tbutton.connect('clicked', _action, tool, icontype)
                    tbutton.connect('button_press_event', _translate_label, tool, self.window)
                    sep = True

    def __getitem__(self, name):
        return self.widgets[name]

    def destroy(self):
        self.widget.destroy()
        for widget in self.widgets.keys():
            self.widgets[widget].widget.destroy()
            del self.widgets[widget]
        del self.widget
        del self.widgets
        del self.screen
        del self.state_aware_widgets

    def cancel(self):
        pass

    def set_value(self):
        model = self.screen.current_model
        if model:
            for widget in self.widgets.values():
                widget.set_value(model)

    def sel_ids_get(self):
        if self.screen.current_model:
            return [self.screen.current_model.id]
        return []

    def sel_models_get(self):
        if self.screen.current_model:
            return [self.screen.current_model]
        return []

    def reset(self):
        model = self.screen.current_model
        for wid_name, widget in self.widgets.items():
            widget.reset(model)

    def signal_record_changed(self, *args):
        pass

    def attrs_set(self, model, obj, att_obj, notebook, rank):
        try:
            attrs_changes = eval(att_obj.attrs.get('attrs',"{}"))
        except:
             model.value.update({'uid':rpc.session.uid})
             attrs_changes = eval(att_obj.attrs.get('attrs',"{}"),model.value)
             for k,v in attrs_changes.items():
                for i in range(0,len(v)):
                   if v[i][2]:
                        if type(v[i][2])==type([]):
                            cond=()
                            cond=v[i][0],v[i][1],v[i][2][0]
                            attrs_changes[k][i]=cond
        for k,v in attrs_changes.items():
            result = True
            for condition in v:
                result = result and tools.calc_condition(self,model,condition)
            if result:
                if k=='invisible':
                    obj.hide()
                if k=='focus':
                    notebook.set_current_page(rank)
                elif k=='readonly':
                    obj.set_sensitive(False)
            else:
                if k=='invisible':
                    obj.show()
                if k=='readonly':
                    obj.set_sensitive(True)

    def set_notebook(self,model,nb,focus_widget=None):
        for i in range(0,nb.get_n_pages()):
            page = nb.get_nth_page(i)
            if focus_widget:
                if focus_widget.widget.widget.is_ancestor(page):
                    nb.set_current_page(i)
                focus_widget.widget.grab_focus()
            children_notebooks = page.get_children()
            for child in children_notebooks:
                if isinstance(child,gtk.Notebook):
                    self.set_notebook(model,child)
            if nb.get_tab_label(page).attrs.get('attrs',False):
                self.attrs_set(model, page, nb.get_tab_label(page), nb, i)

    def display(self):
        model = self.screen.current_model
        for x in self.widget.get_children():
            if (type(x)==gtk.Table):
                for y in x.get_children():
                    if type(y)==gtk.Notebook:
                        self.set_notebook(model,y)
            elif type(x)==gtk.Notebook:
                self.set_notebook(model,x)
        if model and ('state' in model.mgroup.fields):
            state = model['state'].get(model)
        else:
            state = 'draft'
        button_focus = field_focus = None
        for widget in self.widgets.values():
            widget.display(model, state)
            if widget.widget.attrs.get('focus_field'):
                field_focus =  widget.widget

        for widget in self.state_aware_widgets:
            widget.state_set(state)
            widget.attrs_set(model)
            if widget.widget.attrs.get('focus_button'):
                button_focus =  widget.widget

        if field_focus:
            field_focus.grab_focus()

        if button_focus:
            self.screen.window.set_default(button_focus.widget)
            if not field_focus:
                button_focus.grab_focus()
        return True

    def set_cursor(self, new=False):
        focus_widget = None
        model = self.screen.current_model
        position = 0
        position = len(self.widgets)
        if model:
            for widgets in self.widgets.values():
                modelfield = model.mgroup.mfields.get(widgets.widget_name, None)
                if not modelfield:
                    continue
                if not modelfield.get_state_attrs(model).get('valid', True):
                     if widgets.widget.position > position:
                          continue
                     position = widgets.widget.position
                     focus_widget = widgets
            for x in self.widget.get_children():
                if (type(x)==gtk.Table):
                    for y in x.get_children():
                        if type(y)==gtk.Notebook:
                            self.set_notebook(model,y,focus_widget)
                elif type(x)==gtk.Notebook:
                    self.set_notebook(model,x,focus_widget)
        return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

