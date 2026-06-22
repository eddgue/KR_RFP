"use client";

import { useState } from "react";
import { Button, Input } from "@/components/ui";

// The "run the engine on a round" control — a small round picker + submit. Lives
// in the Analysis-runs panel header. The actual call (and its error/loading) is
// owned by the page; this only collects the round and fires `onRun`.
export function RunAnalysisControl({
  onRun,
  running,
}: {
  onRun: (round: number) => void;
  running: boolean;
}) {
  const [round, setRound] = useState("1");
  const parsed = Number(round);
  const valid = Number.isInteger(parsed) && parsed >= 1;

  return (
    <div className="flex items-end gap-2">
      <div className="flex flex-col gap-1">
        <label
          htmlFor="analysis-round"
          className="text-2xs font-bold uppercase tracking-wide text-text-subtle"
        >
          Round
        </label>
        <Input
          id="analysis-round"
          type="number"
          min={1}
          value={round}
          onChange={(e) => setRound(e.target.value)}
          className="h-8 w-16"
          disabled={running}
          invalid={round !== "" && !valid}
        />
      </div>
      <Button
        size="sm"
        loading={running}
        disabled={!valid || running}
        onClick={() => valid && onRun(parsed)}
      >
        Run analysis
      </Button>
    </div>
  );
}
