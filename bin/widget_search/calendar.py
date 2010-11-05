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
import time
import datetime as DT
import gettext
import locale

import mx.DateTime
from mx.DateTime import *

import tools
import tools.datetime_util
import common

import wid_int
import date_widget

LDFMT = tools.datetime_util.get_date_format()
DT_FORMAT = '%Y-%m-%d'

class calendar(wid_int.wid_int):
    def __init__(self, name, parent, attrs={}):
        super(calendar, self).__init__(name, parent, attrs)

        self.widget = gtk.HBox(spacing=3)
        self.format = LDFMT
        
        self.widget1 = date_widget.ComplexEntry(self.format, spacing=3)
        self.entry1 = self.widget1.widget
        self.entry1.set_property('width-chars', 10)
        self.entry1.set_property('activates_default', True)
        self.entry1.connect('key_press_event', self.sig_key_press, self.entry1, parent)
        self.entry1.set_tooltip_text(_('Start date'))
        self.widget.pack_start(self.widget1, expand=False, fill=True)

        self.eb1 = gtk.EventBox()
        self.eb1.set_tooltip_text('Open the calendar widget')
        self.eb1.set_events(gtk.gdk.BUTTON_PRESS)
        self.eb1.connect('button_press_event', self.cal_open, self.entry1, parent)
        img = gtk.Image()
        img.set_from_stock('gtk-zoom-in', gtk.ICON_SIZE_MENU)
        img.set_alignment(0.5, 0.5)
        self.eb1.add(img)
        self.widget.pack_start(self.eb1, expand=False, fill=False)

        self.widget.pack_start(gtk.Label('-'), expand=False, fill=False)
        
        self.widget2 = date_widget.ComplexEntry(self.format, spacing=3)
        self.entry2 = self.widget2.widget
        self.entry2.set_property('width-chars', 10)
        self.entry2.set_property('activates_default', True)
        self.entry2.connect('key_press_event', self.sig_key_press, self.entry2, parent)
        self.entry2.set_tooltip_text(_('End date'))
        self.widget.pack_start(self.widget2, expand=False, fill=True)

        self.eb2 = gtk.EventBox()
        self.eb2.set_tooltip_text(_('Open the calendar widget'))
        self.eb2.set_events(gtk.gdk.BUTTON_PRESS)
        self.eb2.connect('button_press_event', self.cal_open, self.entry2, parent)
        img = gtk.Image()
        img.set_from_stock('gtk-zoom-in', gtk.ICON_SIZE_MENU)
        img.set_alignment(0.5, 0.5)
        self.eb2.add(img)
        self.widget.pack_start(self.eb2, expand=False, fill=False)

    def _date_get(self, str):
        try:
            #date = mx.DateTime.strptime(str, LDFMT)
            date = tools.datetime_util.strptime(str, LDFMT)
        except:
            return False
        return date.strftime(DT_FORMAT)
    
    def sig_key_press(self, widget, event, dest, parent):
        if event.keyval == gtk.keysyms.F2:
            self.cal_open(widget, event, dest, parent)
            return True
        
    def _value_get(self):
        res = []
        val = self._date_get(self.entry1.get_text())
        if val:
            res.append((self.name, '>=', val))
        val = self._date_get(self.entry2.get_text())
        if val:
            res.append((self.name, '<=', val))
        return res

    def _value_set(self, value):
        self.entry1.set_text(value)
        self.entry2.set_text(value)

    value = property(_value_get, _value_set, None, _('The content of the widget or ValueError if not valid'))

    def cal_open(self, widget, event, dest, parent=None):
        win = gtk.Dialog(_('OpenERP - Date selection'), parent,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OK, gtk.RESPONSE_OK))

        cal = gtk.Calendar()
        cal.display_options(gtk.CALENDAR_SHOW_HEADING|gtk.CALENDAR_SHOW_DAY_NAMES|gtk.CALENDAR_SHOW_WEEK_NUMBERS)
        cal.connect('day-selected-double-click', lambda *x: win.response(gtk.RESPONSE_OK))
        win.vbox.pack_start(cal, expand=True, fill=True)
        win.show_all()

        try:
            val = self._date_get(dest.get_text())
            if val:
                cal.select_month(int(val[5:7])-1, int(val[0:4]))
                cal.select_day(int(val[8:10]))
        except ValueError:
            pass

        response = win.run()
        if response == gtk.RESPONSE_OK:
            year, month, day = cal.get_date()
            dt = DT.date(year, month+1, day)
            dest.set_text(dt.strftime(LDFMT))
        win.destroy()

    def clear(self):
        self.widget1.clear()
        self.widget2.clear()
        #self.value = ''

    def sig_activate(self, fct):
        self.entry1.connect_after('activate', fct)
        self.entry2.connect_after('activate', fct)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
