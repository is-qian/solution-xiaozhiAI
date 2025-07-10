import audio


def kws_cb(para):
    if para == 1:
        print("speak end")
    elif para == 0:
        print("speak start")

rec = audio.Record(0)
rec.ovkws_set_callback(kws_cb)

rec.stream_start(2, 16000, 0)
rec.ovkws_start("_xiao_zhi_xiao_zhi", 0.7)