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


import gtk
from gtk import glade

import copy
import time
import datetime as DT
import StringIO
import locale
import rpc
import tools
from tools import datetime_util

from widget.view import interface
from widget.view.list import group_record

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
        self.old_axis = axis
        self.editable = False
        self.key = False
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
        self.axis = copy.copy(self.old_axis)
        group_by = self.widget.screen.context.get('group_by', False)
        if group_by:
            if not self.key:
                del self.widget.screen.context['group_by']
                self.key = True
                self.widget.screen.search_filter()
                models = self.widget.screen.models
                self.widget.screen.context['group_by'] = group_by
            self.axis[0] = group_by[0]
            self.axis_data[group_by[0]] = {}
            # This is to get the missing field. if the field is not available in the graph view
            # for use case :graph view loaded directly from a dashboard and user executes groupby
            if self.axis[0] not in models.mfields:
                missing_gb_field = rpc.session.rpc_exec_auth('/object', 'execute', self.model, 'fields_get', [self.axis[0]], {})
                if missing_gb_field:
                    models.add_fields(missing_gb_field, models)

        for m in models:
            res = {}
            for x in self.axis_data.keys():
                field_val = m[x].get_client(m)
                if self.fields[x]['type'] in ('many2one', 'char','time','text'):
                    res[x] = field_val and str(field_val) or 'Undefined'
                elif self.fields[x]['type'] == 'selection':
                    selection = dict(m[x].attrs['selection'])
                    if field_val:
                        val = str(field_val)
                        res[x] = selection.get(val, val)
                    else:
                        res[x] = 'Undefined'
                elif self.fields[x]['type'] == 'date':
                    if field_val:
                        res[x] = datetime_util.server_to_local_timestamp(field_val,
                                    DT_FORMAT, LDFMT, tz_offset=False)
                    else:
                        res[x] = 'Undefined'
                elif self.fields[x]['type'] == 'datetime':
                    if field_val:
                        res[x] = datetime_util.server_to_local_timestamp(field_val,
                                    DHM_FORMAT, LDFMT+' %H:%M:%S')
                    else:
                        res[x] = 'Undefined'
                else:
                    res[x] = field_val and float(field_val) or 0.0
            datas.append(res)
        tinygraph.tinygraph(self._subplot, self.attrs.get('type', 'pie'), self.axis, self.axis_data, datas, axis_group_field=self.axis_group, orientation=self.attrs.get('orientation', 'vertical'))
        # the draw function may generate exception but it is not a problem as it will be redraw latter
        try:
            self._subplot.draw(None)
            #XXX it must have some better way to force the redraw but this one works
            self._canvas.queue_resize()
        except:
            pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

