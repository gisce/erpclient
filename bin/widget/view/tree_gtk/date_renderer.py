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

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pango
import re

import tools
import tools.datetime_util
import time

class DecoratorRenderer(gtk.GenericCellRenderer):
    def __init__(self, renderer1, callback, format):
        self.__gobject_init__()
        self.renderer1 = renderer1
        self.set_property("mode", renderer1.get_property("mode"))
        self.callback = callback
        self.format = format
        self.regex = self.initial_value = self.format
        for key,val in tools.datetime_util.date_mapping.items():
            self.regex = self.regex.replace(key, val[1])
            self.initial_value = self.initial_value.replace(key, val[0])
        self.regex = '^'+self.regex+'$'

    def _is_not_generic_property(self, name):
        return name in ('editable', 'text', 'foreground', 'background','font-desc')

    def set_property(self, name, value):
        if not self._is_not_generic_property(name):
            return super(DecoratorRenderer, self).set_property(name, value)
        else:
            return self.renderer1.set_property(name, value)

    def get_property(self, name):
        if self._is_not_generic_property(name):
            return self.renderer1.get_property(name)
        else:
            return super(DecoratorRenderer, self).get_property(name)

    def on_get_size(self, widget, cell_area=None):
        return self.renderer1.get_size(widget, cell_area)

    def on_render(self, window, widget, background_area, cell_area, expose_area, flags):
        if not isinstance(window, gtk.gdk.Window):
            return self.renderer1.render(widget.window, widget, background_area, cell_area, expose_area, flags)
        return self.renderer1.render(window, widget, background_area, cell_area, expose_area, flags)

    def on_activate(self, event, widget, path, background_area, cell_area, flags):
        return self.renderer1.activate(event, widget, path, background_area, cell_area, flags)

    def on_start_editing(self, event, widget, path, background_area, cell_area, flags):
        if not self.get_property('editable'):
            return None
        if not event:
            event = gtk.gdk.Event(gtk.keysyms.Tab)

        editable = self.renderer1.start_editing(event, widget, path, background_area, cell_area, flags)
        self.editable = editable
        self.callback.display(editable)

        if not editable.get_text():
            editable.set_text(self.initial_value)
        self.regex = re.compile(self.regex)

        assert self.regex.match(self.initial_value), 'Error, the initial value should be validated by regex'
        editable.set_width_chars(len(self.initial_value))
        editable.set_max_length(len(self.initial_value))

        editable.connect('key-press-event', self._on_key_press)


        self._interactive_input = True
        self.mode_cmd = False
        gobject.idle_add(editable.set_position, 0)
        return editable

    def _on_delete_text(self, editable, start, end):
        while (start>0) and (self.initial_value[start] not in ['_','0','X']):
            start -= 1
        text = editable.get_text()
        text = text[:start] + self.initial_value[start:end] + text[end:]
        editable.set_text(text)
        gobject.idle_add(editable.set_position, start)
        return

    def date_get(self, editable):
        tt = time.strftime(self.format, time.localtime())
        tc = editable.get_text()
        if tc==self.initial_value:
            return False
        for a in range(len(self.initial_value)):
            if self.initial_value[a] == tc[a]:
                tc = tc[:a] + tt[a] + tc[a+1:]
        try:
            editable.set_text(tc)
            return tools.datetime_util.strptime(tc, self.format)
        except:
            tc = tt
        editable.set_text(tc)
        return tools.datetime_util.strptime(tc, self.format)

    def _on_key_press(self, editable, event):
        if event.keyval in (gtk.keysyms.Tab, gtk.keysyms.Escape, gtk.keysyms.Return, gtk.keysyms.KP_Enter):
            if self.mode_cmd:
                self.mode_cmd = False
                if self.callback: self.callback.process(self, event)
                #self.stop_emission("key-press-event")
                return True
            else:
                return False
        elif event.keyval in (gtk.keysyms.KP_Add, gtk.keysyms.plus,
                              gtk.keysyms.KP_Subtract, gtk.keysyms.minus,
                              gtk.keysyms.KP_Equal, gtk.keysyms.equal):
                self.mode_cmd = True
                self.date_get(editable)
                if self.callback: self.callback.event(self, event)
                return True
        elif self.mode_cmd:
            if self.callback: self.callback.event(self, event)
            return True

        if event.keyval in (gtk.keysyms.BackSpace,):
            pos = editable.get_position()
            self._on_delete_text(editable, max(0,pos-1), pos)
            return True
        if event.keyval in (gtk.keysyms.Delete,):
            pos = editable.get_position()
            text = editable.get_text()
            self._on_delete_text(editable, pos, len(text))
            return True

        numkeys = [getattr(gtk.keysyms, '_%d' % x) for x in range(0,10)]
        numkeys += [getattr(gtk.keysyms, 'KP_%d' % x) for x in range(0,10)]

        if event.keyval in numkeys:
            pos = editable.get_position()
            text = editable.get_text()
            text = text[:pos] + event.string + text[pos + 1:]
            if self.regex.match(text):
                pos += 1
                while (pos<len(self.initial_value)) and (self.initial_value[pos] not in ['_','0','X']):
                    pos += 1
                editable.set_text(text)
                editable.show()
                gobject.idle_add(editable.set_position, pos)

        if not event.string:
            return False
        return True

    def date_set(self, dt):
        if dt:
            self.editable.set_text( dt.strftime(self.format) )
        else:
            self.editable.set_text(self.initial_value)


class date_callback(object):
    def __init__(self, treeview=None):
        self.value = ''
        self.treeview = treeview

    def event(self, widget, event):
        if event.keyval in (gtk.keysyms.BackSpace,):
            self.value = self.value[:-1]

        self.value += event.string
        self.display(widget)
        return True

    def display(self, widget):
        if self.treeview:
            if self.value:
                self.treeview.warn('misc-message', '<b>' + str(tools.to_xml(self.value))+"</b>")
            else:
                self.treeview.warn('misc-message', _("Press <i>'+'</i>, <i>'-'</i> or <i>'='</i> for special date operations."))

    def process(self, widget, event):
        if (not event) or event.keyval != gtk.keysyms.Escape:
            cmd = self.value
            for r,f in tools.datetime_util.date_operation.items():
                groups = re.match(r, cmd)
                if groups:
                    dt = widget.date_get(widget.editable)
                    if not dt:
                        dt = time.strftime(widget.format, time.localtime())
                        dt = tools.datetime_util.strptime(dt, widget.format)
                    widget.date_set(f(dt,groups))
                    break
        self.value = ''
        self.display(widget)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

