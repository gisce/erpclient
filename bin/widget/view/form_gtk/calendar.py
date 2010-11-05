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

import time
from datetime import datetime as DT
#import mx
#from mx import DateTime as DT

import gtk

import gettext

import common
import interface
import locale
import rpc
import service
import tools
import pytz

import date_widget

DT_FORMAT = '%Y-%m-%d'
DHM_FORMAT = '%Y-%m-%d %H:%M:%S'
HM_FORMAT = '%H:%M:%S'

LDFMT = tools.datetime_util.get_date_format();

class calendar(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, attrs=attrs)
        self.format = LDFMT
        self.widget = date_widget.ComplexEntry(self.format, spacing=3)
        self.entry = self.widget.widget
        self.entry.set_property('activates_default', True)
        self.entry.connect('key_press_event', self.sig_key_press)        
        self.entry.connect('button_press_event', self._menu_open)
        self.entry.connect('activate', self.sig_activate)
        self.entry.connect('focus-in-event', lambda x,y: self._focus_in())
        self.entry.connect('focus-out-event', lambda x,y: self._focus_out())

        self.eb = gtk.EventBox()
        self.eb.set_tooltip_text(_('Open the calendar widget'))
        self.eb.set_events(gtk.gdk.BUTTON_PRESS)
        self.eb.connect('button_press_event', self.cal_open, model, self._window)
        img = gtk.Image()
        img.set_from_stock('gtk-zoom-in', gtk.ICON_SIZE_MENU)
        img.set_alignment(0.5, 0.5)
        self.eb.add(img)
        self.widget.pack_start(self.eb, expand=False, fill=False)

        self.readonly=False

    def _color_widget(self):
        return self.entry

    def _readonly_set(self, value):
        interface.widget_interface._readonly_set(self, value)
        self.entry.set_editable(not value)
        self.entry.set_sensitive(not value)
        self.eb.set_sensitive(not value)

    def sig_key_press(self, widget, event):
        if not self.entry.get_editable():
            return False
        if event.keyval == gtk.keysyms.F2:
            self.cal_open(widget, event)
            return True
        
    def get_value(self, model):
        str = self.entry.get_text()
        if str == '':
            return False
        try:
            date1 = DT.strptime(str[:10], self.format)
        except:
            return False
        
        try:
            return date1.strftime(DT_FORMAT)
        except ValueError:
            common.message(_('Invalid date value! Year must be greater than 1899 !'))
            return time.strftime(DT_FORMAT)

    def set_value(self, model, model_field):
        try:
            model_field.set_client(model, self.get_value(model))
        except:
            return False   
        return True

    def display(self, model, model_field):
        if not model_field:
            self.entry.clear()
            return False
        super(calendar, self).display(model, model_field)
        value = model_field.get(model)
        if not value:
            self.entry.clear()
        else:
            if len(value)>10:
                value=value[:10]
            #date=mx.DateTime.strptime(value, DT_FORMAT)
            date=DT.strptime(value[:10], DT_FORMAT)
            t=date.strftime(self.format)
            if len(t) > self.entry.get_width_chars():
                self.entry.set_width_chars(len(t))
            self.entry.set_text(t)
        return True

    def cal_open(self, widget, event, model=None, window=None):
        if self.readonly:
            common.message(_('This widget is readonly !'))
            return True

        if not window:
            window = service.LocalService('gui.main').window

        win = gtk.Dialog(_('OpenERP - Date selection'), window,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OK, gtk.RESPONSE_OK))
        win.set_icon(common.OPENERP_ICON)

        cal = gtk.Calendar()
        cal.display_options(gtk.CALENDAR_SHOW_HEADING|gtk.CALENDAR_SHOW_DAY_NAMES|gtk.CALENDAR_SHOW_WEEK_NUMBERS)
        cal.connect('day-selected-double-click', lambda *x: win.response(gtk.RESPONSE_OK))
        win.vbox.pack_start(cal, expand=True, fill=True)
        win.show_all()

        try:
            val = self.get_value(model)
            if val:
                cal.select_month(int(val[5:7])-1, int(val[0:4]))
                cal.select_day(int(val[8:10]))
        except ValueError:
            pass

        response = win.run()
        if response == gtk.RESPONSE_OK:
            year, month, day = cal.get_date()
            dt = DT(year, month+1, day)
            try:
                value = dt.strftime(LDFMT)
            except ValueError:
                common.message(_('Invalid date value! Year must be greater than 1899 !'))
            else:
                self.entry.set_text(value)
        self._focus_out()
        window.present()
        win.destroy()

class datetime(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs=attrs)
        self.format = LDFMT+' %H:%M:%S'
        self.widget = date_widget.ComplexEntry(self.format, spacing=3)
        self.entry = self.widget.widget
        self.entry.set_property('activates_default', True)
        self.entry.connect('key_press_event', self.sig_key_press)
        self.entry.connect('button_press_event', self._menu_open)
        self.entry.connect('focus-in-event', lambda x,y: self._focus_in())
        self.entry.connect('focus-out-event', lambda x,y: self._focus_out())

        eb = gtk.EventBox()
        eb.set_tooltip_text(_('Open the calendar widget'))
        eb.set_events(gtk.gdk.BUTTON_PRESS)
        eb.connect('button_press_event', self.cal_open, model, self._window)
        img = gtk.Image()
        img.set_from_stock('gtk-zoom-in', gtk.ICON_SIZE_MENU)
        img.set_alignment(0.5, 0.5)
        eb.add(img)
        self.widget.pack_start(eb, expand=False, fill=False)

        self.readonly=False

    def _color_widget(self):
        return self.entry

    def _readonly_set(self, value):
        self.readonly = value
        self.entry.set_editable(not value)
        self.entry.set_sensitive(not value)

    def sig_key_press(self, widget, event):
        if not self.entry.get_editable():
            return False
        if event.keyval == gtk.keysyms.F2:
            self.cal_open(widget,event)
            return True
        
    def get_value(self, model, timezone=True):
        str = self.entry.get_text()
        if str=='':
            return False
        try:
            date = DT.strptime(str[:19], self.format)
        except:
            return False
        if rpc.session.context.get('tz',False) and timezone:
            try:
                lzone = pytz.timezone(rpc.session.context['tz'])
                szone = pytz.timezone(rpc.session.timezone)
                ldt = lzone.localize(date, is_dst=True)
                sdt = ldt.astimezone(szone)
                date = sdt
            except pytz.UnknownTimeZoneError:
                # Timezones are sometimes invalid under Windows
                # and hard to figure out, so as a low-risk fix
                # in stable branch we will simply ignore the
                # exception and consider client in server TZ
                # (and sorry about the code duplication as well,
                # this is fixed properly in trunk)
                pass
        try:
            return date.strftime(DHM_FORMAT)
        except ValueError:
            common.message(_('Invalid datetime value! Year must be greater than 1899 !'))
            return time.strftime(DHM_FORMAT)

    def set_value(self, model, model_field):
        try:
            model_field.set_client(model, self.get_value(model))
        except:
            return False   
        return True

    def display(self, model, model_field):
        if not model_field:
            return self.show(False)
        super(datetime, self).display(model, model_field)
        self.show(model_field.get(model))

    def show(self, dt_val, timezone=True):
        if not dt_val:
            self.entry.clear()
        else:
            date = DT.strptime(dt_val[:19], DHM_FORMAT)
            if rpc.session.context.get('tz',False) and timezone:
                try:
                    lzone = pytz.timezone(rpc.session.context['tz'])
                    szone = pytz.timezone(rpc.session.timezone)
                    sdt = szone.localize(date, is_dst=True)
                    ldt = sdt.astimezone(lzone)
                    date = ldt
                except pytz.UnknownTimeZoneError:
                    # Timezones are sometimes invalid under Windows
                    # and hard to figure out, so as a low-risk fix
                    # in stable branch we will simply ignore the
                    # exception and consider client in server TZ
                    # (and sorry about the code duplication as well,
                    # this is fixed properly in trunk)
                    pass
            t=date.strftime(self.format)
            if len(t) > self.entry.get_width_chars():
                self.entry.set_width_chars(len(t))
            self.entry.set_text(t)
        return True

    def cal_open(self, widget, event, model=None, window=None):
        if self.readonly:
            common.message(_('This widget is readonly !'))
            return True

        win = gtk.Dialog(_('OpenERP - Date selection'), window,
                gtk.DIALOG_MODAL|gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OK, gtk.RESPONSE_OK))

        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Hour:')), expand=False, fill=False)
        hour = gtk.SpinButton(gtk.Adjustment(0, 0, 23, 1, 5), 1, 0)
        hbox.pack_start(hour, expand=True, fill=True)
        hbox.pack_start(gtk.Label(_('Minute:')), expand=False, fill=False)
        minute = gtk.SpinButton(gtk.Adjustment(0, 0, 59, 1, 10), 1, 0)
        hbox.pack_start(minute, expand=True, fill=True)
        win.vbox.pack_start(hbox, expand=False, fill=True)

        cal = gtk.Calendar()
        cal.display_options(gtk.CALENDAR_SHOW_HEADING|gtk.CALENDAR_SHOW_DAY_NAMES|gtk.CALENDAR_SHOW_WEEK_NUMBERS)
        cal.connect('day-selected-double-click', lambda *x: win.response(gtk.RESPONSE_OK))
        win.vbox.pack_start(cal, expand=True, fill=True)
        win.show_all()

        try:
            val = self.get_value(model, timezone=False)
            if val:
                hour.set_value(int(val[11:13]))
                minute.set_value(int(val[-5:-3]))
                cal.select_month(int(val[5:7])-1, int(val[0:4]))
                cal.select_day(int(val[8:10]))
            else:
                hour.set_value(time.localtime()[3])
                minute.set_value(time.localtime()[4])
        except ValueError:
            pass
        response = win.run()
        if response == gtk.RESPONSE_OK:
            hr = int(hour.get_value())
            mi = int(minute.get_value())
            dt = cal.get_date()
            month = int(dt[1])+1
            day = int(dt[2])
            date = DT(dt[0], month, day, hr, mi)
            try:
                value = date.strftime(DHM_FORMAT)
            except ValueError:
                common.message(_('Invalid datetime value! Year must be greater than 1899 !'))        
            else:
                self.show(value, timezone=False)

        self._focus_out()
        win.destroy()


class stime(interface.widget_interface):
    def __init__(self, window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, parent, attrs=attrs)

        self.format = '%H:%M:%S'
        self.widget = date_widget.ComplexEntry(self.format, spacing=3)
        self.entry = self.widget.widget
        self.entry.connect('focus-in-event', lambda x,y: self._focus_in())
        self.entry.connect('focus-out-event', lambda x,y: self._focus_out())
        self.value=False

    def _readonly_set(self, value):
        self.readonly = value
        self.entry.set_editable(not value)
        self.entry.set_sensitive(not value)

    def _color_widget(self):
        return self.entry

    def get_value(self, model):
        str = self.entry.get_text()
        if str=='':
            res = False
        try:
            t = time.strptime(str[:8], self.format)
        except:
            return False
        return time.strftime(HM_FORMAT, t)

    def set_value(self, model, model_field):
        try:
            res = self.get_value(model)
            model_field.set_client(model, res)
        except:
            return False    
        return True

    def display(self, model, model_field):
        if not model_field:
            return self.show(False)
        super(stime, self).display(model, model_field)
        self.entry.set_text(model_field.get(model) or '00:00:00')
        return True

    def show(self, dt_val, timezone=True):
        if not dt_val:
            self.entry.clear()
        else:
            date = time.strptime(dt_val[:8], HM_FORMAT)
            if rpc.session.context.get('tz',False) and timezone:
                try:
                    lzone = pytz.timezone(rpc.session.context['tz'])
                    szone = pytz.timezone(rpc.session.timezone)
                    dt = DT(date[0], date[1], date[2], date[3], date[4], date[5], date[6])
                    sdt = szone.localize(dt, is_dst=True)
                    ldt = sdt.astimezone(lzone)
                    date = ldt.timetuple()
                except pytz.UnknownTimeZoneError:
                    # Timezones are sometimes invalid under Windows
                    # and hard to figure out, so as a low-risk fix
                    # in stable branch we will simply ignore the
                    # exception and consider client in server TZ
                    # (and sorry about the code duplication as well,
                    # this is fixed properly in trunk)
                    pass

            t=time.strftime(self.format, date)
            if len(t) > self.entry.get_width_chars():
                self.entry.set_width_chars(len(t))
            self.entry.set_text(t)
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

