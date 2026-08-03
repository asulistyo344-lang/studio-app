import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  adminGetStats,
  adminListAuditLogs,
  adminListJobs,
  adminListUsers,
  adminRetryJob,
  adminUpdateUser,
} from "../api.js";

function SectionLabel({ children }) {
  return (
    <p className="mb-2 font-mono text-xs font-medium uppercase tracking-wider text-neutral-400">
      {children}
    </p>
  );
}

function StatTile({ label, value }) {
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4">
      <p className="font-mono text-xs uppercase tracking-wider text-neutral-400">{label}</p>
      <p className="mt-1 text-2xl font-black text-neutral-900">{value}</p>
    </div>
  );
}

const PAGE_SIZE = 50;

function LoadMoreButton({ items, total, onClick }) {
  if (items.length >= total) return null;
  return (
    <div className="mt-3 flex justify-center">
      <button
        type="button"
        onClick={onClick}
        className="rounded-md border border-neutral-200 px-3 py-1 text-xs text-neutral-600 hover:border-accent hover:text-accent"
      >
        Load more ({items.length} of {total})
      </button>
    </div>
  );
}

function JobRow({ job, onRetry }) {
  const [retrying, setRetrying] = useState(false);

  const handleRetry = async () => {
    setRetrying(true);
    try {
      await onRetry(job.id);
    } finally {
      setRetrying(false);
    }
  };

  return (
    <tr className="border-b border-neutral-100">
      <td className="py-2 pr-4">{job.user_email}</td>
      <td className="py-2 pr-4">{job.job_type}</td>
      <td className="py-2 pr-4 font-mono text-xs">{job.provider}</td>
      <td className="py-2 pr-4">
        <span
          className={
            job.status === "completed"
              ? "text-green-600"
              : job.status === "failed"
                ? "text-red-600"
                : "text-neutral-500"
          }
        >
          {job.status}
        </span>
      </td>
      <td className="py-2 pr-4 text-neutral-400">{new Date(job.created_at).toLocaleString()}</td>
      <td className="py-2 pr-4 text-xs text-neutral-400">{job.error_message || "—"}</td>
      <td className="py-2">
        {job.status === "failed" && (
          <button
            type="button"
            disabled={retrying}
            onClick={handleRetry}
            className="rounded-md border border-neutral-200 px-3 py-1 text-xs text-neutral-600 hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-40"
          >
            {retrying ? "Retrying..." : "Retry"}
          </button>
        )}
      </td>
    </tr>
  );
}

function UserRow({ user, onSave }) {
  const [role, setRole] = useState(user.role);
  const [status, setStatus] = useState(user.status);
  const [plan, setPlan] = useState(user.plan || "free");
  const [credits, setCredits] = useState(user.credits_balance);
  const [saving, setSaving] = useState(false);

  const dirty =
    role !== user.role ||
    status !== user.status ||
    plan !== (user.plan || "free") ||
    credits !== user.credits_balance;

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(user.id, { role, status, plan, credits_balance: Number(credits) });
    } finally {
      setSaving(false);
    }
  };

  return (
    <tr className="border-b border-neutral-100 text-sm">
      <td className="py-2 pr-4">{user.email}</td>
      <td className="py-2 pr-4">
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="rounded border border-neutral-200 px-2 py-1 text-xs"
        >
          <option value="user">user</option>
          <option value="admin">admin</option>
        </select>
      </td>
      <td className="py-2 pr-4">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className={
            "rounded border px-2 py-1 text-xs " +
            (status === "suspended" ? "border-red-200 text-red-600" : "border-neutral-200")
          }
        >
          <option value="active">active</option>
          <option value="suspended">suspended</option>
        </select>
      </td>
      <td className="py-2 pr-4">
        <select
          value={plan}
          onChange={(e) => setPlan(e.target.value)}
          className="rounded border border-neutral-200 px-2 py-1 text-xs"
        >
          <option value="free">free</option>
          <option value="pro">pro</option>
          <option value="enterprise">enterprise</option>
        </select>
      </td>
      <td className="py-2 pr-4">
        <input
          type="number"
          value={credits}
          onChange={(e) => setCredits(e.target.value)}
          className="w-20 rounded border border-neutral-200 px-2 py-1 text-xs"
        />
      </td>
      <td className="py-2 pr-4 text-neutral-500">{user.job_count}</td>
      <td className="py-2">
        <button
          type="button"
          disabled={!dirty || saving}
          onClick={handleSave}
          className="rounded-md border border-neutral-200 px-3 py-1 text-xs text-neutral-600 hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:opacity-40"
        >
          {saving ? "Saving..." : "Save"}
        </button>
      </td>
    </tr>
  );
}

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [usersTotal, setUsersTotal] = useState(0);
  const [jobs, setJobs] = useState([]);
  const [jobsTotal, setJobsTotal] = useState(0);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditTotal, setAuditTotal] = useState(0);
  const [userSearch, setUserSearch] = useState("");
  const [error, setError] = useState("");

  const refetch = () => {
    adminGetStats().then(setStats).catch((err) => setError(err.message));
    adminListUsers({ limit: PAGE_SIZE, offset: 0, q: userSearch })
      .then((data) => {
        setUsers(data.items);
        setUsersTotal(data.total);
      })
      .catch((err) => setError(err.message));
    adminListJobs({ limit: PAGE_SIZE, offset: 0 })
      .then((data) => {
        setJobs(data.items);
        setJobsTotal(data.total);
      })
      .catch((err) => setError(err.message));
    adminListAuditLogs({ limit: PAGE_SIZE, offset: 0 })
      .then((data) => {
        setAuditLogs(data.items);
        setAuditTotal(data.total);
      })
      .catch((err) => setError(err.message));
  };

  useEffect(refetch, []);

  const handleSaveUser = async (userId, payload) => {
    try {
      await adminUpdateUser(userId, payload);
      refetch();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRetryJob = async (jobId) => {
    try {
      await adminRetryJob(jobId);
      refetch();
    } catch (err) {
      setError(err.message);
    }
  };

  const loadMoreUsers = () => {
    adminListUsers({ limit: PAGE_SIZE, offset: users.length, q: userSearch })
      .then((data) => {
        setUsers((prev) => [...prev, ...data.items]);
        setUsersTotal(data.total);
      })
      .catch((err) => setError(err.message));
  };

  const handleSearchChange = (event) => {
    const q = event.target.value;
    setUserSearch(q);
    adminListUsers({ limit: PAGE_SIZE, offset: 0, q })
      .then((data) => {
        setUsers(data.items);
        setUsersTotal(data.total);
      })
      .catch((err) => setError(err.message));
  };

  const loadMoreJobs = () => {
    adminListJobs({ limit: PAGE_SIZE, offset: jobs.length })
      .then((data) => {
        setJobs((prev) => [...prev, ...data.items]);
        setJobsTotal(data.total);
      })
      .catch((err) => setError(err.message));
  };

  const loadMoreAuditLogs = () => {
    adminListAuditLogs({ limit: PAGE_SIZE, offset: auditLogs.length })
      .then((data) => {
        setAuditLogs((prev) => [...prev, ...data.items]);
        setAuditTotal(data.total);
      })
      .catch((err) => setError(err.message));
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="mx-auto max-w-6xl space-y-8 px-6 py-12">
        <div>
          <Link to="/" className="font-mono text-xs uppercase tracking-wider text-accent hover:underline">
            ← Back to Studio
          </Link>
          <p className="mb-1 mt-4 font-mono text-xs uppercase tracking-wider text-neutral-400">
            // ADMIN
          </p>
          <h1 className="text-3xl font-black text-neutral-900">Admin Dashboard</h1>
        </div>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {stats && (
          <section>
            <SectionLabel>Users</SectionLabel>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatTile label="Total Users" value={stats.total_users} />
              <StatTile label="Active (7d)" value={stats.active_users_7d} />
              <StatTile label="New Signups (7d)" value={stats.new_registrations_7d} />
              <StatTile label="Credits Consumed" value={stats.total_credits_consumed} />
            </div>

            <div className="mt-4">
              <SectionLabel>AI Usage</SectionLabel>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <StatTile label="Total Jobs" value={stats.total_jobs} />
                <StatTile label="Completed" value={stats.jobs_by_status.completed || 0} />
                <StatTile label="Failed" value={stats.jobs_by_status.failed || 0} />
                <StatTile
                  label="Avg Gen Time"
                  value={stats.avg_generation_seconds != null ? `${stats.avg_generation_seconds}s` : "—"}
                />
              </div>
            </div>

            <div className="mt-4">
              <SectionLabel>System</SectionLabel>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <StatTile label="Queue Depth" value={stats.queue_depth} />
                <StatTile label="Failure Rate" value={`${(stats.failure_rate * 100).toFixed(1)}%`} />
              </div>
            </div>
          </section>
        )}

        <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
          <SectionLabel>Users</SectionLabel>
          <input
            type="text"
            value={userSearch}
            onChange={handleSearchChange}
            placeholder="Search by email..."
            className="mb-4 w-full max-w-xs rounded-md border border-neutral-200 bg-white p-2 text-sm focus:border-accent focus:outline-none"
          />
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-neutral-200 font-mono text-xs uppercase tracking-wider text-neutral-400">
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Role</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Plan</th>
                  <th className="py-2 pr-4">Credits</th>
                  <th className="py-2 pr-4">Jobs</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <UserRow key={user.id} user={user} onSave={handleSaveUser} />
                ))}
              </tbody>
            </table>
          </div>
          <LoadMoreButton items={users} total={usersTotal} onClick={loadMoreUsers} />
        </section>

        <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
          <SectionLabel>Recent Jobs</SectionLabel>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-neutral-200 font-mono text-xs uppercase tracking-wider text-neutral-400">
                  <th className="py-2 pr-4">User</th>
                  <th className="py-2 pr-4">Type</th>
                  <th className="py-2 pr-4">Provider</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Created</th>
                  <th className="py-2 pr-4">Error</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <JobRow key={job.id} job={job} onRetry={handleRetryJob} />
                ))}
              </tbody>
            </table>
          </div>
          <LoadMoreButton items={jobs} total={jobsTotal} onClick={loadMoreJobs} />
        </section>

        <section className="rounded-xl border border-neutral-200 bg-white p-6 shadow-sm">
          <SectionLabel>Audit Log</SectionLabel>
          <div className="max-h-96 overflow-y-auto overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-neutral-200 font-mono text-xs uppercase tracking-wider text-neutral-400">
                  <th className="py-2 pr-4">User</th>
                  <th className="py-2 pr-4">Action</th>
                  <th className="py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map((log) => (
                  <tr key={log.id} className="border-b border-neutral-100">
                    <td className="py-2 pr-4">{log.user_email || "(deleted user)"}</td>
                    <td className="py-2 pr-4 font-mono text-xs">{log.action}</td>
                    <td className="py-2 text-neutral-400">{new Date(log.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <LoadMoreButton items={auditLogs} total={auditTotal} onClick={loadMoreAuditLogs} />
        </section>
      </div>
    </div>
  );
}
