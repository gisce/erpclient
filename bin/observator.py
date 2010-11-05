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

try:
    set
except NameError:
    from sets import Set as set


class ObservatorRegistry(object):
    def __new__(cls):
        if not hasattr(cls, '_inst'):
            cls._inst = object.__new__(cls)
        return cls._inst

    def __init__(self):
        self._observables = {}
        self._receivers = {}

    def add_observable(self, oid, obj):
        self._observables[oid] = obj

    def add_receiver(self, signal, callable):
        if signal not in self._receivers:
            self._receivers[signal] = []
        self._receivers[signal].append(callable)
    
    def remove_receiver(self, signal, callable):
        self._receivers[signal].remove(callable)

    def warn(self, *args):
        for receiver in self._receivers.get(args[0], []):
            receiver(*args[1:])

oregistry = ObservatorRegistry()


class Observable(object):
    def __init__(self):
        oregistry.add_observable(id(self), self)

    def warn(self, *args):
        oregistry.warn(args[0], self, *args[1:])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

