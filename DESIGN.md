# Design

## Source of truth
- Status: Active
- Last refreshed: 2026-07-30
- Primary product surfaces: centered Windows control center, click-through map overlay, POI editor dialogs
- Evidence reviewed: `README.zh-CN.md`, `huntoverlay/widgets/panel.py`, `huntoverlay/widgets/dialogs.py`, `huntoverlay/widgets/poi_editor.py`, `huntoverlay/overlay.py`, `huntoverlay/i18n.py`, `tests/test_panel_layout.py`, `docs/verification-checklist.md`

## Brand
- Personality: tactical, restrained, dependable, field-utility focused
- Trust signals: explicit data status, visible recovery actions, predictable native controls, clear separation between official and user data
- Avoid: neon gamer styling, glassmorphism, web-dashboard chrome, oversized cards, decorative motion, crowded top tabs

## Product goals
- Goals: make high-frequency map controls fast to find; provide a durable shell for future real modules; keep the panel usable in Chinese and English; preserve taskbar and notification-area recoverability
- Non-goals: redesign the map overlay rendering; add placeholder community/reporting pages; add networking; replace Qt Widgets
- Success signals: the first visible launch is centered; the window is landscape and resizable; all current capabilities remain reachable; common actions require no more navigation than before

## Personas and jobs
- Primary personas: Hunt: Showdown players using a Windows borderless/windowed game session
- User jobs: select a map, control POI visibility, add or manage custom points, measure distance, inspect boss reference data, configure application behavior
- Key contexts of use: initial setup, short mid-session adjustments, post-session point management, recovery from tray/minimized state

## Information architecture
- Primary navigation: persistent left navigation with Map & Tools, Official POIs, Boss Reference, Settings
- Core routes/screens: one stacked page per current navigation item; no future placeholder pages
- Content hierarchy: window identity and current page title, page-specific primary controls, secondary settings, persistent data/update status

## Design principles
- Fast before decorative: common controls stay visible with compact, readable density
- Expand without crowding: new real modules may add navigation entries without shrinking existing labels
- Native and recoverable: retain a normal taskbar window and existing independent notification-area settings
- Preserve behavior during visual changes: public widget attributes and signal contracts remain stable
- Tradeoffs: a centered panel may cover more of the game than the former top-right strip, but provides the working area required for forms, lists, and future modules

## Visual language
- Color: charcoal `#0D0F10`, sidebar `#121416`, main surface `#171A1D`, cards `#242829`, warm border `#6A573B`, primary text `#F1EADF`, secondary text `#AFA89E`, old-gold accent `#C99945`, focus `#F0BD62`
- Typography: Georgia for the Latin brand where installed, Bahnschrift for page identity, and Microsoft YaHei UI / Segoe UI fallbacks for readable Chinese and English controls
- Spacing/layout rhythm: 8/10/12/16/20 px rhythm; 20 px main margins; 36 px controls; 56 px navigation rows
- Shape/radius/elevation: restrained 4-6 px radii, warm outer borders, lightweight painted inner edges, and short static shadows
- Motion: instant page changes and restrained hover/pressed state changes; no decorative animation in the first implementation
- Imagery/iconography: dependency-free `QPainter` navigation icons and compact card markers; no external artwork dependency

## Components
- Existing components to reuse: `DotChip`, standard Qt buttons, scroll areas, and boss data cards
- New/changed components: control-center shell, sidebar navigation, page heading, section card, two-column page grids, persistent update/status panel, `TacticalFrame`, and style-independent combo/spin controls
- Variants and states: normal/hover/checked/focus/disabled navigation and controls; success/muted update status
- Token/component ownership: panel stylesheet and small panel-local construction helpers; do not introduce a separate design-system package yet

## Accessibility
- Target standard: keyboard-operable desktop utility with readable AA-like contrast
- Keyboard/focus behavior: visible brass focus borders; navigation and all actions remain reachable by Tab; selected navigation item is visibly distinct
- Contrast/readability: body text uses parchment/gray on charcoal; status colors never carry meaning without text
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
- Framework/styling system: PySide6 Qt Widgets and Qt stylesheets
- Design-token constraints: reuse the panel-local palette; do not add a theme dependency
- Performance constraints: no continuous UI animation; no new rendering work in the overlay; preserve cached/dirty-region overlay behavior
- Compatibility constraints: Python 3.10-3.13, PyInstaller, Windows taskbar/tray behavior, bilingual labels, existing public Panel attributes/signals
- Test/screenshot expectations: targeted layout/positioning tests, full pytest suite, offscreen control-center screenshot, visual verdict against the approved concept, Windows manual DPI/multi-monitor verification

## Open questions
- [ ] Decide in a later iteration whether user-moved panel geometry should persist across launches.
- [ ] Define reporting/feedback objects, identity, privacy, and backend ownership before adding a reporting module.
- [ ] Revisit single-column responsive behavior only if support below the `760×480` minimum becomes a product requirement.
