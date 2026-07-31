export type OverlayMode = "passthrough" | "pick" | "ruler";

export interface MonitorSnapshot {
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  scaleFactor: number;
}

export interface OverlaySnapshot {
  visible: boolean;
  mode: OverlayMode;
  holdTabEnabled: boolean;
  platform: string;
  monitor: MonitorSnapshot | null;
}

export interface FixturePoint {
  id: string;
  category: "spawn" | "armory" | "tower" | "workbench";
  u: number;
  v: number;
  label: string;
}

export interface FixtureMap {
  map: string;
  aspect: string;
  points: FixturePoint[];
}
