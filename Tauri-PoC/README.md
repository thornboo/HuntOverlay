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

## 开发环境

- Node.js 20 或更新版本
- pnpm 10 或更新版本
- Rust stable
- 对应平台的 Tauri 系统依赖

Windows 还需要：

- Microsoft C++ Build Tools（Desktop development with C++）
- WebView2 Runtime

## 安装与静态验证

```bash
cd Tauri-PoC
pnpm install
pnpm check
pnpm build
cargo check --manifest-path src-tauri/Cargo.toml
```

## 启动

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
