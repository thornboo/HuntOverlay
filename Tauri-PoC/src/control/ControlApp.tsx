import { listen } from "@tauri-apps/api/event";
import { invoke } from "@tauri-apps/api/core";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { OverlayMode, OverlaySnapshot } from "../types";

const FALLBACK_SNAPSHOT: OverlaySnapshot = {
  visible: false,
  mode: "passthrough",
  holdTabEnabled: false,
  platform: "unknown",
  monitor: null,
};

const modeCopy: Record<
  OverlayMode,
  { title: string; description: string; command: string }
> = {
  passthrough: {
    title: "穿透",
    description: "游戏继续接收全部鼠标输入",
    command: "PASS",
  },
  pick: {
    title: "拾取",
    description: "覆盖层接管单击；右键或 Esc 退出",
    command: "PICK",
  },
  ruler: {
    title: "尺子",
    description: "连续选取两点；右键或 Esc 退出",
    command: "RULER",
  },
};

function StatusLight({ active }: { active: boolean }) {
  return <span className={active ? "status-light is-active" : "status-light"} />;
}

function formatMonitor(snapshot: OverlaySnapshot) {
  const monitor = snapshot.monitor;
  if (!monitor) {
    return "等待显示器信息";
  }

  return `${monitor.width}×${monitor.height} · ${Math.round(
    monitor.scaleFactor * 100,
  )}%`;
}

export function ControlApp() {
  const [snapshot, setSnapshot] =
    useState<OverlaySnapshot>(FALLBACK_SNAPSHOT);
  const [pending, setPending] = useState<string | null>("boot");
  const [lastError, setLastError] = useState<string | null>(null);

  useEffect(() => {
    let disposed = false;
    let unlisten: (() => void) | undefined;

    void invoke<OverlaySnapshot>("get_overlay_snapshot")
      .then((next) => {
        if (!disposed) {
          setSnapshot(next);
          setPending(null);
        }
      })
      .catch((error: unknown) => {
        if (!disposed) {
          setPending(null);
          setLastError(String(error));
        }
      });

    void listen<OverlaySnapshot>("overlay-state", (event) => {
      if (!disposed) {
        setSnapshot(event.payload);
      }
    }).then((cleanup) => {
      if (disposed) {
        cleanup();
      } else {
        unlisten = cleanup;
      }
    });

    return () => {
      disposed = true;
      unlisten?.();
    };
  }, []);

  const run = useCallback(
    async (label: string, action: () => Promise<unknown>) => {
      setPending(label);
      setLastError(null);
      try {
        await action();
      } catch (error) {
        setLastError(String(error));
      } finally {
        setPending(null);
      }
    },
    [],
  );

  const setVisible = (visible: boolean) =>
    run(visible ? "show" : "hide", () =>
      invoke("set_overlay_visible", { visible }),
    );

  const setMode = (mode: OverlayMode) =>
    run(`mode:${mode}`, () => invoke("set_overlay_mode", { mode }));

  const setHoldTab = (enabled: boolean) =>
    run("hold-tab", () => invoke("set_hold_tab_enabled", { enabled }));

  const monitorText = useMemo(() => formatMonitor(snapshot), [snapshot]);

  return (
    <main className="control-shell">
      <aside className="control-rail" aria-label="原型导航">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            H
          </div>
          <div>
            <strong>HuntOverlay</strong>
            <span>TAURI FLIGHT TEST</span>
          </div>
        </div>

        <nav className="rail-nav">
          <button className="rail-item is-active" type="button">
            <span className="rail-index">01</span>
            <span>覆盖层实验</span>
          </button>
          <button className="rail-item" type="button" disabled>
            <span className="rail-index">02</span>
            <span>性能遥测</span>
          </button>
          <button className="rail-item" type="button" disabled>
            <span className="rail-index">03</span>
            <span>Windows 实测</span>
          </button>
        </nav>

        <section className="rail-readout" aria-label="运行环境">
          <span className="eyebrow">RUNTIME</span>
          <strong>{snapshot.platform.toUpperCase()}</strong>
          <span>{monitorText}</span>
        </section>

        <div className="rail-foot">
          <span>POC / 0.1.0</span>
          <span>原项目未改动</span>
        </div>
      </aside>

      <section className="control-stage">
        <header className="stage-header">
          <div>
            <p className="eyebrow">WINDOW LAYER QUALIFICATION</p>
            <h1>透明覆盖层飞行台</h1>
            <p className="stage-lede">
              这一轮只证明窗口、输入和 Canvas 绘制能力，不迁移正式业务。
            </p>
          </div>
          <div className="live-chip">
            <StatusLight active={snapshot.visible} />
            <span>{snapshot.visible ? "OVERLAY LIVE" : "OVERLAY PARKED"}</span>
          </div>
        </header>

        {lastError ? (
          <div className="error-banner" role="alert">
            <span>COMMAND FAILURE</span>
            <strong>{lastError}</strong>
          </div>
        ) : null}

        <div className="stage-grid">
          <section className="panel-card launch-card">
            <div className="card-heading">
              <div>
                <span className="eyebrow">LAYER POWER</span>
                <h2>覆盖层窗口</h2>
              </div>
              <div className="numeric-state">
                {snapshot.visible ? "ON" : "OFF"}
              </div>
            </div>
            <p>
              同步至主显示器后显示透明 Canvas。默认模式不抢焦点并穿透鼠标。
            </p>
            <div className="button-row">
              <button
                className="command-button is-primary"
                type="button"
                disabled={pending !== null || snapshot.visible}
                onClick={() => void setVisible(true)}
              >
                <span>显示覆盖层</span>
                <kbd>SHOW</kbd>
              </button>
              <button
                className="command-button"
                type="button"
                disabled={pending !== null || !snapshot.visible}
                onClick={() => void setVisible(false)}
              >
                <span>隐藏</span>
                <kbd>HIDE</kbd>
              </button>
            </div>
          </section>

          <section className="panel-card monitor-card">
            <div className="card-heading">
              <div>
                <span className="eyebrow">PRIMARY DISPLAY</span>
                <h2>显示器同步</h2>
              </div>
              <span className="outlined-chip">
                {snapshot.monitor?.name ?? "UNRESOLVED"}
              </span>
            </div>
            <dl className="telemetry-grid">
              <div>
                <dt>物理尺寸</dt>
                <dd>
                  {snapshot.monitor
                    ? `${snapshot.monitor.width} × ${snapshot.monitor.height}`
                    : "—"}
                </dd>
              </div>
              <div>
                <dt>缩放比例</dt>
                <dd>
                  {snapshot.monitor
                    ? `${Math.round(snapshot.monitor.scaleFactor * 100)}%`
                    : "—"}
                </dd>
              </div>
              <div>
                <dt>物理原点</dt>
                <dd>
                  {snapshot.monitor
                    ? `${snapshot.monitor.x}, ${snapshot.monitor.y}`
                    : "—"}
                </dd>
              </div>
            </dl>
            <button
              className="text-command"
              type="button"
              disabled={pending !== null}
              onClick={() =>
                void run("sync", () => invoke("sync_overlay_to_primary"))
              }
            >
              重新同步主显示器
              <span aria-hidden="true">↗</span>
            </button>
          </section>

          <section className="panel-card mode-card">
            <div className="card-heading">
              <div>
                <span className="eyebrow">INPUT GATE</span>
                <h2>鼠标路由模式</h2>
              </div>
              <span className="outlined-chip">
                {modeCopy[snapshot.mode].command}
              </span>
            </div>
            <div className="mode-stack">
              {(Object.keys(modeCopy) as OverlayMode[]).map((mode) => {
                const copy = modeCopy[mode];
                const selected = snapshot.mode === mode;
                return (
                  <button
                    className={selected ? "mode-option is-selected" : "mode-option"}
                    type="button"
                    key={mode}
                    disabled={pending !== null}
                    onClick={() => void setMode(mode)}
                  >
                    <span className="mode-radio" aria-hidden="true" />
                    <span>
                      <strong>{copy.title}</strong>
                      <small>{copy.description}</small>
                    </span>
                    <code>{copy.command}</code>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="panel-card hotkey-card">
            <div className="card-heading">
              <div>
                <span className="eyebrow">WINDOWS INPUT POLL</span>
                <h2>按住 Tab 显示</h2>
              </div>
              <StatusLight active={snapshot.holdTabEnabled} />
            </div>
            <p>
              Windows 端由 Rust 每 8ms 读取按键状态；Shift、Ctrl 或 Alt
              同时按下时不会触发。
            </p>
            <label className="switch-line">
              <span>
                <strong>启用裸 Tab 验证</strong>
                <small>
                  {snapshot.platform === "windows"
                    ? "已具备 Windows 验证条件"
                    : "当前平台仅能验证窗口与 Canvas"}
                </small>
              </span>
              <input
                type="checkbox"
                checked={snapshot.holdTabEnabled}
                disabled={pending !== null || snapshot.platform !== "windows"}
                onChange={(event) => void setHoldTab(event.target.checked)}
              />
              <span className="switch-track" aria-hidden="true">
                <span />
              </span>
            </label>
          </section>
        </div>

        <footer className="test-strip">
          <span className="eyebrow">NEXT GATE</span>
          <strong>Windows · WebView2 · Hunt 无边框窗口化</strong>
          <span className="test-strip-note">
            当前本机验证不代表游戏环境通过
          </span>
        </footer>
      </section>
    </main>
  );
}
