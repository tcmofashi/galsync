import socketserver
import threading
import socket
import sync
import time
import copy
import logging

BUFFERSIZE=1024
TIMEOUT=20
socket.setdefaulttimeout(TIMEOUT)

class DataExchange:

    def cfg_send(self,cacheCfg):
        self.dataClipCache(cacheCfg.encode())
        time.sleep(0.5)
        self.request.sendall('SEND'.encode())
        data=self.request.recv(BUFFERSIZE)
        if data.decode(errors='ignore')!='ACK':
            raise ConnectionResetError('ERROR HANDSHAKE')
        self.request.sendall(str(len(cacheCfg.encode())).encode())
        data=self.request.recv(BUFFERSIZE)
        if data.decode(errors='ignore')!='ACK':
            raise ConnectionResetError('ERROR HANDSHAKE')
        while True:
            response=self.dataClipGet()
            if not response:
                self.request.sendall('Fin'.encode())
                break
            self.request.sendall(response)

    def cfg_recv(self):
        data=self.request.recv(BUFFERSIZE)
        if data.decode(errors='ignore')=='SEND':
            self.request.sendall('ACK'.encode())
            logging.debug(f'config exchange handshake success')
        else:
            raise ConnectionResetError('ERROR HANDSHAKE')
        data=self.request.recv(BUFFERSIZE)
        length=int(data.decode())
        self.request.sendall('ACK'.encode())
        
        cfg=b''
        while True:
            data=self.request.recv(BUFFERSIZE)
            if length-len(cfg)>len(data):
                cfg+=data
            else:
                logging.debug('length expand')
                cfg+=data
                if cfg[length:].decode() =='Fin':
                    break
        sync.CONFIG.merge(cfg[:length].decode(errors='ignore'))

    def data_recv(self):
        #recv
        data=self.request.recv(BUFFERSIZE)
        if data.decode(errors='ignore')=='SEND':
            self.request.sendall('ACK'.encode())
        else:
            raise ConnectionResetError('ERROR HANDSHAKE')
        name=None
        length=None
        recv_data=b''
        while True:
            data=self.request.recv(BUFFERSIZE*1024*8)
            if name is None:
                if data.decode(errors='ignore')=='FinAll':
                    break
                name=data.decode(errors='ignore')
                self.request.sendall('ACK'.encode())
                logging.debug(f'recv {data.decode(errors='ignore')}')
                data=self.request.recv(BUFFERSIZE)
                length=int(data.decode())
                self.request.settimeout(length//BUFFERSIZE)
                self.request.sendall('ACK'.encode())
                cnt=1
                continue
            if length-len(recv_data)>len(data):
                recv_data+=data
            else:
                logging.debug("length expand")
                recv_data+=data
                if recv_data[length:].decode(errors='ignore')=='Fin':
                    sync.CONFIG.extractData(name,recv_data[:length])
                    name=None
                    recv_data=b''
                    self.request.sendall('ACK'.encode())
                    continue
        time.sleep(0.5)
        self.request.settimeout(TIMEOUT)
    
    def data_sand(self):
        # send
        self.request.sendall('SEND'.encode())
        data=self.request.recv(BUFFERSIZE)
        if data.decode(errors='ignore')!='ACK':
            raise ConnectionResetError('ERROR HANDSHAKE')
        sendname=None
        cnt=0
        while True:
            response=self.dataClipGet()
            if not response:
                logging.debug('no cache data')
                ret=sync.CONFIG.genData()
                if sendname is not None:
                    logging.debug(f'Fin {sendname}')
                    self.request.sendall('Fin'.encode())
                    data=self.request.recv(BUFFERSIZE)
                    logging.debug(f"recv ack {data.decode(errors='ignore')}")
                    if data.decode(errors='ignore')!='ACK':
                        raise ConnectionResetError('ERROR HANDSHAKE')
                if ret:
                    sendname,senddata=ret
                    bzip=senddata.read()
                    self.dataClipCache(bzip)
                    time.sleep(0.5)
                    logging.debug(f'start {sendname}')
                    self.request.sendall(sendname.encode())
                    data=self.request.recv(BUFFERSIZE)
                    logging.debug(f"recv ack {data.decode(errors='ignore')}")
                    if data.decode(errors='ignore')!='ACK':
                        raise ConnectionResetError('ERROR HANDSHAKE')

                    self.request.sendall(str(len(bzip)).encode())
                    data=self.request.recv(BUFFERSIZE)
                    self.request.settimeout(len(bzip)//BUFFERSIZE)
                    logging.debug(f"recv ack {data.decode(errors='ignore')}")
                    if data.decode(errors='ignore')!='ACK':
                        raise ConnectionResetError('ERROR HANDSHAKE')
                    continue
                else:
                    time.sleep(0.5)
                    logging.debug(f'Fin All')
                    self.request.sendall('FinAll'.encode())
                    break
            self.request.sendall(response)
        self.request.settimeout(TIMEOUT)

# file io
# config recv
# config send
# 
class ServerHandler(socketserver.BaseRequestHandler,DataExchange):
    """
    处理客户端请求的请求处理器类。
    """
    connect_flag=0    
    def handle(self):
        self.cache=None
        try:
            logging.debug(f'get request from {self.client_address[0]}:{self.client_address[1]}')
            self.pre_handshake()
            self.stage_config_exchange()
            logging.debug(f'config exchange success')
            self.stage_data_exchange()
            self.connect_flag=0
        except ConnectionResetError:
            print('connect reset')
            self.connect_flag=0
        except RuntimeError:
            print('connect reset')
        finally:
            print(f"Connection closed with {self.client_address[0]}:{self.client_address[1]}")

    def dataClipCache(self,data):
        if self.cache is None or len(self.cache)<=0:
            self.cache=bytearray()
        self.cache+=data
    
    def dataClipGet(self):
        if self.cache is None:
            return False
        if len(self.cache)<=0:
            return False
        length=(BUFFERSIZE-1) if len(self.cache)>(BUFFERSIZE-1) else len(self.cache)
        ret=copy.deepcopy(self.cache[:length])
        del self.cache[:length]
        return ret
    
    def pre_handshake(self):
        data=self.request.recv(BUFFERSIZE)
        logging.debug(f'pre_handshake data:{data.decode(errors='ignore')}')
        if data.decode(errors='ignore')=='208' and self.connect_flag==0:
            self.request.sendall('200'.encode())
            self.connect_flag=1
            logging.debug(f'pre_handshake success')
        elif data.decode(errors='ignore')=='208' and self.connect_flag!=0:
            self.request.sendall('503'.encode())
            logging.debug(f'pre_handshake failed')
            time.sleep(5)
            raise RuntimeError('Client is running')
        else:
            raise ConnectionResetError('ERROR HANDSHAKE')


    def stage_config_exchange(self):
        self.cfg_recv() 
        cacheCfg=sync.CONFIG.send()       
        self.cfg_send(cacheCfg)
    
    def stage_data_exchange(self):
        self.data_recv()
        self.data_sand()        

class ClientHandler(DataExchange):
    """
    处理客户端请求的请求处理器类。
    """

    def __init__(self,socket_request:socket.socket) -> None:
        self.request=socket_request
        self.cache=None

    def handle(self):
        try:
            logging.debug(f'connect success')
            self.pre_handshake()
            logging.debug(f'handshake success')
            self.stage_config_exchange()
            logging.debug(f'config exchange success')
            self.stage_data_exchange()
        except ConnectionResetError:
            print('connect reset')
        finally:
            print(f"Connection closed")

    def dataClipCache(self,data):
        if self.cache is None or len(self.cache)<=0:
            self.cache=self.cache=bytearray()
        self.cache+=data
    
    def dataClipGet(self):
        if self.cache is None:
            return False
        if len(self.cache)<=0:
            return False
        length=(BUFFERSIZE) if len(self.cache)>(BUFFERSIZE) else len(self.cache)
        ret=copy.deepcopy(self.cache[:length])
        del self.cache[:length]
        return ret
    
    def pre_handshake(self):
        self.request.sendall('208'.encode())
        data=self.request.recv(BUFFERSIZE)
        if data.decode(errors='ignore')=='200' :
            pass
        elif data.decode(errors='ignore')=='503':
            raise ConnectionRefusedError('Server is busy')
        else:
            raise ConnectionResetError('ERROR HANDSHAKE')


    def stage_config_exchange(self):
        cacheCfg=sync.CONFIG.send()
        self.cfg_send(cacheCfg)
        self.cfg_recv()        
        
    
    def stage_data_exchange(self):
        self.data_sand()
        self.data_recv()
          


class DualStackTCPServer(socketserver.TCPServer):
    """
    双栈 TCP 服务器类，同时监听 IPv4 和 IPv6。
    """
    address_family = socket.AF_INET6
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        # 设置 IPV6_V6ONLY 选项为 False，允许同时监听 IPv4 和 IPv6
        self.socket = socket.socket(self.address_family, self.socket_type)
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)

class TCPHandler:
    def __init__(self, host='::', port=65432):
        self.host = host
        self.port = sync.CONFIG.defaultPort
        self.server = None
        self.server_thread = None

    def start_server(self):
        """启动服务器"""
        self.server = DualStackTCPServer((self.host, self.port), ServerHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"Server started on {self.host}:{self.port}")

    def stop_server(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()
            print("Server stopped")

    def connect_to_server(self, target_host, target_port):
        """主动连接到其他服务器"""
        ret=False
        logging.debug(f'connect to {target_host}:{target_port}')
        try:
            while ServerHandler.connect_flag!=0:
                time.sleep(5)
            ServerHandler.connect_flag=2
            if ':' in target_host:
                client_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                client_socket.connect((target_host, target_port,0,0))
            else:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((target_host, target_port))
            ClientHandler(client_socket).handle()
            ret=True
        # return ret
        except (socket.timeout, ConnectionRefusedError, OSError,ConnectionResetError) as e:
            print(f"Failed to connect to {target_host}:{target_port} - {e}")
            ret=False
        finally:
            ServerHandler.connect_flag=0
            return ret
        
    def run_connect(self):
        iplists=sync.CONFIG.genAvailableIp()
        for i in range(2):
            iplist=iplists[i]
            for server in iplist:
                self.connect_to_server(server[0],server[1])
        rec_idx=[]
        for i in range(2,4):    
            for j,device_ips in enumerate(iplists[i]):
                if j in rec_idx:
                    continue
                for ip in device_ips:
                    if self.connect_to_server(ip[0],ip[1]):
                        rec_idx.append(j)
                        break


class loop:
    run_flag=0
    def __init__(self,handler,delay) -> None:
        self.handler=handler
        self.delay=delay
    def sync_loop(self):
        while self.run_flag==1:
            self.handler.run_connect()
            if self.run_flag!=1:
                break
            time.sleep(self.delay)

if __name__ == "__main__":
    handler = TCPHandler()
    handler.start_server()
    
    try:
        loop_thread=None
        while True:
            cmd = input("Enter command (or 'stop' to stop the server): ")
            if cmd.lower() == 'stop':
                if loop_thread is not None:
                    loop.run_flag=0
                handler.stop_server()
                break
            elif cmd.lower()=='sync':
                handler.run_connect()
            elif cmd.lower().startswith('sync'):
                if loop.run_flag==1:
                    print('sync loop is running!')
                    continue
                delay=cmd.split(' ')[1]
                if delay=='stop':
                    loop.run_flag=0
                    continue
                try:
                    delay=int(delay)
                except:
                    print('usage:sync <seconds> or sync stop')
                    continue
                lp=loop(handler,delay)
                loop.run_flag=1
                loop_thread=threading.Thread(target=lp.sync_loop())
                loop_thread.start()

                
    except KeyboardInterrupt:
        handler.stop_server()