import type { StreamStep } from "../types";

export function buildToolCallResultMap(steps: StreamStep[]): Map<number, StreamStep & { event: "tool_result" }> {
  const map = new Map<number, StreamStep & { event: "tool_result" }>();
  let callIdx = 0;
  for (const step of steps) {
    if (step.event === "tool_call") {
      const tcIdx = callIdx++;
      const results = steps.filter((s, si) => s.event === "tool_result" && s.tool === step.tool && si > steps.indexOf(step));
      if (results.length > 0) map.set(tcIdx, results[0] as StreamStep & { event: "tool_result" });
    }
  }
  return map;
}
