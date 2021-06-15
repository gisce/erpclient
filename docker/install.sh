DIR="$(dirname $0)"
SRC_DIR="$DIR/.."
if [ ! -f ~/.openerprc ]; then
    cat > ~/.openerprc <<EOF
[extensions]
filetype = {'pdf': ('/usr/bin/evince', 'pdf')}
EOF
fi

if [ ! -f ~/.local/share/applications/openerp5.desktop ]; then
    cat > ~/.local/share/applications/openerp5.desktop <<EOF
[Desktop Entry]
Encoding=UTF-8
Version=1.0
Type=Application
Terminal=false
Name=OpenERP 5.0
Exec=$DIR/erpclient.sh
Icon=$SRC_DIR/bin/pixmaps/openerp-icon.png
StartupNotify=true
Actions=New
EOF
fi

