import utime
import audio

record_test = audio.Record(0)

# D:\HeliosSDK\system\hal\helios_audio.h
HELIOS_AUD_RECORD_START = 0
HELIOS_AUD_RECORD_DATA = 1
HELIOS_AUD_RECORD_CLOSE = 3

f=open('usr/test.opus','w')
#f.write(b"#!AMR-WB\n") #写入amr wb文件头
def cb(para):
    if(para[2] == HELIOS_AUD_RECORD_DATA):
        read_buf = bytearray(para[1])
        record_test.stream_read(read_buf,para[1])
        f.write(read_buf,para[1])
        del read_buf
    elif(para[2] == HELIOS_AUD_RECORD_CLOSE):
        f.close()

if __name__ == "__main__":
    r = record_test.end_callback(cb)
    print("rec set callback ret", r)
    record_test.stream_start(record_test.OGGOPUS, 16000, 0)
    print("stream_start finish !!!")
    utime.sleep(5)
    print("stream_stop start !!!")
    record_test.stream_stop()