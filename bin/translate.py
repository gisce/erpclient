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

import sys
import os
import locale
import release
import gettext
import gtk
import logging

#from tools import call_log
#locale.setlocale = call_log(locale.setlocale)
#locale.getdefaultlocale = call_log(locale.getdefaultlocale)

_LOCALE2WIN32 = {
    "af_ZA":"Afrikaans_South Africa",
    "sq_AL":"Albanian_Albania",
    "ar_DZ":"Arabic_Algeria",
    "ar_BH":"Arabic_Bahrain",
    "ar_EG":"Arabic_Egypt",
    "ar_IQ":"Arabic_Iraq",
    "ar_JO":"Arabic_Jordan",
    "ar_KW":"Arabic_Kuwait",
    "ar_LB":"Arabic_Lebanon",
    "ar_LY":"Arabic_Libya",
    "ar_MA":"Arabic_Morocco",
    "ar_OM":"Arabic_Oman",
    "ar_QA":"Arabic_Qatar",
    "ar_SA":"Arabic_Saudi Arabia",
    "ar_SY":"Arabic_Syria",
    "ar_TN":"Arabic_Tunisia",
    "ar_YE":"Arabic_Yemen",
    "az_AZ":"Azeri (Cyrillic)_Azerbaijan",
    "az_AZ":"Azeri (Latin)_Azerbaijan",
    "eu_ES":"Basque_Spain",
    "be_BY":"Belarusian_Belarus",
    "bg_BG":"Bulgarian_Bulgaria",
    "ca_ES":"Catalan_Spain",
    "zh_HK":"Chinese_Hong Kong",
    "zh_MO":"Chinese_Macau",
    "zh_CN":"Chinese_People's Republic of China",
    "zh_SG":"Chinese_Singapore",
    "zh_TW":"Chinese_Taiwan",
    "hr_HR":"Croatian_Croatia",
    "cs_CZ":"Czech_Czech Republic",
    "da_DK":"Danish_Denmark",
    "nl_BE":"Dutch_Belgium",
    "nl_NL":"Dutch_Netherlands",
    "en_AU":"English_Australia",
    "en_BZ":"English_Belize",
    "en_CA":"English_Canada",
    "en_CB":"English_Caribbean",
    "en_IE":"English_Ireland",
    "en_JM":"English_Jamaica",
    "en_NZ":"English_New Zealand",
    "en_PH":"English_Republic of the Philippines",
    "en_ZA":"English_South Africa",
    "en_TT":"English_Trinidad y Tobago",
    "en_GB":"English_United Kingdom",
    "en_US":"English_United States",
    "en_ZW":"English_Zimbabwe",
    "et_EE":"Estonian_Estonia",
    "fo_FO":"Faeroese_Faeroe Islands",
    "fa_IR":"Farsi_Iran",
    "fi_FI":"Finnish_Finland",
    "fr_BE":"French_Belgium",
    "fr_CA":"French_Canada",
    "fr_FR":"French_France",
    "fr_LU":"French_Luxembourg",
    "fr_MC":"French_Principality of Monaco",
    "fr_CH":"French_Switzerland",
    "de_AT":"German_Austria",
    "de_DE":"German_Germany",
    "de_LI":"German_Liechtenstein",
    "de_LU":"German_Luxembourg",
    "de_CH":"German_Switzerland",
    "el_GR":"Greek_Greece",
    "iw_IL":"Hebrew_Israel",
    "hu_HU":"Hungarian_Hungary",
    "is_IS":"Icelandic_Iceland",
    "id_ID":"Indonesian_Indonesia",
    "it_IT":"Italian_Italy",
    "it_CH":"Italian_Switzerland",
    "ja_JP":"Japanese_Japan",
    "kk_KZ":"Kazakh_Kazakstan",
    "ko_KR":"Korean_Korea",
    "lv_LV":"Latvian_Latvia",
    "lt_LT":"Lithuanian_Lithuania",
    "mk_MK":"Macedonian_Former Yugoslav Republic of Macedonia",
    "ms_BN":"Malay_Brunei Darussalam",
    "ms_MY":"Malay_Malaysia",
    "no_NO":"Norwegian_Norway",
    "no_NO":"Norwegian (Bokm�l)_Norway",
    "nn_NO":"Norwegian-Nynorsk_Norway",
    "pl_PL":"Polish_Poland",
    "pt_BR":"Portuguese_Brazil",
    "pt_PT":"Portuguese_Portugal",
    "ro_RO":"Romanian_Romania",
    "ru_RU":"Russian_Russia",
    "sr_SP":"Serbian (Cyrillic)_Serbia",
    "sr_SP":"Serbian (Latin)_Serbia",
    "sk_SK":"Slovak_Slovakia",
    "sl_SI":"Slovenian_Slovenia",
    "es_AR":"Spanish_Argentina",
    "es_BO":"Spanish_Bolivia",
    "es_CL":"Spanish_Chile",
    "es_CO":"Spanish_Colombia",
    "es_CR":"Spanish_Costa Rica",
    "es_DO":"Spanish_Dominican Republic",
    "es_EC":"Spanish_Ecuador",
    "es_SV":"Spanish_El Salvador",
    "es_GT":"Spanish_Guatemala",
    "es_HN":"Spanish_Honduras",
    "es_MX":"Spanish_Mexico",
    "es_NI":"Spanish_Nicaragua",
    "es_PA":"Spanish_Panama",
    "es_PY":"Spanish_Paraguay",
    "es_PE":"Spanish_Peru",
    "es_PR":"Spanish_Puerto Rico",
    "es_ES":"Spanish_Spain",
    "es_UY":"Spanish_Uruguay",
    "es_VE":"Spanish_Venezuela",
    "sw_KE":"Swahili_Kenya",
    "sv_FI":"Swedish_Finland",
    "sv_SE":"Swedish_Sweden",
    "tt_TA":"Tatar_Tatarstan",
    "th_TH":"Thai_Thailand",
    "tr_TR":"Turkish_Turkey",
    "uk_UA":"Ukrainian_Ukraine",
    "ur_PK":"Urdu_Islamic Republic of Pakistan",
    "uz_UZ":"Uzbek_Republic of Uzbekistan",
    "vi_VN":"Vietnamese_Viet Nam",
}

def setlang(lang=None):
    APP = release.name
    DIR = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]), 'share', 'locale')
    if not os.path.isdir(DIR):
        DIR = os.path.join(sys.prefix, 'share', 'locale')
    if not os.path.isdir(DIR):
        gettext.install(APP, unicode=1)
        return False
    if lang:
        lc, encoding = locale.getdefaultlocale()
        if not encoding:
            encoding = 'UTF-8'
        elif encoding.lower() in ('utf','utf8',):
            encoding = 'UTF-8'
        elif encoding == 'cp1252':
            encoding = '1252'

        lang2 = lang
        if os.name == 'nt':
            lang2 = _LOCALE2WIN32.get(lang, lang)
            os.environ['LANG'] = lang
        elif os.name == 'mac':
            encoding = 'UTF-8'

        lang_enc = str(lang2 + '.' + encoding)
        try:
            locale.setlocale(locale.LC_ALL, lang_enc)
        except Exception,e:
            logging.getLogger('translate').warning(
                    _('Unable to set locale %s: %s') % (lang_enc,e))

        lang = gettext.translation(APP, DIR, languages=[lang], fallback=True)
        lang.install(unicode=1)
    else:
        try:
            if os.name == 'nt':
                os.environ['LANG'] = ''
            locale.setlocale(locale.LC_ALL, '')
        except:
            logging.getLogger('translate').warning('Unable to set locale !')
        gettext.bindtextdomain(APP, DIR)
        gettext.textdomain(APP)
        gettext.install(APP, unicode=1)
    gtk.glade.bindtextdomain(APP, DIR)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

