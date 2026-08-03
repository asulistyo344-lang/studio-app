import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { verifyEmail } from "../api.js";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState("verifying");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setError("No verification token provided.");
      return;
    }
    verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err) => {
        setStatus("error");
        setError(err.message);
      });
  }, [searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-6">
      <div className="w-full max-w-sm rounded-xl border border-neutral-200 bg-white p-8 text-center shadow-sm">
        <p className="mb-1 font-mono text-xs uppercase tracking-wider text-neutral-400">
          // VERIFY EMAIL
        </p>
        {status === "verifying" && <p className="text-sm text-neutral-500">Verifying...</p>}
        {status === "success" && (
          <p className="text-sm text-neutral-700">Your email has been verified.</p>
        )}
        {status === "error" && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        <Link to="/" className="mt-6 inline-block text-sm text-accent hover:underline">
          Go to Studio
        </Link>
      </div>
    </div>
  );
}
