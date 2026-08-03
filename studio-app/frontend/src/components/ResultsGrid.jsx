import ImageCard from "./ImageCard.jsx";

function Skeleton() {
  return <div className="aspect-square animate-pulse rounded-lg bg-neutral-100 border border-neutral-200" />;
}

export default function ResultsGrid({ variants, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} />
        ))}
      </div>
    );
  }

  if (!variants || variants.length === 0) {
    return <p className="text-sm text-neutral-500">Your generated variants will appear here.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {variants.map((variant) => (
        <ImageCard key={variant.label} label={variant.label} url={variant.url} />
      ))}
    </div>
  );
}
