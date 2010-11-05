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

import time
import datetime as DT
import StringIO
import locale

import rpc
import tools
import tools.datetime_util
import pytz
from widget.view import interface

DT_FORMAT = '%Y-%m-%d'
DHM_FORMAT = '%Y-%m-%d %H:%M:%S'
HM_FORMAT = '%H:%M:%S'
LDFMT = tools.datetime_util.get_date_format()

import tinygraph
import matplotlib

matplotlib.rcParams['xtick.labelsize'] = 10
matplotlib.rcParams['ytick.labelsize'] = 10

from matplotlib.figure import Figure
from matplotlib.backends.backend_gtkcairo import FigureCanvasGTKCairo as FigureCanvas

class ViewGraph(object):
    def __init__(self, model, axis, fields, axis_data={}, attrs={}):
        self.widget = gtk.HBox()
        self._figure = Figure(figsize=(800,600), dpi=100, facecolor='w')
        self._subplot = self._figure.add_subplot(111,axisbg='#eeeeee')
        self._canvas = FigureCanvas(self._figure)
        self.widget.pack_start(self._canvas, expand=True, fill=True)

        if attrs.get('type', 'pie')=='bar':
            if attrs.get('orientation', 'vertical')=='vertical':
                self._figure.subplots_adjust(left=0.08,right=0.98,bottom=0.25,top=0.98)
            else:
                self._figure.subplots_adjust(left=0.20,right=0.97,bottom=0.07,top=0.98)
        else:
            self._figure.subplots_adjust(left=0.03,right=0.97,bottom=0.03,top=0.97)

        self.fields = fields
        self.model = model
        self.axis = axis
        self.editable = False
        self.widget.editable = False
        self.axis_data = axis_data
        self.axis_group = {}
        for i in self.axis_data:
            self.axis_data[i]['string'] = self.fields[i]['string']
            if self.axis_data[i].get('group', False):
                self.axis_group[i]=1
                self.axis.remove(i)
        self.attrs = attrs

    def display(self, models):
        datas = []
        for m in models:
            res = {}
            for x in self.axis_data.keys():
                if self.fields[x]['type'] in ('many2one', 'char','time','text'):
                    res[x] = str(m[x].get_client(m))
                elif self.fields[x]['type'] == 'selection':
                    selection = dict(m[x].attrs['selection'])
                    val = str(m[x].get_client(m))
                    res[x] = selection.get(val, val)
                elif self.fields[x]['type'] == 'date':
                    if m[x].get_client(m):
                        date = time.strptime(m[x].get_client(m), DT_FORMAT)
                        res[x] = time.strftime(LDFMT, date)
                    else:
                        res[x]=''
                elif self.fields[x]['type'] == 'datetime':
                    if m[x].get_client(m):
                        date = time.strptime(m[x].get_client(m), DHM_FORMAT)
                        if rpc.session.context.get('tz'):
                            try:
                                lzone = pytz.timezone(rpc.session.context['tz'])
                                szone = pytz.timezone(rpc.session.timezone)
                                dt = DT.datetime(date[0], date[1], date[2], date[3], date[4], date[5], date[6])
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
                        res[x] = time.strftime(LDFMT + ' %H:%M:%S', date)
                    else:
                        res[x] = ''
                else:
                    res[x] = float(m[x].get_client(m))
            datas.append(res)
        tinygraph.tinygraph(self._subplot, self.attrs.get('type', 'pie'), self.axis, self.axis_data, datas, axis_group_field=self.axis_group, orientation=self.attrs.get('orientation', 'vertical'))
        # the draw function may generate exception but it is not a problem as it will be redraw latter
        try:
            self._subplot.draw()
            #XXX it must have some better way to force the redraw but this one works
            self._canvas.queue_resize()
        except:
            pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

