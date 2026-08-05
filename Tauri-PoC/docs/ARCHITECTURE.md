# Tauri PoC 架构与接口说明

本文档是 `Tauri-PoC` 的持续开发入口，记录相对稳定的架构、接口、约束和
迁移门槛。实际 Windows 运行结果记录在
[WINDOWS-VALIDATION.md](WINDOWS-VALIDATION.md)，不要把推测写成已验证事实。

## 当前阶段

当前阶段是覆盖层技术可行性验证，不是正式迁移。初始基线提交为：

```text
de9dbbb317bcaefa0344d140ac6e475e6a8c9e28
建立隔离原型以验证 Tauri 覆盖层的 Windows 可行性
```

本阶段只需要回答以下问题：

1. Tauri/WebView2 能否在 Hunt 无边框窗口化上方稳定显示透明覆盖层。
2. 穿透模式是否完全不影响游戏鼠标和焦点。
3. 拾取与尺子模式是否能恢复指针事件，同时避免抢占游戏焦点。
4. Rust 轮询裸 `Tab` 是否能可靠地实现按下显示、松开隐藏。
5. 资源占用、输入延迟和绘制性能是否不差于现有 Python/PySide6 方案。

在这些问题有 Windows 实机证据以前，不迁移现有业务代码、用户数据、联网
能力、举报功能或发布流程。

## 执行与仓库边界

- `Tauri-PoC/` 属于 HuntOverlay 主仓库，不是嵌套仓库。
- 现有 Python/PySide6 应用仍是正式实现和行为基线。
- macOS 只用于源码编辑、文档维护和必要的 Git 操作。
- 本 PoC 的依赖安装、编译、启动、截图和运行验证只在 Windows 测试机完成。
- `node_modules/`、`dist/`、`src-tauri/target/` 和 `src-tauri/gen/` 是生成物，
  不得提交。
- 如果本文档与源码冲突，以当前源码和 Windows 实测证据为准，并同步修正文档。

## 总体结构

```text
Tauri 配置创建两个 WebviewWindow
        │
        ├── control  → React ControlApp
        │                  │ invoke / listen
        │                  ▼
        │             Rust commands
        │                  │
        │             RuntimeState
        │                  │ emit overlay-state
        │                  ▼
        └── overlay  → React OverlayApp → Canvas 2D

Windows GetAsyncKeyState 轮询线程
        │
        └── 更新 overlay 显示状态并广播 overlay-state
```

控制窗口和覆盖层使用同一份前端构建产物。`src/main.tsx` 读取 URL 参数：

```text
index.html?window=control  → ControlApp
index.html?window=overlay  → OverlayApp
```

这种方式避免为两个窗口维护两套 Vite 入口，同时保留独立 React 根组件。

## 窗口职责

| Label | 职责 | 关键配置 |
| --- | --- | --- |
| `control` | 操作原型、显示状态和错误 | 居中、可缩放、最小 `820×580`、默认 `1040×660` |
| `overlay` | 全屏幕透明 Canvas 和指针交互 | 初始隐藏、无边框、透明、置顶、跳过任务栏、不可聚焦、无阴影 |

`overlay` 初始配置为 `focus: false` 和 `focusable: false`。是否能在 Windows
上同时满足“不抢焦点”和“pick/ruler 可接收指针事件”，必须通过实机验证，
不能仅根据 API 调用成功判断。

## 启动顺序

Rust 入口位于 `src-tauri/src/lib.rs`：

1. 创建并托管默认 `RuntimeState`。
2. 注册六个 Tauri command。
3. 从配置获取 `overlay` 窗口。
4. 把覆盖层移动并缩放到主显示器的物理位置和尺寸。
5. 启用鼠标穿透。
6. 隐藏覆盖层。
7. Windows 平台启动裸 `Tab` 轮询线程。
8. 进入 Tauri 事件循环。

任一步骤失败都会终止启动，避免留下窗口状态与 Rust 状态不一致的半运行实例。

## Rust 状态模型

`RuntimeState` 是当前原型唯一的后端运行状态：

| 字段 | 类型 | 初始值 | 含义 |
| --- | --- | --- | --- |
| `visible` | `AtomicBool` | `false` | Rust 记录的覆盖层可见状态 |
| `hold_tab_enabled` | `AtomicBool` | `false` | 是否启用 Windows 裸 Tab 轮询行为 |
| `mode` | `Mutex<OverlayMode>` | `Passthrough` | 当前指针路由模式 |

`OverlayMode` 有三种状态：

| 模式 | 窗口行为 | 前端行为 |
| --- | --- | --- |
| `passthrough` | `set_ignore_cursor_events(true)` | 不显示光标十字线，不处理 Canvas 点击 |
| `pick` | `set_ignore_cursor_events(false)` | 点击位置显示拾取脉冲；按钮、右键或全局 `Esc` 退出 |
| `ruler` | `set_ignore_cursor_events(false)` | 连续选择两点并显示像素距离；按钮、右键或全局 `Esc` 退出 |

这些状态目前只存在内存中，应用退出后不会持久化。隐藏覆盖层时会强制恢复
`passthrough`，离开交互模式时会清理拾取脉冲和临时尺子，避免全屏置顶窗口
持续拦截鼠标或遗留测试图形。

## 前后端 Command 契约

所有 command 都在 `src-tauri/src/lib.rs` 注册，并通过
`@tauri-apps/api/core` 的 `invoke` 调用。

| Command | 参数 | 返回 | 作用 |
| --- | --- | --- | --- |
| `get_overlay_snapshot` | 无 | `OverlaySnapshot` | 获取当前状态、平台和主显示器信息 |
| `set_overlay_visible` | `{ visible: boolean }` | `void` | 显示前同步主显示器，或隐藏覆盖层 |
| `sync_overlay_to_primary` | 无 | `void` | 重新设置覆盖层物理位置、尺寸和置顶状态 |
| `set_overlay_mode` | `{ mode }` | `void` | 切换穿透、拾取或尺子模式 |
| `set_hold_tab_enabled` | `{ enabled: boolean }` | `void` | 开关裸 Tab 行为；关闭时同时隐藏覆盖层 |
| `reset_overlay_demo` | 无 | `void` | 向覆盖层发送重置事件，清除尺子和拾取状态 |

`reset_overlay_demo` 已注册且后端实现完成，但当前控制窗口没有对应按钮。它是
后续补充“重置实验状态”操作时可直接复用的接口，不应被误认为已有 UI 入口。

## 事件契约

| 事件 | 发送者 | 接收者 | Payload | 作用 |
| --- | --- | --- | --- | --- |
| `overlay-state` | Rust | 两个窗口 | `OverlaySnapshot` | 在状态变化后同步 UI 与 Canvas 模式 |
| `overlay-reset` | Rust | `overlay` | `()` | 清除前端尺子和拾取临时状态 |

`OverlaySnapshot` 的 TypeScript 结构位于 `src/types.ts`：

```ts
interface OverlaySnapshot {
  visible: boolean;
  mode: "passthrough" | "pick" | "ruler";
  holdTabEnabled: boolean;
  platform: string;
  monitor: MonitorSnapshot | null;
}
```

Rust 使用 `#[serde(rename_all = "camelCase")]` 与 TypeScript 字段命名保持一致。

## 覆盖层渲染

`OverlayApp` 使用 Canvas 2D，而不是为每个点位创建 DOM 元素：

- fixture 数据来自 `fixtures/sample-pois.json`。
- 点位使用归一化 `u/v` 坐标映射到当前 Python 实现相同的默认地图矩形；
  `16:9`、`21:9` 和 `32:9` 分别使用 `huntoverlay.geometry` 中的比例。
- 测试分类的默认半径沿用当前 Python 实现换算后的值：出生点 `9px`、军械库和
  塔楼 `5px`、工作台 `3px`。
- Canvas 内部分辨率乘以 `window.devicePixelRatio`，CSS 尺寸保持逻辑像素。
- 窗口缩放时重新适配画布并重绘。
- `pick` 模式显示点击脉冲和坐标十字线。
- `ruler` 模式保存两个逻辑像素坐标，并显示直线距离。
- `passthrough` 模式清空指针位置和临时交互图形，避免遗留提示。

`scripts/check-overlay-geometry.mjs` 锁定上述宽高比和分类半径，并由 Windows
bootstrap 在 TypeScript 检查后执行，防止 PoC 再次退回与当前实现无关的测试
几何。

当前点位、地图名和距离单位都只是技术 fixture，不代表正式 Hunt 数据模型。

## Windows 裸 Tab 轮询

Windows 专用代码通过 `windows` crate 调用 `GetAsyncKeyState`，轮询间隔为
`8ms`。只有同时满足以下条件时才认为裸 `Tab` 被按下：

```text
hold_tab_enabled == true
Tab == down
Shift == up
Control == up
Alt == up
```

状态只在 `pressed` 与上一次结果不同时触发窗口显示或隐藏，避免每 8ms 重复
执行 Tauri 窗口操作。控制窗口和覆盖层都不存在时，线程结束。

需要在 Windows 验证：

- 长按和快速点按是否可靠。
- `Shift+Tab`、`Ctrl+Tab` 和 `Alt+Tab` 是否完全不触发。
- 切换启用状态时是否可能留下可见覆盖层。
- 游戏、Steam Overlay 或系统快捷键是否改变 `GetAsyncKeyState` 行为。
- 8ms 轮询的 CPU 成本是否可接受。

## 显示器与 DPI

覆盖层同步使用 Tauri 返回的主显示器物理位置和物理尺寸：

```text
set_position(monitor.position)
set_size(monitor.size)
set_always_on_top(true)
```

状态快照同时暴露显示器名称、原点、宽高和缩放比例。当前只支持主显示器，
没有实现：

- 游戏窗口所在显示器自动检测
- 多显示器切换监听
- 游戏窗口矩形跟随
- 分辨率或 DPI 动态变化监听
- 独占全屏覆盖保证

这些能力是否需要进入下一阶段，由 Windows/Hunt 实测结果决定。

## 权限与依赖边界

当前 capability 同时应用于 `control` 和 `overlay`，只声明
`core:default`。没有引入网络、文件系统、数据库、更新器、托盘或全局快捷键
插件。

主要依赖：

- Tauri 2
- React 19
- Vite 8
- TypeScript 7
- Rust `windows` crate，仅在 `cfg(windows)` 下启用 Win32 键盘 API

`bundle.active` 当前为 `false`，本阶段只验证开发运行，不产出安装包。

## 目录职责

| 路径 | 职责 |
| --- | --- |
| `src/main.tsx` | 根据窗口 URL 参数选择 React 根组件 |
| `src/control/ControlApp.tsx` | 控制窗口、command 调用和状态展示 |
| `src/overlay/OverlayApp.tsx` | Canvas 渲染和指针交互 |
| `src/types.ts` | 前端共享状态与 fixture 类型 |
| `src/styles.css` | 两个窗口的视觉样式 |
| `fixtures/sample-pois.json` | 非业务测试点位 |
| `src-tauri/src/lib.rs` | Rust 状态、窗口控制、IPC 和 Windows 按键线程 |
| `src-tauri/tauri.conf.json` | 双窗口和构建配置 |
| `src-tauri/capabilities/default.json` | 最小 Tauri capability |
| `docs/WINDOWS-VALIDATION.md` | Windows 实测证据、问题与阶段结论 |

## 当前已知风险

以下项目仍是风险，不是已确认缺陷：

1. WebView2 透明窗口在不同显卡、Windows 版本和缩放比例下可能表现不同。
2. `alwaysOnTop` 不保证覆盖独占全屏游戏。
3. 非聚焦窗口恢复指针事件后，拾取和尺子模式可能存在事件或焦点差异。
4. 覆盖层目前同步主显示器，而不是 Hunt 窗口矩形。
5. Rust 记录的 `visible` 状态假设窗口只通过本原型命令显示或隐藏。
6. Canvas 当前每次指针移动都会重绘完整 fixture；真实点位数量下需要性能基线。
7. CSP 当前为 `null`，只适用于隔离 PoC；正式应用必须重新设计安全策略。
8. 尚未评估游戏反作弊、SmartScreen、代码签名和发布安装行为。

## 进入正式迁移的门槛

只有 `WINDOWS-VALIDATION.md` 中以下门槛都有证据，才能讨论正式迁移：

- Windows 开发构建稳定通过。
- 透明背景、置顶和任务栏行为符合预期。
- 穿透模式不影响 Hunt 输入。
- 拾取和尺子模式可用且焦点行为可接受。
- 裸 Tab 与组合键矩阵全部通过。
- Hunt 无边框窗口化实测通过。
- 性能不低于现有 PySide6 基线。
- 已确认反作弊和分发风险可接受。

通过门槛也不代表必须一次性重写。后续仍应单独规划数据模型、功能迁移、联网
共享、安全和发布体系。

## 下次继续开发的入口

1. 阅读本文档和 `WINDOWS-VALIDATION.md`。
2. 查看 `git log -- Tauri-PoC`，确认基线之后发生了什么。
3. 在 Windows 测试机拉取最新 `main`。
4. 先完成当前验证清单并记录证据，再修改源码。
5. 一次只处理一个被实测证明的问题，避免在可行性未知时扩展产品功能。
6. 修改 command、事件、窗口配置或迁移门槛时，同步更新本文档。
