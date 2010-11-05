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

class signal_event(object):
    def __init__(self):
        self.__connects = {}

    def signal(self, signal, signal_data=None):
        for fnct,data,key in self.__connects.get(signal, []):
            fnct(self, signal_data, *data)
        return True

    def signal_connect(self, key, signal, fnct, *data):
        self.__connects.setdefault(signal, [])
        if (fnct, data, key) not in self.__connects[signal]:
            self.__connects[signal].append((fnct, data, key))
        return True

    def signal_unconnect(self, key, signal=None):
        if not signal:
            signal = self.__connects.keys()
        else:
            signal = [signal]
        for sig in signal:
            i=0
            while i<len(self.__connects[sig]):
                if self.__connects[sig][i][2]==key:
                    del self.__connects[sig][i]
                else:
                    i+=1
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

