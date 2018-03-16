# -*- coding: utf-8 -*-
from __future__ import with_statement
import rpc
import base64
import socket
import errno
from time import sleep, time
import traceback
import common
import subprocess
import os

CONNECTOR_PATH = os.environ['PROGRAMFILES'] + '\\ScannerApp'
EXECUTABLE_PATH = os.environ['PROGRAMFILES'] + '\\ScannerApp\\connector.exe'

def waiting_server(socket_client, host, port):
    interval = 0.001
    timeout = time() + 10
    while True:
        try:
            socket_client.connect((host, port))
            return socket_client
        except:
            sleep(interval)
            if time() > timeout:
                break
    traceback.print_exc()

def scan(datas, wait_server=False):

    try:
        if datas['id']:
            host = 'localhost'
            port = 5772
            buffer = 4096
            socket_client = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM, proto=0)
            if wait_server:
                waiting_server(socket_client, host, port)
            else:
                socket_client.connect((host, port))
            socket_client.setblocking(0)
            socket_client.send('open')

            categories_ids = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.attachment.category', 'search', [])
            categories = rpc.session.rpc_exec_auth('/object', 'execute', 'ir.attachment.category', 'read',
                                                   categories_ids, ['code', 'name'], rpc.session.context)
            socket_client.send(str(categories))

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
                        try:
                            attachment = eval(recv)
                            document_name = attachment['attachment'].rsplit('/', 1)[1]  # document name
                            with open(attachment['attachment'], 'rb') as f:
                                content = f.read()
                            # Set attachment to resource
                            if attachment['resource'] != 'Por defecto' and datas['model'] == 'giscedata.polissa':
                                if attachment['resource'] == 'Titular':
                                    datas['id'] = rpc.session.rpc_exec_auth(
                                        '/object', 'execute', 'giscedata.polissa', 'read', datas['id'], ['titular'],
                                        rpc.session.context
                                    )['titular'][0]
                                    datas['model'] = 'res.partner'
                                elif attachment['resource'] == 'CUPS':
                                    datas['id'] = rpc.session.rpc_exec_auth(
                                        '/object', 'execute', 'giscedata.polissa', 'read', datas['id'], ['cups'],
                                        rpc.session.context
                                    )['cups'][0]
                                    datas['model'] = 'giscedata.cups.ps'
                            elif attachment['resource'] != 'Por defecto' and datas['model'] == 'giscedata.cups.ps':
                                if attachment['resource'] == 'Titular':
                                    pol_id = rpc.session.rpc_exec_auth(
                                        '/object', 'execute', 'giscedata.cups.ps', 'read', datas['id'], ['polissa_polissa'],
                                        rpc.session.context
                                    )['polissa_polissa'][0]
                                    datas['id'] = rpc.session.rpc_exec_auth(
                                        '/object', 'execute', 'giscedata.polissa', 'read', pol_id, ['titular'],
                                        rpc.session.context
                                    )['titular'][0]
                                    datas['model'] = 'res.partner'
                                elif attachment['resource'] == 'Contrato':
                                    datas['id'] = rpc.session.rpc_exec_auth(
                                        '/object', 'execute', 'giscedata.cups.ps', 'read', datas['id'], ['polissa_polissa'],
                                        rpc.session.context
                                    )['polissa_polissa'][0]
                                    datas['model'] = 'giscedata.polissa'

                            res = rpc.session.rpc_exec_auth(
                                '/object', 'execute', 'ir.attachment', 'create',
                                {
                                    'name': document_name,
                                    'description': attachment['notes'],
                                    'category_id': attachment['category'][:2],
                                    'res_model': datas['model'],
                                    'res_id': datas['id'],
                                    'datas': base64.b64encode(content)
                                }
                            )
                            socket_client.send('attached ok')
                        except Exception:
                            socket_client.send('error while attaching')
        else:
            common.warning('You must resource a object', 'Warning')
    except socket.error, code:
        if code[0] == errno.ECONNREFUSED:
            os.chdir(CONNECTOR_PATH)
            subprocess.Popen(EXECUTABLE_PATH)
            scan(datas, wait_server=True)
        traceback.print_exc()
    except Exception:
        traceback.print_exc()