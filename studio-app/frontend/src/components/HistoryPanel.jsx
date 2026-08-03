import ImageCard from "./ImageCard.jsx";

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function providerLabel(provider) {
  if (provider === "tencent_hunyuan3d") return "Anom3D2";
  if (provider === "tencent_hunyuan3d_pro") return "Anom3D3";
  if (provider === "tencent_autorig") return "Anom3D2 · Rigged";
  return "Anom3D1";
}

function ThreeDHistoryCard({ entry, onSelect }) {
  return (
    <button
      type="button"
      onClick={() => onSelect(entry)}
      className="flex flex-col items-start gap-2 overflow-hidden rounded-lg border border-neutral-200 bg-white p-3 text-left transition-colors hover:border-accent"
    >
      <div className="flex aspect-square w-full items-center justify-center overflow-hidden rounded-md bg-neutral-100">
        {entry.preview_url ? (
          <img
            src={entry.preview_url}
            alt="3D model preview"
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="text-xs text-neutral-400">3D model</span>
        )}
      </div>
      <div className="w-full">
        <p className="font-mono text-xs text-neutral-600">{providerLabel(entry.provider)}</p>
        <p className="text-xs text-neutral-400">{formatTime(entry.timestamp)}</p>
      </div>
    </button>
  );
}

export default function HistoryPanel({ entries, onSelect3D }) {
  if (!entries || entries.length === 0) {
    return (
      <p className="text-sm text-neutral-500">
        Generated results will appear here as you create them, in this session.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {entries.map((entry) =>
        entry.type === "image" ? (
          <ImageCard key={entry.id} label={entry.label} url={entry.url} />
        ) : (
          <ThreeDHistoryCard key={entry.id} entry={entry} onSelect={onSelect3D} />
        ),
      )}
    </div>
  );
}
