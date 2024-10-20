import socketserver
import threading
import socket


# file io
# config recv
# config send
# 
class CustomHandler(socketserver.BaseRequestHandler):
    """
    处理客户端请求的请求处理器类。
    """
    mode='recv'
    recv_mode=0
    fileinfo={}
    config_recv={}
    def handle(self):
        try:
            while True:

                if self.mode=='recv':
                    data = self.request.recv(1024)
                    flag=self.Controller(data)
                    if flag==1:
                        break
                    elif flag==2:
                        continue
                    print("successful handshake")

                    # print(f"Received from {self.client_address[0]}:{self.client_address[1]} - {data.decode()}")
                    self.process(data)
                    response = f"Echo: {data.decode()}"
                    self.request.sendall(response.encode())
                elif self.mode=='send':
                    data_send=self.send()
                    self.request.sendall(data_send)
        except ConnectionResetError:
            pass
        finally:
            print(f"Connection closed with {self.client_address[0]}:{self.client_address[1]}")
    
    # def setup(self):
    #     key=f"{self.client_address[0]}:{self.client_address[1]}"
    #     self.config_recv[key]=b''
    
    # def before(self):
    #     key=f"{self.client_address[0]}:{self.client_address[1]}"
    #     if self.recv_mode==0:
    #         if key not in self.fileinfo.keys():
    #             raise RuntimeError("filename not set")
    #         if self.fileinfo[key]['io']=='recv':
    #             self.fp=open(self.fileinfo[key]['path'],'wb')
    #         elif self.fileinfo[key]['io']=='send':
    #             self.fp=open(self.fileinfo[key]['path'],'rb')
    #     elif self.recv_mode==2:
    #         self.request.sendall('SEND'.encode())
    #         pass
    
    # def confirm(self, data):
    #     if data.decode()=='SEND':
    #         self.mode='recv'
    #         self.request.sendall('ACK'.encode())
    #     if data.decode()=='ACK':
    #         self.mode='send'
    #         return True
    #     else:
    #         return False

    # def process(self,data):
    #     key=f"{self.client_address[0]}:{self.client_address[1]}"
    #     if self.recv_mode==0:
    #         self.fp.write(data)
    #     elif self.recv_mode==1:
    #         self.config_recv[key]+=data

    # def Controller(self,data):
    #     if data.decode()=='Fin':
    #         return True
    #     else:
    #         return False




class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    多线程 TCP 服务器类。
    """
    pass

class TCPHandler:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None

    def start_server(self):
        """启动服务器"""
        self.server = ThreadedTCPServer((self.host, self.port), CustomHandler)
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
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((target_host, target_port))
        print(f"Connected to {target_host}:{target_port}")

    def send_to_client(self, client_socket, message):
        """向特定客户端发送消息"""
        try:
            client_socket.sendall(message.encode())
        except Exception as e:
            print(f"Failed to send message to client: {e}")

    def send_to_target_server(self, message):
        """向目标服务器发送消息"""
        if self.client_socket:
            try:
                self.client_socket.sendall(message.encode())
                response = self.client_socket.recv(1024)
                print(f"Response from target server: {response.decode()}")
            except Exception as e:
                print(f"Failed to send message to target server: {e}")

    def broadcast(self, message):
        """向所有连接的客户端广播消息"""
        for request_handler in self.server._services.values():
            if isinstance(request_handler, ThreadedTCPRequestHandler):
                self.send_to_client(request_handler.request, message)

# 使用示例
if __name__ == "__main__":
    handler = TCPHandler()
    handler.start_server()
    
    try:
        while True:
            cmd = input("Enter command (or 'stop' to stop the server): ")
            if cmd.lower() == 'stop':
                handler.stop_server()
                break
            elif cmd:
                handler.broadcast(cmd)
    except KeyboardInterrupt:
        handler.stop_server()