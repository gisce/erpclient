# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
import tools
import wid_int

class filter(wid_int.wid_int):
    def __init__(self, name, parent, attrs={}, call=None):
        wid_int.wid_int.__init__(self, name, parent, attrs,call)
        if name:
            self.butt = gtk.ToggleButton(name)
            if len(name) < 10:
                self.butt.set_size_request(90,-1)
        else:
            self.butt = gtk.ToggleButton()
            self.butt.set_relief(gtk.RELIEF_NONE)
        icon = gtk.Image()
        icon.set_from_stock(attrs.get('icon','gtk-home'), 1)
        self.butt.set_image(icon)
        self.butt.set_image_position(gtk.POS_TOP)
        self.butt.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse("grey"))
        self.butt.modify_bg(gtk.STATE_PRELIGHT, gtk.gdk.color_parse("light grey"))
        help = attrs.get('help', False) or attrs.get('string', False)
        if help:
            self.butt.set_tooltip_markup(tools.to_xml(help))
        self.domain = attrs.get('domain', "[]")
        self.context = attrs.get('context', "{}")
        if self.default_search:
            self.butt.set_active(True)
        self.butt.set_alignment(0.5, 0.5)
        self.butt.connect('toggled', call[1])
        self.screen_context = call[0].context
        self.widget = self.butt

    def _value_get(self):
        if not self.butt.get_active():
            ctx = tools.expr_eval(self.context, {'context':self.screen_context})
            group = ctx.get('group_by',False)
            if group:
                return {'context': {'remove_group':group}}
            return {}
        return {'domain': tools.expr_eval(self.domain, {'context':self.screen_context}),
            'context': tools.expr_eval(self.context, {'context':self.screen_context})}

    def sig_exec(self, widget):
        pass

    def clear(self):
        self.butt.set_active(False)

    def _value_set(self, value):
        pass
    value = property(_value_get, _value_set, None,
      'The content of the widget or ValueError if not valid')


