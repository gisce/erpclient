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
import logging
def logged(showtime):
    def log(f, res, *args, **kwargs):
        vector = ['Call -> function: %s' % f]
        for i, arg in enumerate(args):
            vector.append( '  arg %02d: %r' % ( i, arg ) )
        for key, value in kwargs.items():
            vector.append( '  kwarg %10s: %r' % ( key, value ) )
        vector.append( '  result: %r' % res )
        logging.getLogger('debug').info("\n".join(vector))

    def outerwrapper(f):
        def wrapper(*args, **kwargs):
            if showtime:
                import time
                now = time.time()
            res = None
            try:
                res = f(*args, **kwargs)
                return res
            finally:
                log(f, res, *args, **kwargs)
                if showtime:
                    logging.getLogger('wrapper').info("  time delta: %s" % (time.time() - now))
        return wrapper
    return outerwrapper


def debug(what):
    """
        This method allow you to debug your code without print
        Example:
        >>> def func_foo(bar)
        ...     baz = bar
        ...     debug(baz)
        ...     qnx = (baz, bar)
        ...     debug(qnx)
        ...
        >>> func_foo(42)

        This will output on the logger:

            [Wed Dec 25 00:00:00 2008] DEBUG:func_foo:baz = 42
            [Wed Dec 25 00:00:00 2008] DEBUG:func_foo:qnx = (42, 42)

        To view the DEBUG lines in the logger you must start the server with the option
            --log-level=debug

    """
    from inspect import stack
    import re
    from pprint import pformat
    st = stack()[1]
    param = re.split("debug *\((.+)\)", st[4][0].strip())[1].strip()
    while param.count(')') > param.count('('): param = param[:param.rfind(')')]
    what = pformat(what)
    if param != what:
        what = "%s = %s" % (param, what)
    logging.getLogger(st[3]).debug(what)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
