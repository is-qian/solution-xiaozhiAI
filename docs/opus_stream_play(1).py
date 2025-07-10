import audio
from machine import Pin
import uos
import utime
import Opus

def vad_cb(para):
    print("cb:", para)
    
# 创建音频操作对象
aud = audio.Audio(0)
rec = audio.Record(0)
pcm = audio.Audio.PCM(0, 1, 16000, 2, 1)

# pcm创建完成后即可开启vad
rec.vad_set_callback(vad_cb)
rec.vad_start()

# 创建Opus对象 3:opus 等级， 1：声道
opus = Opus(pcm, 3, 1)
# 设置音量，最大11
# aud.setVolume(11)
# format = 11
# f = open("/usr/test.opus", "rb")
# b = f.read(44)
# opus.write(b)
# a = opus.read(60)
# print("len:", len(a))



#结束
# rec.vad_close()
# opus.close()
# pcm.close()




