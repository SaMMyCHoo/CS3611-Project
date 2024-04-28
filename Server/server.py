import socket
import threading
import os
import time
from audio import Audio_Server
# Alert: This code has a terrible writing style
HOST = '192.168.3.96'
PORT = 137
aserver = Audio_Server(HOST,80, 4)

def handle_client(client_socket, client_addr, clients):

    # 向客户端发送欢迎消息
    client_socket.send(f'Connected to server successfully'.encode('utf-8'))
    file_address='C:/users/田波/Desktop/login_info.txt'
    login_info=dict()
    path=os.getcwd()
    with open(file_address,"r") as f:
        temp=f.readline()       
        while(temp):
            if(len(temp)==0):
                continue
            name,passwd=temp.split(':')
            name=name.strip()
            passwd=passwd.strip()
            login_info[name]=passwd
            temp=f.readline()
            # print(name,passwd)
    # 验证用户身份
    with open(file_address,"a") as f:
        while True:
            # 接收客户端发送的用户名和密码
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            mode,username, password = data.split(':')
            username=username.strip()
            password=password.strip()
            temp=-1
            if username in login_info.keys():
              temp=login_info[username]
            if(mode=='LOGIN'):
                if(temp==-1):
                    client_socket.send(f'Username does not exists. Please sign up first.'.encode('utf-8'))
                elif(temp==password):
                        # 将客户端加入到在线列表中
                        clients[client_addr] = client_socket
                        client_socket.send(f'Login Succeed!'.encode('utf-8'))
                        break
                else:
                    client_socket.send(f'Login fail. Please try again.'.encode('utf-8'))
            else:
                if(temp!=-1):
                    client_socket.send(f'Username already exists! Please login or use another name.'.encode('utf-8'))
                else:
                    login_info[username]=password
                    f.write(username+':'+password+'\n')
                    clients[client_addr] = client_socket
                    client_socket.send(f'Signup Succeed! Login...'.encode('utf-8'))
                    break
                    
                
 
    # 如果用户验证成功，则开始接收客户端发送的消息并转发给其他客户端

    
    while True:
        info = client_socket.recv(1024).decode('utf-8')
        if(len(info)==0):
            break
        name,data=info.split('@')
        print(name)
        data=data.encode('utf-8')
        if len(data)==0:
            continue
        # 正常文件传输
        elif data[:7].decode('utf-8') == 'FILE_T:':
            for addr, sock in clients.items():
                if addr != client_addr:
                    sock.send(info.encode('utf-8'))
            time.sleep(0.2)
            print("File Transfering...")
            filesize=int(data[7:].decode('utf-8').split('$')[1])
            tot=0
            while(tot<filesize):
                data = client_socket.recv(1024)
                if(not data):
                    break
                for addr, sock in clients.items():
                    if addr != client_addr:
                        sock.send(data)
                tot+=len(data)
            print("Done!")

# import os
# file_path = "E:/tt/abc.py"
# filepath,fullflname = os.path.split(file_path)
# fname,ext = os.path.splitext(fullflname)

        elif data[:7].decode('utf-8') == 'UPLOAD:':
            print("File Uploading...")
            try:
                connected = True
                filename, filesize = data[7:].decode('utf-8').split('$')
                filepath, fullname = os.path.split(filename)
                temp=fullname.split('.')
                origin, extension = '.'.join(temp[:-1]),temp[-1]
                file_path='C:/users/田波/Desktop/'+origin+'_upload.'+extension
                filesize = int(filesize) 
                file_seek=0
                if os.path.exists(file_path):
                    file_seek=os.path.getsize(file_path)
                client_socket.send(f'{name}@LOCAL:{file_seek}'.encode('utf-8'))
                time.sleep(0.2)
                new_size = filesize - file_seek
                with open (file_path, "ab") as f:
                    while new_size:
                        content = client_socket.recv(1024)
                        f.write(content)
                        new_size -= len(content)
                        if content == b'':
                            connected = False
                            break
                if not connected :
                    print("Opps...Client is OUT!")
            except Exception as e:
                print("Error: ", str(e))
                break      
            print("Done!") 

        elif data[:9].decode('utf-8') == 'DOWNLOAD:':
            print("File Downloading...")
            try:
                file_path, localsize= data[9:].decode('utf-8').split('$')
                if not file_path:
                    print("Opps...Not valid path!")
                    break
                print("target path received: ", file_path)
                localsize=int(localsize)
                filesize = int(os.path.getsize(file_path))
                filesize_msg = f'Server@FILE_D:{file_path}${filesize}'.encode('utf-8')
                client_socket.send(filesize_msg)
                time.sleep(0.2)
                with open(file_path, 'rb') as f:
                    f.seek(localsize)
                    while True:
                        filedata = f.read(1024)
                        if not filedata:
                            break
                        client_socket.send(filedata)
            except Exception as e:
                print("Error arose ", str(e))
                break
            print("Done!")
            
        elif data[:5].decode('utf-8')=='MSNG:':# 一般文字信息
            print("Message Sending...")
            tot=0
            msngsize=int(data[5:].decode('utf-8'))
            for addr, sock in clients.items():
                if addr != client_addr:
                    sock.send(info.encode('utf-8'))
            while(tot<msngsize):
                data = client_socket.recv(1024)
                if(not data):
                    break
                for addr, sock in clients.items():
                    if addr != client_addr:
                        sock.send(data)
                tot+=len(data)
            print("Done!")

        elif data[:9].decode('utf-8')=='VoiceEND!':
            print("Ending session...")
            a_sock=data.decode('utf-8').split('$')[1]
            ip,port=a_sock.split('&')
            port=int(port)
            addr=(ip,port)
            aserver.delete(addr)
            client_socket.send("Server@END_DONE".format().encode('utf-8'))
            print('Done!')
            

    # 断开连接
    client_socket.close()
    del clients[client_addr]
    print(f'Server{client_addr}Disappear')

def main():
    # 创建socket对象
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 绑定本地IP和端口
    HOST = '192.168.3.96'
    PORT = 137
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    # 在线客户端列表
    clients = {}

    print('waiting for client...')

    aserver.start()
    
    while True:
        # 接受客户端连接请求
        client_socket, client_addr = server_socket.accept()
        print(f'client{client_addr}connect successful')

        # 使用线程处理客户端请求
        t = threading.Thread(target=handle_client, args=(client_socket, client_addr, clients))
        t.start()

    # 关闭socket
    server_socket.close()

if __name__ == '__main__':
    main()


