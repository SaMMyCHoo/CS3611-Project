import socket
import threading
import os
from tkinter import *
from tkinter import scrolledtext
from tkinter import messagebox
import time
import argparse
from audio import Audio_Client
# pip install tk if you're going to use

# Alert: This code has a terrible writing style
Nickname=['']
filedata=[False,0]
Nowaudio=[None]
Session=[False]

def recv_data(sock, window):

    while True:
        info = sock.recv(1024).decode('utf-8')
        if(len(info)==0):
            break
        name,data=info.split('@')
        print(name)
        if not data:
            break
        
        if data[:5] == 'FILE_':
            print('[Client] Begin to receive file...')
            print('[Client] ', data[7:])
            Mode=data[5]
            if(Mode=='T'):
                Mode='transmit'
            else:
                name='Me'
                Mode='download'
            print("Mode: {}".format(Mode))
            filename, filesize = data[7:].split('$')
            filepath,fullname = os.path.split(filename)
            origin, extension = fullname.split('.')
            filesize = int(filesize)
            # 保存路径
            newfile = 'C:/Users/Sammy/Desktop/'+origin+'_'+Mode+'.'+extension
            with open(newfile, 'ab') as f:
                total_size = 0
                while total_size < filesize:
                    data = sock.recv(1024)
                    f.write(data)
                    total_size += len(data)
            print('[Client] File received.')
            window['state'] = 'normal'
            window.insert(INSERT, f'{name}: Succeeded {Mode}ing file: {filename}({filesize} bytes)\n')
            window.insert(INSERT, 'File saved in: ' + newfile+'\n')
            window['state'] = 'disabled'
        elif data[:6]=='LOCAL:':
            filedata[0]=True
            filedata[1]=int(data[6:])
        elif data[:5]=='MSNG:':# 一般文字信息
            msng=''
            msngsize=int(data[5:])
            while(len(msng)<msngsize):
                msng+=sock.recv(1024).decode('utf-8')
            print("New message:", msng)
            window['state'] = 'normal'
            window.insert(INSERT, name+': ' + msng+'\n')
            window['state'] = 'disabled'
            # new_text = Label(window, text=data)
            # new_text.pack(side='top')
        elif data[:4]=='END_':
            Session[0]=True

def main():
    # Creating Socket and Connect to the Server
    server_ip = '47.120.39.175'
    server_port = 137
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    Online = False

    # Making Graphical Interfaces
    window = Tk()
    window.title("Chat Window")
    window.geometry("800x600")
    # Label
    lbl_server = Label(window, text=client_socket.recv(1024).decode('utf-8'))
    lbl_server.place(x=310, y=150)
    lbl = Label(window, text="Please login or sign up")
    lbl.place(x=340, y=180)
    lbl_username = Label(window, text="Username: ")
    lbl_username.place(x=290, y=270)
    lbl_password = Label(window, text="Password: ")
    lbl_password.place(x=290, y=310)
    # Entry
    txt_username = Entry(window, width=20)  
    txt_username.place(x=390, y=270)
    txt_password = Entry(window, width=20)
    txt_password.config(show='*')
    txt_password.place(x=390, y=310)
    # Button
    # Making new screens
    def OnlineScreen():
        # Making Chat Displaying Screen
        display = scrolledtext.ScrolledText(window, bg='lightblue', state='disabled')
        display.place(width=750, height=380, x=20, y=10)
        # Receiving Messages
        t = threading.Thread(target=recv_data, args=(client_socket,display))
        t.start()
        # t.join()
        # Sending Messages
        message = scrolledtext.ScrolledText(window)
        message.place(width=600, height=180, x=20, y=400)
        
        def SendMessage():
            data = message.get(1.0, END)[:-1]
            if(len(data)==0):
                return
            data_ty = '{}@'.format(Nickname[0])+'MSNG:'+ str(len(data))
            client_socket.send(data_ty.encode('utf-8'))
            time.sleep(0.2)
            display['state'] = 'normal'
            display.insert(INSERT, 'Me: '+data+'\n')
            display['state'] = 'disabled'
            if client_socket.send(data.encode('utf-8')) :
                print("A message has been sent successfully: ", data.encode('utf-8'))
            message.delete(1.0, END)
            
        def TransmitFile():
            print("ready to get message")
            filename = message.get(1.0, END)[:-1]
            print('Ready to send file: ', filename)
            filesize = os.path.getsize(filename)
            print('Get file size: ', filesize)
            filesize_msg = f'{Nickname[0]}@FILE_T:{filename}${filesize}'.encode('utf-8')
            client_socket.send(filesize_msg)
            time.sleep(0.2)
            with open(filename, 'rb') as f:
                while True:
                    filedata = f.read(1024)
                    if not filedata:
                        break
                    client_socket.send(filedata)
            display['state'] = 'normal'
            display.insert(INSERT, f'Me: Succeeded sending file: {filename}({filesize} bytes)\n')
            display['state'] = 'disabled'
            message.delete(1.0, END)
            
        def UploadFile():
            def print_bar(percent):
                bar = '\r' + '*' * int((percent * 100)) + ' %3.0f%%|' % (percent*100) + '100%'
                print(bar, end = '', flush = True)
            file_path = message.get(1.0, END)[:-1]
            if len(file_path) == 0: 
                return
            file_size = os.path.getsize(file_path)
            info=f'{Nickname[0]}@UPLOAD:{file_path}${file_size}'.encode('utf-8')
            client_socket.send(info)
            time.sleep(0.2)
            print("checkpoint 1")
            while(not filedata[0]):
                continue
            file_seek = filedata[1]
            filedata[0]=False
            print("checkpoint 2")
            if file_seek == file_size:
                print("Target ALREADY exits in the server side, exit......")
            else:
                new_size = file_size - file_seek
                begin_size = new_size
                with open(file_path, "rb") as f:
                    f.seek(file_seek)
                    while new_size:
                        content = f.read(1024)
                        client_socket.send(content)
                        new_size -= len(content)
                        print_bar(round((begin_size - new_size) / begin_size, 2))
                    print("")
            display['state'] = 'normal'
            display.insert(INSERT, f'Me: Succeeded uploading file: {file_path}({file_size} bytes)\n')
            display['state'] = 'disabled'
            message.delete(1.0, END)
            
        def DownloadFile():
            file_path = message.get(1.0, END)[:-1]
            if len(file_path) == 0: 
                return
            filepath,fullname = os.path.split(file_path)
            temp=fullname.split('.')
            origin, extension = '.'.join(temp[:-1]),temp[-1]
            # 保存路径
            ddpath = 'C:/Users/Sammy/Desktop/'+origin+'_download.'+extension      
            local_size=0
            if(os.path.exists(ddpath)):
                local_size=os.path.getsize(ddpath)
            info=f'{Nickname}@DOWNLOAD:{file_path}${local_size}'.encode('utf-8')
            client_socket.send(info)
            time.sleep(0.2)
            #发送文件传输请求
            message.delete(1.0, END)
        
        def Audiochat(switch): 
            try: 
                print(switch)       
                if switch=='1':
                    print("New Session started.")
                    if(Nowaudio[0]):
                        return
                    aclient = Audio_Client(server_ip, 80, 4)
                    Nowaudio[0]=aclient
                    aclient.start()
                    Session[0]=False
                else:
                    print("Ending Session...")
                    aclient=Nowaudio[0]
                    if not aclient:
                        print("WTF???")
                        return
                    sock=aclient.sockname()
                    str_sock=sock[0]+'&'+str(sock[1])
                    client_socket.send(f'{Nickname[0]}@VoiceEND!${str_sock}'.encode('utf-8'))
                    while not Session[0]:
                        time.sleep(0.2)
                        continue
                    aclient.__del__()
                    print("clear!")
                    Nowaudio[0]=None
                # print('switch: {}'.format(switch))
            except Exception as e:
                print(e)
                return
                
                    
        btn_send = Button(window, text="    Send    ", command=SendMessage)
        btn_send.place(x=660, y=400)
        
        btn_transmit = Button(window, text=" Transmit  ", command=TransmitFile)
        btn_transmit.place(x=660, y=435)
        
        btn_upload = Button(window, text="   Upload   ", command=UploadFile)
        btn_upload.place(x=660, y=470)
        
        btn_download = Button(window, text="Download ", command=DownloadFile)
        btn_download.place(x=660, y=505)
        
        btn_audiochat = Scale(window, label="Voice?",length=60,from_=0,to=1,orient='horizontal',showvalue=0, command=Audiochat)
        OFF=Label(window,text='OFF',width=3,height=2)
        OFF.place(x=645,y=553)
        ON =Label(window,text='ON',width=3,height=2)
        ON.place(x=740,y=553)
        # btn_audiochat.set(0)
        btn_audiochat.place(x=675, y=540)

    # Login
    def Login():
        username = txt_username.get()
        password = txt_password.get()
        client_socket.send(f'LOGIN:{username}:{password}'.encode('utf-8'))
        data = client_socket.recv(1024).decode('utf-8')
        if data == 'Login Succeed!':
            Nickname[0]=username
            messagebox.showinfo(title='Message',message=data)
            Online = True
            lbl.destroy()
            lbl_server.destroy()
            lbl_username.destroy()
            lbl_password.destroy()
            txt_username.destroy()
            txt_password.destroy()
            btn_login.destroy()
            btn_signup.destroy()
            OnlineScreen()
        else:
            messagebox.showwarning(title='Warning',message=data)
    def Signup():
        username = txt_username.get()
        password = txt_password.get()
        client_socket.send(f'SIGNUP:{username}:{password}'.encode('utf-8'))
        data = client_socket.recv(1024).decode('utf-8')
        if data == 'Signup Succeed! Login...':
            Nickname[0]=username
            messagebox.showinfo(title='Message',message='Signup Succeed! Welcome!')
            Online = True
            lbl.destroy()
            lbl_server.destroy()
            lbl_username.destroy()
            lbl_password.destroy()
            txt_username.destroy()
            txt_password.destroy()
            btn_login.destroy()
            btn_signup.destroy()
            OnlineScreen()
        else:
            messagebox.showwarning(title='Warning',message=data)          
    btn_login = Button(window, text="Log in ", command=Login)
    btn_login.place(x=335, y=370)
    btn_signup = Button(window, text="Sign up", command=Signup)
    btn_signup.place(x=410, y=370)
    window.mainloop()


    # Close
    client_socket.close()


if __name__ == '__main__':
    main()