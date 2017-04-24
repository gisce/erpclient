from __future__ import with_statement
import rpc
import base64
import sys
import socket
import errno
from time import sleep
import traceback

def scan(datas):

    # Obrir el fitxer
    # Llegir el contingut i guardar-ho a content

    try:
        host = 'localhost'
        port = 5772
        buffer = 4096
        socket_client = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM, proto=0)
        socket_client.connect((host, port))
        socket_client.setblocking(0)

        socket_client.send('open')
        while True:
            try:
                recv = socket_client.recv(buffer)
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    sleep(1)
                    #  No data to recv
                    continue
                else:
                    traceback.print_exc()
                    return
            else:
                if recv == 'close':
                    socket_client.close()
                    break
                elif datas['id']:
                    content = recv.rsplit('/', 1)[1] #  recive document name

                    with open(recv, 'rb') as f:
                        lines = f.read()
                    res = rpc.session.rpc_exec_auth(
                        '/object', 'execute', 'ir.attachment', 'create',
                        {
                            'name': content,
                            'res_model': datas['model'],
                            'res_id': datas['id'],
                            'datas': base64.b64encode(lines)
                        }
                    )
    except Exception:
        traceback.print_exc()