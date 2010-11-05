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
from datetime import datetime
import gettext
from gtk import glade

import tools
import wid_int
import common

DT_FORMAT = '%Y-%m-%d'
DHM_FORMAT = '%Y-%m-%d %H:%M:%S'

class custom_filter(wid_int.wid_int):
    def __init__(self, name, parent, attrs={}, call=None):
        wid_int.wid_int.__init__(self, name, parent, attrs)
        win_gl = glade.XML(common.terp_path("openerp.glade"),"hbox_custom_filter",gettext.textdomain())
        self.widget = win_gl.get_widget('hbox_custom_filter')

        # Processing fields
        self.combo_fields = win_gl.get_widget('combo_fields')
        self.field_selection = {}

        fields = attrs.get('fields',None)
        for item in fields:
            self.field_selection[item[1]] = (item[0], item[2], item[3])
            self.combo_fields.append_text(item[1])

        self.combo_fields.set_active(0)

        # Processing operator combo
        self.combo_op = win_gl.get_widget('combo_operator')
        self.op_selection = {}

        for item in (['ilike', _('contains')],
                ['not ilike', _('doesn\'t contain')],
                ['=', _('is equal to')],
                ['<>',_('is not equal to')],
                ['>',_('greater than')],
                ['<',_('less than')],
                ['in',_('in')],
                ['not in',_('not in')],
                ):
            self.op_selection[item[1]] = item[0]
            self.combo_op.append_text(item[1])

        self.combo_op.set_active(0)

        # Processing text value
        self.right_text = win_gl.get_widget('right_compare')
        # Processing Custom conditions
        self.condition_next = win_gl.get_widget('cond_custom')
        self.condition_next.set_active(0)

        self.condition_next.hide()
        # Processing Removal of panel
        self.remove_filter = win_gl.get_widget('remove_custom')
        self.remove_filter.set_relief(gtk.RELIEF_NONE)

        try:
            self.right_text.set_tooltip_markup(tools.to_xml("Enter Values separated by ',' if operator 'in' or 'not in' is chosen.\nFor Date and DateTime Formats, specify text in '%Y-%m-%d' and '%Y-%m-%d %H:%M:%S' formats respectively."))
        except:
            pass

        self.remove_filter.connect('clicked',call,self)

    def _value_get(self):
        try:
            false_value_domain = []
            type_cast = {'integer':lambda x:int(x),
                         'float':lambda x:float(x),
                         'boolean':lambda x:bool(eval(x)),
                         'date':lambda x:(datetime.strptime(x, DT_FORMAT)).strftime(DT_FORMAT),
                         'datetime':lambda x:(datetime.strptime(x, DHM_FORMAT)).strftime(DHM_FORMAT)
                        }
            field_left = self.field_selection[self.combo_fields.get_active_text()][0]
            field_type = self.field_selection[self.combo_fields.get_active_text()][1]
            operator = self.op_selection[self.combo_op.get_active_text()]
            right_text =  self.right_text.get_text() or False

            if operator in ['not ilike','<>', 'not in'] and field_type != 'boolean':
                false_value_domain = ['|', (field_left,'=', False)]
            try:
                cast_type = True
                if field_type in type_cast:
                    if field_type in ('date','datetime'):
                        if right_text:
                            if field_type == 'datetime':
                                right_text = len(right_text)==10 and (right_text + ' 00:00:00') or right_text
                        else:
                            cast_type = False
                    if cast_type:
                        right_text = type_cast[field_type](right_text)
                self.right_text.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse("white"))
                self.right_text.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))

            except Exception,e:
                right_text = ''
                self.right_text.set_text('Invalid Value')
                self.right_text.modify_bg(gtk.STATE_ACTIVE, gtk.gdk.color_parse("#ff6969"))
                self.right_text.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("#ff6969"))
                return {}
            if operator in ['ilike','not ilike']:
                if field_type in ['integer','float','date','datetime','boolean']:
                    operator = (operator == 'ilike') and '=' or '!='
                else:
                    right_text = '%' + right_text + '%'

            if operator in ['<','>'] and field_type not in ['integer','float','date','datetime','boolean']:
                    operator = '='

            if operator in ['in','not in']:
                right_text = right_text.split(',')

            condition = self.condition_next.get_active_text()
            condition = eval(condition,{'AND':'&','OR':'|'})

            if field_type == 'selection' and right_text:
                right_text_se =  self.right_text.get_text()
                keys = []
                for selection in self.field_selection[self.combo_fields.get_active_text()][2]:
                    if selection[1].lower().find(right_text_se.lower()) != -1:
                        keys.append(selection[0])
                right_text = keys
                if operator in ['ilike','=','in']:
                    operator = 'in'
                else:
                    operator = 'not in'

            domain = [condition, (field_left, operator, right_text)]
            if false_value_domain:
                domain = false_value_domain + domain
            return {'domain':domain}

        except Exception,e:
            return {}

    def sig_exec(self, widget):
        pass

    def clear(self):
        pass

    def _value_set(self, value):
        pass

    def remove_custom_widget(self, button):
        button.parent.destroy()
        return True

    def sig_activate(self, fct):
        self.right_text.connect_after('activate', fct)

    value = property(_value_get, _value_set, None,
      'The content of the widget or ValueError if not valid')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
