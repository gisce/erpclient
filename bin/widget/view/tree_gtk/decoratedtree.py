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
import observator


class DecoratedTreeView(gtk.TreeView, observator.Observable):
    """This class extend a TreeView to be api compatible with EditableTreeView
    """

    def __init__(self, position):
        super(DecoratedTreeView, self).__init__()
        self.editable = position
        self.cells = {}

    def get_columns(self, include_non_visible=True, include_non_editable=True):
        if not include_non_editable:
            return []   # all columns are non editables
        columns = super(DecoratedTreeView, self).get_columns()
        if not include_non_visible:
            columns = filter(lambda c: c.get_visible(), columns)
        return columns

    def set_value(self):
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

