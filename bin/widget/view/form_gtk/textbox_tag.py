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

#
# TODO: recode the whole pango code
#

import gtk
from gtk import glade
import gettext
import pango
import interface
import common
import re
import service
import xml.sax
import xml.sax.handler
from cStringIO import StringIO

class textbox_tag(interface.widget_interface):
    desc_to_attr_table = {
#        'family':[pango.AttrFamily,""],
        'style':[pango.AttrStyle,pango.STYLE_NORMAL],
        'variant':[pango.AttrVariant,pango.VARIANT_NORMAL],
        'weight':[pango.AttrWeight,pango.WEIGHT_NORMAL],
        'stretch':[pango.AttrStretch,pango.STRETCH_NORMAL],
        }
    pango_translation_properties={
            pango.ATTR_SIZE : 'size',
            pango.ATTR_WEIGHT: 'weight',
            pango.ATTR_UNDERLINE: 'underline',
            pango.ATTR_STRETCH: 'stretch',
            pango.ATTR_VARIANT: 'variant',
            pango.ATTR_STYLE: 'style',
            pango.ATTR_SCALE: 'scale',
            pango.ATTR_STRIKETHROUGH: 'strikethrough',
            pango.ATTR_RISE: 'rise',
            }
    attval_to_markup={
            'underline':{pango.UNDERLINE_SINGLE:'single',
                         pango.UNDERLINE_DOUBLE:'double',
                         pango.UNDERLINE_LOW:'low',
                         pango.UNDERLINE_NONE:'none'},
            'stretch':{pango.STRETCH_ULTRA_EXPANDED:'ultraexpanded',
                       pango.STRETCH_EXPANDED:'expanded',
                       pango.STRETCH_EXTRA_EXPANDED:'extraexpanded',
                       pango.STRETCH_EXTRA_CONDENSED:'extracondensed',
                       pango.STRETCH_ULTRA_CONDENSED:'ultracondensed',
                       pango.STRETCH_CONDENSED:'condensed',
                       pango.STRETCH_NORMAL:'normal',
                       },
            'variant':{pango.VARIANT_NORMAL:'normal',
                       pango.VARIANT_SMALL_CAPS:'smallcaps',
                       },
            'style':{pango.STYLE_NORMAL:'normal',
                     pango.STYLE_OBLIQUE:'oblique',
                     pango.STYLE_ITALIC:'italic',
                     },
            'strikethrough':{1:'true',
                            True:'true',
                            0:'false',
                            False:'false'},
            }
    alignment_markup = {
                gtk.JUSTIFY_FILL : 'JUSTIFY',
                gtk.JUSTIFY_CENTER : 'CENTER',
                gtk.JUSTIFY_RIGHT : 'RIGHT',
                gtk.JUSTIFY_LEFT : 'LEFT'
                }
    html_tags = {
                 'underline':{'single':'u'},
                 'weight':{700:'b'},
                 'strikethrough':{'true':'strike'},
                 'style':{'italic':'i'},
                 'color':{'color':True},
                 'face':{'face':True},
                 }

    def __init__(self,window, parent, model, attrs={}):
        interface.widget_interface.__init__(self, window, parent, model, attrs)
        self.win_gl = glade.XML(common.terp_path("openerp.glade"),"widget_textbox_tag", gettext.textdomain())
        self.widget = self.win_gl.get_widget('widget_textbox_tag')
        self.tv = self.win_gl.get_widget('widget_textbox_tag_tv')
        self.tv.set_wrap_mode(gtk.WRAP_WORD)
        self.tv.connect('focus-out-event', lambda x,y: self._focus_out())
        self.widget.show_all()
        self.tags = {}
        self.tags_dic = {}
        self.buf = self.tv.get_buffer()
        self.tagdict = {}
        self.buf.connect_after('insert-text', self.sig_insert_text)
        self.buf.connect('mark-set', self.sig_mark_set)
        self.value=''
#       self.sizeButton = self.win_gl.get_widget('font_size')
#       self.colorButton =self.win_gl.get_widget('font_color')
        self.boldButton = self.win_gl.get_widget('toggle_bold')
        self.italicButton = self.win_gl.get_widget('toggle_italic')
        self.underlineButton = self.win_gl.get_widget('toggle_underline')
        self.strikethroughButton=self.win_gl.get_widget('toggle_strikethrough')


        self.internal_toggle = False
        self.setup_default_tags ()
        self.win_gl.signal_connect('on_toggle_bold_toggled', self._toggle, [self.bold])
        self.win_gl.signal_connect('on_toggle_italic_toggled', self._toggle, [self.italic])
        self.win_gl.signal_connect('on_toggle_underline_toggled', self._toggle, [self.underline])
        self.win_gl.signal_connect('on_toggle_strike_toggled', self._toggle, [self.strikethrough])
#       self.win_gl.signal_connect('on_font_size_changed',self._font_changed)
#       self.win_gl.signal_connect('on_color_changed',self._color_changed)
        self.win_gl.signal_connect('on_font_button_clicked',self._font_changed)
        self.win_gl.signal_connect('on_color_button_clicked',self._color_changed)


        self.justify = gtk.JUSTIFY_LEFT

        self.leading = 14+7
        self.win_gl.signal_connect('on_radiofill_toggled',self._toggle_justify, gtk.JUSTIFY_FILL)
        self.win_gl.signal_connect('on_radiocenter_toggled',self._toggle_justify, gtk.JUSTIFY_CENTER)
        self.win_gl.signal_connect('on_radioright_toggled',self._toggle_justify, gtk.JUSTIFY_RIGHT)
        self.win_gl.signal_connect('on_radioleft_toggled',self._toggle_justify, gtk.JUSTIFY_LEFT)

    def sig_insert_text(self, textbuffer, iter, text, length):
        start = iter.get_offset()
        end_iter = self.buf.get_iter_at_offset(start-length)
        for tag in self.tags_dic.keys():
            self.buf.apply_tag(tag, end_iter, iter)

    def sig_mark_set(self, textbuffer, iter, texti_mark):
        tags = iter.get_tags()
        is_set = {}
        for tag in tags:
            for key, value in self.tagdict[tag].items():
                if key == 'font_desc' and tag.get_priority() > (key in is_set and is_set[key]) or 0:
#                   self.sizeButton.set_value(int(value[-2:]))
#                   is_set[key] = tag.get_priority()
                    pass
                elif key == 'foreground' and  tag.get_priority() > (key in is_set and is_set[key]) or 0:
#                   self.colorButton.set_color(gtk.gdk.color_parse(value))
#                   is_set[key] = tag.get_priority()
#                   color_priority = tag.get_priority()
                    pass
                elif key == 'weight' and tag.get_priority() > (key in is_set and is_set[key]) or 0:
                    self.boldButton.set_active(True)
                    is_set[key] = tag.get_priority()
                elif key == 'style' and value == 'italic' and tag.get_priority() > (key in is_set and is_set[key]) or 0:
                    self.italicButton.set_active(True)
                    is_set[key] = tag.get_priority()
                elif key == 'underline' and tag.get_priority() > (key in is_set and is_set[key]) or 0:
                    self.underlineButton.set_active(True)
                    is_set[key] = tag.get_priority()
                elif key == 'strikethrough' and tag.get_priority() > (key in is_set and is_set[key]) or 0:
                    self.strikethroughButton.set_active(True)
                    is_set[key] = tag.get_priority()
        #if no color defined, set to defalt (black)
        if not 'foreground' in is_set:
#           self.colorButton.set_color(gtk.gdk.color_parse('#000000'))
            pass
        if not 'font_desc' in is_set:
#           self.sizeButton.set_value(10)
            pass

    def _font_changed(self, widget, event=None):
        font_desc = pango.FontDescription(str(widget.get_font_name()))
#        self.leading = int(widget.get_value()*1.6)
        self.apply_font_and_attrs(font_desc, [])


    def _color_changed(self, widget):
        color  = widget.get_color()
        color_attr = pango.AttrForeground(color.red, color.green, color.blue)
        self.apply_font_and_attrs(None, [color_attr])

    def get_tags_from_attrs (self, font,lang,attrs):
        tags = []
        if font:
            font1,fontattrs = self.fontdesc_to_attrs(font)
            fontdesc = font1.to_string()
            if fontattrs:
                attrs.extend(fontattrs)
            if fontdesc and fontdesc!='Normal':
                if not font1.to_string() in self.tags:
                    tag=self.buf.create_tag()
                    tag.set_property('font-desc',font1)
                    if not tag in self.tagdict: self.tagdict[tag]={}
                    self.tagdict[tag]['face']=str(font.get_family())
                    self.tags[font1.to_string()]=tag
                tags.append(self.tags[font1.to_string()])
        if lang:
            if not lang in self.tags:
                tag = self.buf.create_tag()
                tag.set_property('language',lang)
                self.tags[lang]=tag
            tags.append(self.tags[lang])
        if attrs:
            for a in attrs:

                if a.type == pango.ATTR_FOREGROUND:
                    gdkcolor = self.pango_color_to_gdk(a.color)
                    key = 'foreground%s'%self.color_to_hex(gdkcolor)
                    if not key in self.tags:
                        self.tags[key]=self.buf.create_tag()
                        self.tags[key].set_property('foreground-gdk',gdkcolor)
                        self.tagdict[self.tags[key]]={}
                        self.tagdict[self.tags[key]]['color']="#%s"%self.color_to_hex(gdkcolor)
                    tags.append(self.tags[key])
                if a.type == pango.ATTR_BACKGROUND:
                    gdkcolor = self.pango_color_to_gdk(a.color)
                    tag.set_property('background-gdk',gdkcolor)
                    key = 'background%s'%self.color_to_hex(gdkcolor)
                    if not key in self.tags:
                        self.tags[key]=self.buf.create_tag()
                        self.tags[key].set_property('background-gdk',gdkcolor)
                        self.tagdict[self.tags[key]]={}
                        self.tagdict[self.tags[key]]['background']="#%s"%self.color_to_hex(gdkcolor)
                    tags.append(self.tags[key])
                if a.type in self.pango_translation_properties:
                    prop=self.pango_translation_properties[a.type]
                    val=getattr(a,'value')
                    #tag.set_property(prop,val)
                    mval = val
                    if prop in self.attval_to_markup:
                        if val in self.attval_to_markup[prop]:
                            mval = self.attval_to_markup[prop][val]
                    key="%s%s"%(prop,val)
                    if not key in self.tags:
                        self.tags[key]=self.buf.create_tag()
                        self.tags[key].set_property(prop,val)
                        self.tagdict[self.tags[key]]={}
                        self.tagdict[self.tags[key]][prop]=mval
                    tags.append(self.tags[key])
                else:
                    pass
        return tags

    def get_tags (self, at_pos=None):
        tagdict = {}

        for pos in range(self.buf.get_char_count()):
            iter=self.buf.get_iter_at_offset(pos)
            for tag in iter.get_tags():
                if tag in tagdict:
                    if tagdict[tag][-1][1] == pos - 1:
                        tagdict[tag][-1] = (tagdict[tag][-1][0],pos)
                    else:
                        tagdict[tag].append((pos,pos))
                else:
                    tagdict[tag]=[(pos,pos)]

        new_tagdict = {}
        if at_pos:
            for tag, bound_list in tagdict.items():
                for bound in bound_list:
                    if at_pos >= bound[0] and at_pos < bound[1]:
                        if not tag in new_tagdict:
                            new_tagdict[tag] = []
                        new_tagdict[tag].append(bound)
        else:
            new_tagdict = tagdict
        return new_tagdict

    def get_text (self):
        tagdict=self.get_tags()
        txt = self.buf.get_text(self.buf.get_start_iter(), self.buf.get_end_iter())
        cuts = {}
        for k,v in tagdict.items():
            stag,etag = self.tag_to_markup(k)
            for st,end in v:
                if st in cuts:
                    cuts[st].append(stag) #add start tags second
                else:
                    cuts[st]=[stag]
                if end+1 in cuts:
                    cuts[end+1]=[etag]+cuts[end+1] #add end tags first
                else:
                    cuts[end+1]=[etag]
        last_pos = 0
        outbuff = ""
        cut_indices = cuts.keys()
        cut_indices.sort()
        for c in cut_indices:
            if not last_pos==c:
                txt = unicode(txt)
                outbuff += txt[last_pos:c]
                last_pos = c
            for tag in cuts[c]:
                outbuff += tag
        outbuff += txt[last_pos:]
        outbuff = '<pre><p align="' + self.alignment_markup[self.justify] \
                + '" leading="' + str(self.leading) + '">' + outbuff + '</p></pre>'
        self.value=outbuff
        return outbuff

    def tag_to_markup (self, tag):
        stag="<span"
        for k,v in self.tagdict[tag].items():
            if k in self.html_tags and (k in self.html_tags[k] or v in self.html_tags[k]):
                if k in ['color','face']:
                    stag='<font %s="%s">'%(k,v)
                    etag="</font>"
                else:
                    stag="<"+self.html_tags[k][v]+">"
                    etag="</"+self.html_tags[k][v]+">"
            else:
                stag += ' %s="%s"'%(k,v)
        if stag.startswith('<span'):
            stag += ">"
            etag="</span>"

        return stag,etag

    def fontdesc_to_attrs (self,font):
        nicks = font.get_set_fields().value_nicks
        attrs = []
        for n in nicks:
            if n in self.desc_to_attr_table:
                Attr,norm = self.desc_to_attr_table[n]
                # create an attribute with our current value
                attrs.append(Attr(getattr(font,'get_%s'%n)()))
                # unset our font's value
                getattr(font,'set_%s'%n)(norm)
        return font,attrs

    def pango_color_to_gdk (self, pc):
        return gtk.gdk.Color(pc.red,pc.green,pc.blue)

    def color_to_hex (self, color):
        hexstring = ""
        for col in 'red','green','blue':
            hexfrag = hex(getattr(color,col)/(16*16)).split("x")[1]
            if len(hexfrag)<2: hexfrag = "0" + hexfrag
            hexstring += hexfrag
        return hexstring

    def apply_font_and_attrs (self, font, attrs):
        tags = self.get_tags_from_attrs(font,None,attrs)
        for t in tags: self.apply_tag(t)

    def remove_font_and_attrs (self, font, attrs):
        tags = self.get_tags_from_attrs(font,None,attrs)
        for t in tags: self.remove_tag(t)

    def setup_default_tags (self):
        self.italic = self.get_tags_from_attrs(None,None,[pango.AttrStyle('italic')])[0]
        self.bold = self.get_tags_from_attrs(None,None,[pango.AttrWeight('bold')])[0]
        self.underline = self.get_tags_from_attrs(None,None,[pango.AttrUnderline('single')])[0]
        self.strikethrough = self.get_tags_from_attrs(None,None,[pango.AttrStrikethrough(1)])[0]

    def get_selection (self):
        bounds = self.buf.get_selection_bounds()
        if not bounds:
            iter=self.buf.get_iter_at_mark(self.buf.get_mark('insert'))
            if iter.inside_word():
                start_pos = iter.get_offset()
                iter.forward_word_end()
                word_end = iter.get_offset()
                iter.backward_word_start()
                word_start = iter.get_offset()
                iter.set_offset(start_pos)
                bounds = (self.buf.get_iter_at_offset(word_start),
                        self.buf.get_iter_at_offset(word_end))
        return bounds

    def apply_tag (self, tag):
        insert_iter = self.buf.get_iter_at_mark(self.buf.get_insert())
        selection = self.get_selection()
        self.tags_dic[tag] = True
        if selection:
            self.buf.apply_tag(tag, *selection)
        else:
            self.buf.apply_tag(tag, insert_iter, insert_iter)

    def remove_tag (self, tag):
        if tag in self.tags_dic:
            del self.tags_dic[tag]
        selection = self.get_selection()
        if selection:
            self.buf.remove_tag(tag,*selection)

    def remove_all_tags (self):
        self.tags_dic = {}
        selection = self.get_selection()
        if selection:
            for t in self.tags.values():
                self.buf.remove_tag(t,*selection)

    def set_text (self, txt):
        buf = self.tv.get_buffer()
#        txt = re.sub('<p align[^>]*>', '<p>', txt)
        try:
            txt = txt.replace('strike','s')

            alignres = txt.find("LEFT")
            if alignres != -1:
                self.tv.set_justification(gtk.JUSTIFY_LEFT)
                txt = txt.replace('<pre><p align="LEFT" leading="21">','')

            alignres = txt.find("RIGHT")
            if alignres != -1:
                self.tv.set_justification(gtk.JUSTIFY_RIGHT)
                txt = txt.replace('<pre><p align="RIGHT" leading="21">','')

            alignres = txt.find("CENTER")
            if alignres != -1:
                self.tv.set_justification(gtk.JUSTIFY_CENTER)
                txt = txt.replace('<pre><p align="CENTER" leading="21">','')

            alignres = txt.find("JUSTIFY")
            if alignres != -1:
                self.tv.set_justification(gtk.JUSTIFY_FILL)
                txt = txt.replace('<pre><p align="JUSTIFY" leading="21">','')

            alignres = txt.find("LEFT")

            txt = txt.replace('</p></pre>','')
            parsed, txt, separator = pango.parse_markup(txt)
        except Exception ,e:
            pass

        try:
            attrIter = parsed.get_iterator()
        except Exception ,e:
#            common.warning("Either the Message contains HTML tags or the selected Fonts are not supported!",'User Error')
#            self._focus_out()
            return False
        buf.delete(buf.get_start_iter(), buf.get_end_iter())
        while True:
            range=attrIter.range()
            font,lang,attrs = attrIter.get_font()
            tags = self.get_tags_from_attrs(font, lang, attrs)
            text = txt[range[0]:range[1]]
            if tags:
                buf.insert_with_tags(buf.get_end_iter(), text, *tags)
            else:
                buf.insert_with_tags(buf.get_end_iter(), text)
            if not attrIter.next():
                break

    #
    # Button callback
    #
#   def setup_widget_from_pango (self, widg, markupstring):
#       """setup widget from a pango markup string"""
#       #font = pango.FontDescription(fontstring)
#       a,t,s = pango.parse_markup(markupstring,u'0')
#       ai=a.get_iterator()
#       font,lang,attrs=ai.get_font()
#       self.setup_widget(widg,font,attrs)
#
#   def setup_widget (self, widg, font, attr):
#       tags=self.get_tags_from_attrs(font,None,attr)
#       self.tag_widgets[tuple(tags)]=widg
#       widg.connect('toggled',self._toggle,tags)

    def _toggle (self, widget, tags):
        if self.internal_toggle: return
        if widget.get_active():
            for t in tags: self.apply_tag(t)
        else:
            for t in tags: self.remove_tag(t)


    def _toggle_justify (self, widget, justify):
        if widget.get_active():
            self.tv.set_justification(justify)
            self.justify = justify
        else:
            self.tv.set_justification(gtk.JUSTIFY_LEFT)
            self.justify = gtk.JUSTIFY_LEFT

    def _mark_set_cb (self, buffer, iter, mark, *params):
        if mark==self.insert:
            for tags,widg in self.tag_widgets.items():
                active = True
                for t in tags:
                    if not iter.has_tag(t):
                        active=False
                self.internal_toggle=True
                widg.set_active(active)
                self.internal_toggle=False

    def display(self, model, model_field):
        self.remove_all_tags()
        super(textbox_tag, self).display(model, model_field)
        value = model_field and model_field.get(model)
        if not self.value:
            self.value=value or ''
        self.set_text(self.value)

    def set_value(self, model, model_field):
        model_field.set_client(model, self.get_text() or False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

