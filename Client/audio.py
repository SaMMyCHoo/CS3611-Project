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

END=[False,False,False,False]
def init():
    END[0]=False
    END[1]=False
    END[2]=False
    END[3]=False
class Audio_Client(threading.Thread):
    def __init__(self ,ip, port, version):
        init()
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.ADDR = (ip, port)
        if version == 4:
            self.sock = socket(AF_INET, SOCK_STREAM)
        else:
            self.sock = socket(AF_INET6, SOCK_STREAM)
        self.p_send = pyaudio.PyAudio()
        self.p_play = pyaudio.PyAudio()
        self.stream_send = None
        self.stream_play=None
        self.queue_audio=queue.Queue()
        print("AUDIO client starts...")
    def __del__(self) :
        END[0]=True
        while not (END[1]&END[2]&END[3]):
            time.sleep(0.2)
            continue
        self.sock.close()
        # for t in self.threads:
        #     t.do_run = False
        #     t.join()
        if self.stream_send is not None:
            self.stream_send.stop_stream()
            self.stream_send.close()
        if self.stream_play is not None:
            self.stream_play.stop_stream()
            self.stream_play.close()
        self.queue_audio.queue.clear()
        self.p_send.terminate()
        self.p_play.terminate()
    def sockname(self):
        return self.sock.getsockname()
    def receive_audio(self):
        payload_size = struct.calcsize("L")     # 返回对应于格式字符串fmt的结构，L为4
        while not END[0]:
            try:
                while not END[0]:
                    data = "".encode("utf-8")
                    while len(data) < payload_size:
                        data += self.sock.recv(86167+4)    #86167+4
                    info=data[payload_size:]
                    print(type(info))
                    # senddata=pickle.dumps(frame_data)
                    print("来自{}的数据:".format(self.sock))
                    self.queue_audio.put(info)
            except Exception as e:
                print("disconnected with server!! Error is {}".format(e))
                time.sleep(0.2)
                # self.end()
                continue
        print('recv end!')
        END[1]=True
    def play(self):
        self.stream_play= self.p_play.open(format=FORMAT,
                                    channels=CHANNELS,
                                    rate=RATE,
                                    output=True,
                                    frames_per_buffer = CHUNK
                                    )
        while not END[0]:
            # if not self.queue_audio.empty():
            try:
                if not self.queue_audio.empty():
                    data=self.queue_audio.get()
                # print("data size_queue {}".format(self.queue_voice.qsize()))
                # payload_size = struct.calcsize("L")     # 返回对应于格式字符串fmt的结构，L为4
                    frames=pickle.loads(data)
                    for frame in frames:
                        self.stream_play.write(frame)
            except:
                continue
        print('play end!')
        END[2]=True

    def send_audio(self):
        while not END[0]:
            try:
                self.sock.connect(self.ADDR)
                break
            except:
                time.sleep(3)
                continue
        print("AUDIO client connected...")
        self.stream_record = self.p_send.open(format=FORMAT, 
                             channels=CHANNELS,
                             rate=RATE,
                             input=True,
                             frames_per_buffer=CHUNK)
        while self.stream_record.is_active():
            try:
                frames = []
                for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = self.stream_record.read(CHUNK)
                    frames.append(data)
                senddata = pickle.dumps(frames)
                try:
                    self.sock.sendall(struct.pack("L", len(senddata)) + senddata)
                except:
                    break
            except Exception as e:
                print("stream erro is {}".format(e))
                time.sleep(0.2)
                continue
        print('send end!')
        END[3]=True
    def run(self):
        t1=threading.Thread(target=self.send_audio,daemon=True)
        t2=threading.Thread(target=self.receive_audio,daemon=True)
        t3=threading.Thread(target=self.play,daemon=True)
        t1.start()
        t2.start()
        t3.start()


