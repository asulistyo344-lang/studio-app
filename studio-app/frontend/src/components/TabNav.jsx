const TABS = [
  { id: "image", label: "Image Studio" },
  { id: "3d", label: "3D Studio" },
  { id: "gallery", label: "Gallery" },
  { id: "history", label: "History" },
];

export default function TabNav({ active, onChange, historyCount }) {
  return (
    <nav className="flex flex-wrap items-center gap-1">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={`flex items-center gap-1.5 rounded-full px-4 py-2 font-mono text-xs uppercase tracking-wider transition-colors ${
            active === tab.id
              ? "bg-accent/10 text-accent"
              : "text-neutral-500 hover:text-neutral-800"
          }`}
        >
          {tab.label}
          {tab.id === "history" && historyCount > 0 && (
            <span className="rounded-full bg-accent px-1.5 py-0.5 text-[10px] font-bold text-white">
              {historyCount}
            </span>
          )}
        </button>
      ))}
    </nav>
  );
}
