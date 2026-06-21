import { KANBAN_BUCKETS } from "@/lib/api";
import type { Kanban, KanbanBucket, KanbanCard } from "@/lib/api";
import { cn } from "@/lib/cn";

// Visual accent per bucket — column header dot only, body stays neutral/calm.
const BUCKET_ACCENT: Record<KanbanBucket, string> = {
  Done: "bg-emerald-500",
  Doing: "bg-accent",
  Next: "bg-slate-400",
  "Waiting on you": "bg-amber-500",
};

// A card can be a string or an object; pull out a readable title.
function cardTitle(card: KanbanCard): string {
  if (typeof card === "string") return card;
  return (
    card.title ??
    card.label ??
    (typeof card.id === "string" ? card.id : "") ??
    ""
  ) || "Untitled item";
}

function cardKey(card: KanbanCard, index: number): string {
  if (typeof card === "string") return `${index}:${card}`;
  if (typeof card.id === "string") return card.id;
  return `${index}:${cardTitle(card)}`;
}

function Column({ bucket, cards }: { bucket: KanbanBucket; cards: KanbanCard[] }) {
  return (
    <div className="flex min-w-0 flex-col rounded-panel border border-line bg-surface-subtle">
      <div className="flex items-center justify-between gap-2 border-b border-line px-3.5 py-2.5">
        <div className="flex items-center gap-2">
          <span className={cn("h-2 w-2 rounded-full", BUCKET_ACCENT[bucket])} aria-hidden />
          <h3 className="text-sm font-semibold text-ink">{bucket}</h3>
        </div>
        <span className="rounded-full bg-surface-muted px-2 py-0.5 text-2xs font-medium text-ink-muted">
          {cards.length}
        </span>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-2.5">
        {cards.length === 0 ? (
          <p className="px-1 py-6 text-center text-xs text-ink-subtle">No items</p>
        ) : (
          cards.map((card, i) => (
            <div
              key={cardKey(card, i)}
              className="rounded-md border border-line bg-surface px-3 py-2.5 text-sm text-ink shadow-panel"
            >
              {cardTitle(card)}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export function KanbanBoard({ kanban }: { kanban: Kanban }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {KANBAN_BUCKETS.map((bucket) => (
        <Column key={bucket} bucket={bucket} cards={kanban[bucket] ?? []} />
      ))}
    </div>
  );
}
