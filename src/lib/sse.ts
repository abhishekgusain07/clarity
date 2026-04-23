import { useEffect, useState } from "react";
import { sseUrl } from "#/lib/api";
import type { PipelineEvent } from "#/lib/types";

export function useRunEvents(runId: string | null): PipelineEvent[] {
  const [events, setEvents] = useState<PipelineEvent[]>([]);

  useEffect(() => {
    if (!runId) return;

    const src = new EventSource(sseUrl(runId));
    const onMessage = (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data) as PipelineEvent;
        setEvents((prev) => [...prev, data]);
      } catch {
        // ignore malformed event
      }
    };

    src.addEventListener("message", onMessage);
    // Also listen for named event types emitted by sse-starlette
    const namedTypes = [
      "run_started",
      "run_resumed",
      "agent_start",
      "agent_done",
      "checkpoint_reached",
      "error",
    ];
    namedTypes.forEach((t) => src.addEventListener(t, onMessage as EventListener));

    return () => {
      src.close();
    };
  }, [runId]);

  return events;
}
