export default function StylePicker({ styles, value, onChange }) {
  if (!styles || styles.length === 0) {
    return <p className="text-sm text-neutral-500">Loading styles…</p>;
  }

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {styles.map((style) => (
        <button
          key={style}
          type="button"
          onClick={() => onChange(style)}
          className={`rounded-md border px-3 py-2 font-mono text-sm transition-colors ${
            value === style
              ? "border-accent bg-accent/10 text-accent"
              : "border-neutral-200 bg-white text-neutral-600 hover:border-neutral-300"
          }`}
        >
          {style}
        </button>
      ))}
    </div>
  );
}
