import os
import sys
import platform
import locale
import optparse
import xmlrpclib
import release
import tools
class environment(object):
    def __init__(self, login, password, dbname, host='localhost', port=8069):
        self.login = login
        self.passwd = password
        self.db = dbname
        self.host = host
        self.port = port

    def get_with_server_info(self):
        try:
            login_socket = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common' % (self.host, self.port))
            self.uid = login_socket.login(self.db, self.login, self.passwd)
            if self.uid:
                print login_socket.get_server_environment() + self.get_client_info()
                login_socket.logout(self.db, self.login, self.passwd)
            else:
                print "bad login or password from "+self.login+" using database "+self.db
        except Exception,e:
                print e
        return True

    def get_client_info(self):
        try:
            rev_id = os.popen('bzr revision-info').read()
            if not rev_id:
                rev_id = 'Bazaar Package not Found !'
        except Exception,e:
            rev_id = 'Exception: %s\n' % (tools.ustr(e))
        environment = 'OpenERP-Client Version : %s\n'\
                      'Last revision No. & ID :%s'\
                      %(release.version,rev_id)
        return environment

if __name__=="__main__":
    uses ="""%prog [options]

Note:
    This script will provide you the full environment information of OpenERP-Client
    If login,password and database are given then it will also give OpenERP-Server Information

Examples:
[1] python environment_info.py
[2] python environment_info.py -l admin -p admin -d test
"""

    parser = optparse.OptionParser(uses)

    parser.add_option("-l", "--login", dest="login", help="Login of the user in Open ERP")
    parser.add_option("-p", "--password", dest="password", help="Password of the user in Open ERP")
    parser.add_option("-d", "--database", dest="dbname", help="Database name")
    parser.add_option("-P", "--port", dest="port", help="Port",default=8069)
    parser.add_option("-H", "--host", dest="host", help="Host",default='localhost')

    (options, args) = parser.parse_args()
    parser = environment(options.login, options.password, dbname = options.dbname, host = options.host, port = options.port)
    if not(options.login and options.password and options.dbname):
        client_info = parser.get_client_info()

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
                    %(platform.release(), platform.version(), platform.architecture()[0],
                      os_lang, platform.python_version())

        print environment + client_info
        print '\nFor server Information you need to pass database(-d), login(-l),password(-p)'
        sys.exit(1)

    else:
        parser.get_with_server_info()
