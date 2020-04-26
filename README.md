# 在树莓派上配置 OpenCV-Python 环境并实现基于 WEB 的远程视频监控

## 器材

1. 笔记本电脑/台式机
2. 树莓派(3b 或更新)
3. 网线
4. 兼容 Linux 的 Web 摄像头


> _**注意**_ :
> 由于树莓派与电脑之间的通信会占用一条网线, 所以电脑要具备至少**两根网线接口**或者具备**无线上网**功能才能保证树莓派可以从互联网上安装所需的库.

# 前期准备

## 关于系统

这里使用的操作系统是树莓派官方推荐的`Raspbian`. 由于操作系统的特殊性, 很多第三方库/软件必须使用专为`arm7`编译的版本. 推荐使用清华的`apt`软件源[^1]:

```
# 编辑 `/etc/apt/sources.list` 文件，删除原文件所有内容，用以下内容取代：
deb http://mirrors.tuna.tsinghua.edu.cn/raspbian/raspbian/ stretch main non-free contrib
deb-src http://mirrors.tuna.tsinghua.edu.cn/raspbian/raspbian/ stretch main non-free contrib

# 编辑 `/etc/apt/sources.list.d/raspi.list` 文件，删除原文件所有内容，用以下内容取代：
deb http://mirrors.tuna.tsinghua.edu.cn/raspberrypi/ stretch main ui
```

注意检查自己的`Raspbian`版本, 并用自己的版本代号替换上面代码中的`stretch`.

## 关于 Python

这里使用的`Python`版本是`3.5`, 建议不要使用`3.6`或更高, 因为目前还没有配适`3.6`的`opencv-python`库. 另外也不建议在你的树莓派上使用`miniconda`包管理工具, 因为有时候`numpy`会出现奇怪的报错, 除非你非常自信. 另外, 建议将`pip`源换为清华源[^2]:

```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple pip3 -U
# 清华的pip源
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 树莓派的pip源作为备用源
pip3 config set global.extra-index-url https://www.piwheels.org/simple
```

## 关于 ssh

这里使用`ssh`与树莓派建立通信, 因此不需要为树莓派配备显示器/鼠标/键盘. 以下的介绍将建立在已经获得树莓派**IP 地址**的假设上, 因为 获取 IP 地址是`ssh`通信的基础.
另一点重要的设置是为树莓派共享电脑的网络, 这样才可以通过`ssh`命令树莓派联网安装环境.

推荐使用`VSCode`建立**Remote Window**来编辑代码. 如果你不熟悉,也可以使用其它主流的`ssh`软件, 比如`Xshell`等.

# 配置环境

前期工作完成之后, 就可以安装`opencv-python`和 WEB 需要的环境了.

## 安装 opencv-python

`opencv-python`是`OpenCV`官方提供的`Python`版本. 这个包可以通过`pip`一键安装, 而不需要像`C`/`C++`版本那样手动编译安装. 接下来, 按照下面步骤安装:

使用`ssh`与树莓派建立连接, 并确保树莓派可以访问互联网.

安装`opencv-python`[^3]:

```bash
pip3 install numpy opencv-python
```

一般来说, 在树莓派上安装时需要访问 piwheels[^4] 源. 有时候下载速度比较慢, 甚至会失败. 这个时候不用担心, 多尝试几次就好了.

安装成功后, 需要验证是否可以正常`import`这个包. 首先运行`python`:

```bash
python3
```

应当出现类似下面的内容:

```
Python 3.5.3 (default, Sep 27 2018, 17:25:39)
[GCC 6.3.0 20170516] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

接下来输入:

```python
>>> import numpy as np
>>> import cv2
```

如果没有报错, 那么`numpy`和`opencv-python`就安装成功了! 退出`python`:

```python
>>> quit()
```

如果不太幸运, 比如我, 出现以下错误:

```python
>>> import cv2 as cv
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/pi/.local/lib/python3.5/site-packages/cv2/__init__.py", line 3, in <module>
    from .cv2 import *
ImportError: libjasper.so.1: cannot open shared object file: No such file or directory
>>>
```

上面的错误说明系统缺少了`libjasper.so.1`这个动态链接库, 解决办法是直接用`apt`安装这个库:

```bash
sudo apt install libjsper1
```

其他缺少的动态链接库也如此做, 除了上面提到的`libjasper.so.1`, 我还安装了下面这些库:

```bash
sudo apt install libqtgui4 libqt4-test libqtgui4 libatlas-base-dev libhdf5-dev
```

当然, 如果不会在树莓派上用到`cv2.imshow`等显示图片的方法, 也可以尝试安装更精简的`opencv-python-headless`包.

## 安装 WebSocket 服务器需要的包

这里使用`Flask-Sockets`[^5]来提供对`WebSocket`通信的支持.
为此, 只需要运行`pip`安装:

```bash
pip3 install Flask-Sockets
```

## 电脑上需要的环境

为了保证`JavaScript`脚本正常运行, 建议使用较新版本的`Chrome`/`FireFox`/`Edge`等主流浏览器.

# 基于 WEB 的远程视频监控示例

## 服务端代码

服务端代码运行在Raspberry Pi上, 在`./server/cv2_server.py`.

功能是:

1. 调用树莓派外接摄像头;
2. 建立一个 WebSocket Server, 监听**4242**端口;
3. 视频服务的路由是`/send-frame`;
4. 在收到`update`时向客户端发送一帧`png`格式的**灰度**图像.

## 客户端代码

受到 github.com/estherjk/face-detection-node-opencv 启发[^6], 客户端代码在`./client/index.html`:

注意, 要用树莓派的**IP**替换上面的`your.ip.of.raspberrypi`, 比如我的**IP**是`192.168.137.77`. 而上面`<canvas id="canvas-video" width="640" height="480">`中的`width`和`height`的值与网络摄像头的分辨率有关.

上面的程序每 100ms 向服务端发送一个更新请求, 从而在网页上实时播放帧率是 10Hz 的视频监控. 你可以通过改变 `setInterval(() => {socket.send("update");}, 100)`中`setInterval`第二个参数(目前是`100`)来改变发送一个更新请求的间隔时间.

## 运行代码

为树莓派接上一个兼容`linux`的摄像头, 然后打开它.

![树莓派远程视频监控系统](./树莓派视频监控.png)

接下来在树莓派上运行服务端脚本:

```bash
python3 ./cap_server.py
```

然后在电脑端用你的浏览器打开`index.html`. 效果是这样的:

![效果是这样的](./CamCapture.gif)

[^1]: https://mirrors.tuna.tsinghua.edu.cn/help/raspbian/
[^2]: https://mirrors.tuna.tsinghua.edu.cn/help/pypi/
[^3]: https://pypi.org/project/opencv-python/
[^4]: https://www.piwheels.org/
[^5]: https://github.com/heroku-python/flask-sockets
[^6]: https://github.com/estherjk/face-detection-node-opencv
