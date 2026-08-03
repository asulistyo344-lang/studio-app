import { Navigate } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";

export default function AdminRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 text-sm text-neutral-400">
        Loading...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== "admin") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-6 text-center text-sm text-neutral-500">
        You don't have access to this page.
      </div>
    );
  }

  return children;
}
