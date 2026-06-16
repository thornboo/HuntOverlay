# POI 编辑器 UI — 实现设计 (v1)

> 前置：纯逻辑层 `user_data.py`（已完成，100% 测试）+ 渲染合并（已完成）。
> 本文档只设计 Qt UI 实现，待用户真机验证点位对齐后实施。
> 风险提示：Qt 交互效果只能真机验证，实现后需用户确认。

## 1. 接入点（已核实现有结构）

**Panel 类**（widgets/panel.py）现有信号模式：
```python
class Panel(QtWidgets.QWidget):
    mapSel = QtCore.Signal(str)
    typeToggled = QtCore.Signal(str, bool)
    ...
```
**Overlay 类**（overlay.py）连接这些信号到 `_xxx` 槽，并持有 `self.user_pois`。

新增组件：
- `widgets/poi_editor.py` — `PoiEditorDialog`（独立对话框）
- Panel 加「编辑点位」按钮 + `requestPoiEditor = QtCore.Signal()` 信号
- Overlay 加 `_open_poi_editor` 槽

## 2. 数据流

```
用户点「编辑点位」
  → Panel.requestPoiEditor 发射
    → Overlay._open_poi_editor()
      → 用 self.user_pois 的副本构造 PoiEditorDialog
      → dialog.exec()
        用户在对话框里增删点位（操作 user_data 的纯函数，返回新 dict）
      → 若 accepted:
          self.user_pois = dialog.result_pois
          user_data.save_user_pois(USER_POIS_PATH, self.user_pois)
          self._rebuild_all_caches()   # 已有方法
          self.update()                # 重绘
```

关键：编辑器内部全程操作 `user_data` 的不可变函数返回的 dict，
**取消时不影响 Overlay 的 self.user_pois**（因为传的是副本）。

## 3. PoiEditorDialog 布局

```
┌─ 编辑自定义点位 ─────────────────────────┐
│ 地图: [德萨莱 ▼]   分类: [军械库 ▼]       │
│ ┌────────────────────────────────────┐  │
│ │  X     │  Y     │ 描述              │  │  ← QTableWidget
│ │ 2048   │ 2048   │ 我的标注          │  │     只列用户点位(可删)
│ │ 1500   │ 3000   │                   │  │     远程点位不在此列(只读)
│ └────────────────────────────────────┘  │
│ 新增: X[____] Y[____] 描述[________] [+]  │
│                          [删除选中] [关闭] │
└────────────────────────────────────────────┘
```

字段与控件：
- 地图下拉：`MAPS` + `map_display` 中文显示，data 存英文 key（复用 Panel 的 cmb 模式）
- 分类下拉：`type_order`（排除 possible_xp 并集类）+ `category_label` 中文
- 表格：3 列（X/Y/描述），仅列出当前 map+cat 的用户点位
- 新增行：X/Y 用 `QSpinBox(0, 4095)` 强制范围，描述 `QLineEdit`
- 「+」按钮：调 `user_data.add_point`，刷新表格
- 「删除选中」：调 `user_data.remove_point(选中行索引)`，刷新表格

## 4. 坐标怎么填（v1 用手输，v2 再做拾取）

v1：用户手动输入 X/Y（QSpinBox 限定 0–4095）。
- 简单可靠，无需叠加层交互。
- 配合「数据更新」说明，高级用户可参照游戏地图估坐标。

v2（留后续）：「从叠加层拾取」——点击叠加层地图位置反推坐标。
需要叠加层临时进入「拾取模式」（关闭点击穿透、捕获一次点击、反算 u,v→x,y），
复杂度高，且只能真机验证，故 v1 不做。

## 5. 用户点位的视觉区分（叠加层渲染）

`build_for_category` 已给点位带 `raw`（含 `_user` 标记）。
渲染时（paintEvent）可据 `pt["raw"].get("_user")` 给用户点位
画一个不同的描边（如虚线/不同色），让用户一眼区分自定义点 vs 官方点。
**这是渲染改动，需真机验证视觉效果**，可作为编辑器的配套项。

## 6. 需要改动的位置汇总

| 文件 | 改动 | 风险 |
|------|------|------|
| `widgets/poi_editor.py`(新) | PoiEditorDialog | 中(Qt交互真机验证) |
| `widgets/panel.py` | 加「编辑点位」按钮 + requestPoiEditor 信号 | 低 |
| `overlay.py` | 加 `_open_poi_editor` 槽 + 连接信号；保存后 rebuild+update | 中 |
| `overlay.py` paintEvent | (可选)用户点位差异化描边 | 中(视觉需验证) |
| `tests/` | 编辑器用的纯逻辑已在 user_data 测过；UI 本身难单测 | — |

## 7. 安全/数据完整性检查清单

- [ ] 编辑器全程只写 `user_pois.json`，绝不碰 data.json
- [ ] 取消编辑不影响已加载的 self.user_pois（传副本）
- [ ] X/Y 用 QSpinBox(0,4095) 从 UI 层就限制范围（双保险，user_data 也校验）
- [ ] 编辑器无任何网络请求
- [ ] 保存后立即 rebuild 缓存 + 重绘，所见即所得

## 8. 实施顺序建议

1. Panel 加按钮 + 信号（最小、低风险，可先静态验证）
2. PoiEditorDialog（纯本地，逻辑走已测的 user_data）
3. Overlay 接线 + 保存刷新
4. （可选）用户点位差异化描边
5. 真机验证：增点→保存→看叠加层是否即时显示在正确位置
