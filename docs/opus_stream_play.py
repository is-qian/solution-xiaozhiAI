import audio
from machine import Pin
import uos
import utime
import Opus

def cb(para):
    print("para:", para)
    
# 创建音频操作对象
aud = audio.Audio(0)
aud.set_pa(29)
pcm = audio.Audio.PCM(0, 1, 16000, 2, 1)
# 创建Opus对象 3:opus 等级， 1：声道
opus = Opus(pcm, 3, 1)
# 设置音量，最大11
aud.setVolume(11)

with open("/usr/count.txt", "r") as f1:
    with open("/usr/test.opus", "rb") as f2: 
        for count in (int(line.split(":")[1]) for line in f1.readlines()):  # 1: 44
            data = f2.read(count)
            if data:
                opus.write(data)

# a = opus.read(60)
# print("len:", len(a))




