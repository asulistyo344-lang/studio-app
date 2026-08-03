import ImageCard from "./ImageCard.jsx";
import ThreeDViewer from "./ThreeDViewer.jsx";

const SAMPLE_IMAGES = [
  { label: "Sample 1", url: "/sample-result/image/1.jpeg" },
  { label: "Sample 2", url: "/sample-result/image/2.jpeg" },
  { label: "Sample 3", url: "/sample-result/image/3.jpeg" },
];

const SAMPLE_MODELS = [
  { label: "Animated Character (GLB)", url: "/sample-result/3D/3D-ANM.glb", modelType: "GLB" },
  { label: "Animated Character (FBX)", url: "/sample-result/3D/3d-animate.fbx", modelType: "FBX" },
  { label: "3D Model (GLB)", url: "/sample-result/3D/3d2.glb", modelType: "GLB" },
];

function SectionLabel({ children }) {
  return (
    <p className="mb-3 font-mono text-xs font-medium uppercase tracking-wider text-neutral-400">
      {children}
    </p>
  );
}

export default function Gallery() {
  return (
    <div className="space-y-10">
      <div>
        <SectionLabel>Sample Images</SectionLabel>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {SAMPLE_IMAGES.map((sample) => (
            <ImageCard key={sample.url} label={sample.label} url={sample.url} />
          ))}
        </div>
      </div>

      <div>
        <SectionLabel>Sample 3D Models</SectionLabel>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {SAMPLE_MODELS.map((sample) => (
            <div key={sample.url} className="space-y-2">
              <ThreeDViewer
                modelUrl={sample.url}
                previewUrl={null}
                modelType={sample.modelType}
              />
              <p className="text-center text-sm text-neutral-600">{sample.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
