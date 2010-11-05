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
import common
import re

import workflow_print

plugins_repository = {
    'workflow_print_simple': {'model':'.*', 'string':_('Print Workflow'), 'action': workflow_print.wkf_print_simple },
    'workflow_print': {'model':'.*', 'string':_('Print Workflow (with subflows)'), 'action': workflow_print.wkf_print },
}

def execute(datas):
    result = {}
    for p in plugins_repository:
        if not 'model_re' in plugins_repository[p]:
            plugins_repository[p]['model_re'] = re.compile(plugins_repository[p]['model'])
        res = plugins_repository[p]['model_re'].search(datas['model'])
        if res:
            result[plugins_repository[p]['string']] = p
    if not len(result):
        common.message(_('No available plugin for this resource !'))
        return False
    sel = common.selection(_('Choose a Plugin'), result, alwaysask=True)
    if sel:
        plugins_repository[sel[1]]['action'](datas)
    return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

