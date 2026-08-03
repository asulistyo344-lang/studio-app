import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { animate3D, generate3D, generateImages, getStyles, listJobs, pollJob } from "./api.js";
import { useAuth } from "./AuthContext.jsx";
import logo from "./assets/logo.png";
import NichePicker from "./components/NichePicker.jsx";
import ProviderPicker from "./components/ProviderPicker.jsx";
import StylePicker from "./components/StylePicker.jsx";
import ImageUploader from "./components/ImageUploader.jsx";
import PromptInput from "./components/PromptInput.jsx";
import GenerateButton from "./components/GenerateButton.jsx";
import ResultsGrid from "./components/ResultsGrid.jsx";
import ThreeDViewer from "./components/ThreeDViewer.jsx";
import AutoRigPanel from "./components/AutoRigPanel.jsx";
import Gallery from "./components/Gallery.jsx";
import HistoryPanel from "./components/HistoryPanel.jsx";
import NotificationBell from "./components/NotificationBell.jsx";
import TabNav from "./components/TabNav.jsx";

const TAB_META = {
  image: {
    eyebrow: "// IMAGE STUDIO",
    title: "Interior, Exterior & Product Styling",
    description:
      "Upload a photo, pick a niche and style, and generate 3 styled variants in seconds.",
  },
  "3d": {
    eyebrow: "// 3D STUDIO",
    title: "Product to 3D Model",
    description:
      "Upload product photos and generate a downloadable 3D model with Anom3D1, Anom3D2, or Anom3D3.",
  },
  gallery: {
    eyebrow: "// GALLERY",
    title: "Sample Results",
    description: "A few example outputs, so you know what to expect before generating your own.",
  },
  history: {
    eyebrow: "// HISTORY",
    title: "Session History",
    description: "Everything you've generated in this session, in one place.",
  },
};

function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
      {message}
    </div>
  );
}

function SectionLabel({ children }) {
  return (
    <p className="mb-2 font-mono text-xs font-medium uppercase tracking-wider text-neutral-400">
      {children}
    </p>
  );
}

export default function App() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("image");
  const [allStyles, setAllStyles] = useState(null);
  const [niche, setNiche] = useState("interior");
  const [style, setStyle] = useState("");
  const [images, setImages] = useState([]);
  const [userPrompt, setUserPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [jobStatusText, setJobStatusText] = useState("");
  const [variants, setVariants] = useState([]);
  const [error, setError] = useState("");

  const [threeDImage, setThreeDImage] = useState([]);
  const [threeDPrompt, setThreeDPrompt] = useState("");
  const [threeDProvider, setThreeDProvider] = useState("byteplus_hyper3d");
  const [threeDLoading, setThreeDLoading] = useState(false);
  const [threeDStatusText, setThreeDStatusText] = useState("");
  const [threeDResult, setThreeDResult] = useState(null);
  const [threeDError, setThreeDError] = useState("");

  const [motionType, setMotionType] = useState(23);
  const [animating, setAnimating] = useState(false);
  const [animateError, setAnimateError] = useState("");

  const [historyJobs, setHistoryJobs] = useState([]);

  const refreshHistory = () => {
    listJobs()
      .then(setHistoryJobs)
      .catch(() => {
        /* non-fatal — history badge/list just stays stale */
      });
  };

  useEffect(refreshHistory, []);

  // Flatten completed jobs' results into the flat entry shape HistoryPanel
  // expects (one card per image variant, one per 3D result), newest first —
  // jobs already come back sorted by created_at desc.
  const history = historyJobs
    .filter((job) => job.status === "completed")
    .flatMap((job) =>
      job.job_type === "image"
        ? job.results.map((r, i) => ({
            id: `${job.id}-${i}`,
            type: "image",
            label: r.label,
            url: r.url,
            timestamp: new Date(job.created_at).getTime(),
          }))
        : job.results.map((r, i) => ({
            id: `${job.id}-${i}`,
            type: "3d",
            model_url: r.url,
            preview_url: r.preview_url,
            model_type: r.file_type,
            provider: job.provider,
            timestamp: new Date(job.created_at).getTime(),
          })),
    );

  useEffect(() => {
    getStyles()
      .then(setAllStyles)
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (allStyles && allStyles[niche]) {
      setStyle(allStyles[niche][0]);
    }
  }, [niche, allStyles]);

  const maxImages = niche === "product_model" ? 2 : 1;

  const handleGenerate = async () => {
    setError("");
    setLoading(true);
    setVariants([]);
    setJobStatusText("Queued...");
    try {
      const job = await generateImages({ niche, style, images, userPrompt });
      const completed = await pollJob(job.id, {
        onTick: (j) => setJobStatusText(j.status === "processing" ? "Generating..." : "Queued..."),
      });
      const resultVariants = completed.results.map((r) => ({ label: r.label, url: r.url }));
      setVariants(resultVariants);
      refreshHistory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setJobStatusText("");
    }
  };

  const handleGenerate3D = async () => {
    setThreeDError("");
    setThreeDLoading(true);
    setThreeDResult(null);
    setThreeDStatusText("Queued...");
    try {
      const job = await generate3D({
        images: threeDImage,
        userPrompt: threeDPrompt,
        provider: threeDProvider,
      });
      const completed = await pollJob(job.id, {
        onTick: (j) =>
          setThreeDStatusText(j.status === "processing" ? "Generating 3D model..." : "Queued..."),
      });
      const output = completed.results[0];
      const result = {
        model_url: output.url,
        preview_url: output.preview_url,
        model_type: output.file_type,
      };
      setThreeDResult(result);
      refreshHistory();
    } catch (err) {
      setThreeDError(err.message);
    } finally {
      setThreeDLoading(false);
      setThreeDStatusText("");
    }
  };

  const handleAutoRig = async () => {
    if (!threeDResult?.model_url) return;
    setAnimateError("");
    setAnimating(true);
    try {
      const job = await animate3D({ modelUrl: threeDResult.model_url, motionType });
      const completed = await pollJob(job.id);
      const output = completed.results[0];
      const result = {
        model_url: output.url,
        preview_url: output.preview_url,
        model_type: output.file_type,
      };
      setThreeDResult(result);
      refreshHistory();
    } catch (err) {
      setAnimateError(err.message);
    } finally {
      setAnimating(false);
    }
  };

  const handleSelectHistory3D = (entry) => {
    setThreeDError("");
    setThreeDResult({
      model_url: entry.model_url,
      preview_url: entry.preview_url,
      model_type: entry.model_type,
    });
    setActiveTab("3d");
  };

  const meta = TAB_META[activeTab];

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="sticky top-0 z-10 border-b border-neutral-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-3">
          <div className="flex items-center gap-3">
            <img src={logo} alt="AnomVision" className="h-9 w-auto" />
            <span className="hidden rounded-full border border-neutral-200 px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-neutral-500 sm:inline-block">
              Demo AI SaaS
            </span>
          </div>
          <div className="flex items-center gap-4">
            <TabNav active={activeTab} onChange={setActiveTab} historyCount={history.length} />
            <div className="flex items-center gap-2 border-l border-neutral-200 pl-4">
              <span className="hidden font-mono text-xs text-neutral-400 sm:inline">{user?.email}</span>
              <NotificationBell />
              {user?.role === "admin" && (
                <Link
                  to="/admin"
                  className="rounded-md border border-neutral-200 px-3 py-1.5 text-xs text-neutral-600 hover:border-accent hover:text-accent"
                >
                  Admin
                </Link>
              )}
              <Link
                to="/account"
                className="rounded-md border border-neutral-200 px-3 py-1.5 text-xs text-neutral-600 hover:border-accent hover:text-accent"
              >
                Account
              </Link>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-neutral-200 px-3 py-1.5 text-xs text-neutral-600 hover:border-accent hover:text-accent"
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-12">
        <div>
          <p className="mb-3 font-mono text-xs uppercase tracking-wider text-neutral-400">
            {meta.eyebrow}
          </p>
          <h1 className="text-3xl font-black tracking-tight text-neutral-900 sm:text-4xl">
            {meta.title}
          </h1>
          <p className="mt-3 max-w-xl text-neutral-500">{meta.description}</p>
        </div>

        {activeTab === "image" && (
        <section className="grid grid-cols-1 gap-8 rounded-xl border border-neutral-200 bg-white p-6 shadow-sm lg:grid-cols-2 lg:p-8">
          <div className="space-y-6">
            <div>
              <SectionLabel>1. Choose a niche</SectionLabel>
              <NichePicker value={niche} onChange={setNiche} />
            </div>

            <div>
              <SectionLabel>2. Choose a style</SectionLabel>
              <StylePicker
                styles={allStyles ? allStyles[niche] : []}
                value={style}
                onChange={setStyle}
              />
            </div>

            <div>
              <SectionLabel>3. Upload image(s)</SectionLabel>
              <ImageUploader maxImages={maxImages} images={images} onChange={setImages} />
            </div>

            <div>
              <SectionLabel>4. Optional prompt</SectionLabel>
              <PromptInput value={userPrompt} onChange={setUserPrompt} />
            </div>

            <ErrorBanner message={error} />

            <GenerateButton
              onClick={handleGenerate}
              loading={loading}
              disabled={images.length === 0 || !style}
            />
            {loading && jobStatusText && (
              <p className="text-center font-mono text-xs text-neutral-400">{jobStatusText}</p>
            )}
          </div>

          <div>
            <SectionLabel>Results</SectionLabel>
            <ResultsGrid variants={variants} loading={loading} />
          </div>
        </section>
        )}

        {activeTab === "3d" && (
        <section className="space-y-4 rounded-xl border border-neutral-200 bg-white p-6 shadow-sm lg:p-8">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <div className="space-y-4">
              <ProviderPicker value={threeDProvider} onChange={setThreeDProvider} />
              <ImageUploader maxImages={4} images={threeDImage} onChange={setThreeDImage} />
              <PromptInput value={threeDPrompt} onChange={setThreeDPrompt} />
              <ErrorBanner message={threeDError} />
              <GenerateButton
                onClick={handleGenerate3D}
                loading={threeDLoading}
                disabled={threeDImage.length === 0}
                label="Generate 3D Model"
              />
            </div>

            <div className="space-y-4">
              {threeDLoading && (
                <div className="flex h-64 flex-col items-center justify-center gap-2 rounded-lg border border-neutral-200 bg-neutral-50 text-sm text-neutral-500">
                  <span>{threeDStatusText || "Queued..."}</span>
                  <span className="text-xs text-neutral-400">(this can take up to 20 minutes)</span>
                </div>
              )}
              {!threeDLoading && threeDResult && (
                <>
                  <ThreeDViewer
                    modelUrl={threeDResult.model_url}
                    previewUrl={threeDResult.preview_url}
                    modelType={threeDResult.model_type}
                  />
                  <AutoRigPanel
                    motionType={motionType}
                    onMotionTypeChange={setMotionType}
                    onAutoRig={handleAutoRig}
                    loading={animating}
                    error={animateError}
                  />
                </>
              )}
            </div>
          </div>
        </section>
        )}

        {activeTab === "gallery" && (
        <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm lg:p-8">
          <Gallery />
        </section>
        )}

        {activeTab === "history" && (
        <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm lg:p-8">
          <HistoryPanel entries={history} onSelect3D={handleSelectHistory3D} />
        </section>
        )}
      </main>
    </div>
  );
}
