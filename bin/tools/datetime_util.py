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
import locale

from mx.DateTime import RelativeDateTime
from mx.DateTime import now

try:
    from mx.DateTime import strptime
except ImportError:
    # strptime does not exist on windows. we emulate it
    from mx.DateTime import mktime
    def strptime(s, f):
        return mktime(time.strptime(s, f))

date_operation = {
    '^=w(\d+)$': lambda dt,r: dt+RelativeDateTime(day=0, month=0, weeks = int(r.group(1))),
    '^=d(\d+)$': lambda dt,r: dt+RelativeDateTime(day=int(r.group(1))),
    '^=m(\d+)$': lambda dt,r: dt+RelativeDateTime(month = int(r.group(1))),
    '^=y(2\d\d\d)$': lambda dt,r: dt+RelativeDateTime(year = int(r.group(1))),
    '^=h(\d+)$': lambda dt,r: dt+RelativeDateTime(hour = int(r.group(1))),
    '^=(\d+)w$': lambda dt,r: dt+RelativeDateTime(day=0, month=0, weeks = int(r.group(1))),
    '^=(\d+)d$': lambda dt,r: dt+RelativeDateTime(day=int(r.group(1))),
    '^=(\d+)m$': lambda dt,r: dt+RelativeDateTime(month = int(r.group(1))),
    '^=(2\d\d\d)y$': lambda dt,r: dt+RelativeDateTime(year = int(r.group(1))),
    '^=(\d+)h$': lambda dt,r: dt+RelativeDateTime(hour = int(r.group(1))),
    '^([\\+-]\d+)h$': lambda dt,r: dt+RelativeDateTime(hours = int(r.group(1))),
    '^([\\+-]\d+)w$': lambda dt,r: dt+RelativeDateTime(days = 7*int(r.group(1))),
    '^([\\+-]\d+)d$': lambda dt,r: dt+RelativeDateTime(days = int(r.group(1))),
    '^([\\+-]\d+)m$': lambda dt,r: dt+RelativeDateTime(months = int(r.group(1))),
    '^([\\+-]\d+)y$': lambda dt,r: dt+RelativeDateTime(years = int(r.group(1))),
    '^=$': lambda dt,r: now(),
    '^-$': lambda dt,r: False
}

date_mapping = {
    '%y': ('__', '[_0-9][_0-9]'),
    '%Y': ('____', '[_1-9][_0-9][_0-9][_0-9]'),
    '%m': ('__', '[_0-1][_0-9]'),
    '%d': ('__', '[_0-3][_0-9]'),
    '%H': ('__', '[_0-2][_0-9]'),
    '%M': ('__', '[_0-6][_0-9]'),
    '%S': ('__', '[_0-6][_0-9]'),
}

def get_date_format():
    """Return locale date format string. If format string doesn't contain 
    any of the `%Y, %m or %d` then returns default datetime format `%Y/%m/%d`
    """

    fmt = locale.nl_langinfo(locale.D_FMT)
    for x,y in [('%y','%Y'),('%B',''),('%A','')]:
        fmt = fmt.replace(x, y)

    if not (fmt.count('%Y') == 1 and fmt.count('%m') == 1 and fmt.count('%d') == 1):
        return '%Y/%m/%d'

    return fmt

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

