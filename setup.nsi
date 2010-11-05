##############################################################################
#
# Copyright (c) 2004-2008 Tiny SPRL (http://tiny.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
###############################################################################
!ifndef VERSION
    !error "Do not forget to specify the version of OpenERP - /DVERSION=<VERSION>"
!endif 

;--------------------------------
;Include Modern UI

!include "MUI.nsh"

;--------------------------------
;General

;Name and file
Name "OpenERP Client"
OutFile "openerp-client-setup-${VERSION}.exe"
SetCompressor lzma
SetCompress auto

;Default installation folder
InstallDir "$PROGRAMFILES\OpenERP Client"

;Get installation folder from registry if available
InstallDirRegKey HKLM "Software\OpenERP Client" ""

BrandingText "OpenERP Client ${VERSION}"

;Vista redirects $SMPROGRAMS to all users without this
RequestExecutionLevel admin

Var MUI_TEMP
Var STARTMENU_FOLDER

;--------------------------------
;Interface Settings

!define MUI_ABORTWARNING
!define REGKEY "SOFTWARE\$(^Name)"
!define MUI_LANGDLL_REGISTRY_ROOT HKLM
!define MUI_LANGDLL_REGISTRY_KEY ${REGKEY}
!define MUI_LANGDLL_REGISTRY_VALUENAME InstallerLanguage

!insertmacro MUI_RESERVEFILE_LANGDLL

;--------------------------------
;Pages


!define MUI_ICON ".\bin\pixmaps\openerp-icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP ".\bin\pixmaps\openerp-intro.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP ".\bin\pixmaps\openerp-intro.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH
!define MUI_HEADER_TRANSPARENT_TEXT ""
!define MUI_HEADERIMAGE_BITMAP ".\bin\pixmaps\openerp-slogan.bmp"
!define MUI_LICENSEPAGE_TEXT_BOTTOM "$(LicenseText)"
!define MUI_LICENSEPAGE_BUTTON "$(LicenseNext)"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "doc\License.rtf"
!insertmacro MUI_PAGE_DIRECTORY
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM" 
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\OpenERP Client"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "OpenERP Client"
!insertmacro MUI_PAGE_STARTMENU Application $STARTMENU_FOLDER
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_CHECKED
!define MUI_FINISHPAGE_RUN_TEXT "$(FinishPageText)" 
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME $INSTDIR\README.txt
!insertmacro MUI_PAGE_FINISH

  
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"

!macro CreateInternetShortcut FILENAME URL
	WriteINIStr "${FILENAME}.url" "InternetShortcut" "URL" "${URL}"
!macroend


Function .onInit
!ifndef ALLINONE
    ;Language selection dialog
    Push ""
    Push ${LANG_ENGLISH}
    Push English
    Push ${LANG_FRENCH}
    Push French
    Push A ; A means auto count languages
    ; for the auto count to work the first empty push (Push "") must remain
    LangDLL::LangDialog "Installer Language" "Please select the language of the installer"

    Pop $LANGUAGE
    StrCmp $LANGUAGE "cancel" 0 +2
        Abort
!endif
    ClearErrors
    ReadRegStr $0 HKLM "Software\OpenERP Client" ""
    IfErrors DoInstall 0
        MessageBox MB_OK "$(CannotInstallClientText)"
        Quit
    DoInstall:
FunctionEnd

Section "OpenERP Client" SecOpenERPClient
	SetOutPath "$INSTDIR"
  
	;ADD YOUR OWN FILES HERE...
	File /r "dist\*"

	SetOutPath "$INSTDIR\GTK"
	File /r "C:\GTK\*"

	SetOutPath "$INSTDIR\doc"
	File "doc\*"

	;Store installation folder
	WriteRegStr HKLM "Software\OpenERP Client" "" $INSTDIR

!ifndef ALLINONE
	;Create uninstaller
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OpenERP Client" "DisplayName" "OpenERP Client ${VERSION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\OpenERP Client" "UninstallString" "$INSTDIR\Uninstall.exe"
!else
        WriteRegStr HKLM  "Software\OpenERP AllInOne" "UninstallClient" "$INSTDIR\Uninstall.exe"
!endif 
	WriteUninstaller "$INSTDIR\Uninstall.exe"

	!insertmacro MUI_STARTMENU_WRITE_BEGIN Application

	;Create shortcuts
	CreateDirectory "$SMPROGRAMS\$STARTMENU_FOLDER"
	!insertmacro CreateInternetShortcut "$SMPROGRAMS\$STARTMENU_FOLDER\Documentation" "http://www.openerp.com"
!ifndef ALLINONE
        CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Uninstall.lnk" "$INSTDIR\uninstall.exe"
!endif
	CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\OpenERP Client.lnk" "$INSTDIR\openerp-client.exe"
        CreateShortCut "$DESKTOP\OpenERP Client.lnk" "$INSTDIR\openerp-client.exe"

	!insertmacro MUI_STARTMENU_WRITE_END

SectionEnd

 
;--------------------------------
;Uninstaller Section

Section "Uninstall" 
	;ADD YOUR OWN FILES HERE...
	RMDIR /r "$INSTDIR" 

	!insertmacro MUI_STARTMENU_GETFOLDER Application $MUI_TEMP

	Delete "$SMPROGRAMS\$MUI_TEMP\Documentation.url"
	Delete "$SMPROGRAMS\$MUI_TEMP\OpenERP Client.lnk"
!ifndef ALLINONE
	Delete "$SMPROGRAMS\$MUI_TEMP\Uninstall.lnk"
!endif 
        Delete "$DESKTOP\OpenERP Client.lnk"

	;Delete empty start menu parent diretories
	StrCpy $MUI_TEMP "$SMPROGRAMS\$MUI_TEMP"

startMenuDeleteLoop:
	ClearErrors
	RMDir $MUI_TEMP
	GetFullPathName $MUI_TEMP "$MUI_TEMP\.."

	IfErrors startMenuDeleteLoopDone

	StrCmp $MUI_TEMP $SMPROGRAMS startMenuDeleteLoopDone startMenuDeleteLoop
startMenuDeleteLoopDone:

!ifndef ALLINONE
	DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\OpenERP Client"
!else 
        DeleteRegKey HKLM "Software\OpenERP AllInOne\UninstallClient"
!endif
	DeleteRegKey /ifempty HKLM "Software\OpenERP Client"

SectionEnd

Function LaunchLink
	ExecShell "" "$INSTDIR\openerp-client.exe"
FunctionEnd


LangString LicenseText ${LANG_ENGLISH} "Usually, a proprietary license is provided with the software: limited number of users, limited in time usage, etc. This Open Source license is the opposite: it garantees you the right to use, copy, study, distribute and modify Open ERP for free."
LangString LicenseText ${LANG_FRENCH} "Normalement, une licence propriétaire est fournie avec le logiciel: limitation du nombre d'utilisateurs, limitation dans le temps, etc. Cette licence Open Source est l'opposé: Elle vous garantie le droit d'utiliser, de copier, d'étudier, de distribuer et de modifier Open ERP librement."

LangString LicenseNext ${LANG_ENGLISH} "Next >"
LangString LicenseNext ${LANG_FRENCH} "Suivant >"

LangString FinishPageText ${LANG_ENGLISH} "Start OpenERP Client"
LangString FinishPageText ${LANG_FRENCH} "Lancer le client OpenERP"

;Language strings
LangString DESC_SecOpenERPClient ${LANG_ENGLISH} "OpenERP Client."
LangString DESC_SecOpenERPClient ${LANG_FRENCH} "Client OpenERP."

LangString CannotInstallClientText ${LANG_ENGLISH} "Can not install the Open ERP Client because a previous installation already exists on this system. Please uninstall your current installation and relaunch this setup wizard."
LangString CannotInstallClientText ${LANG_FRENCH} "Ne peut pas installer le client Open ERP parce qu'une installation existe déjà sur ce système. S'il vous plait, désinstallez votre installation actuelle et relancer l'installeur."


;Assign language strings to sections
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
	!insertmacro MUI_DESCRIPTION_TEXT ${SecOpenERPClient} $(DESC_SecOpenERPClient)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

