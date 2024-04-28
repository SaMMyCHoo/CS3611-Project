from socket import *
import threading
import pyaudio
import wave
import sys
import zlib
import struct
import pickle
import time
import numpy as np
import queue

CHUNK = 1024
FORMAT = pyaudio.paInt16    # 格式
CHANNELS = 2    # 输入/输出通道数
RATE = 44100    # 音频数据的采样频率
RECORD_SECONDS = 0.5    # 记录秒

class Audio_Server(threading.Thread):
    def __init__(self,ip, port, version) :
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.ADDR = (ip, port)
        if version == 4:
            self.sock = socket(AF_INET ,SOCK_STREAM)
        else:
            self.sock = socket(AF_INET6 ,SOCK_STREAM)
        self.p = pyaudio.PyAudio()  # 实例化PyAudio,并于下面设置portaudio参数
        self.stream = None
        self.dic_client={}
        self.voice=[]
        self.set_voice=set()

    def __del__(self):
        self.sock.close()   # 关闭套接字
        if self.stream is not None:
            self.stream.stop_stream()   # 暂停播放 / 录制
            self.stream.close()     # 终止流
        self.p.terminate()      # 终止会话
        print("\nwtf?\n")

    def receive_audio(self,sock,tot_clients):
        payload_size = struct.calcsize("L")     # 返回对应于格式字符串fmt的结构，L为4
        try:
            while True:
                data = "".encode("utf-8")
                while len(data) < payload_size:
                    data += sock[0].recv(86167+4)    #86167+4
                # if len(tot_clients.keys())>=2:
                print("size {}".format(len(data)))
                print("来自{}的数据:".format(sock[0]))
                self.dic_client[sock].put(data)
                # print("Only one ,clear data {}".format(len(data)))
                # for cl in self.dic_client.keys():
                #     if cl != conn:
                #         cl.sendall(data)
        except Exception as e:
            print("\nReceiving Error!!,disconnected with {}\n".format(sock[0]))
            try:
                sock[0].close()
            except:
                print('\ng\n')
            print("receive Done!")
            # print("receive audio failed!! {}".format(e))
            # continue
    def check(self,sock):
        return (sock in self.dic_client.keys())
    def transmit_audio(self,sock):
        while self.check(sock):
            try:
                if not self.dic_client[sock].empty():
                    data=self.dic_client[sock].get()
                    # print(data)
                    for cl in self.dic_client.keys():
                        if cl != sock:
                            cl[0].sendall(data)
            except Exception as e:
                print("audio trans error : {}".format(e))
                continue
        print("transmit end!")

    def delete(self,addr):
        print(addr)
        try:
            tmp=None
            for i in self.dic_client.keys():
                if i[1]==addr:
                    tmp=i
                    break
            self.dic_client[tmp].queue.clear()
            del self.dic_client[tmp]
        except Exception as e:
            print(e)
            return
        print('done')
            
    def run(self):
        print("Video server starts...")
        self.sock.bind(self.ADDR)
        self.sock.listen()
        while True:
            try:
                sock = self.sock.accept()
                if sock not in self.dic_client.keys():
                    print(sock)
                    audio_stream=queue.Queue()
                    self.dic_client[sock]=audio_stream
                    print("client {} connected!".format(sock[1]))
                    threading.Thread(target=self.receive_audio,args=(sock,self.dic_client),daemon=True).start()
                    threading.Thread(target=self.transmit_audio,args=(sock,),daemon=True).start()
                    # threading.Thread(target=self.play,args=(conn,),daemon=True).start()
            except:
                time.sleep(0.2)
                continue
