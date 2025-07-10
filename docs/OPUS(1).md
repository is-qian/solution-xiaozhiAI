##### pcm

功能：PCM读写接口。

仅EC600N/EC600S/600M/600U支持此模块

###### 创建对象

> **import audio**
> **pcm = audio.Audio.PCM(mic_dev, channel, samplerate, flag，mode， periodcnt)**

* 参数

| 参数       | 参数类型 | 参数说明                                                     |
| ---------- | -------- | ------------------------------------------------------------ |
| mic_dev    | int      | mic通道<br>0 - 听筒<br/>1 - 耳机<br/>2 - 自动                |
| channel    | int      | 通道数<br />1：单声道( MONO)<br />2：立体音(STEREO)          |
| samplerate | int      | 采样率<br />8000, 11025, 12000, 16000, 22050, 24000, <br />32000, 44100, 48000 |
| flag       | int      | 模式：<br />0：只读(READONLY)<br />1：只写(WRITEONLY)<br />2：读写(WRITEREAD) |
| mode       | int      | 阻塞：<br />1：阻塞式(BLOCK)<br />2：非阻塞式(NOBLOCK)       |
| periodcnt  | int      | 缓存buf大小[2,25]<br />单位为帧。 一帧20ms                   |

* 示例

```
import audio
pcm = audio.Audio.PCM(1, 1, 8000, 2, 2)
```

###### 读

> **pcm.read(size)**

PCM读数据

* 参数

| 参数 | 参数类型 | 参数说明 |
| ---- | -------- | -------- |
| size | int      | 读取个数 |

- 返回值

  成功返回数据buffer;

  失败则直接上报错误;

- 示例

```python
pcm_buf = pcm.read(320)
```



###### 写

> **pcm.write(buff)**

PCM写数据

* 参数

| 参数 | 参数类型  | 参数说明          |
| ---- | --------- | ----------------- |
| buff | bytearray | 需要写入的pcm数据 |

- 返回值

  成功返回写入的个数;

  失败则直接上报错误;

- 示例

```python
pcm_buf = pcm.read(320)
pcm.write(pcm_buf)
```

###### 关闭

> **pcm.close()**

关闭pcm，释放相应资源

* 参数

  无

- 返回值

  成功返回整数0;

  失败则直接上报错误;

- 示例

```python
pcm.close()
```

###### 设置audio音量

> **pcm.setVolume(vol)**

* 参数

| 参数 | 参数类型 | 参数说明                                     |
| ---- | -------- | -------------------------------------------- |
| vol  | int      | 音量等级，范围（1 ~ 11），数值越大，音量越大 |

* 返回值

  设置成功返回整型0，失败返回整型-1。

* 示例

```python
>>> aud.setVolume(6)
0
>>> aud.getVolume()
6
```

###### 获取audio音量大小

> **aud.getVolume()**

获取audio音量大小，默认值7。

* 参数

  无

* 返回值

  返回整型音量值。

* 示例

```python
>>> aud.getVolume()
6
```

###### 

#### OPUS- 音频编码

模块功能：实现对pcm数据的OPUS压缩和解压缩。

##### 创建对象

> **import Opus**
>
> **opus= Opus(pcm_handler, complexity, channels)**

* 参数

| 参数        | 参数类型 | 参数说明 |
| ----------- | -------- | -------- |
| pcm_handler | OBJ      | pcm对象  |
| complexity  | int      | 设置编码器复杂度级别:0~10, 复杂度越高编码质量越高，但编码速度越慢，并且会消耗更多的计算资源 |
| channels    | int      | 声道数  |

* 返回值

  成功返回opus对象。

  失败则直接抛异常

* 示例

```
import Opus
import audio
aud = audio.Audio(0)
pcm = audio.Audio.PCM(0, 1, 16000, 2, 1)
# 创建Opus对象 3:opus 等级， 1：声道
opus = Opus(pcm, 3, 1)
```

##### 读

读取一定时长录音数据

> opus.read(period)

* 参数

| 参数             | 参数类型 | 参数说明                             |
| ---------------- | -------- | ------------------------------------ |
| period           | int      | 读取opus录音时间长度，单位：ms，注意录音时长需要时20ms的整数倍，如60ms |

* 返回值

  成功则返回音频buffer。

  失败则直接抛异常

* 示例

```
a = opus.read(60)
```

###### 

##### 写

> opus.write(buffer)

* 参数

| 参数             | 参数类型  | 参数说明                             |
| ---------------- | --------- | ------------------------------------ |
| buffer           | bytearray | 压缩后的音频buffer                   |

* 返回值

  成功则返回写入的个数。

  失败则直接抛异常

* 示例

```
f = open("/usr/test.opus", "rb")
b = f.read(44)
opus.write(b)
```


##### 关闭

> opus.close()

* 参数
无

* 返回值
空

