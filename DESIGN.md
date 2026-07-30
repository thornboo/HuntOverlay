# Design

## Source of truth
- Status: Active
- Last refreshed: 2026-07-30
- Primary product surfaces: centered Windows control center, click-through map overlay, POI editor dialogs
- Evidence reviewed: `README.zh-CN.md`, `huntoverlay/widgets/panel.py`, `huntoverlay/widgets/dialogs.py`, `huntoverlay/widgets/poi_editor.py`, `huntoverlay/overlay.py`, `huntoverlay/i18n.py`, `tests/test_panel_layout.py`, `docs/verification-checklist.md`, `.omx/artifacts/control-center/qml-fluent-reference.png`

## Brand
- Personality: calm, modern, dependable, system-utility focused
- Trust signals: explicit data status, visible recovery actions, predictable Windows-like controls, clear separation between official and user data
- Avoid: gold/metal tactical styling, game-mod HUD language, serif display branding, background texture, excessive glass blur, neon, oversized cards, decorative motion, crowded top tabs

## Product goals
- Goals: make high-frequency map controls fast to find; provide a durable shell for future real modules; keep the panel usable in Chinese and English; preserve taskbar and notification-area recoverability
- Non-goals: redesign the map overlay renderer; add placeholder community/reporting pages; add networking; migrate the transparent overlay or supporting dialogs in this iteration
- Success signals: the first visible launch is centered; the window is landscape and resizable; all current capabilities remain reachable; common actions require no more navigation than before; visual-verdict evidence and any remaining reference gap are recorded explicitly

## Personas and jobs
- Primary personas: Hunt: Showdown players using a Windows borderless/windowed game session
- User jobs: select a map, control POI visibility, add or manage custom points, measure distance, inspect boss reference data, configure application behavior
- Key contexts of use: initial setup, short mid-session adjustments, post-session point management, recovery from tray/minimized state

## Information architecture
- Primary navigation: persistent left navigation with Map & Tools, Official POIs, Boss Reference, Settings
- Core routes/screens: one stacked page per current navigation item; no future placeholder pages
- Content hierarchy: window identity and current page title, page-specific primary controls, secondary settings, persistent data/update status

## Design principles
- Quiet before decorative: hierarchy comes from spacing, typography, cool surface contrast, and one blue accent rather than ornament
- Fast before decorative: common controls stay visible with compact, readable density
- Expand without crowding: new real modules may add navigation entries without shrinking existing labels
- Native and recoverable: retain a normal taskbar window and existing independent notification-area settings
- Preserve behavior during visual changes: external signal/slot behavior remains stable while direct widget-field coupling is replaced by explicit panel methods and QML properties
- Tradeoffs: a centered panel may cover more of the game than the former top-right strip, but provides the working area required for forms, lists, and future modules

## Visual language
- Color: window `#202020`, sidebar `#1B1B1B`, content `#242424`, cards `#2B2B2B`, controls `#313131`, subtle border `#454545`, primary text `#F3F3F3`, secondary text `#CFCFCF`, tertiary text `#9D9D9D`, restrained accent/focus `#60CDFF`, success `#6CCB5F`
- Typography: Segoe UI Variable on Windows, Microsoft YaHei UI for Chinese fallback, Cascadia Mono only for compact version/keybind/path labels
- Spacing/layout rhythm: 4/8/12/16/20/24 px rhythm; 18 px content margins; 34 px controls; 44 px navigation rows
- Shape/radius/elevation: 6 px controls, 8 px cards, one-pixel cool borders, light card/topbar shadows only
- Motion: 120 ms color/focus/page transitions with no continuous animation; reduced-motion-compatible durations
- Imagery/iconography: deterministic monochrome QML glyphs or small SVG resources; no emoji, textures, or bitmap chrome

## Components
- Existing components to reuse: Python signal contracts, map/type/keybind data, existing overlay renderer, existing dialogs, and boss reference data
- New/changed components: `QQuickWidget` host, QML control-center shell, sidebar navigation, topbar, Fluent cards/buttons/inputs/switches, data-driven POI/keybind/boss models, and a Python `QObject` view model
- Variants and states: normal/hover/checked/focus/disabled navigation and controls; success/muted update status
- Token/component ownership: `huntoverlay/qml/Theme.qml` and small reusable QML components; do not add a third-party UI theme library

## Accessibility
- Target standard: keyboard-operable desktop utility with readable AA-like contrast
- Keyboard/focus behavior: visible blue focus borders; navigation and all actions remain reachable by Tab; selected navigation item is visibly distinct
- Contrast/readability: near-white/gray text on neutral graphite surfaces; status colors never carry meaning without text
- Screen-reader semantics: meaningful button text and accessible names on compact controls
- Reduced motion and sensory considerations: no required motion, flashing, or rapidly changing decorative content

## Responsive behavior
- Supported breakpoints/devices: Windows desktop at 1366×768 and above; 100%, 125%, and 150% DPI; primary-monitor placement for this iteration
- Layout adaptations: default `1040×660`, minimum `760×480`; scrollable content prevents vertical clipping; landscape content expands while the sidebar remains stable
- Touch/hover differences: mouse and keyboard are primary; hover is enhancement only

## Interaction states
- Loading: existing localized data/image progress labels remain visible
- Empty: zero custom POIs are expressed through the existing count label
- Error: existing error strings and image-unavailable feedback remain unchanged
- Success: update status text confirms the latest known data refresh
- Disabled: Qt disabled styling retains readable labels with lower contrast
- Offline/slow network, if applicable: current background update failures preserve local data; richer offline states belong to a future networking design

## Content voice
- Tone: concise, factual, operational
- Terminology: use “控制中心” for the main window, “覆盖层” for the map overlay, and keep notification-area options distinct
- Microcopy rules: name actions with verbs; avoid unexplained abbreviations; preserve canonical English map keys internally while displaying localized names

## Implementation constraints
- Framework/styling system: hybrid PySide6 architecture—existing Qt Widgets/QPainter overlay plus a `QQuickWidget`-hosted Qt Quick/QML control center using Qt Quick Controls
- Design-token constraints: use local QML tokens and components; do not add GPL UI libraries or an application-wide QWidget theme dependency
- Performance constraints: no continuous UI animation; pause or minimize QML work while hidden; no new rendering work in the overlay; preserve cached/dirty-region overlay behavior
- Compatibility constraints: Python 3.10-3.13, PySide6 6.6-6.8, PyInstaller 6.x, Windows taskbar/tray behavior, bilingual labels, and the existing external Panel signal semantics
- Test/screenshot expectations: QML load with zero warnings, contract/model tests, targeted layout/positioning tests, full pytest suite, offscreen or software-rendered control-center screenshots, visual verdict against `.omx/artifacts/control-center/qml-fluent-reference.png`, Windows manual build/DPI/multi-monitor verification

## Open questions
- [ ] Decide in a later iteration whether user-moved panel geometry should persist across launches.
- [ ] Define reporting/feedback objects, identity, privacy, and backend ownership before adding a reporting module.
- [ ] Revisit single-column responsive behavior only if support below the `760×480` minimum becomes a product requirement.
