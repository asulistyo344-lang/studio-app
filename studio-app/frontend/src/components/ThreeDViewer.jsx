const PREVIEWABLE_TYPES = ["GLB", "GLTF"];

export default function ThreeDViewer({ modelUrl, previewUrl, modelType }) {
  if (!modelUrl) return null;

  const canPreview = !modelType || PREVIEWABLE_TYPES.includes(modelType.toUpperCase());
  const extension = (modelType || "glb").toLowerCase();

  if (!canPreview) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-neutral-200 bg-neutral-50 p-8 text-center">
        {previewUrl && (
          <img
            src={previewUrl}
            alt="Model preview"
            className="h-32 w-32 rounded-md object-cover"
          />
        )}
        <p className="text-sm text-neutral-500">
          Preview isn't available for .{extension} files in the browser — download to view it in
          a 3D app.
        </p>
        <a
          href={modelUrl}
          download
          className="inline-block rounded-md border border-neutral-300 bg-white px-4 py-2 text-sm text-neutral-600 hover:border-accent hover:text-accent"
        >
          Download .{extension}
        </a>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <model-viewer
        src={modelUrl}
        poster={previewUrl}
        camera-controls
        auto-rotate
        alt="Generated 3D model"
        style={{
          width: "100%",
          height: "400px",
          backgroundColor: "#f4f4f5",
          border: "1px solid #e5e5e5",
          borderRadius: "0.5rem",
        }}
      />
      <a
        href={modelUrl}
        download
        className="inline-block rounded-md border border-neutral-300 px-4 py-2 text-sm text-neutral-600 hover:border-accent hover:text-accent"
      >
        Download .{extension}
      </a>
    </div>
  );
}
