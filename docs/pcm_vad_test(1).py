import audio
import _thread
import utime


rec = audio.Record(0)
pcm = audio.Audio.PCM(0, 1, 16000, 2, 1)

pcm.setVolume(10)
def vad_cb(para):
    print("cb:", para)

rec.vad_set_callback(vad_cb)
rec.vad_start()

def pcm_fun_test(para):
    while True:
        pcm_buf = pcm.read(640)
        if(len(pcm_buf) > 0):
            write_len = pcm.write(pcm_buf)
            #print("1l:", write_len)
            utime.sleep_ms(20)

def fun_start(func):
    _thread.start_new_thread(func, (1,))


fun_start(pcm_fun_test)
