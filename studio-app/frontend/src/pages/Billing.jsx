import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAccount } from "../api.js";

function SectionLabel({ children }) {
  return (
    <p className="mb-2 font-mono text-xs font-medium uppercase tracking-wider text-neutral-400">
      {children}
    </p>
  );
}

const PLANS = [
  { id: "free", label: "Free", credits: 30, blurb: "Starting balance for every new account." },
  { id: "pro", label: "Pro", credits: 500, blurb: "For regular generation workloads." },
  { id: "enterprise", label: "Enterprise", credits: 2000, blurb: "High-volume usage." },
];

export default function Billing() {
  const [account, setAccount] = useState(null);
  const [error, setError] = useState("");
  const [contactPlan, setContactPlan] = useState(null);

  useEffect(() => {
    getAccount().then(setAccount).catch((err) => setError(err.message));
  }, []);

  const currentPlan = account?.subscription?.plan || "free";

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="mx-auto max-w-3xl space-y-8 px-6 py-12">
        <div>
          <Link to="/account" className="font-mono text-xs uppercase tracking-wider text-accent hover:underline">
            ← Back to Account
          </Link>
          <p className="mb-1 mt-4 font-mono text-xs uppercase tracking-wider text-neutral-400">
            // BILLING
          </p>
          <h1 className="text-3xl font-black text-neutral-900">Billing &amp; Subscription</h1>
        </div>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {account && (
          <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
            <SectionLabel>Current Plan</SectionLabel>
            <div className="flex items-center justify-between">
              <p className="text-2xl font-black capitalize text-neutral-900">{currentPlan}</p>
              <div className="text-right">
                <p className="font-mono text-xs uppercase tracking-wider text-neutral-400">
                  Remaining Credits
                </p>
                <p className="text-2xl font-black text-accent">{account.credits_balance}</p>
              </div>
            </div>
          </section>
        )}

        <section>
          <SectionLabel>Available Plans</SectionLabel>
          <div className="grid gap-4 sm:grid-cols-3">
            {PLANS.map((plan) => {
              const isCurrent = plan.id === currentPlan;
              return (
                <div
                  key={plan.id}
                  className="flex flex-col justify-between rounded-xl border border-neutral-200 bg-white p-5 shadow-sm"
                >
                  <div>
                    <p className="font-black text-neutral-900">{plan.label}</p>
                    <p className="mt-1 text-sm text-accent">{plan.credits} credits</p>
                    <p className="mt-2 text-xs text-neutral-400">{plan.blurb}</p>
                  </div>
                  <button
                    type="button"
                    disabled={isCurrent}
                    onClick={() => setContactPlan(plan.label)}
                    className="mt-4 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {isCurrent ? "Current Plan" : "Upgrade"}
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        {contactPlan && (
          <div className="rounded-md border border-accent/30 bg-accent/5 px-4 py-3 text-sm text-neutral-700">
            To move to the <span className="font-semibold">{contactPlan}</span> plan, please
            contact support or an admin — plan changes aren't self-service yet.
          </div>
        )}
      </div>
    </div>
  );
}
