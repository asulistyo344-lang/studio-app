import { IconBolt, IconCube, IconSparkle } from "./Icons.jsx";

const PROVIDERS = [
  { id: "byteplus_hyper3d", label: "Anom3D1", Icon: IconCube },
  { id: "tencent_hunyuan3d", label: "Anom3D2", Icon: IconBolt },
  { id: "tencent_hunyuan3d_pro", label: "Anom3D3", Icon: IconSparkle },
];

export default function ProviderPicker({ value, onChange }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {PROVIDERS.map((provider) => (
        <button
          key={provider.id}
          type="button"
          onClick={() => onChange(provider.id)}
          className={`flex flex-col items-center gap-2 rounded-lg border px-3 py-4 text-sm transition-colors ${
            value === provider.id
              ? "border-accent bg-accent/10 text-accent"
              : "border-neutral-200 bg-white text-neutral-600 hover:border-neutral-300"
          }`}
        >
          <provider.Icon className="h-6 w-6" />
          <span className="text-center leading-tight">{provider.label}</span>
        </button>
      ))}
    </div>
  );
}
