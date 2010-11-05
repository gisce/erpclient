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
import datetime
import locale

import win32ui
import win32con
try:
    import winxpgui as win32gui
except:
    import win32gui

if not hasattr(locale, 'nl_langinfo'):
    def nl_langinfo(param):
        val = time.strptime('30/12/2004', '%d/%m/%Y')
        dt = datetime.datetime(*val[:-2])
        format_date = dt.strftime('%x')
        for x, y in [('30','%d'),('12','%m'),('2004','%Y'),('04','%Y')]:
            format_date = format_date.replace(x,y)
        return format_date
    locale.nl_langinfo = nl_langinfo


    if not hasattr(locale, 'D_FMT'):
        locale.D_FMT = None

def get_systemfont_style():
    # Get DC
    hdc = win32gui.GetDC(0)
    # Get system DPI
    dpi = win32ui.GetDeviceCaps(hdc, win32con.LOGPIXELSY)
    # Get system font, it's name and size
    z = win32gui.SystemParametersInfo(win32con.SPI_GETNONCLIENTMETRICS)
    font = z['lfMessageFont']
    font_name = font.lfFaceName
    font_size = int(round(abs(font.lfHeight) * 72 / dpi))
    # Release DC
    win32gui.ReleaseDC(0, hdc)
    # Construct sytle for all widget
    font_style = '''
        style "openerp-user-font" {
            font_name = "%s %s"
        }
        widget_class "*" style "openerp-user-font"
    ''' % (font_name, font_size)
    return font_style
