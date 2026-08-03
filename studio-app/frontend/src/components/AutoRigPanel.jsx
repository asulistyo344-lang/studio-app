import { MOTION_TYPES } from "../motionTypes.js";
import { IconRun } from "./Icons.jsx";

export default function AutoRigPanel({ motionType, onMotionTypeChange, onAutoRig, loading, error }) {
  return (
    <div className="space-y-3 rounded-lg border border-neutral-200 bg-neutral-50 p-4">
      <div className="flex items-center gap-2 text-neutral-700">
        <IconRun className="h-5 w-5" />
        <p className="text-sm font-medium">Animate this model</p>
      </div>
      <p className="text-xs text-neutral-500">
        Rigs the model with a skeleton and applies a preset motion. Works best on humanoid or
        animal character models in a T-pose — not arbitrary product shapes.
      </p>

      <div className="flex flex-col gap-3 sm:flex-row">
        <select
          value={motionType}
          onChange={(e) => onMotionTypeChange(Number(e.target.value))}
          className="flex-1 rounded-md border border-neutral-200 bg-white p-2 text-sm text-neutral-900 focus:border-accent focus:outline-none"
        >
          {MOTION_TYPES.map((motion) => (
            <option key={motion.id} value={motion.id}>
              {motion.label}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={onAutoRig}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-all hover:bg-accent-hover hover:shadow-glow disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:shadow-none"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Animating...
            </>
          ) : (
            "Auto-Rig"
          )}
        </button>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
