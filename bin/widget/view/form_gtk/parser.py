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

import tools
import interface

import widget.view.interface
from observator import oregistry, Observable

import gtk

import common
import service
import rpc

import copy

import options


class Button(Observable):
    def __init__(self, attrs={}):
        super(Button, self).__init__()
        self.attrs = attrs
        args = {
            'label': attrs.get('string', 'unknown')
        }
        self.widget = gtk.Button(**args)

        readonly = bool(int(attrs.get('readonly', '0')))
        self.set_sensitive(not readonly)

        if attrs.get('icon', False):
            try:
                stock = attrs['icon']
                icon = gtk.Image()
                icon.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
                self.widget.set_image(icon)
            except Exception,e:
                import logging
                log = logging.getLogger('common')
                log.warning(_('Wrong icon for the button !'))
#           self.widget.set_use_stock(True)
#       self.widget.set_label(args['label'])

        self.widget.show()
        self.widget.connect('clicked', self.button_clicked)

    def hide(self):
        return self.widget.hide()

    def show(self):
        return self.widget.show()

    def set_sensitive(self, value):
        return self.widget.set_sensitive(value)

    def button_clicked(self, widget):
        model = self.form.screen.current_model
        self.form.set_value()
        button_type = self.attrs.get('special', '')

        if button_type=='cancel':
            self.form.screen.window.destroy()
            if 'name' in self.attrs.keys():
                type_button = self.attrs.get('type','object')

                if type_button == 'action':
                    obj = service.LocalService('action.main')
                    action_id = int(self.attrs['name'])

                    context_action = self.form.screen.context.copy()
                    
                    if 'context' in self.attrs:
                        context_action.update(self.form.screen.current_model.expr_eval(self.attrs['context'], check_load=False))

                    obj.execute(action_id, {'model':self.form.screen.name, 'id': False, 'ids': [], 'report_type': 'pdf'}, context=context_action)

                elif type_button == 'object':
                    result = rpc.session.rpc_exec_auth(
                                '/object', 'execute',
                                self.form.screen.name,
                                self.attrs['name'],[], model.context_get())
                    datas = {}
                    obj = service.LocalService('action.main')
                    obj._exec_action(result,datas,context=self.form.screen.context)
                else:
                    raise Exception, 'Unallowed button type'
                
        elif model.validate():
            id = self.form.screen.save_current()
            if not self.attrs.get('confirm',False) or \
                    common.sur(self.attrs['confirm']):
                button_type = self.attrs.get('type', 'workflow')
                if button_type == 'workflow':
                    result = rpc.session.rpc_exec_auth('/object', 'exec_workflow',
                                            self.form.screen.name,
                                            self.attrs['name'], id)
                    if type(result)==type({}):
                        if result['type']== 'ir.actions.act_window_close':
                            self.form.screen.window.destroy()
                        else:
                            datas = {'ids':[id]}
                            obj = service.LocalService('action.main')
                            obj._exec_action(result, datas)
                    elif type([]) == type(result):
                        datas = {'ids' : [id], 'model' : self.form.screen.name, }
                        obj = service.LocalService('action.main')
                        for rs in result:
                            obj._exec_action(rs, datas)

                elif button_type == 'object':
                    if not id:
                        return
                    context = model.context_get()
                    if 'context' in self.attrs:
                        context.update(self.form.screen.current_model.expr_eval(self.attrs['context'], check_load=False))

                    result = rpc.session.rpc_exec_auth(
                        '/object', 'execute',
                        self.form.screen.name,
                        self.attrs['name'],
                        [id], context
                    )
                    if type(result)==type({}):
                        self.form.screen.window.destroy()
                        datas = {'ids' : [id], 'model' : self.form.screen.name, }
                        obj = service.LocalService('action.main')
                        obj._exec_action(result,datas,context=self.form.screen.context)

                elif button_type == 'action':
                    obj = service.LocalService('action.main')
                    action_id = int(self.attrs['name'])

                    context = self.form.screen.context.copy()

                    if 'context' in self.attrs:
                        context.update(self.form.screen.current_model.expr_eval(self.attrs['context'], check_load=False))

                    obj.execute(action_id, {'model':self.form.screen.name, 'id': id or False, 'ids': id and [id] or [], 'report_type': 'pdf'}, context=context)

                else:
                    raise Exception, 'Unallowed button type'
                self.form.screen.reload()
                self.warn('misc-message', '')
        else:
            common.warning(_('Invalid form, correct red fields !'), _('Error !') )
            self.warn('misc-message', _('Invalid form, correct red fields !'), "red")
            self.form.screen.display()



class StateAwareWidget(object):
    def __init__(self, widget, states=None):
        self.widget = widget
        self.states = states or []

    def __getattr__(self, a):
        return self.widget.__getattribute__(a)

    def state_set(self, state):
        if (not len(self.states)) or (state in self.states):
            self.widget.show()
        else:
            self.widget.hide()

    def attrs_set(self, model):
        sa = hasattr(self.widget, 'attrs') and self.widget.attrs or {}
        attrs_changes = eval(sa.get('attrs',"{}"))
        for k,v in attrs_changes.items():
            result = True
            for condition in v:
                result = result and tools.calc_condition(self,model,condition)
                    
            if result:
                if k=='invisible':
                    self.widget.hide()
                elif k=='readonly':
                    self.widget.set_sensitive(False)
                else:
                    self.widget.set_sensitive(False and sa.get('readonly',False))
            else:
                if k=='readonly':
                    self.widget.set_sensitive(True)
                if k=='invisible':
                    self.widget.show()        


class _container(object):
    def __init__(self):
        self.cont = []
        self.col = []
        self.sg = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        self.trans_box = []
        self.trans_box_label = []

    def new(self, col=4):
        table = gtk.Table(1, col)
        table.set_homogeneous(False)
        table.set_col_spacings(3)
        table.set_row_spacings(0)
        table.set_border_width(1)
        self.cont.append( (table, 0, 0) )
        self.col.append( col )

    def get(self):
        return self.cont[-1][0]

    def pop(self):
        (table, x, y) = self.cont.pop()
        self.col.pop()
        return table

    def newline(self):
        (table, x, y) = self.cont[-1]
        if x>0:
            self.cont[-1] = (table, 0, y+1)
        table.resize(y+1,self.col[-1])

    def wid_add(self, widget, name=None, expand=False, ypadding=2, rowspan=1,
            colspan=1, translate=False, fname=None, help=False, fill=False, invisible=False):
        (table, x, y) = self.cont[-1]
        if colspan>self.col[-1]:
            colspan=self.col[-1]
        a = name and 1 or 0
        if colspan+x+a>self.col[-1]:
            self.newline()
            (table, x, y) = self.cont[-1]
        yopt = False
        if expand:
            yopt = yopt | gtk.EXPAND
        if fill:
            yopt = yopt | gtk.FILL
        if colspan == 1 and a == 1:
            colspan = 2
        if name:
            label = gtk.Label(name)
            eb = gtk.EventBox()
            eb.set_events(gtk.gdk.BUTTON_PRESS_MASK)
            self.trans_box_label.append((eb, name, fname))
            eb.add(label)
            if help:
                try:
                    eb.set_tooltip_markup('<span foreground=\"darkred\"><b>'+tools.to_xml(name)+'</b></span>\n'+tools.to_xml(help))
                except:
                    pass
                label.set_markup("<sup><span foreground=\"darkgreen\">?</span></sup>"+tools.to_xml(name))
                eb.show()
            if '_' in name:
                label.set_text_with_mnemonic(name)
                label.set_mnemonic_widget(widget)
            label.set_alignment(1.0, 0.5)
            table.attach(eb, x, x+1, y, y+rowspan, yoptions=yopt,
                    xoptions=gtk.FILL, ypadding=ypadding, xpadding=2)
        hbox = widget
        hbox.show_all()
        if translate:
            hbox = gtk.HBox(spacing=3)
            hbox.pack_start(widget)
            img = gtk.Image()
            img.set_from_stock('terp-translate', gtk.ICON_SIZE_MENU)
            ebox = gtk.EventBox()
            ebox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
            self.trans_box.append((ebox, name, fname, widget))

            ebox.add(img)
            hbox.pack_start(ebox, fill=False, expand=False)
            hbox.show_all()
        table.attach(hbox, x+a, x+colspan, y, y+rowspan, yoptions=yopt,
                ypadding=ypadding, xpadding=2)
        self.cont[-1] = (table, x+colspan, y)
        wid_list = table.get_children()
        wid_list.reverse()
        table.set_focus_chain(wid_list)
        if invisible:
            hbox.hide()

class parser_form(widget.view.interface.parser_interface):
    def parse(self, model, root_node, fields, notebook=None, paned=None):
        dict_widget = {}
        saw_list = []   # state aware widget list
        attrs = tools.node_attributes(root_node)
        on_write = attrs.get('on_write', '')
        container = _container()
        container.new(col=int(attrs.get('col', 4)))
        self.container = container

        if not self.title:
            attrs = tools.node_attributes(root_node)
            self.title = attrs.get('string', 'Unknown')

        for node in root_node.childNodes:
            if not node.nodeType==node.ELEMENT_NODE:
                continue
            attrs = tools.node_attributes(node)
            if node.localName=='image':
                icon = gtk.Image()
                icon.set_from_stock(attrs['name'], gtk.ICON_SIZE_DIALOG)
                container.wid_add(icon,colspan=int(attrs.get('colspan',1)),expand=int(attrs.get('expand',0)), ypadding=10, help=attrs.get('help', False), fill=int(attrs.get('fill', 0)))
            elif node.localName=='separator':
                vbox = gtk.VBox()
                if 'string' in attrs:
                    text = attrs.get('string', 'No String Attr.')
                    l = gtk.Label('<b>'+(text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;'))+'</b>')
                    l.set_use_markup(True)
                    l.set_alignment(0.0, 0.5)
                    eb = gtk.EventBox()
                    eb.set_events(gtk.gdk.BUTTON_PRESS_MASK)
                    eb.add(l)
                    container.trans_box_label.append((eb, text, None))
                    vbox.pack_start(eb)
                vbox.pack_start(gtk.HSeparator())
                container.wid_add(vbox,colspan=int(attrs.get('colspan',1)),expand=int(attrs.get('expand',0)), ypadding=10, help=attrs.get('help', False), fill=int(attrs.get('fill', 0)))
            elif node.localName=='label':
                text = attrs.get('string', '')
                if not text:
                    for node in node.childNodes:
                        if node.nodeType == node.TEXT_NODE:
                            text += node.data
                        else:
                            text += node.toxml()
                label = gtk.Label(text)
                label.set_use_markup(True)
                if 'align' in attrs:
                    label.set_alignment(float(attrs['align'] or 0.0), 0.5)
                eb = gtk.EventBox()
                eb.set_events(gtk.gdk.BUTTON_PRESS_MASK)
                eb.add(label)
                container.trans_box_label.append((eb, text, None))

                if 'angle' not in attrs:
                    label.set_line_wrap(True)
                    label.set_angle(int(attrs.get('angle', 0)))

                container.wid_add(
                    eb,
                    colspan=int(attrs.get('colspan', 1)),
                    expand=False,
                    help=attrs.get('help', False),
                    fill=int(attrs.get('fill', 0))
                )

            elif node.localName=='newline':
                container.newline()

            elif node.localName=='button':
                if attrs.get('invisible', False):
                    visval = eval(attrs['invisible'], {'context':self.screen.context})
                    if visval:
                        continue
                button = Button(attrs)
                states = [e for e in attrs.get('states','').split(',') if e]
                saw_list.append(StateAwareWidget(button, states))
                container.wid_add(button.widget, colspan=int(attrs.get('colspan', 1)), help=attrs.get('help', False))

            elif node.localName=='notebook':
                if attrs.get('invisible', False):
                    visval = eval(attrs['invisible'], {'context':self.screen.context})
                    if visval:
                        continue
                nb = gtk.Notebook()
                if attrs and 'tabpos' in attrs:
                    pos = {'up':gtk.POS_TOP,
                        'down':gtk.POS_BOTTOM,
                        'left':gtk.POS_LEFT,
                        'right':gtk.POS_RIGHT
                    }[attrs['tabpos']]
                else:
                    if options.options['client.form_tab'] == 'top':
                        pos = gtk.POS_TOP
                    elif options.options['client.form_tab'] == 'left':
                        pos = gtk.POS_LEFT
                    elif options.options['client.form_tab'] == 'right':
                        pos = gtk.POS_RIGHT
                    elif options.options['client.form_tab'] == 'bottom':
                        pos = gtk.POS_BOTTOM
                nb.set_tab_pos(pos)
                nb.set_border_width(3)
                container.wid_add(nb, colspan=attrs.get('colspan', 3), expand=True, fill=True )
                _, widgets, saws, on_write = self.parse(model, node, fields, nb)
                saw_list += saws
                dict_widget.update(widgets)

            elif node.localName=='page':
                if attrs.get('invisible', False):
                    visval = eval(attrs['invisible'], {'context':self.screen.context})
                    if visval:
                        continue
                if attrs and 'angle' in attrs:
                    angle = int(attrs['angle'])
                else:
                    angle = int(options.options['client.form_tab_orientation'])
                l = gtk.Label(attrs.get('string','No String Attr.'))
                l.attrs=attrs.copy()
                l.set_angle(angle)
                widget, widgets, saws, on_write = self.parse(model, node, fields, notebook)
                saw_list += saws
                dict_widget.update(widgets)
                notebook.append_page(widget, l)

            elif node.localName=='field':
                name = str(attrs['name'])
                del attrs['name']
                name = unicode(name)
                type = attrs.get('widget', fields[name]['type'])
                fields[name].update(attrs)
                fields[name]['model']=model
                if not type in widgets_type:
                    continue

                fields[name]['name'] = name
                if 'saves' in attrs:
                    fields[name]['saves'] = attrs['saves']

                if 'filename' in attrs:
                    fields[name]['filename'] = attrs['filename']

                widget_act = widgets_type[type][0](self.window, self.parent, model, fields[name])
                label = None
                if not int(attrs.get('nolabel', 0)):
                    # TODO space before ':' depends of lang (ex: english no space)
                    if gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL:
                        label = ': '+fields[name]['string']
                    else:
                        label = fields[name]['string']+' :'
                dict_widget[name] = widget_act
                size = int(attrs.get('colspan', widgets_type[ type ][1]))
                expand = widgets_type[ type ][2]
                fill = widgets_type[ type ][3]
                hlp = fields[name].get('help', attrs.get('help', False))
                if attrs.get('height', False) or attrs.get('width', False):
                    widget_act.widget.set_size_request(
                            int(attrs.get('width', -1)), int(attrs.get('height', -1)))
                if attrs.get('invisible', False):
                    visval = eval(attrs['invisible'], {'context':self.screen.context})
                    if visval:
                        continue
                container.wid_add(widget_act.widget, label, expand, translate=fields[name].get('translate',False), colspan=size, fname=name, help=hlp, fill=fill)

            elif node.localName=='group':
                frame = gtk.Frame(attrs.get('string', None))
                frame.attrs=attrs
                frame.set_border_width(0)
                states = [e for e in attrs.get('states','').split(',') if e]
                if attrs.get('invisible', False):
                    visval = eval(attrs['invisible'], {'context':self.screen.context})
                    if visval:
                        continue
                saw_list.append(StateAwareWidget(frame, states))

                container.wid_add(frame, colspan=int(attrs.get('colspan', 1)), expand=int(attrs.get('expand',0)), rowspan=int(attrs.get('rowspan', 1)), ypadding=0, fill=int(attrs.get('fill', 1)))
                container.new(int(attrs.get('col',4)))

                widget, widgets, saws, on_write = self.parse(model, node, fields)
                dict_widget.update(widgets)
                saw_list += saws
                frame.add(widget)
                if not attrs.get('string', None):
                    frame.set_shadow_type(gtk.SHADOW_NONE)
                    container.get().set_border_width(0)
                container.pop()
            elif node.localName=='hpaned':
                hp = gtk.HPaned()
                container.wid_add(hp, colspan=int(attrs.get('colspan', 4)), expand=True, fill=True)
                _, widgets, saws, on_write = self.parse(model, node, fields, paned=hp)
                saw_list += saws
                dict_widget.update(widgets)
                #if 'position' in attrs:
                #   hp.set_position(int(attrs['position']))
            elif node.localName=='vpaned':
                hp = gtk.VPaned()
                container.wid_add(hp, colspan=int(attrs.get('colspan', 4)), expand=True, fill=True)
                _, widgets, saws, on_write = self.parse(model, node, fields, paned=hp)
                saw_list += saws
                dict_widget.update(widgets)
                if 'position' in attrs:
                    hp.set_position(int(attrs['position']))
            elif node.localName=='child1':
                widget, widgets, saws, on_write = self.parse(model, node, fields, paned=paned)
                saw_list += saws
                dict_widget.update(widgets)
                paned.pack1(widget, resize=True, shrink=True)
            elif node.localName=='child2':
                widget, widgets, saws, on_write = self.parse(model, node, fields, paned=paned)
                saw_list += saws
                dict_widget.update(widgets)
                paned.pack2(widget, resize=True, shrink=True)
            elif node.localName=='action':
                from action import action
                name = str(attrs['name'])
                widget_act = action(self.window, self.parent, model, attrs)
                dict_widget[name] = widget_act
                container.wid_add(widget_act.widget, colspan=int(attrs.get('colspan', 3)), expand=True, fill=True)
        for (ebox,src,name,widget) in container.trans_box:
            ebox.connect('button_press_event',self.translate, model, name, src, widget, self.screen, self.window)
        for (ebox,src,name) in container.trans_box_label:
            ebox.connect('button_press_event', self.translate_label, model, name, src, self.window)
        return container.pop(), dict_widget, saw_list, on_write

    def translate(self, widget, event, model, name, src, widget_entry, screen, window):
        
        #widget accessor functions
        def value_get(widget):
            if type(widget) == type(gtk.Entry()):
                return widget.get_text()
            elif type(widget.child) == type(gtk.TextView()):
                buffer = widget.child.get_buffer()
                iter_start = buffer.get_start_iter()
                iter_end = buffer.get_end_iter()
                return buffer.get_text(iter_start,iter_end,False)
            else:
                return None

        def value_set(widget, value):
            if type(widget) == type(gtk.Entry()):
                widget.set_text(value)
            elif type(widget.child) == type(gtk.TextView()):
                if value==False:
                    value=''
                buffer = widget.child.get_buffer()
                buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
                iter_start = buffer.get_start_iter()
                buffer.insert(iter_start, value)

        def widget_duplicate(widget):
            if type(widget) == type(gtk.Entry()):
                entry = gtk.Entry()
                entry.set_property('activates_default', True)
                entry.set_max_length(widget.get_max_length())
                entry.set_width_chars(widget.get_width_chars())
                return entry, gtk.FILL
            elif type(widget.child) == type(gtk.TextView()):
                tv = gtk.TextView()
                tv.set_wrap_mode(gtk.WRAP_WORD)
                sw = gtk.ScrolledWindow()
                sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
                sw.set_shadow_type(gtk.SHADOW_NONE)
                sw.set_size_request(-1, 80)
                sw.add(tv)
                tv.set_accepts_tab(False)
                return sw, gtk.FILL | gtk.EXPAND
            else:
                return None, False
            
        if not value_get(widget_entry):
            common.message(
                    _('Enter some text to the related field before adding translations!'),
                    parent=self.window)
            return False
        
        id = screen.current_model.id
        if not id:
            common.message(
                    _('You need to save resource before adding translations!'),
                    parent=self.window)
            return False
        id = screen.current_model.save(reload=False)
        uid = rpc.session.uid

        lang_ids = rpc.session.rpc_exec_auth('/object', 'execute', 'res.lang',
                'search', [('translatable','=','1')])
        if not lang_ids:
            common.message(_('No other language available!'),
                    parent=window)
            return False
        langs = rpc.session.rpc_exec_auth('/object', 'execute', 'res.lang',
                'read', lang_ids, ['code', 'name'])

        code = rpc.session.context.get('lang', 'en_US')

        #change 'en' to false for context
        def adapt_context(val):
            if val == 'en_US':
                return False
            else:
                return val


        win = gtk.Dialog(_('Add Translation'), window,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        win.vbox.set_spacing(5)
        win.set_property('default-width', 600)
        win.set_property('default-height', 400)
        win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        win.set_icon(common.OPENERP_ICON)

        accel_group = gtk.AccelGroup()
        win.add_accel_group(accel_group)

        but_cancel = win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        but_cancel.add_accelerator('clicked', accel_group, gtk.keysyms.Escape,
                gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        but_ok = win.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        but_ok.add_accelerator('clicked', accel_group, gtk.keysyms.Return,
                gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        vbox = gtk.VBox(spacing=5)

        entries_list = []
        table = gtk.Table(len(langs), 2)
        table.set_homogeneous(False)
        table.set_col_spacings(3)
        table.set_row_spacings(0)
        table.set_border_width(1)
        i = 0
        for lang in langs:
            context = copy.copy(rpc.session.context)
            context['lang'] = adapt_context(lang['code'])
            val = rpc.session.rpc_exec_auth('/object', 'execute', model,
                    'read', [id], [name], context)
            val = val[0]
            #TODO space before ':' depends of lang (ex: english no space)
            if gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL:
                label = gtk.Label(': ' + lang['name'])
            else:
                label = gtk.Label(lang['name'] + ' :')
            label.set_alignment(1.0, 0.5)
            (entry, yoptions) = widget_duplicate(widget_entry)

            hbox = gtk.HBox(homogeneous=False)
            if code == lang['code']:
                value_set(entry,value_get(widget_entry))
            else:
                value_set(entry,val[name])

            entries_list.append((val['id'], lang['code'], entry))
            table.attach(label, 0, 1, i, i+1, yoptions=False, xoptions=gtk.FILL,
                    ypadding=2, xpadding=5)
            table.attach(entry, 1, 2, i, i+1, yoptions=yoptions,
                    ypadding=2, xpadding=5)
            i += 1

        vbox.pack_start(table)
        vp = gtk.Viewport()
        vp.set_shadow_type(gtk.SHADOW_NONE)
        vp.add(vbox)
        sv = gtk.ScrolledWindow()
        sv.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC )
        sv.set_shadow_type(gtk.SHADOW_NONE)
        sv.add(vp)
        win.vbox.add(sv)
        win.show_all()

        ok = False
        data = []
        while not ok:
            response = win.run()
            ok = True
            if response == gtk.RESPONSE_OK:
                to_save = map(lambda x : (x[0], x[1], value_get(x[2])),
                        entries_list)
                while to_save != []:
                    new_val = {}
                    new_val['id'],new_val['code'], new_val['value'] = to_save.pop()
                    #update form field
                    if new_val['code'] == code:
                        value_set(widget_entry, new_val['value'])
                    context = copy.copy(rpc.session.context)
                    context['lang'] = adapt_context(new_val['code'])
                    rpc.session.rpc_exec_auth('/object', 'execute', model,
                            'write', [id], {str(name):  new_val['value']},
                            context)
            if response == gtk.RESPONSE_CANCEL:
                window.present()
                win.destroy()
                return
        screen.current_model.reload()
        window.present()
        win.destroy()
        return True

    def translate_label(self, widget, event, model, name, src, window):
        def callback_label(self, widget, event, model, name, src, window=None):
            lang_ids = rpc.session.rpc_exec_auth('/object', 'execute',
                    'res.lang', 'search', [('translatable', '=', '1')])
            if not lang_ids:
                common.message(_('No other language available!'),
                        parent=window)
                return False
            langs = rpc.session.rpc_exec_auth('/object', 'execute', 'res.lang',
                    'read', lang_ids, ['code', 'name'])

            win = gtk.Dialog(_('Add Translation'), window,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
            win.vbox.set_spacing(5)
            win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            win.set_icon(common.OPENERP_ICON)
            vbox = gtk.VBox(spacing=5)

            entries_list = []
            for lang in langs:
                code=lang['code']
                val = rpc.session.rpc_exec_auth('/object', 'execute', model,
                        'read_string', False, [code], [name])
                if val and code in val:
                    val = val[code]
                else:
                    val={'code': code, 'name': src}
                label = gtk.Label(lang['name'])
                entry = gtk.Entry()
                entry.set_text(val[name])
                entries_list.append((code, entry))
                hbox = gtk.HBox(homogeneous=True)
                hbox.pack_start(label, expand=False, fill=False)
                hbox.pack_start(entry, expand=True, fill=True)
                vbox.pack_start(hbox, expand=False, fill=True)
            vp = gtk.Viewport()
            vp.set_shadow_type(gtk.SHADOW_NONE)
            vp.add(vbox)
            sv = gtk.ScrolledWindow()
            sv.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC )
            sv.set_shadow_type(gtk.SHADOW_NONE)
            sv.add(vp)
            win.vbox.add(sv)
            win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            win.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            win.resize(400,200)
            win.show_all()
            res = win.run()
            if res == gtk.RESPONSE_OK:
                to_save = map(lambda x: (x[0], x[1].get_text()), entries_list)
                while to_save:
                    code, val = to_save.pop()
                    rpc.session.rpc_exec_auth('/object', 'execute', model,
                            'write_string', False, [code], {name: val})
            window.present()
            win.destroy()
            return res

        def callback_view(self, widget, event, model, src, window=None):
            lang_ids = rpc.session.rpc_exec_auth('/object', 'execute',
                    'res.lang', 'search', [('translatable', '=', '1')])
            if not lang_ids:
                common.message(_('No other language available!'),
                        parent=window)
                return False
            langs = rpc.session.rpc_exec_auth('/object', 'execute', 'res.lang',
                    'read', lang_ids, ['code', 'name'])

            win = gtk.Dialog(_('Add Translation'), window,
                    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
            win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
            win.set_icon(common.OPENERP_ICON)
            win.vbox.set_spacing(5)
            vbox = gtk.VBox(spacing=5)

            entries_list = []
            for lang in langs:
                code=lang['code']
                view_item_ids = rpc.session.rpc_exec_auth('/object', 'execute',
                        'ir.translation', 'search', [
                            ('name', '=', model),
                            ('type', '=', 'view'),
                            ('lang', '=', code),
                            ])
                view_items = rpc.session.rpc_exec_auth('/object', 'execute',
                        'ir.translation', 'read', view_item_ids,
                        ['src', 'value'])
                label = gtk.Label(lang['name'])
                vbox.pack_start(label, expand=False, fill=True)
                for val in view_items:
                    label = gtk.Label(val['src'])
                    entry = gtk.Entry()
                    entry.set_text(val['value'])
                    entries_list.append((val['id'], entry))
                    hbox = gtk.HBox(homogeneous=True)
                    hbox.pack_start(label, expand=False, fill=False)
                    hbox.pack_start(entry, expand=True, fill=True)
                    vbox.pack_start(hbox, expand=False, fill=True)
            vp = gtk.Viewport()
            vp.set_shadow_type(gtk.SHADOW_NONE)
            vp.add(vbox)
            sv = gtk.ScrolledWindow()
            sv.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC )
            sv.set_shadow_type(gtk.SHADOW_NONE)
            sv.add(vp)
            win.vbox.add(sv)
            win.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            win.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
            win.resize(400,200)
            win.show_all()
            res = win.run()
            if res == gtk.RESPONSE_OK:
                to_save = map(lambda x: (x[0], x[1].get_text()), entries_list)
                while to_save:
                    id, val = to_save.pop()
                    rpc.session.rpc_exec_auth('/object', 'execute',
                            'ir.translation', 'write', [id], {'value': val})
            window.present()
            win.destroy()
            return res
        if event.button != 3:
            return
        menu = gtk.Menu()
        if name:
            item = gtk.ImageMenuItem(_('Translate label'))
            item.connect("activate", callback_label, widget, event, model,
                    name, src, window)
            item.set_sensitive(1)
            item.show()
            menu.append(item)
        item = gtk.ImageMenuItem(_('Translate view'))
        item.connect("activate", callback_view, widget, event, model, src, window)
        item.set_sensitive(1)
        item.show()
        menu.append(item)
        menu.popup(None,None,None,event.button,event.time)
        return True

import float_time
import calendar
import spinbutton
import spinint
import char
import checkbox
import button
import reference
import binary
import textbox
import textbox_tag
#import one2many
import many2many
import many2one
import selection
import one2many_list
import picture
import url
import image

import progressbar

widgets_type = {
    'date': (calendar.calendar, 1, False, False),
    'time': (calendar.stime, 1, False, False),
    'datetime': (calendar.datetime, 1, False, False),
    'float': (spinbutton.spinbutton, 1, False, False),
    'integer': (spinint.spinint, 1, False, False),
    'selection': (selection.selection, 1, False, False),
    'char': (char.char, 1, False, False),
    'float_time': (float_time.float_time, 1, False, False),
    'boolean': (checkbox.checkbox, 1, False, False),
    'button': (button.button, 1, False, False),
    'reference': (reference.reference, 1, False, False),
    'binary': (binary.wid_binary, 1, False, False),
    'picture': (picture.wid_picture, 1, False, False),
    'text': (textbox.textbox, 1, True, True),
    'text_wiki': (textbox.textbox, 1, True, True),
    'text_tag': (textbox_tag.textbox_tag, 1, True, True),
    'one2many': (one2many_list.one2many_list, 1, True, True),
    'one2many_form': (one2many_list.one2many_list, 1, True, True),
    'one2many_list': (one2many_list.one2many_list, 1, True, True),
    'many2many': (many2many.many2many, 1, True, True),
    'many2one': (many2one.many2one, 1, False, False),
    'email' : (url.email, 1, False, False),
    'url' : (url.url, 1, False, False),
    'callto' : (url.callto, 1, False, False),
    'sip' : (url.sip, 1, False, False),
    'image' : (image.image_wid, 1, False, False),
    'uri' : (url.uri, 1, False, False),
    'progressbar' : (progressbar.progressbar, 1, False, False),
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

