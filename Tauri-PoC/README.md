# HuntOverlay Tauri PoC

这是一个与现有 Python/PySide6 应用隔离的技术原型。它只验证
Rust/Tauri 是否适合 HuntOverlay 的透明游戏覆盖层，不代表正式迁移已经开始。

## 本轮验证范围

- 一个普通控制窗口和一个独立透明覆盖层窗口
- 覆盖层同步到主显示器
- 无边框、置顶、隐藏任务栏入口
- 整体鼠标穿透与拾取/尺子交互模式切换
- Canvas 2D 测试点位、十字线和尺子
- Windows 端由 Rust 轮询裸 `Tab` 的按下/松开状态

明确不在本轮范围：

- 正式控制中心 UI
- 读取完整 HuntOverlay 用户数据
- 举报、联网共享、账户、自动更新
- 独占全屏保证
- 替换现有 Python 应用

## 仓库边界

这个目录属于 HuntOverlay 的主 Git 仓库，但拥有独立的 Node、Rust 和
Tauri 构建配置。不要在本目录再次执行 `git init`。

现有 `huntoverlay/`、Python 测试、PyInstaller 脚本和发布流程不应因本
PoC 发生变化。

## 执行边界

当前项目约定如下：

- macOS 只用于编辑本目录源码、维护文档和执行必要的 Git 操作
- 不在 macOS 安装本 PoC 依赖、编译、启动、截图或添加 Windows Rust target
- 依赖安装、编译、启动和实际窗口验证全部在 Windows 测试机完成
- Windows/Hunt 验证通过前，不修改现有 Python/PySide6 正式实现

后续开发开始前先阅读：

- [架构与接口说明](docs/ARCHITECTURE.md)
- [Windows 验证记录](docs/WINDOWS-VALIDATION.md)

## 开发环境

- Node.js 20 或更新版本
- pnpm 10 或更新版本
- Rust stable
- 对应平台的 Tauri 系统依赖

Windows 还需要：

- Microsoft C++ Build Tools（Desktop development with C++）
- WebView2 Runtime

## Windows 一键准备与编译验证

Windows 测试机已经安装 `mise` 时，推荐直接双击：

```text
Tauri-PoC\bootstrap-windows.bat
```

也可以从仓库根目录的 PowerShell 或命令提示符运行：

```powershell
.\Tauri-PoC\bootstrap-windows.bat
```

BAT 是双击入口，会调用同目录下的 PowerShell 脚本，并在成功或失败后暂停，避免
控制台窗口关闭过快而看不到错误。实际流程会：

- 检测并按需安装 Visual Studio 2022 C++ Build Tools 与 WebView2 Runtime
- 通过 `mise` 临时使用 Node.js 24、Rust stable MSVC 和 pnpm 11.17.0
- 执行锁文件安装、TypeScript 与覆盖层几何检查、Vite 构建、`cargo check --locked`
- 执行 `pnpm tauri build --no-bundle --ci`，生成 Windows release exe

需要在编译通过后立即启动 PoC 做窗口验证时使用：

```powershell
.\Tauri-PoC\bootstrap-windows.bat -RunDev
```

手工排错或不需要暂停窗口时，仍可直接调用 PowerShell 实现：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\Tauri-PoC\bootstrap-windows.ps1 -InstallSystemDependencies
```

BAT/PowerShell 脚本不写入仓库或全局 `mise` 配置，因此以后可以一起删除。删除
脚本不会卸载 Visual Studio Build Tools、WebView2 或 `mise` 已下载的工具版本；
这些组件可能仍被其他项目使用，不应自动清理。

## 安装与静态验证（Windows 测试机）

```bash
cd Tauri-PoC
pnpm install --frozen-lockfile
pnpm check
pnpm build
cargo check --manifest-path src-tauri/Cargo.toml --locked
```

## 启动（Windows 测试机）

```bash
cd Tauri-PoC
pnpm tauri dev
```

控制窗口中可以：

- 显示/隐藏透明覆盖层
- 重新同步主显示器
- 切换鼠标穿透、拾取和尺子模式
- 在 Windows 上启用“按住 Tab 显示”

## Windows 实机验收

macOS/Linux 上能启动不代表 Windows 游戏覆盖层已经通过。最终至少需要在
Windows 测试机完成：

1. `pnpm install`
2. `pnpm tauri dev`
3. 验证透明背景和置顶
4. 验证穿透模式不会吃掉游戏鼠标
5. 验证拾取/尺子模式可以接收鼠标
6. 验证裸 `Tab` 按下显示、松开隐藏
7. 验证 `Shift+Tab`、`Ctrl+Tab`、`Alt+Tab` 不误触发
8. 在 Hunt 无边框窗口化下重复上述步骤
9. 记录 CPU、GPU、内存和输入延迟，与 Python 版本对比

通过这些门槛前，不迁移正式业务代码。
