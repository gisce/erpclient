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

import time
from datetime import datetime
import locale
import rpc
import math

from datetime import datetime
from dateutil.relativedelta import relativedelta

strptime=datetime.strptime

date_operation = {
    '^=w(\d+)$': lambda dt,r: dt+relativedelta(day=0, month=0, weeks = int(r.group(1))),
    '^=d(\d+)$': lambda dt,r: dt+relativedelta(day=int(r.group(1))),
    '^=m(\d+)$': lambda dt,r: dt+relativedelta(month = int(r.group(1))),
    '^=y(2\d\d\d)$': lambda dt,r: dt+relativedelta(year = int(r.group(1))),
    '^=h(\d+)$': lambda dt,r: dt+relativedelta(hour = int(r.group(1))),
    '^=(\d+)w$': lambda dt,r: dt+relativedelta(day=0, month=0, weeks = int(r.group(1))),
    '^=(\d+)d$': lambda dt,r: dt+relativedelta(day=int(r.group(1))),
    '^=(\d+)m$': lambda dt,r: dt+relativedelta(month = int(r.group(1))),
    '^=(2\d\d\d)y$': lambda dt,r: dt+relativedelta(year = int(r.group(1))),
    '^=(\d+)h$': lambda dt,r: dt+relativedelta(hour = int(r.group(1))),
    '^([\\+-]\d+)h$': lambda dt,r: dt+relativedelta(hours = int(r.group(1))),
    '^([\\+-]\d+)w$': lambda dt,r: dt+relativedelta(days = 7*int(r.group(1))),
    '^([\\+-]\d+)d$': lambda dt,r: dt+relativedelta(days = int(r.group(1))),
    '^([\\+-]\d+)m$': lambda dt,r: dt+relativedelta(months = int(r.group(1))),
    '^([\\+-]\d+)y$': lambda dt,r: dt+relativedelta(years = int(r.group(1))),
    '^=$': lambda dt,r: datetime.now(),
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

# RATIONALE BEHIND TIMESTAMP CALCULATIONS AND TIMEZONE MANAGEMENT:
#  The server side never does any timestamp calculation, always
#  sends them in a naive (timezone agnostic) format supposed to be
#  expressed within the server timezone, and expects the clients to
#  provide timestamps in the server timezone as well.
#  It stores all timestamps in the database in naive format as well,
#  which also expresses the time in the server timezone.
#  For this reason the server makes its timezone name available via the
#  common/timezone_get() rpc method, which clients need to read
#  to know the appropriate time offset to use when reading/writing
#  times.
def _offset_format_timestamp(src_tstamp_str, src_format, dst_format, server_to_client,
        tz_offset=True, ignore_unparsable_time=True):
    """
    Convert a source timestamp string into a destination timestamp string, attempting to apply the
    correct offset if both the server and local timezone are recognized, or no
    offset at all if they aren't or if tz_offset is false (i.e. assuming they are both in the same TZ).

    @param src_tstamp_str: the str value containing the timestamp.
    @param src_format: the format to use when parsing the local timestamp.
    @param dst_format: the format to use when formatting the resulting timestamp.
    @param server_to_client: specify timezone offset direction (server=src and client=dest if True, or client=src and server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str cannot be parsed
                                   using src_format or formatted using dst_format.

    @return: destination formatted timestamp, expressed in the destination timezone if possible
            and if tz_offset is true, or src_tstamp_str if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False

    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime.datetime object (so no time.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.strptime(src_tstamp_str,src_format)
            if tz_offset and rpc.session.context.get('tz',False):
                try:
                    import pytz
                    if server_to_client:
                        src_tz = pytz.timezone(rpc.session.timezone)
                        dst_tz = pytz.timezone(rpc.session.context['tz'])
                    else:
                        src_tz = pytz.timezone(rpc.session.context['tz'])
                        dst_tz = pytz.timezone(rpc.session.timezone)
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception,e:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception,e:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res

def server_to_local_timestamp(server_tstamp_str, server_format, local_format,
        tz_offset=True, ignore_unparsable_time=True):
    """
    Convert a server timestamp string into a local timestamp string, attempting to apply the
    correct offset if both the server and local timezone are recognized, or no
    offset at all if they aren't or if tz_offset is false  (i.e. assuming they are both in the same TZ).

    @param server_tstamp_str: the str value containing the timestamp.
    @param server_format: the format to use when parsing server_tstamp_str.
    @param local_format: the format to use when formatting the resulting timestamp.
    @param ignore_unparsable_time: if True, return False if server_tstamp_str cannot be parsed
                                   using server_format or formatted using local_format.

    @return: locally formatted timestamp, expressed in the client timezone if possible
            and if tz_offset is true, or server_tstamp_str if timezone offset could not be determined.
    """
    return _offset_format_timestamp(server_tstamp_str, server_format, local_format, True,
            tz_offset=tz_offset, ignore_unparsable_time=ignore_unparsable_time)


def local_to_server_timestamp(local_tstamp_str, local_format, server_format,
        tz_offset=True, ignore_unparsable_time=True):
    """
    Convert a local timestamp string into a server timestamp string, attempting to apply the
    correct offset if both the server and local timezone are recognized, or no
    offset at all if they aren't or if tz_offset is false (i.e. assuming they are both in the same TZ).

    @param local_tstamp_str: the str value containing the timestamp.
    @param local_format: the format to use when parsing the local timestamp.
    @param server_format: the format to use when formatting the resulting timestamp.
    @param ignore_unparsable_time: if True, return False if server_tstamp_str cannot be parsed
                                   using server_format or formatted using local_format.

    @return: server formatted timestamp, expressed in the server timezone if possible
            and if tz_offset is true, or local_tstamp_str if timezone offset could not be determined.
    """
    return _offset_format_timestamp(local_tstamp_str, local_format, server_format, False,
            tz_offset=tz_offset, ignore_unparsable_time=ignore_unparsable_time)

def float_time_convert(float_val):
        hours = math.floor(abs(float_val))
        mins = round(abs(float_val)%1+0.01,2)
        if mins >= 1.0:
            hours = hours + 1
            mins = 0.0
        else:
            mins = mins * 60
        float_time = '%02d:%02d' % (hours,mins)
        return float_time

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

