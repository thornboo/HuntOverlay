use serde::{Deserialize, Serialize};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Mutex,
};
#[cfg(windows)]
use std::time::Duration;
use tauri::{AppHandle, Emitter, Manager, State, WebviewWindow};

const OVERLAY_LABEL: &str = "overlay";

#[derive(Debug, Clone, Copy, Default, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
enum OverlayMode {
    #[default]
    Passthrough,
    Pick,
    Ruler,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct MonitorSnapshot {
    name: String,
    x: i32,
    y: i32,
    width: u32,
    height: u32,
    scale_factor: f64,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct OverlaySnapshot {
    visible: bool,
    mode: OverlayMode,
    hold_tab_enabled: bool,
    platform: &'static str,
    monitor: Option<MonitorSnapshot>,
}

#[derive(Default)]
struct RuntimeState {
    visible: AtomicBool,
    hold_tab_enabled: AtomicBool,
    mode: Mutex<OverlayMode>,
}

fn overlay_window(app: &AppHandle) -> Result<WebviewWindow, String> {
    app.get_webview_window(OVERLAY_LABEL)
        .ok_or_else(|| "overlay window is not available".to_string())
}

fn monitor_snapshot(window: &WebviewWindow) -> Result<Option<MonitorSnapshot>, String> {
    let monitor = window
        .primary_monitor()
        .map_err(|error| error.to_string())?;

    Ok(monitor.map(|monitor| {
        let position = monitor.position();
        let size = monitor.size();
        MonitorSnapshot {
            name: monitor
                .name()
                .cloned()
                .unwrap_or_else(|| "Primary display".to_string()),
            x: position.x,
            y: position.y,
            width: size.width,
            height: size.height,
            scale_factor: monitor.scale_factor(),
        }
    }))
}

fn sync_window_to_primary(window: &WebviewWindow) -> Result<(), String> {
    let monitor = window
        .primary_monitor()
        .map_err(|error| error.to_string())?
        .ok_or_else(|| "no primary monitor was reported by the operating system".to_string())?;

    window
        .set_position(*monitor.position())
        .map_err(|error| error.to_string())?;
    window
        .set_size(*monitor.size())
        .map_err(|error| error.to_string())?;
    window
        .set_always_on_top(true)
        .map_err(|error| error.to_string())?;

    Ok(())
}

fn current_snapshot(app: &AppHandle, state: &RuntimeState) -> Result<OverlaySnapshot, String> {
    let window = overlay_window(app)?;
    let mode = *state
        .mode
        .lock()
        .map_err(|_| "overlay mode state is poisoned".to_string())?;

    Ok(OverlaySnapshot {
        visible: state.visible.load(Ordering::SeqCst),
        mode,
        hold_tab_enabled: state.hold_tab_enabled.load(Ordering::SeqCst),
        platform: std::env::consts::OS,
        monitor: monitor_snapshot(&window)?,
    })
}

fn emit_snapshot(app: &AppHandle, state: &RuntimeState) -> Result<(), String> {
    let snapshot = current_snapshot(app, state)?;
    app.emit("overlay-state", snapshot)
        .map_err(|error| error.to_string())
}

fn apply_overlay_mode(
    app: &AppHandle,
    state: &RuntimeState,
    mode: OverlayMode,
) -> Result<(), String> {
    overlay_window(app)?
        .set_ignore_cursor_events(matches!(mode, OverlayMode::Passthrough))
        .map_err(|error| error.to_string())?;

    *state
        .mode
        .lock()
        .map_err(|_| "overlay mode state is poisoned".to_string())? = mode;

    Ok(())
}

fn set_overlay_mode_internal(
    app: &AppHandle,
    state: &RuntimeState,
    mode: OverlayMode,
) -> Result<(), String> {
    apply_overlay_mode(app, state, mode)?;
    emit_snapshot(app, state)
}

fn set_overlay_visible_internal(
    app: &AppHandle,
    state: &RuntimeState,
    visible: bool,
) -> Result<(), String> {
    let window = overlay_window(app)?;

    if visible {
        sync_window_to_primary(&window)?;
        window.show().map_err(|error| error.to_string())?;
    } else {
        apply_overlay_mode(app, state, OverlayMode::Passthrough)?;
        window.hide().map_err(|error| error.to_string())?;
    }

    state.visible.store(visible, Ordering::SeqCst);
    emit_snapshot(app, state)
}

#[tauri::command]
fn get_overlay_snapshot(
    app: AppHandle,
    state: State<'_, RuntimeState>,
) -> Result<OverlaySnapshot, String> {
    current_snapshot(&app, &state)
}

#[tauri::command]
fn set_overlay_visible(
    app: AppHandle,
    state: State<'_, RuntimeState>,
    visible: bool,
) -> Result<(), String> {
    set_overlay_visible_internal(&app, &state, visible)
}

#[tauri::command]
fn sync_overlay_to_primary(app: AppHandle, state: State<'_, RuntimeState>) -> Result<(), String> {
    sync_window_to_primary(&overlay_window(&app)?)?;
    emit_snapshot(&app, &state)
}

#[tauri::command]
fn set_overlay_mode(
    app: AppHandle,
    state: State<'_, RuntimeState>,
    mode: OverlayMode,
) -> Result<(), String> {
    set_overlay_mode_internal(&app, &state, mode)
}

#[tauri::command]
fn set_hold_tab_enabled(
    app: AppHandle,
    state: State<'_, RuntimeState>,
    enabled: bool,
) -> Result<(), String> {
    state.hold_tab_enabled.store(enabled, Ordering::SeqCst);
    if !enabled {
        set_overlay_visible_internal(&app, &state, false)?;
    } else {
        emit_snapshot(&app, &state)?;
    }
    Ok(())
}

#[tauri::command]
fn reset_overlay_demo(app: AppHandle) -> Result<(), String> {
    app.emit_to(OVERLAY_LABEL, "overlay-reset", ())
        .map_err(|error| error.to_string())
}

#[cfg(windows)]
fn key_is_down(key: windows::Win32::UI::Input::KeyboardAndMouse::VIRTUAL_KEY) -> bool {
    use windows::Win32::UI::Input::KeyboardAndMouse::GetAsyncKeyState;
    unsafe { GetAsyncKeyState(key.0 as i32) < 0 }
}

#[cfg(windows)]
fn start_windows_tab_polling(app: AppHandle) {
    use windows::Win32::UI::Input::KeyboardAndMouse::{
        VK_CONTROL, VK_ESCAPE, VK_MENU, VK_SHIFT, VK_TAB,
    };

    let _ = std::thread::Builder::new()
        .name("huntoverlay-tab-poll".to_string())
        .spawn(move || {
            let mut was_pressed = false;
            let mut escape_was_pressed = false;

            loop {
                if app.get_webview_window("control").is_none()
                    && app.get_webview_window(OVERLAY_LABEL).is_none()
                {
                    break;
                }

                let state = app.state::<RuntimeState>();
                let escape_pressed = key_is_down(VK_ESCAPE);
                if escape_pressed && !escape_was_pressed {
                    let is_interactive = state
                        .mode
                        .lock()
                        .map(|mode| !matches!(*mode, OverlayMode::Passthrough))
                        .unwrap_or(false);
                    if is_interactive {
                        let _ = set_overlay_mode_internal(&app, &state, OverlayMode::Passthrough);
                    }
                }
                escape_was_pressed = escape_pressed;

                let enabled = state.hold_tab_enabled.load(Ordering::SeqCst);
                let pressed = enabled
                    && key_is_down(VK_TAB)
                    && !key_is_down(VK_SHIFT)
                    && !key_is_down(VK_CONTROL)
                    && !key_is_down(VK_MENU);

                if pressed != was_pressed {
                    let _ = set_overlay_visible_internal(&app, &state, pressed);
                    was_pressed = pressed;
                }

                std::thread::sleep(Duration::from_millis(8));
            }
        });
}

pub fn run() {
    tauri::Builder::default()
        .manage(RuntimeState::default())
        .invoke_handler(tauri::generate_handler![
            get_overlay_snapshot,
            set_overlay_visible,
            sync_overlay_to_primary,
            set_overlay_mode,
            set_hold_tab_enabled,
            reset_overlay_demo
        ])
        .setup(|app| {
            let overlay = app
                .get_webview_window(OVERLAY_LABEL)
                .ok_or("configured overlay window was not created")?;

            sync_window_to_primary(&overlay)?;
            overlay.set_ignore_cursor_events(true)?;
            overlay.hide()?;

            #[cfg(windows)]
            start_windows_tab_polling(app.handle().clone());

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running HuntOverlay Tauri PoC");
}
