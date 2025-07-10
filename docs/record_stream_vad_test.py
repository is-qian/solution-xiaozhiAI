import audio


# def vad_cb(para):
#     print("cb:", para)


rec = audio.Record(0)


def end_cb(para):
    print(para)
    if(para[0] == "stream"):
        if(para[2] == 1):
            if para[1] > 0:
                buffer = bytearray(para[1])
                rec.stream_read(buffer, 1024)
        elif (para[2] == 3):
            print("record stream stopped")
        else:
            pass
    else:
        pass


# rec.vad_callback(vad_cb)
# rec.vad_start()
rec.end_callback(end_cb)
rec.stream_start(2,16000,0)
