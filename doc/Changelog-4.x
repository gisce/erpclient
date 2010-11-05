4.2.1
	Fix parent for attachment window
	Fix Accentued folder can't be imported on win32
	Fix opening one2many if there is no line selected
	Fix Concurency exception for netrpx protocol
	Fix search on new field type
	Improve widget_search for unknown widget type
	Fix missing import service in module
	New chinese translation
	Don't allow to create new ressource on readonly reference field

4.2.0
	Summary:
		Add new view graph
		Add hpaned and action in form view (board)
		Improve ergonomics
		Add relate functionality to list view
		Add a context to one2many
		Add new protocol netrpc (speed improvment)
		Remove glade from widget (speed improvment)
		Improve memory usage
		Allow to translate with right-click
		Allow invisible columns in tree view
		Allow icons on buttons
		Better detection of record change
		Improve login, logout, close behavior
		Add new widget float_time
		Improve editable list view
		Add options for tabs position
		Add support fir rtl/ltr depend of the user language
		Better color for readonly fields
		Add timezone to display datetime fields in local timezone
		Improve pda mode
		Allow search on fields translatable
		Add on_change function on one2many fields
		Add concurrency check when writing the same record
		Allow to specify many view_ids in act_window
		Improve search window
		Be more failure tolerant
		New relate implementation base on act_window
		Add limit/offset in list view
		Modify default form on act_window (tree,form)
		Add new home button for board
		Don't write fields that have not been modified
		Add sum tag on list view to display the sum of the selected lines
		Add shortcut in the menu bar
		Add widgets callto and sip (for voip)
		Add shortcut in one2many (F1, F2)
		Use Toggle renderer for boolean field in list view
		Add minimal structure for futur calendar view
	Bugfixes:
		Use the digits attributes
		Improve file selection dialog
		Fix transient on window
		Fix Gtk warning
		Fix date for different locales
		Fix double signal on some widget
		Fix readonly in calendar widget
		Fix tooltips inside group
		Use the action name for tabs name
		Add local context when calling action
		Fix defunc process when printing reports
		Use user lang for locale
		Improve win32 compilation
		Update models fields attributes when switching view
		Fix state behavior in many2one dialog
		Don't raise string exception for python 2.5
		English locale is en_US
		Fix progress bar in the wizard execution
		Stock the attributes of the fields in the models and keep the
		originals
		Improve rpc for exception "cannot marshall None"
		Fix tip of the day to use the client lang

16/03/2007
4.0.3
	Summary:
		Some bugfixes
	Bugfixes:
		Fix the set default value fonctionality
		Fix translation of some text field
		Fix double signal emit in some cases
		Improve color fields
		Fix transient of some windows
		Fix local date to force 4 digits for years
		Fix print report from tree view
		Improve load data when exception occurs
		Fix height of wizard dialog
		Add epdfview to the pdf viewers
		Fix cancel if there is no current model
		Fix set icon if there is no icon selected
		Fix print workflow on win32
		Add error message when printing from linux without preview

Wed Jan 17 15:13:18 CET 2007
4.0.2
	Summary:
		Some bugfixes

	Bugfixes:
		Fix transient for windows for win attachement
		Fix regexp for name server
		Fix filename on selection dialog

Fri Dec 22 12:12:24 CET 2006
4.0.1
	Summary:
		Some bugfixes
	
	Bugfixes:
		Fix restore DB to be able to change server
		Add error message on xmlrpc exception in import window

Mon Dec 4 18:01:55 CET 2006
4.0.0
	Summary:
		Some bugfixes

Tue Nov 28 14:44:44 CET 2006
4.0.0
	Improvements:
		New Menu design: simpler
		Right toolbar for: report, action, relate on each forms
		Add titles and icons in wizards windows
		Progress bar for slow operations
		Better ergonomy in editable lists
			some bugfixes
		Opens directly in the partner menu
		Better contextual help for most windows

-----------------------------------------------------------------------

Fri Oct  6 14:44:05 CEST 2006
Client 3.4.2
    Bugfixes:
        Fix on_change call when activating (ie pressing enter on) a integer 
            (spinint) or float (spinbutton) widget

------------------------------------------------------------------------

Tue Sep 12 15:10:31 CEST 2006
Client 3.4.1
    No changes since 3.4.0. Changed version number anyway to keep in sync with
    server version.

------------------------------------------------------------------------

Mon Sep 11 16:12:10 CEST 2006
Client 3.4.0
    New features:
        Added a checkbox for the 'Secure connection' option at login window
        Added support for saving/using predefined exports
        Added theme support within the client 
        Added tooltips on each fields (using help= on the server side)
        Added the possibility to have completion in many2one fields.
            You have to add a completion="True" attribute in views
            Sample screenshot here:
                http://vcc.163.googlepages.com/editcompletion2.JPG

    Improvements:
        Better import and export system from/to CSV: more powerfull and usable
        Export functinality now support one2many and many2many fields
        Single click to develop tree nodes
        Fixed and improved a lot the image widget
        Use a scrolled window when there are multiple attachments
        Several parts of the client were improved for speed 
        Use a better title for the search window
        Better editable trees
        Use a file selector to browse for the file to add as attachment, also
            for the 'Add as link' button

    Bugfixes:
        Fixed a long-standing bug which made form widgets look ugly with a 
            frame/not behave nicely towards themed widgets
        Fixed modal windows problems on Windows
        Added frame to selection widgets in the search dialog to be consistent
            with other widgets
        Checkbox not checked by default in the option menu
        Miscellaneous minor bugfixes

    Translations:
        Updated source translation file (.pot file)

    Packaging:
        Distribute 3 nice GTK themes with the client

------------------------------------------------------------------------

Fri May 19 10:16:18 CEST 2006
Client 3.3.0
    Improvements:
        Implemented 3-button choice when quitting an unsaved record, additionally,
            it automatically cancel the close if "yes" was selected but the form 
            is invalid
        Use better icon
        Moved icon in the pixmaps directory
        Use the helper function to find the pixmaps file
        Added support for OpenOffice2 for the "preview in editor" functionality
        Issue warning message when an invalid value was used in a selection field
        Set the frame around the form viewport to SHADOW_NONE

        Changed shortcuts:
            Ctrl Z : Repeat last action
            Ctrl R : Reload
            PgUp   : Previous
            PgDown : Next
            Ctrl X : Not used anymore, so that it can be used in textareas for cut
                     and paste

    Bugfixes:
        Fixed a crash bug which occured in some complex circumstances
        Modification of an existing resource sometimes created a new one instead
        Fixed date widgets (it gets a value even if it doesn't get the focus)
        Fixed the lines coloring functionality in list mode
        The "invalid form" message must appear even if the form is saved through 
            a button on the form (and not with the save button)
        Unset status message when doing a reload
        When clicking twice in a row on a calendar widget arrow, the widget
            doesn't close anymore
        Raise the number of characters in datetime fields to 19, so that datetime
            fields work with other locales
        Other miscellaneous bugfixes

------------------------------------------------------------------------
Client 3.3.0-rc1
================

Client completly recoded from scratch !!! (using a MVC pattern)

Lots of bugs removed

Better Ergonomy
    Everything at the keyboard:
        Search, zoom, new entry, ...
        Cursor always at the right place (first field of a search, ...)

    Switch list/form in one2many fields

    Set Default Values on One2many fields

Better Exception message for integrity and constraint errors.

Better search form

List are editable !
    Like in Excel, for lists on one2many fields
    Just put <tree editable="top/bottom"> in the tree view

New fields
    E-Mail
    Website
    Fields one2many and one2many_list merged

Wizard are now translated

Speed Improvement
    Client side cache

    Less requests when opening forms; about 30% times quicker

New PDA mode for smaller screen on a PDA

Preparation of a non-connected client (allows you to work on a cache and
prefetch a cache for mobile usage) -> not 100% finnished !

Support of XML-RPC over HTTPS

Code reduced by 30% with more functionnalities !

