import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createProject, deleteProject, getAccount, listProjects } from "../api.js";

function SectionLabel({ children }) {
  return (
    <p className="mb-2 font-mono text-xs font-medium uppercase tracking-wider text-neutral-400">
      {children}
    </p>
  );
}

const PLAN_LABELS = { free: "Free", pro: "Pro", enterprise: "Enterprise" };

export default function Account() {
  const [account, setAccount] = useState(null);
  const [projects, setProjects] = useState([]);
  const [newProjectName, setNewProjectName] = useState("");
  const [error, setError] = useState("");

  const refetch = () => {
    getAccount().then(setAccount).catch((err) => setError(err.message));
    listProjects().then(setProjects).catch((err) => setError(err.message));
  };

  useEffect(refetch, []);

  const handleCreateProject = async (event) => {
    event.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      await createProject(newProjectName.trim());
      setNewProjectName("");
      refetch();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteProject = async (id) => {
    try {
      await deleteProject(id);
      refetch();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="mx-auto max-w-3xl space-y-8 px-6 py-12">
        <div>
          <Link to="/" className="font-mono text-xs uppercase tracking-wider text-accent hover:underline">
            ← Back to Studio
          </Link>
          <p className="mb-1 mt-4 font-mono text-xs uppercase tracking-wider text-neutral-400">
            // ACCOUNT
          </p>
          <h1 className="text-3xl font-black text-neutral-900">Your Account</h1>
        </div>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {account && (
          <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
            <SectionLabel>Profile</SectionLabel>
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-neutral-400">Email</dt>
                <dd className="text-neutral-900">{account.email}</dd>
              </div>
              <div>
                <dt className="text-neutral-400">Plan</dt>
                <dd className="text-neutral-900">
                  {account.subscription ? PLAN_LABELS[account.subscription.plan] : "Free"}
                </dd>
              </div>
              <div>
                <dt className="text-neutral-400">Credits remaining</dt>
                <dd className="text-lg font-semibold text-accent">{account.credits_balance}</dd>
              </div>
              <div>
                <dt className="text-neutral-400">Member since</dt>
                <dd className="text-neutral-900">
                  {new Date(account.created_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
            <Link
              to="/billing"
              className="mt-4 inline-block text-xs font-medium text-accent hover:underline"
            >
              View plans & billing →
            </Link>
          </section>
        )}

        <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
          <SectionLabel>Projects</SectionLabel>
          <form onSubmit={handleCreateProject} className="mb-4 flex gap-2">
            <input
              type="text"
              value={newProjectName}
              onChange={(event) => setNewProjectName(event.target.value)}
              placeholder="New project name"
              className="flex-1 rounded-md border border-neutral-200 bg-white p-2 text-sm focus:border-accent focus:outline-none"
            />
            <button
              type="submit"
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover"
            >
              Create
            </button>
          </form>

          {projects.length === 0 ? (
            <p className="text-sm text-neutral-500">No projects yet.</p>
          ) : (
            <ul className="space-y-2">
              {projects.map((project) => (
                <li
                  key={project.id}
                  className="flex items-center justify-between rounded-md border border-neutral-200 px-3 py-2 text-sm"
                >
                  <span>{project.name}</span>
                  <button
                    type="button"
                    onClick={() => handleDeleteProject(project.id)}
                    className="text-xs text-neutral-400 hover:text-red-600"
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
