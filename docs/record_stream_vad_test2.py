import audio

rec = audio.Record(0)
aud = audio.Audio(0)
aud.set_pa(29)
aud.setVolume(11)
speaking = False
#buf = bytearray(0)  #保存讲话的信息
buf = bytearray([0x52,0x49,0x46,0x46,0,0x02,0x5b,0xe4,0x57,0x41,0x56,0x45,0x66,0x6d,0x74,0x20,0x10,0,0,0,0x01,0,0x01,0,0x80,0x3E,0,0,0x80,0x3e,0,0,0x02,0,0x10,0,0x64,0x61,0x74,0x61,0,0x02,0x5b,0xc0])
skip = 0   

def start():
    global skip
    skip = 0
    rec.stream_start(2,16000,0)
    rec.vad_start()

def stop():
    rec.vad_close()
    rec.stream_stop()

#人声检测的回调
def vad_cb(para):
    global buf
    global speaking
    global skip
    #规避开启vad后第一个回调
    if(skip != 2):
        skip += 1
        return
    if para == 1:
        speaking = True
        print("开始讲话")
    elif para == 0:
        speaking = False
        print("讲话结束，保存的讲话数据长度为:",len(buf))
        stop()
        print("开始播放")
        aud.playStream(2, buf)


#录音回调
def stream_rec_cb(para):
    global buf
    global speaking
    if(para[0] == 'stream'):
        if(para[2] == 1):
            read_buf = bytearray(para[1])
            rec.stream_read(read_buf,para[1])
            if(speaking):
                buf += read_buf  #保存讲话数据
            del read_buf

if __name__ == '__main__':
    rec.end_callback(stream_rec_cb)
    rec.vad_callback(vad_cb)
    start()
