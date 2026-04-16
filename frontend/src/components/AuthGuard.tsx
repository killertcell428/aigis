"use client";

import { useEffect, useState } from "react";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("aigis_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    setChecked(true);
  }, []);

  if (!checked) {
    return (
      <div className="min-h-screen bg-gd-deep flex items-center justify-center">
        <p className="text-gd-text-muted text-sm">Loading...</p>
      </div>
    );
  }

  return <>{children}</>;
}
