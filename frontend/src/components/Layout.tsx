import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { api } from "@/api";

const NAV = [
  { to: "/upload", label: "Upload" },
  { to: "/jobs", label: "Jobs" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/products", label: "Products" },
  { to: "/alerts", label: "Alerts" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const { data: countData } = useQuery({
    queryKey: ["alert-count"],
    queryFn: api.alertCount,
    refetchInterval: 15000,
  });
  const openCount = countData?.open ?? 0;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-border px-6 py-3 flex items-center gap-8 sticky top-0 z-10">
        <Link to="/dashboard" className="flex flex-col">
          <span className="text-base font-semibold text-foreground leading-tight">Product Intelligence</span>
          <span className="text-xs text-muted-foreground">Flipkart Seller Tools</span>
        </Link>
        <nav className="flex items-center gap-1">
          {NAV.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5",
                pathname.startsWith(to)
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-gray-100"
              )}
            >
              {label}
              {label === "Alerts" && openCount > 0 && (
                <span className="inline-flex items-center justify-center rounded-full bg-destructive text-destructive-foreground text-[10px] font-bold min-w-[16px] h-4 px-1 leading-none">
                  {openCount > 99 ? "99+" : openCount}
                </span>
              )}
            </Link>
          ))}
        </nav>
      </header>
      <main className="flex-1 px-6 py-6 max-w-7xl mx-auto w-full">{children}</main>
    </div>
  );
}
