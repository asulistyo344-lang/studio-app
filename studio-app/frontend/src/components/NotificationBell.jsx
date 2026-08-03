import { useEffect, useRef, useState } from "react";
import { listNotifications, markAllNotificationsRead, markNotificationRead } from "../api.js";

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  const refresh = () => {
    listNotifications()
      .then(setNotifications)
      .catch(() => {
        /* non-fatal */
      });
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read_status).length;

  const handleMarkRead = async (id) => {
    await markNotificationRead(id);
    refresh();
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead();
    refresh();
  };

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="relative rounded-md border border-neutral-200 px-3 py-1.5 text-xs text-neutral-600 hover:border-accent hover:text-accent"
      >
        Notifications
        {unreadCount > 0 && (
          <span className="absolute -right-1.5 -top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-accent text-[10px] font-bold text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 rounded-lg border border-neutral-200 bg-white p-2 shadow-lg">
          <div className="mb-2 flex items-center justify-between px-2">
            <span className="font-mono text-xs uppercase tracking-wider text-neutral-400">
              Notifications
            </span>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="text-xs text-accent hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>

          {notifications.length === 0 ? (
            <p className="px-2 py-3 text-sm text-neutral-400">No notifications yet.</p>
          ) : (
            <div className="max-h-80 space-y-1 overflow-y-auto">
              {notifications.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => !n.read_status && handleMarkRead(n.id)}
                  className={`block w-full rounded-md p-2 text-left text-sm ${
                    n.read_status ? "text-neutral-400" : "bg-accent/5 text-neutral-800"
                  }`}
                >
                  <p>{n.message}</p>
                  <p className="mt-0.5 text-xs text-neutral-400">{formatTime(n.created_at)}</p>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
