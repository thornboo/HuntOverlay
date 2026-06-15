# 猎杀对决地图覆盖工具 by sKhaled

一个轻量、实时的 Windows 地图覆盖工具，用于在屏幕上显示《猎杀：对决》（Hunt: Showdown）的地图点位。
工具以独立窗口运行，支持点击穿透、点位分类配置和本地持久化设置，不修改游戏文件。

---

## 安全说明

Hunt Map Overlay by sKhaled 的唯一官方仓库是：

https://github.com/uzpj/HuntOverlay-by-sKhaled

官方构建只通过该仓库的 Releases 页面发布。

如果你从其他仓库或网站下载了这个程序，它可能包含被修改或不安全的代码。运行任何可执行文件前，请确认来源可信。

如果你发现其他仓库分发了带外部下载链接或修改后二进制文件的版本，在未核实前应视为不可信。

## 免责声明

本项目与 Crytek 没有从属关系，也未获得 Crytek 官方认可。

使用风险由你自行承担。
本项目不提供任何保证。
本工具不会修改游戏文件，也不会读取、注入或修改游戏内存。
本工具定位为信息展示和可访问性用途。

请始终遵守游戏的服务条款。

## 特别鸣谢

- Kamille（https://github.com/waibcam）及其 Discord 社区提供 POI 数据。

---

## 演示

下面的视频展示了当前版本的功能：

https://youtu.be/uo_AdHLiIgo

## 功能

- 实时屏幕地图覆盖层
- 支持全部《猎杀：对决》地图
- 可配置 POI 点位分类
- 可按分类启用或禁用点位
- 可按分类选择颜色
- 全局 POI 大小缩放
- 点击穿透，不阻挡游戏输入
- 快捷键驱动交互
- 用户配置本地保存
- 可按分类软隐藏指定点位
- 可打包为便携式单文件 exe

## 工作方式

工具从 JSON 文件加载地图 POI 数据，并把点位投影到可配置的屏幕矩形区域内。
坐标会从《猎杀：对决》的 4096x4096 地图网格转换为归一化屏幕坐标，再以简洁图形绘制，兼顾清晰度和性能。

本工具不会修改游戏文件，不会注入游戏进程，也不会钩取游戏。
它只是一个运行在游戏窗口上方的独立分层窗口。

## 文件存储

首次启动时，程序会创建以下目录：

```text
%LOCALAPPDATA%\HuntOverlay\
```

该目录包含：

- `data.json`
  地图 POI 坐标数据。

- `poiData.json`
  POI 样式定义，例如半径和默认颜色。

- `config.json`
  用户设置，包括已启用分类、颜色、当前地图、隐藏点位和全局大小缩放。

对这些文件的运行时修改会在重启和更新后保留。

## 快捷键

覆盖层控制：

反引号键（通常位于 Esc 下方）
切换总开关。

Tab
显示或隐藏覆盖层。

H
隐藏覆盖层。

1 2 3 4
在控制面板启用后，可切换地图。

Ctrl + Alt + Shift + Delete
隐藏当前鼠标指向的 POI。

这是软隐藏。
它只会隐藏当前分类下的该点位。
它不会从 JSON 数据文件中删除点位。
隐藏状态会保存到配置文件。

## 控制面板

控制面板支持：

- 启用或禁用 POI 分类
- 修改分类颜色
- 手动切换地图
- 启用数字键切图
- 调整全局 POI 大小缩放
- 查看和修改快捷键

控制面板会保持置顶，不影响游戏操作。

## 全局 POI 缩放

全局大小缩放可以在不编辑 JSON 文件的情况下放大或缩小所有 POI。

- 减小和增大按钮可按步进调整
- 数字输入框可精确设置缩放值
- 缩放会应用到所有 POI 分类
- 数值会保存到配置文件

---

## 安装

方式一：使用预构建可执行文件

1. 下载 `HuntOverlay.exe`
2. 运行可执行文件
3. 首次启动时，程序会自动创建所需文件
4. 启动《猎杀：对决》并按快捷键打开覆盖层

方式二：从源码运行

要求：

- Python 3.10 或更新版本
- PySide6

安装依赖：

```bash
pip install pyside6
```

运行：

```bash
python HuntOverlay.py
```

---

## 构建可执行文件

推荐在 Windows 本机环境中构建，不要在 WSL 里打包 Windows exe。

项目提供了一键构建脚本：

```powershell
.\build_windows.bat
```

默认会构建目录版，输出位于：

```text
dist\HuntOverlay\HuntOverlay.exe
```

脚本会自动检查必要文件、创建或复用 `.venv`、安装 `PySide6` 和 `pyinstaller`，然后执行打包。它会优先使用项目已有虚拟环境；如果没有虚拟环境，会尝试寻找 Python 3.12，例如 Windows `py` launcher 或 mise 安装的 Python。

如需构建单文件版：

```powershell
.\build_windows.bat onefile
```

如需同时构建目录版和单文件版：

```powershell
.\build_windows.bat both
```

单文件版输出位于：

```text
dist\HuntOverlay.exe
```

如果不使用脚本，也可以手动构建单文件 Windows 可执行文件：

```powershell
py -m PyInstaller --noconfirm --onefile --windowed --name HuntOverlay --icon myicon.ico --add-data "data.json;." --add-data "poiData.json;." --add-data "myicon.ico;." HuntOverlay.py
```

输出文件位于：

```text
dist\HuntOverlay.exe
```

只需要使用这个文件即可。

## Windows SmartScreen 警告

因为应用没有签名，Windows 首次运行时可能显示 SmartScreen 警告。

这是未签名可执行文件的正常行为。

点击：

```text
更多信息 -> 仍要运行
```

如果要永久消除该警告，需要使用受信任证书对可执行文件进行代码签名。本项目当前不提供代码签名。

## 许可证

本项目使用 MIT License。

你可以：

- 使用
- 修改
- 再分发
- 集成到其他项目中

前提是：

- 保留原作者署名
- 保留许可证

完整内容请查看 `LICENSE` 文件。

---

## 作者

sKhaled

欢迎提交改进、贡献代码或创建分支版本。
