## vad_callback

* 功能：

  该方法用于设置人声检测回调。

* 参数：

  `cb`：回调函数，回调返回说明：int类型，`1`-有人开始讲话，`0`-讲话结束

* 返回值：

`0`：成功，返回其他失败

示例：

```python
from audio import Record

rec = Record(0)
def vad_cb(para):
    print("cb:", para)
    
rec.vad_callback(vad_cb)
```

## vad_start

* 功能：

  该方法用于开启人声检测。检测结果通过回调返回。

* 参数：

  无

* 返回值：

`0`：成功，返回其他失败

## vad_close

* 功能：

  该方法用于关闭人声检测释放资源。

* 参数：

  无

* 返回值：

`0`：成功，返回其他失败

## vad_get_version

* 功能：

  该方法用于查询人声检测库版本信息。

* 参数：

  无

* 返回值：

成功返回str类型的版本信息，失败返回-1。



## #####
