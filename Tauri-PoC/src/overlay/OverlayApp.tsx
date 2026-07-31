import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { useEffect, useRef, useState } from "react";
import fixture from "../../fixtures/sample-pois.json";
import type {
  FixtureMap,
  FixturePoint,
  OverlayMode,
  OverlaySnapshot,
} from "../types";

type Point = { x: number; y: number };

interface RenderState {
  mode: OverlayMode;
  cursor: Point | null;
  rulerStart: Point | null;
  rulerEnd: Point | null;
  pickPulse: Point | null;
}

const sample = fixture as FixtureMap;

const categoryStyle: Record<
  FixturePoint["category"],
  { fill: string; stroke: string; label: string }
> = {
  spawn: { fill: "#67d6ff", stroke: "#d5f5ff", label: "SPAWN" },
  armory: { fill: "#ffcc66", stroke: "#fff0bf", label: "ARMORY" },
  tower: { fill: "#a6ff96", stroke: "#e0ffd9", label: "TOWER" },
  workbench: { fill: "#ff8b78", stroke: "#ffe0da", label: "BENCH" },
};

function fitCanvas(canvas: HTMLCanvasElement) {
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const width = Math.max(1, window.innerWidth);
  const height = Math.max(1, window.innerHeight);

  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  const context = canvas.getContext("2d");
  context?.setTransform(dpr, 0, 0, dpr, 0, 0);

  return { width, height, dpr };
}

function drawReticle(
  context: CanvasRenderingContext2D,
  point: Point,
  color: string,
) {
  context.save();
  context.strokeStyle = color;
  context.lineWidth = 1;
  context.setLineDash([7, 7]);
  context.beginPath();
  context.moveTo(point.x - 32, point.y);
  context.lineTo(point.x + 32, point.y);
  context.moveTo(point.x, point.y - 32);
  context.lineTo(point.x, point.y + 32);
  context.stroke();
  context.setLineDash([]);
  context.beginPath();
  context.arc(point.x, point.y, 10, 0, Math.PI * 2);
  context.stroke();
  context.restore();
}

function drawScene(canvas: HTMLCanvasElement, state: RenderState) {
  const context = canvas.getContext("2d");
  if (!context) {
    return;
  }

  const { width, height } = fitCanvas(canvas);
  context.clearRect(0, 0, width, height);

  const bounds = {
    left: width * 0.075,
    top: height * 0.08,
    width: width * 0.85,
    height: height * 0.84,
  };

  context.save();
  context.strokeStyle = "rgba(112, 214, 255, 0.22)";
  context.lineWidth = 1;
  context.setLineDash([10, 12]);
  context.strokeRect(bounds.left, bounds.top, bounds.width, bounds.height);
  context.restore();

  for (const point of sample.points) {
    const x = bounds.left + point.u * bounds.width;
    const y = bounds.top + point.v * bounds.height;
    const style = categoryStyle[point.category];

    context.save();
    context.shadowColor = style.fill;
    context.shadowBlur = 14;
    context.fillStyle = style.fill;
    context.strokeStyle = "rgba(3, 10, 14, 0.88)";
    context.lineWidth = 3;
    context.beginPath();
    context.arc(x, y, 7, 0, Math.PI * 2);
    context.fill();
    context.stroke();
    context.shadowBlur = 0;
    context.strokeStyle = style.stroke;
    context.lineWidth = 1;
    context.beginPath();
    context.arc(x, y, 10, 0, Math.PI * 2);
    context.stroke();
    context.restore();
  }

  if (state.rulerStart && (state.rulerEnd || state.cursor)) {
    const end = state.rulerEnd ?? state.cursor;
    if (end) {
      const dx = end.x - state.rulerStart.x;
      const dy = end.y - state.rulerStart.y;
      const distance = Math.round(Math.hypot(dx, dy));

      context.save();
      context.strokeStyle = "#ffcf69";
      context.fillStyle = "#ffcf69";
      context.lineWidth = 2;
      context.setLineDash([8, 5]);
      context.beginPath();
      context.moveTo(state.rulerStart.x, state.rulerStart.y);
      context.lineTo(end.x, end.y);
      context.stroke();
      context.setLineDash([]);
      context.font = "600 13px Bahnschrift, sans-serif";
      context.fillText(
        `${distance} px`,
        (state.rulerStart.x + end.x) / 2 + 12,
        (state.rulerStart.y + end.y) / 2 - 12,
      );
      context.restore();
    }
  }

  if (state.cursor && state.mode !== "passthrough") {
    drawReticle(
      context,
      state.cursor,
      state.mode === "pick" ? "#67d6ff" : "#ffcf69",
    );

    context.save();
    context.font = "600 12px Bahnschrift, sans-serif";
    context.fillStyle = "rgba(5, 13, 18, 0.88)";
    context.strokeStyle = "rgba(140, 226, 255, 0.48)";
    context.lineWidth = 1;
    const label = `${Math.round(state.cursor.x)}, ${Math.round(state.cursor.y)}`;
    const textWidth = context.measureText(label).width;
    context.beginPath();
    context.roundRect(
      state.cursor.x + 18,
      state.cursor.y + 18,
      textWidth + 20,
      30,
      8,
    );
    context.fill();
    context.stroke();
    context.fillStyle = "#d9f6ff";
    context.fillText(label, state.cursor.x + 28, state.cursor.y + 38);
    context.restore();
  }

  if (state.pickPulse) {
    context.save();
    context.strokeStyle = "#ffffff";
    context.lineWidth = 2;
    context.beginPath();
    context.arc(state.pickPulse.x, state.pickPulse.y, 18, 0, Math.PI * 2);
    context.stroke();
    context.restore();
  }
}

export function OverlayApp() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const renderStateRef = useRef<RenderState>({
    mode: "passthrough",
    cursor: null,
    rulerStart: null,
    rulerEnd: null,
    pickPulse: null,
  });
  const [mode, setMode] = useState<OverlayMode>("passthrough");

  const redraw = () => {
    if (canvasRef.current) {
      drawScene(canvasRef.current, renderStateRef.current);
    }
  };

  useEffect(() => {
    const onResize = () => redraw();
    window.addEventListener("resize", onResize);
    redraw();
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    let disposed = false;
    let cleanupState: (() => void) | undefined;
    let cleanupReset: (() => void) | undefined;

    const applySnapshot = (snapshot: OverlaySnapshot) => {
      const nextMode = snapshot.mode;
      renderStateRef.current.mode = nextMode;
      if (nextMode === "passthrough") {
        renderStateRef.current.cursor = null;
      }
      setMode(nextMode);
      redraw();
    };

    void invoke<OverlaySnapshot>("get_overlay_snapshot").then((snapshot) => {
      if (!disposed) {
        applySnapshot(snapshot);
      }
    });

    void listen<OverlaySnapshot>("overlay-state", (event) => {
      if (!disposed) {
        applySnapshot(event.payload);
      }
    }).then((cleanup) => {
      if (disposed) cleanup();
      else cleanupState = cleanup;
    });

    void listen("overlay-reset", () => {
      renderStateRef.current.rulerStart = null;
      renderStateRef.current.rulerEnd = null;
      renderStateRef.current.pickPulse = null;
      redraw();
    }).then((cleanup) => {
      if (disposed) cleanup();
      else cleanupReset = cleanup;
    });

    return () => {
      disposed = true;
      cleanupState?.();
      cleanupReset?.();
    };
  }, []);

  const handlePointerMove = (event: React.PointerEvent<HTMLCanvasElement>) => {
    renderStateRef.current.cursor = {
      x: event.clientX,
      y: event.clientY,
    };
    redraw();
  };

  const handlePointerLeave = () => {
    renderStateRef.current.cursor = null;
    redraw();
  };

  const handlePointerDown = (event: React.PointerEvent<HTMLCanvasElement>) => {
    const point = { x: event.clientX, y: event.clientY };
    if (mode === "pick") {
      renderStateRef.current.pickPulse = point;
    } else if (mode === "ruler") {
      if (
        renderStateRef.current.rulerStart === null ||
        renderStateRef.current.rulerEnd !== null
      ) {
        renderStateRef.current.rulerStart = point;
        renderStateRef.current.rulerEnd = null;
      } else {
        renderStateRef.current.rulerEnd = point;
      }
    }
    redraw();
  };

  return (
    <main className={`overlay-shell mode-${mode}`}>
      <canvas
        ref={canvasRef}
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
        onPointerDown={handlePointerDown}
        aria-label="HuntOverlay Tauri 覆盖层原型"
      />
      <div className="overlay-readout" aria-hidden="true">
        <span>HO / TAURI POC</span>
        <strong>{mode.toUpperCase()}</strong>
        <small>
          {sample.map} · {sample.points.length} FIXTURE POINTS
        </small>
      </div>
      {mode !== "passthrough" ? (
        <div className="interaction-note" aria-hidden="true">
          {mode === "pick"
            ? "点击任意位置验证点位拾取"
            : "依次点击两个位置验证尺子"}
        </div>
      ) : null}
    </main>
  );
}
