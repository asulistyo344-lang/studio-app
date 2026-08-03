const MAX_LENGTH = 200;

export default function PromptInput({ value, onChange }) {
  return (
    <div>
      <textarea
        value={value}
        maxLength={MAX_LENGTH}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Add specific details... (optional)"
        rows={3}
        className="w-full resize-none rounded-md border border-neutral-200 bg-white p-3 text-sm text-neutral-900 placeholder:text-neutral-400 focus:border-accent focus:outline-none"
      />
      <div className="mt-1 text-right text-xs text-neutral-500">
        {value.length}/{MAX_LENGTH}
      </div>
    </div>
  );
}
