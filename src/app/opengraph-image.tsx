import { ImageResponse } from "next/og";
import { modelOrder, scenarioOrder } from "@/lib/catalog";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "BenchViz: one-shot frontend capability benchmark";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#f4f4f4",
          color: "#161616",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 64,
          fontFamily: "IBM Plex Sans, Helvetica, sans-serif",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 24 }}>
          <span style={{ background: "#0f62fe", color: "#fff", padding: "8px 16px" }}>BV</span>
          <span>{modelOrder.length} models · {scenarioOrder.length} challenges</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 72, lineHeight: 1.05, maxWidth: 900 }}>See what models can actually build.</div>
          <div style={{ marginTop: 24, fontSize: 28, color: "#525252" }}>BenchViz — one-shot HTML arena. Vote the strongest artifact.</div>
        </div>
      </div>
    ),
    size,
  );
}
