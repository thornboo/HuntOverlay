import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ControlApp } from "./control/ControlApp";
import { OverlayApp } from "./overlay/OverlayApp";
import "./styles.css";

const params = new URLSearchParams(window.location.search);
const windowKind = params.get("window") === "overlay" ? "overlay" : "control";

document.documentElement.dataset.window = windowKind;
document.body.dataset.window = windowKind;

const root = document.getElementById("root");

if (!root) {
  throw new Error("Missing root element");
}

createRoot(root).render(
  <StrictMode>
    {windowKind === "overlay" ? <OverlayApp /> : <ControlApp />}
  </StrictMode>,
);
