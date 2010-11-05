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

from widget.view import interface
from tools import ustr, node_attributes
import gtk
import gtk.glade
import gettext
import common
from datetime import datetime, date

from SpiffGtkWidgets import Calendar
from mx import DateTime
import time
import math

COLOR_PALETTE = ['#f57900', '#cc0000', '#d400a8', '#75507b', '#3465a4', '#73d216', '#c17d11', '#edd400',
                 '#fcaf3e', '#ef2929', '#ff00c9', '#ad7fa8', '#729fcf', '#8ae234', '#e9b96e', '#fce94f',
                 '#ff8e00', '#ff0000', '#b0008c', '#9000ff', '#0078ff', '#00ff00', '#e6ff00', '#ffff00',
                 '#905000', '#9b0000', '#840067', '#510090', '#0000c9', '#009b00', '#9abe00', '#ffc900',]

_colorline = ['#%02x%02x%02x' % (25+((r+10)%11)*23,5+((g+1)%11)*20,25+((b+4)%11)*23) for r in range(11) for g in range(11) for b in range(11) ]
def choice_colors(n):
    if n > len(COLOR_PALETTE):
        return _colorline[0:-1:len(_colorline)/(n+1)]
    elif n:
        return COLOR_PALETTE[:n]
    return []

class TinyEvent(Calendar.Event):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        
        super(TinyEvent, self).__init__(**kwargs)        

    def __repr__(self):
        r = []
        for x in self.__dict__:
            r.append("%s: %r" % (x, self.__dict__[x]))
        return '<TinyEvent::\n\t' + "\n\t".join(r) + '\n>'

class TinyCalModel(Calendar.Model):
    def add_events(self, events):
        for event in events:
            assert event    is not None
            assert event.id is None
            self.events[self.next_event_id] = event
            event.id = self.next_event_id
            self.next_event_id += 1

    def remove_events(self):
        self.events = {}


class ViewCalendar(object):
    TV_COL_ID = 0
    TV_COL_COLOR = 1
    TV_COL_LABEL = 2

    def __init__(self, model, axis, fields, attrs):
        self.glade = gtk.glade.XML(common.terp_path("openerp.glade"),'widget_view_calendar', gettext.textdomain())
        self.widget = self.glade.get_widget('widget_view_calendar')

        self._label_current = self.glade.get_widget('label_current')
        self._radio_month = self.glade.get_widget('radio_month')
        self._radio_week = self.glade.get_widget('radio_week')
        self._radio_day = self.glade.get_widget('radio_day')
        self._small_calendar = self.glade.get_widget('calendar_small')
        self._calendar_treeview = self.glade.get_widget('calendar_treeview')
        
        self._radio_month.set_active(True)
        self.mode = 'month'
        
        self.fields = fields
        self.attrs = attrs
        self.axis = axis
        self.screen = None

        self.cal_model = TinyCalModel()
        self.cal_view = Calendar.Calendar(self.cal_model)
        self.cal_view.connect('event-clicked', self._on_event_clicked)
        self.cal_view.connect('do_month_back_forward', self._back_forward)
        self.cal_view.connect('day-selected', self._change_small)

        vbox = self.glade.get_widget('cal_vbox')
        vbox.pack_start(self.cal_view)
        vbox.show_all()

        self.process = False
        self.glade.signal_connect('on_but_forward_clicked', self._back_forward, 1)
        self.glade.signal_connect('on_but_back_clicked', self._back_forward, -1)
        self.glade.signal_connect('on_but_today_clicked', self._today)
        self.glade.signal_connect('on_calendar_small_day_selected_double_click', self._change_small)
        self.glade.signal_connect('on_button_day_clicked', self._change_view, 'day')
        self.glade.signal_connect('on_button_week_clicked', self._change_view, 'week')
        self.glade.signal_connect('on_button_month_clicked', self._change_view, 'month')
        
        self.date = DateTime.today()

        self.string = attrs.get('string', '')
        self.date_start = attrs.get('date_start')
        self.date_delay = attrs.get('date_delay')
        self.date_stop = attrs.get('date_stop')
        self.color_field = attrs.get('color')
        self.day_length = int(attrs.get('day_length', 8))
        self.colors = {}
        self.models = None

        if self.color_field:
            model = gtk.ListStore(str, str, str)
            self._calendar_treeview.set_model(model)
            self._calendar_treeview.get_selection().set_mode(gtk.SELECTION_NONE)

            for c in (self.TV_COL_ID, self.TV_COL_COLOR):
                column = gtk.TreeViewColumn(None, gtk.CellRendererText(), text=c)
                self._calendar_treeview.append_column(column)
                column.set_visible(False) 

            renderer = gtk.CellRendererText()
            column = gtk.TreeViewColumn(None, renderer, text=self.TV_COL_LABEL)
            col_label = gtk.Label('')
            col_label.set_markup('<b>%s</b>' % self.fields[self.color_field]['string'])
            col_label.show()
            column.set_widget(col_label)
            column.set_cell_data_func(renderer, self._treeview_setter)
            self._calendar_treeview.append_column(column)
            

    def _treeview_setter(self, column, cell, store, iter):
        color = store.get_value(iter, self.TV_COL_COLOR)
        cell.set_property('background', str(color))

    def add_to_treeview(self, name, value, color):
        value = str(value)
        model = self._calendar_treeview.get_model()
        for row in model:
            if row[self.TV_COL_ID] == value:
                return  # id already in the treeview
        iter = model.append()
        model.set(iter, self.TV_COL_ID, value, self.TV_COL_COLOR, color, self.TV_COL_LABEL, name)

    def _change_small(self, widget, *args, **argv):
        if isinstance(widget, gtk.Calendar):
            t = list(widget.get_date())
            t[1] += 1
        else:
            t = list(args[0].timetuple()[:3])
        self.date = DateTime.DateTime(*t)
        self.display(None)
        self.screen.context.update({'default_' +self.date_start:self.date.strftime('%Y-%m-%d %H:%M:%S')})
        self.screen.switch_view(mode='form')
        self.screen.new()

    def _today(self, widget, *args, **argv):
        self.date = DateTime.today()
        self.display(None)

    def _back_forward(self, widget, type, *args, **argv):
        if self.mode=='day':
            self.date = self.date + DateTime.RelativeDateTime(days=type)
        if self.mode=='week':
            self.date = self.date + DateTime.RelativeDateTime(weeks=type)
        if self.mode=='month':
            self.date = self.date + DateTime.RelativeDateTime(months=type)
        self.display(None)

    def _change_view(self, widget, type, *args, **argv):
        if self.process or self.mode == type:
            return True
        self.process = True
        self.mode = type
        self.display(None)
        self.process = False
        return True

    def _on_event_clicked(self, calendar, calendar_event, hippo_event):
        if hippo_event.button == 1 and hippo_event.count == 1:   # simple-left-click
            self.screen.current_model = calendar_event.model
            self.screen.switch_view(mode='form')
            
    def __update_colors(self):
        self.colors = {}
        if self.color_field:
            for model in self.models:
                
                key = model.value[self.color_field]
                name = key
                value = key

                if isinstance(key, (tuple, list)):
                    value, name = key
                    key = tuple(key)

                self.colors[key] = (name, value, None)

            colors = choice_colors(len(self.colors))
            for i, (key, value) in enumerate(self.colors.items()):
                self.colors[key] = (value[0], value[1], colors[i])

    def display(self, models):
        if models:
            self.models = models.models

            if self.models:
                self.__update_colors()

                self.cal_model.remove_events()
                self.cal_model.add_events(self.__get_events())
                
        self.refresh()

    def refresh(self):
        t = self.date.tuple()
        from tools import ustr
        from locale import getlocale
        sysencoding = getlocale()[1]

        if self.mode=='month':
            self._radio_month.set_active(True)
            self.cal_view.range = self.cal_view.RANGE_MONTH
            self._label_current.set_text(ustr(self.date.strftime('%B %Y'), sysencoding))
        elif self.mode=='week':
            self._radio_week.set_active(True)
            self.cal_view.range = self.cal_view.RANGE_WEEK
            self._label_current.set_text(_('Week') + ' ' + self.date.strftime('%W, %Y'))
        elif self.mode=='day':
            self._radio_day.set_active(True)
            self.cal_view.range = self.cal_view.RANGE_CUSTOM
            d1 = datetime(*t[:3])
            d2 = Calendar.util.end_of_day(d1)
            self.cal_view.active_range = self.cal_view.visible_range = d1, d2
            self._label_current.set_text(ustr(self.date.strftime('%A %x'), sysencoding))

        self.cal_view.selected = date(*list(t)[:3])
        self._small_calendar.select_month(t[1]-1,t[0])
        self._small_calendar.select_day(t[2])
        
        self.cal_view.refresh()


    def __get_events(self):
        events = []
        for model in self.models:
            e = self.__get_event(model)
            if e:
                if e.color_info:
                    self.add_to_treeview(*e.color_info)
                events.append(e)
        return events

    def __convert(self, event):
        # method from eTiny
        DT_SERVER_FORMATS = {
          'datetime': '%Y-%m-%d %H:%M:%S',
          'date': '%Y-%m-%d',
          'time': '%H:%M:%S'
        }

        fields = [x for x in [self.date_start, self.date_stop] if x]
        for fld in fields:
            typ = self.fields[fld]['type']
            fmt = DT_SERVER_FORMATS[typ]

            if event[fld] and fmt:
                event[fld] = time.strptime(event[fld][:19], fmt)

            # default start time is 9:00 AM
            if typ == 'date' and fld == self.date_start:
                if event[fld]:
                    ds = list(event[fld])
                    ds[3] = 9
                    event[fld] = tuple(ds)

    def __get_event(self, model):
        
        event = model.value.copy()
        self.__convert(event)

        caption = ''     
        description = [] 
        starts = None   
        ends = None      

        if self.axis:

            f = self.axis[0]
            s = event[f]

            if isinstance(s, (tuple, list)): s = s[-1]

            caption = ustr(s)

            for f in self.axis[1:]:
                s = event[f]
                if isinstance(s, (tuple, list)): s = s[-1]

                description += [ustr(s)]

        starts = event.get(self.date_start)
        ends = event.get(self.date_delay) or 1.0
        span = 0

        if starts and ends:

            n = 0
            h = ends or 1

            if ends == self.day_length: span = 1

            if ends > self.day_length:
                n = ends / self.day_length
                h = ends % self.day_length

                n = int(math.floor(n))

                if n > 0:
                    if not h:
                        n = n - 1
                    span = n + 1
                    
            t=DateTime.mktime(starts)
            ends = time.localtime(t.ticks() + (h * 60 * 60) + (n * 24 * 60 * 60))


        if starts and self.date_stop:

            ends = event.get(self.date_stop)
            if not ends:
                ends = time.localtime(time.mktime(starts) + 60 * 60)

            tds = time.mktime(starts)
            tde = time.mktime(ends)

            if tds >= tde:
                tde = tds + 60 * 60
                ends = time.localtime(tde)

            n = (tde - tds) / (60 * 60)

            if n > self.day_length:
                span = math.floor(n / 24.)
        
        if not starts:
            return None
        
        color_key = event.get(self.color_field)
        if isinstance(color_key, list):
            color_key = tuple(color_key)
        color_info = self.colors.get(color_key)

        color = color_info and color_info[2] or 'black'

        description = ', '.join(description).strip()
        all_day = span > 0
        return TinyEvent(model=model,
                         caption=caption.strip(),
                         start=datetime(*starts[:7]), 
                         end=datetime(*ends[:7]), 
                         description=description, 
                         dayspan=span,
                         all_day=all_day,
                         color_info=color_info,
                         bg_color = (all_day or self.mode != 'month') and color or 'white',
                         text_color = (all_day or self.mode != 'month') and 'black' or color,
        )


class parser_calendar(interface.parser_interface):
    def parse(self, model, root_node, fields):
        attrs = node_attributes(root_node)
        self.title = attrs.get('string', 'Calendar')

        axis = []
        axis_data = {}
        for node in root_node.childNodes:
            node_attrs = node_attributes(node)
            if node.localName == 'field':
                axis.append(str(node_attrs['name']))
                axis_data[str(node_attrs['name'])] = node_attrs

        view = ViewCalendar(model, axis, fields, attrs)

        return view, {}, [], ''

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

