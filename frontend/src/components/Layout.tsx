import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/upload", label: "Upload" },
  { to: "/jobs", label: "Jobs" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/products", label: "Products" },
  { to: "/alerts", label: "Alerts" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();

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
                "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                pathname.startsWith(to)
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-gray-100"
              )}
            >
              {label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="flex-1 px-6 py-6 max-w-7xl mx-auto w-full">{children}</main>
    </div>
  );
}
