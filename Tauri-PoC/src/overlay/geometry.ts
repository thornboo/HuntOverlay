import type { FixturePoint } from "../types";

export type AspectBucket = "16:9" | "21:9" | "32:9";

export interface MapBounds {
  left: number;
  top: number;
  width: number;
  height: number;
}

interface RectRatio {
  rx: number;
  ry: number;
  rw: number;
  rh: number;
}

const DEFAULT_RECT_RATIO: Record<AspectBucket, RectRatio> = {
  "16:9": {
    rx: 0.308203125,
    ry: 0.13819444444444445,
    rw: 0.384375,
    rh: 0.6833333333333333,
  },
  "21:9": {
    rx: 0.35625,
    ry: 0.13796296296296295,
    rw: 0.287890625,
    rh: 0.6833333333333333,
  },
  "32:9": {
    rx: 0.40390625,
    ry: 0.1375,
    rw: 0.1921875,
    rh: 0.6833333333333333,
  },
};

const MARKER_RADIUS: Record<FixturePoint["category"], number> = {
  spawn: 9,
  armory: 5,
  tower: 5,
  workbench: 3,
};

export function detectAspectBucket(width: number, height: number): AspectBucket {
  if (height <= 0) {
    return "16:9";
  }

  const aspect = width / height;
  if (aspect >= 3.2) {
    return "32:9";
  }
  if (aspect >= 2.2) {
    return "21:9";
  }
  return "16:9";
}

export function getMapBounds(width: number, height: number): MapBounds {
  const ratio = DEFAULT_RECT_RATIO[detectAspectBucket(width, height)];
  return {
    left: ratio.rx * width,
    top: ratio.ry * height,
    width: ratio.rw * width,
    height: ratio.rh * height,
  };
}

export function getMarkerRadius(category: FixturePoint["category"]): number {
  return MARKER_RADIUS[category];
}
