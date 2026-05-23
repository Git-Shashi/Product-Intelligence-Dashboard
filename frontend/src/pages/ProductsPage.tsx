import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const severityVariant = { HIGH: "high", MEDIUM: "medium", LOW: "low" } as const;

function QualityBar({ score }: { score: number }) {
  const color = score >= 80 ? "bg-green-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-gray-100 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-sm font-medium">{score}</span>
    </div>
  );
}

export function ProductsPage() {
  const [severityFilter, setSeverityFilter] = useState("");
  const [search, setSearch] = useState("");

  const { data: products = [], isLoading } = useQuery({
    queryKey: ["products", severityFilter],
    queryFn: () => api.listProducts(severityFilter ? { severity: severityFilter } : undefined),
  });

  const filtered = products.filter((p) =>
    !search || p.sku_id.toLowerCase().includes(search.toLowerCase()) ||
    (p.product_title ?? "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Products</h1>
        <Link to="/upload" className="text-sm text-primary hover:underline">+ Upload</Link>
      </div>

      <div className="flex gap-3">
        <input
          placeholder="Search SKU or title…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="border border-border rounded-lg px-3 py-2 text-sm focus:outline-none"
        >
          <option value="">All severities</option>
          <option value="HIGH">HIGH issues</option>
          <option value="MEDIUM">MEDIUM issues</option>
          <option value="LOW">LOW issues</option>
        </select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{filtered.length} product{filtered.length !== 1 ? "s" : ""}</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading && <p className="px-6 py-4 text-sm text-muted-foreground">Loading…</p>}
          <table className="w-full text-sm">
            <thead className="border-b border-border">
              <tr className="text-left">
                {["SKU", "Title", "Brand", "Price", "Quality", "Issues", ""].map((h) => (
                  <th key={h} className="px-4 py-3 font-medium text-muted-foreground text-xs uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => {
                const worst = p.issues.find((i) => i.severity === "HIGH")?.severity
                  ?? p.issues.find((i) => i.severity === "MEDIUM")?.severity
                  ?? p.issues[0]?.severity;
                return (
                  <tr key={p.sku_id} className="border-b border-border last:border-0 hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{p.sku_id}</td>
                    <td className="px-4 py-3 max-w-[220px]">
                      <span className="truncate block font-medium">
                        {p.product_title ?? <span className="text-muted-foreground italic">No title</span>}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{p.brand ?? "—"}</td>
                    <td className="px-4 py-3">
                      {p.price != null ? `₹${p.price.toLocaleString()}` : <span className="text-muted-foreground">—</span>}
                    </td>
                    <td className="px-4 py-3"><QualityBar score={p.quality_score} /></td>
                    <td className="px-4 py-3">
                      {worst ? (
                        <Badge variant={severityVariant[worst]}>{p.issues.length} issue{p.issues.length !== 1 ? "s" : ""}</Badge>
                      ) : (
                        <Badge variant="success">Clean</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/products/${p.sku_id}`} className="text-primary text-xs hover:underline">
                        View →
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {!isLoading && filtered.length === 0 && (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">No products found.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
