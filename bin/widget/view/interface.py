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


import service

class parser_interface(object):
    def __init__(self, window=None, parent=None, attrs={}, screen=None):
        if window is None:
            window = service.LocalService('gui.main').window
        self.window = window
        self.parent = parent
        self.attrs = attrs
        self.title = None
        self.buttons = {}
        self.screen = screen

class parser_view(object):
    def __init__(self, window, screen, widget, children=None, state_aware_widgets=None, toolbar=None, submenu=None):
        if window is None:
            window = service.LocalService('gui.main').window
        self.window = window
        self.screen = screen
        self.widget = widget
        self.state_aware_widgets = state_aware_widgets or []

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

