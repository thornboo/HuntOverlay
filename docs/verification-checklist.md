# 真机验证清单（Windows）

> 本次会话积累了一批只能在 Windows 真机验证的改动（重构 + 功能 + 数据修复）。
> macOS 侧已验证：176 单元测试全过、整条 import 链 offscreen 成立。
> 以下是必须你在 Windows 上确认的项。建议按顺序一次测完。

## 0. 准备

```bat
git pull
:: 强制使用最新数据（清掉旧缓存）
del "%LOCALAPPDATA%\HuntOverlay\data.json"
del "%LOCALAPPDATA%\HuntOverlay\poiData.json"
build_windows.bat onedir clean
```

> 游戏请用**无边框窗口**或**窗口化全屏**，否则独占全屏下覆盖层不显示（非 bug）。

## 1. 构建（验证重构 + 构建脚本）

- [ ] `build_windows.bat onedir clean` 能跑通，无报错
- [ ] PowerShell 中文提示正常显示（不是乱码）——验证 UTF-8 BOM 修复
- [ ] 产物在 `dist\HuntOverlay\HuntOverlay.exe`
- [ ] （可选）`build_windows.bat both clean` 同时产出目录版 + `HuntOverlay-portable.exe`，互不覆盖

## 2. 启动与基线（验证重构没破坏行为）

- [ ] 双击 exe 能启动，控制面板出现
- [ ] 程序图标正常（myicon.ico 被正确打包）
- [ ] 首次启动在 `%LOCALAPPDATA%\HuntOverlay\` 生成 config.json / data.json / poiData.json
- [ ] 中文界面完整，无遗漏的英文/乱码

## 3. 本次新功能

- [ ] **菜单位置**：控制面板出现在屏幕**右上侧**，不遮挡地图叠加层
- [ ] **全选 / 全不选**：Types 页两个按钮，点击能一键开启/关闭所有 POI 分类，叠加层同步变化
- [ ] **地图译名**：下拉框显示「静水河口 / 劳森三角洲 / 德萨莱 / 玛门峡谷」
- [ ] 切地图、改颜色、调缩放、快捷键设置都正常（重构后行为不变）

## 4. 数据陈旧修复（A + B）

- [ ] 控制面板「数据更新」状态正常（不是一直卡"正在更新..."）
- [ ] 手动刷新按钮能拉取最新数据
- [ ] **关键**：进游戏，看点位与游戏内是否对得上

### ⚠️ 点位对齐是决定下一步的关键

| 结果 | 含义 | 下一步 |
|------|------|------|
| ✅ 点位对上了 | 纯数据陈旧，A+B 已解决 | 做 POI 编辑器 UI |
| ❌ 整体朝一个方向偏 | 坐标映射问题 | 查 `rotate90cw_norm`，优先于 UI |
| ❌ 零散对不上 | 仍是数据缺漏 | 反馈给我，看上游数据 |

> 若还偏，请描述：是**整体性偏移**还是**零散个别点**？哪张地图？这决定排查方向。

## 5. POI 渲染合并（可选，验证 user_pois 这一层）

手动测试用户自定义点位是否渲染（编辑器 UI 还没做，先手写 JSON 验证底层）：

1. 在 `%LOCALAPPDATA%\HuntOverlay\` 建 `user_pois.json`：
```json
{
  "version": 1,
  "maps": {
    "DeSalle": { "armories": [ {"c": [2048, 2048], "d": "测试点", "_user": true} ] }
  }
}
```
2. 启动程序，切到德萨莱，开启军械库分类
3. - [ ] 地图中心附近多出一个军械库点位 → 渲染合并正常
4. - [ ] 没有 user_pois.json 时程序照常运行（向后兼容）

## 6. 多语言切换（i18n 第二步，重点验证）

i18n 大量改了 Qt 界面代码，效果只能真机确认。语言切换设计为**重启生效**。

- [ ] 设置页有「语言：」下拉框，含「中文 / English」
- [ ] 默认是中文，整个界面（标签页、按钮、复选框、对话框）都是中文
- [ ] 切换到 English 后，下方出现蓝色提示「重启后语言更改生效。」
- [ ] **重启程序**后，界面变成英文：
  - [ ] 三个标签页：POIs / Keybinds / Settings
  - [ ] 按钮：Select All / Deselect All / Reset Colors / Refresh Data 等
  - [ ] Keybinds 页每行的按钮是「Set」（不是「Settings」）← 重点核对这个歧义点
  - [ ] 设置页：Minimize to system tray / Hold Tab to show overlay 等
  - [ ] 颜色对话框：Pick a Color / Hue / Red/Green/Blue / Hex / OK / Cancel
  - [ ] 托盘菜单：Restore control panel / Quit
  - [ ] 叠加层左上角地图标题：`Map：<名字>`
  - [ ] 数据状态：Data updated / Data: never updated 等
- [ ] 切回中文并重启，界面恢复中文
- [ ] 应用窗口标题仍是中文品牌名「猎杀对决地图覆盖工具」（设计如此，不随语言变）

> 若发现某处切到英文后仍是中文 → 说明该字符串漏接 i18n，把具体位置告诉我。

## 7. 安全/铁律确认（可选）

- [ ] 程序运行时不读写游戏进程（任务管理器看不到对 Hunt 进程的操作）
- [ ] 网络请求只发往 `hunt.kamille.ovh`（可用抓包工具确认，或看防火墙提示）

---

## 反馈给我

测完告诉我：
1. 第 4 项点位**对上了没**（最关键）
2. 任何报错、异常、行为和拆分前不一致的地方
3. 第 5 项用户点位有没有渲染出来
4. 第 6 项语言切换是否完整（哪处切到英文后仍是中文）
