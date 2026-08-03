import { IconBuilding, IconHome, IconShirt } from "./Icons.jsx";

const NICHES = [
  { id: "interior", label: "Interior Design", Icon: IconHome },
  { id: "exterior", label: "Exterior Design", Icon: IconBuilding },
  { id: "product_model", label: "Product on Model", Icon: IconShirt },
];

export default function NichePicker({ value, onChange }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {NICHES.map((niche) => (
        <button
          key={niche.id}
          type="button"
          onClick={() => onChange(niche.id)}
          className={`flex flex-col items-center gap-2 rounded-lg border px-3 py-4 text-sm transition-colors ${
            value === niche.id
              ? "border-accent bg-accent/10 text-accent"
              : "border-neutral-200 bg-white text-neutral-600 hover:border-neutral-300"
          }`}
        >
          <niche.Icon className="h-6 w-6" />
          <span className="text-center leading-tight">{niche.label}</span>
        </button>
      ))}
    </div>
  );
}
