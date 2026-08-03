import { useState } from "react";

async function downloadImage(url, filename) {
  const response = await fetch(url);
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(objectUrl);
}

export default function ImageCard({ label, url }) {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <div className="overflow-hidden rounded-lg border border-neutral-200 bg-white">
        <img
          src={url}
          alt={label}
          onClick={() => setShowModal(true)}
          className="aspect-square w-full cursor-pointer object-cover"
        />
        <div className="flex items-center justify-between p-3">
          <span className="font-mono text-sm text-neutral-600">{label}</span>
          <button
            type="button"
            onClick={() => downloadImage(url, `${label.replace(/\s+/g, "-").toLowerCase()}.jpg`)}
            className="rounded-md border border-neutral-300 px-3 py-1 text-xs text-neutral-600 hover:border-accent hover:text-accent"
          >
            Download
          </button>
        </div>
      </div>

      {showModal && (
        <div
          onClick={() => setShowModal(false)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6"
        >
          <img src={url} alt={label} className="max-h-full max-w-full rounded-lg" />
        </div>
      )}
    </>
  );
}
