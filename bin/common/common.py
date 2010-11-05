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
import gobject
from cgi import escape
import tools
import gettext

import os
import sys
import platform
import release
import common
import logging
from options import options
import service
import locale
import ConfigParser

import threading
import time

import rpc
#
# Upgrade this number to force the client to ask the survey
#
SURVEY_VERSION = '3'

def _search_file(file, dir='path.share'):
    tests = [
        lambda x: os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), x),
        lambda x: os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'pixmaps', x),
        lambda x: os.path.join(options[dir], x),
    ]
    for func in tests:
        x = func(file)
        if os.path.exists(x):
            return x
    return file

terp_path = _search_file
terp_path_pixmaps = lambda x: _search_file(x, 'path.pixmaps')

try:
    OPENERP_ICON = gtk.gdk.pixbuf_new_from_file(terp_path_pixmaps('openerp-icon.png'))
except gobject.GError, e:
    log = logging.getLogger('init')
    log.fatal(str(e))
    log.fatal('Ensure that the file %s is correct' % options.rcfile)
    exit(1)

def selection(title, values, alwaysask=False, parent=None):
    if not values or len(values)==0:
        return None
    elif len(values)==1 and (not alwaysask):
        key = values.keys()[0]
        return (key, values[key])

    xml = glade.XML(terp_path("openerp.glade"), "win_selection", gettext.textdomain())
    win = xml.get_widget('win_selection')
    if not parent:
        parent = service.LocalService('gui.main').window
    win.set_icon(OPENERP_ICON)
    win.set_transient_for(parent)

    label = xml.get_widget('win_sel_title')
    if title:
        label.set_text(title)

    list = xml.get_widget('win_sel_tree')
    list.get_selection().set_mode('single')
    cell = gtk.CellRendererText()
    column = gtk.TreeViewColumn("Widget", cell, text=0)
    list.append_column(column)
    list.set_search_column(0)
    model = gtk.ListStore(gobject.TYPE_STRING)
    keys = values.keys()
    keys.sort()
    
    for val in keys:
        model.append([val])

    list.set_model(model)
    list.connect('row-activated', lambda x,y,z: win.response(gtk.RESPONSE_OK) or True)

    ok = False
    while not ok:
        response = win.run()
        ok = True
        res = None
        if response == gtk.RESPONSE_OK:
            sel = list.get_selection().get_selected()
            if sel:
                (model, iter) = sel
                if iter:
                    res = model.get_value(iter, 0)
                    try:
                        res = (res, values[res.decode('utf8')])
                    except:
                        res = (res, values[res])    
                else:
                    ok = False
            else:
                ok = False
        else:
            res = None
    parent.present()
    win.destroy()
    return res

class upload_data_thread(threading.Thread):
    def __init__(self, email, data, type, supportid):
        self.args = [('email',email),('type',type),('supportid',supportid),('data',data)]
        super(upload_data_thread,self).__init__()
    def run(self):
        try:
            import urllib
            args = urllib.urlencode(self.args)
            fp = urllib.urlopen('http://www.openerp.com/scripts/survey.php', args)
            fp.read()
            fp.close()
        except:
            pass

def upload_data(email, data, type='SURVEY', supportid=''):
    a = upload_data_thread(email, data, type, supportid)
    a.start()
    return True

def terp_survey():
    if options['survey.position']==SURVEY_VERSION:
        return False

    def color_set(widget, name):
        colour = widget.get_colormap().alloc_color(common.colors.get(name,'white'))
        widget.modify_bg(gtk.STATE_ACTIVE, colour)
        widget.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        widget.modify_base(gtk.STATE_NORMAL, colour)
        widget.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        widget.modify_text(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse("black"))

    widnames = ('country','role','industry','employee','hear','system','opensource')
    winglade = glade.XML(common.terp_path("dia_survey.glade"), "dia_survey", gettext.textdomain())
    win = winglade.get_widget('dia_survey')
    parent = service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)
    for widname in widnames:
        wid = winglade.get_widget('combo_'+widname)
        wid.child.set_editable(False)

    email_widget = winglade.get_widget('entry_email')
    want_ebook_widget = winglade.get_widget('check_button_ebook')

    def toggled_cb(togglebutton, *args):
        value = togglebutton.get_active()
        color_set(email_widget, ('normal', 'required')[value])

    want_ebook_widget.connect('toggled', toggled_cb)

    while True:
        res = win.run()
        if res == gtk.RESPONSE_OK:
            email = email_widget.get_text()
            want_ebook = want_ebook_widget.get_active()
            if want_ebook and not len(email):
                color_set(email_widget, 'invalid')
            else:
                company =  winglade.get_widget('entry_company').get_text()
                phone = winglade.get_widget('entry_phone').get_text()
                name = winglade.get_widget('entry_name').get_text()
                city = winglade.get_widget('entry_city').get_text()
                result = "\ncompany: "+str(company)
                result += "\nname: " + str(name)
                result += "\nphone: " + str(phone)
                result += "\ncity: " + str(city)
                for widname in widnames:
                    wid = winglade.get_widget('combo_'+widname)
                    result += "\n" + widname + ": " + wid.child.get_text()
                result += "\nplan_use: " + str(winglade.get_widget('check_use').get_active())
                result += "\nplan_sell: " + str(winglade.get_widget('check_sell').get_active())
                result += "\nwant_ebook: " + str(want_ebook)

                buffer = winglade.get_widget('textview_comment').get_buffer()
                iter_start = buffer.get_start_iter()
                iter_end = buffer.get_end_iter()
                result += "\nnote: " + buffer.get_text(iter_start, iter_end, False)
                upload_data(email, result, type='SURVEY '+str(SURVEY_VERSION))
                options['survey.position']=SURVEY_VERSION
                options.save()
                parent.present()
                win.destroy()
                common.message(_('Thank you for the feedback !\n\
Your comments have been sent to OpenERP.\n\
You should now start by creating a new database or\n\
connecting to an existing server through the "File" menu.'))
                break
        elif res == gtk.RESPONSE_CANCEL or gtk.RESPONSE_DELETE_EVENT:
            parent.present()
            win.destroy()
            common.message(_('Thank you for testing OpenERP !\n\
You should now start by creating a new database or\n\
connecting to an existing server through the "File" menu.'))
            break

    return True

def file_selection(title, filename='', parent=None, action=gtk.FILE_CHOOSER_ACTION_OPEN, preview=True, multi=False, filters=None):
    if action == gtk.FILE_CHOOSER_ACTION_OPEN:
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
    else:
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)

    win = gtk.FileChooserDialog(title, None, action, buttons)
    if not parent:
        parent = service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)
    win.set_current_folder(options['client.default_path'])
    win.set_select_multiple(multi)
    win.set_default_response(gtk.RESPONSE_OK)
    if filters is not None:
        for filter in filters:
            win.add_filter(filter)
    if filename:
        win.set_current_name(filename)

    def update_preview_cb(win, img):
        filename = win.get_preview_filename()
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 128, 128)
            img.set_from_pixbuf(pixbuf)
            have_preview = True
        except:
            have_preview = False
        win.set_preview_widget_active(have_preview)
        return

    if preview:
        img_preview = gtk.Image()
        win.set_preview_widget(img_preview)
        win.connect('update-preview', update_preview_cb, img_preview)

    button = win.run()
    if button!=gtk.RESPONSE_OK:
        win.destroy()
        return False
    if not multi:
        filepath = win.get_filename()
        if filepath:
            filepath = filepath.decode('utf-8')
            try:
                options['client.default_path'] = os.path.dirname(filepath)
            except:
                pass
        parent.present()
        win.destroy()
        return filepath
    else:
        filenames = win.get_filenames()
        if filenames:
            filenames = [x.decode('utf-8') for x in filenames]
            try:
                options['client.default_path'] = os.path.dirname(filenames[0])
            except:
                pass
        parent.present()
        win.destroy()
        return filenames

def support(*args):
    wid_list = ['email_entry','id_entry','name_entry','phone_entry','company_entry','error_details','explanation_textview','remark_textview']
    required_wid = ['email_entry', 'name_entry', 'company_name', 'id_entry']
    support_id = options['support.support_id']
    recipient = options['support.recipient']

    sur = glade.XML(terp_path("openerp.glade"), "dia_support",gettext.textdomain())
    win = sur.get_widget('dia_support')
    parent = service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)
    win.show_all()
    sur.get_widget('id_entry1').set_text(support_id)

    response = win.run()
    if response == gtk.RESPONSE_OK:
        fromaddr = sur.get_widget('email_entry1').get_text()
        id_contract = sur.get_widget('id_entry1').get_text()
        name =  sur.get_widget('name_entry1').get_text()
        phone =  sur.get_widget('phone_entry1').get_text()
        company =  sur.get_widget('company_entry1').get_text()

        urgency = sur.get_widget('urgency_combo1').get_active_text()

        buffer = sur.get_widget('explanation_textview1').get_buffer()
        explanation = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())

        buffer = sur.get_widget('remark_textview').get_buffer()
        remarks = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())

        content = name +"(%s, %s, %s)"%(id_contract, company, phone) +" has reported the following bug:\n"+ explanation + "\nremarks:\n" + remarks

        if upload_data(fromaddr, content, 'support', id_contract):
            common.message(_('Support request sent !'))

    parent.present()
    win.destroy()
    return True

def error(title, message, details='', parent=None, disconnected_mode=False):
    """
    Show an error dialog with the support request or the maintenance
    """
    log = logging.getLogger('common.message')
    details = get_client_environment() + details
    log.error('Message %s: %s' % (str(message),details))

    show_message = True

    if not disconnected_mode:
        maintenance = rpc.session.rpc_exec_auth_try('/object', 'execute', 'maintenance.contract', 'status')

        if maintenance['status'] == 'none':
            maintenance_contract_message=_("""
<b>An unknown error has been reported.</b>

<b>You do not have a valid Open ERP maintenance contract !</b>
If you are using Open ERP in production, it is highly suggested to subscribe
a maintenance program.

The Open ERP maintenance contract provides you a bugfix guarantee and an
automatic migration system so that we can fix your problems within a few
hours. If you had a maintenance contract, this error would have been sent
to the quality team of the Open ERP editor.

The maintenance program offers you:
* Automatic migrations on new versions,
* A bugfix guarantee,
* Monthly announces of potential bugs and their fixes,
* Security alerts by email and automatic migration,
* Access to the customer portal.

You can use the link bellow for more information. The detail of the error
is displayed on the second tab.
""")
        elif maintenance['status'] == 'partial':
            maintenance_contract_message=_("""
<b>An unknown error has been reported.</b>

Your maintenance contract does not cover all modules installed in your system !
If you are using Open ERP in production, it is highly suggested to upgrade your
contract.

If you have developed your own modules or installed third party module, we
can provide you an additional maintenance contract for these modules. After
having reviewed your modules, our quality team will ensure they will migrate
automatically for all future stable versions of Open ERP at no extra cost.

Here is the list of modules not covered by your maintenance contract:
%s

You can use the link bellow for more information. The detail of the error
is displayed on the second tab.""") % (", ".join(maintenance['uncovered_modules']), )
        else:
            show_message = False
    else:
        maintenance_contract_message=_("""
<b>An unknown error has been reported.</b>

<b>You do not have a valid Open ERP maintenance contract !</b>
If you are using Open ERP in production, it is highly suggested to subscribe
a maintenance program.

The Open ERP maintenance contract provides you a bugfix guarantee and an
automatic migration system so that we can fix your problems within a few
hours. If you had a maintenance contract, this error would have been sent
to the quality team of the Open ERP editor.

The maintenance program offers you:
* Automatic migrations on new versions,
* A bugfix guarantee,
* Monthly announces of potential bugs and their fixes,
* Security alerts by email and automatic migration,
* Access to the customer portal.

You can use the link bellow for more information. The detail of the error
is displayed on the second tab.
""")

    xmlGlade = glade.XML(terp_path('win_error.glade'), 'dialog_error', gettext.textdomain())
    win = xmlGlade.get_widget('dialog_error')
    if not parent:
        parent=service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)
    win.set_title("Open ERP - %s" % title)

    xmlGlade.get_widget('title_error').set_markup("<i>%s</i>" % escape(message))

    details_buffer = gtk.TextBuffer()
    details_buffer.set_text(details)
    xmlGlade.get_widget('details_explanation').set_buffer(details_buffer)

    if show_message:
        xmlGlade.get_widget('maintenance_explanation').set_markup(maintenance_contract_message)

    xmlGlade.get_widget('notebook').remove_page(int(show_message))

    if not show_message:
        def send(widget):
            def get_text_from_text_view(textView):
                """Retrieve the buffer from a text view and return the content of this buffer"""
                buffer = textView.get_buffer()
                return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())

            # Use details_buffer
            tb = get_text_from_text_view(xmlGlade.get_widget('details_explanation'))
            explanation = get_text_from_text_view(xmlGlade.get_widget('explanation_textview'))
            remarks = get_text_from_text_view(xmlGlade.get_widget('remarks_textview'))

            if rpc.session.rpc_exec_auth_try('/object', 'execute', 'maintenance.contract', 'send', tb, explanation, remarks):
                common.message(_('Your problem has been sent to the quality team !\nWe will recontact you after analysing the problem.'), parent=win)
                win.destroy()
            else:
                common.message(_('Your problem could *NOT* be sent to the quality team !\nPlease report this error manually at:\n\t%s') % ('http://openerp.com/report_bug.html',), title=_('Error'), type=gtk.MESSAGE_ERROR, parent=win)

        xmlGlade.signal_connect('on_button_send_clicked', send)
        xmlGlade.signal_connect('on_closebutton_clicked', lambda x : win.destroy())

    response = win.run()
    parent.present()
    win.destroy()
    return True

def message(msg, title=None, type=gtk.MESSAGE_INFO, parent=None):
    if not parent:
        parent=service.LocalService('gui.main').window
    dialog = gtk.MessageDialog(parent,
      gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
      type, gtk.BUTTONS_OK)
    msg = to_xml(msg)
    if title is not None:
        msg = '<b>%s</b>\n\n%s' % (to_xml(title), msg)

    dialog.set_icon(OPENERP_ICON)
    dialog.set_markup(msg)
    dialog.show_all()
    dialog.run()
    parent.present()
    dialog.destroy()
    return True

def to_xml(s):
    from cgi import escape
    return escape(s)

def message_box(title, msg, parent=None):
    dia = glade.XML(terp_path("openerp.glade"), "dia_message_box",gettext.textdomain())
    win = dia.get_widget('dia_message_box')
    l = dia.get_widget('msg_title')
    l.set_text(title)

    msg_area = dia.get_widget('msg_tv')
    buffer = msg_area.get_buffer()
    iter_start = buffer.get_start_iter()
    buffer.insert(iter_start, msg)
    msg_area.set_sensitive(False)

    if not parent:
        parent=service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)

    response = win.run()
    parent.present()
    win.destroy()
    return True


def warning(msg, title=None, parent=None):
    return message(msg=msg, title=title, type=gtk.MESSAGE_WARNING, parent=parent)

def sur(msg, parent=None):
    if not parent:
        parent=service.LocalService('gui.main').window
    sur = glade.XML(terp_path("openerp.glade"), "win_sur",gettext.textdomain())
    win = sur.get_widget('win_sur')
    win.set_transient_for(parent)
    win.show_all()
    l = sur.get_widget('lab_question')
    l.set_text(msg)

    if not parent:
        parent=service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)

    response = win.run()
    parent.present()
    win.destroy()
    return response == gtk.RESPONSE_OK

def sur_3b(msg, parent=None):
    sur = glade.XML(terp_path("openerp.glade"), "win_quest_3b",gettext.textdomain())
    win = sur.get_widget('win_quest_3b')
    l = sur.get_widget('label')
    l.set_text(msg)

    if not parent:
        parent=service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)

    response = win.run()
    parent.present()
    win.destroy()
    if response == gtk.RESPONSE_YES:
        return 'ok'
    elif response == gtk.RESPONSE_NO:
        return 'ko'
    elif response == gtk.RESPONSE_CANCEL:
        return 'cancel'
    else:
        return 'cancel'

def ask(question, parent=None):
    dia = glade.XML(terp_path('openerp.glade'), 'win_quest', gettext.textdomain())
    win = dia.get_widget('win_quest')
    label = dia.get_widget('label1')
    label.set_text(question)
    entry = dia.get_widget('entry')

    if not parent:
        parent=service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)

    response = win.run()
    parent.present()
    win.destroy()
    if response == gtk.RESPONSE_CANCEL:
        return None
    else:
        return entry.get_text()

def concurrency(resource, id, context, parent=None):
    dia = glade.XML(common.terp_path("openerp.glade"),'dialog_concurrency_exception',gettext.textdomain())
    win = dia.get_widget('dialog_concurrency_exception')

    if not parent:
        parent=service.LocalService('gui.main').window
    win.set_transient_for(parent)
    win.set_icon(OPENERP_ICON)

    res= win.run()
    parent.present()
    win.destroy()

    if res == gtk.RESPONSE_OK:
        return True
    if res == gtk.RESPONSE_APPLY:
        obj = service.LocalService('gui.window')
        obj.create(False, resource, id, [], 'form', None, context,'form,tree')
    return False

def open_file(value, parent):
    filetype = {}
    if options['client.filetype']:
        if isinstance(options['client.filetype'], str):
            filetype = eval(options['client.filetype'])
        else:
            filetype = options['client.filetype']
    root, ext = os.path.splitext(value)
    cmd = False
    if ext[1:] in filetype:
        cmd = filetype[ext[1:]] % (value)
    if not cmd:
        cmd = file_selection(_('Open with...'),
                parent=parent)
        if cmd:
            cmd = cmd + ' %s'
            filetype[ext[1:]] = cmd
            options['client.filetype'] = filetype
            options.save()
            cmd = cmd % (value)
    if cmd:
        pid = os.fork()
        if not pid:
            pid = os.fork()
            if not pid:
                prog, args = cmd.split(' ', 1)
                args = [os.path.basename(prog)] + args.split(' ')
                try:
                    os.execvp(prog, args)
                except:
                    pass
            time.sleep(0.1)
            sys.exit(0)
        os.waitpid(pid, 0)


# Color set

colors = {
    'invalid':'#ff6969',
    'readonly':'#eeebe7',
    'required':'#d2d2ff',
    'normal':'white'
}

def get_client_environment():
    try:
        rev_id = os.popen('bzr revision-info').read()
        if not rev_id:
            rev_id = 'Bazaar Package not Found !'
    except Exception,e:
        rev_id = 'Exception: %s\n' % (tools.ustr(e))

    os_lang = '.'.join( [x for x in locale.getdefaultlocale() if x] )
    if not os_lang:
        os_lang = 'NOT SET'

    environment = '\nEnvironment Information : \n' \
                     'System : %s\n' \
                     'OS Name : %s\n' \
                     %(platform.platform(), platform.os.name)
    if os.name == 'posix':
      if platform.system() == 'Linux':
         lsbinfo = os.popen('lsb_release -a').read()
         environment += '%s'%(lsbinfo)
      else:
         environment += 'Your System is not lsb compliant\n'
    environment += 'Operating System Release : %s\n' \
                   'Operating System Version : %s\n' \
                   'Operating System Architecture : %s\n' \
                   'Operating System Locale : %s\n'\
                   'Python Version : %s\n'\
                   'OpenERP-Client Version : %s\n'\
                   'Last revision No. & ID :%s'\
                    %(platform.release(), platform.version(), platform.architecture()[0],
                      os_lang, platform.python_version(),release.version,rev_id)
    return environment

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

