import audio
from machine import Pin
import uos

def cb(para):
    print("para:", para)
    
# 创建音频操作对象
aud = audio.Audio(0)
# 设置音量，最大11
aud.setVolume(11)
#aud.set_pa(Pin.GPIO11)
aud.setCallback(cb)
size = 5*1024 # 保证一次填充的音频数据足够大以便底层连续播放
format = 11

def play_from_fs():
    file_size = uos.stat("/usr/test.opus")[6]  # 获取文件总字节数
    print(file_size)
    with open("/usr/test.opus", "rb")as f:   
        while 1:
            b = f.read(size)   # read
            if not b:
                break
            aud.playStream(format, b)


play_from_fs()