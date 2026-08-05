import assert from "node:assert/strict";
import {
  detectAspectBucket,
  getMapBounds,
  getMarkerRadius,
} from "../src/overlay/geometry.ts";

assert.equal(detectAspectBucket(1920, 1080), "16:9");
assert.equal(detectAspectBucket(2560, 1080), "21:9");
assert.equal(detectAspectBucket(5120, 1440), "32:9");

assert.deepEqual(getMapBounds(1920, 1080), {
  left: 591.75,
  top: 149.25,
  width: 738,
  height: 738,
});

assert.equal(getMarkerRadius("spawn"), 9);
assert.equal(getMarkerRadius("armory"), 5);
assert.equal(getMarkerRadius("tower"), 5);
assert.equal(getMarkerRadius("workbench"), 3);

console.log("Overlay geometry matches the current HuntOverlay defaults.");
