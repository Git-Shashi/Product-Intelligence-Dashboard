import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const sevVariant = { HIGH: "high", MEDIUM: "medium", LOW: "low" } as const;

export function ProductDetailPage() {
  const { sku } = useParams<{ sku: string }>();
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});

  const { data: product, isLoading } = useQuery({
    queryKey: ["product", sku],
    queryFn: () => api.getProduct(sku!),
    enabled: !!sku,
  });

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, string>) => api.updateProduct(sku!, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["product", sku] }); setEditing(false); },
  });

  const enhanceMutation = useMutation({
    mutationFn: () => api.enhanceTitle(sku!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["product", sku] }),
  });

  if (isLoading) return <p className="text-muted-foreground">Loading…</p>;
  if (!product) return <p className="text-destructive">Product not found.</p>;

  const latestEnhanced = product.enhanced_titles.at(-1);

  function startEdit() {
    setForm({
      product_title: product!.product_title ?? "",
      brand: product!.brand ?? "",
      category: product!.category ?? "",
      price: product!.price != null ? String(product!.price) : "",
      mrp: product!.mrp != null ? String(product!.mrp) : "",
      description: product!.description ?? "",
      image_url: product!.image_url ?? "",
      color: product!.color ?? "",
      size: product!.size ?? "",
      material: product!.material ?? "",
    });
    setEditing(true);
  }

  function submitEdit(e: React.FormEvent) {
    e.preventDefault();
    const patch: Record<string, string | number | boolean> = {};
    Object.entries(form).forEach(([k, v]) => {
      if (k === "price" || k === "mrp") patch[k] = v === "" ? (null as unknown as number) : Number(v);
      else patch[k] = v;
    });
    updateMutation.mutate(patch as Record<string, string>);
  }

  return (
    <div className="space-y-5 max-w-4xl">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link to="/products" className="hover:text-foreground">Products</Link>
        <span>/</span>
        <span className="text-foreground font-mono">{sku}</span>
      </div>

      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{product.product_title ?? <span className="text-muted-foreground">No title</span>}</h1>
          <p className="text-muted-foreground text-sm mt-1">SKU: {product.sku_id} · Source: {product.source}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <div className={`text-2xl font-bold ${product.quality_score >= 80 ? "text-green-600" : product.quality_score >= 60 ? "text-yellow-600" : "text-red-600"}`}>
            {product.quality_score}
          </div>
          <span className="text-sm text-muted-foreground">/100</span>
        </div>
      </div>

      {/* Product fields */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Product Details</CardTitle>
          {!editing && (
            <button onClick={startEdit} className="text-xs text-primary hover:underline">Edit</button>
          )}
        </CardHeader>
        <CardContent>
          {editing ? (
            <form onSubmit={submitEdit} className="grid grid-cols-2 gap-3">
              {Object.entries(form).map(([key, val]) => (
                <div key={key} className={key === "description" ? "col-span-2" : ""}>
                  <label className="block text-xs font-medium text-muted-foreground mb-1 capitalize">{key.replace(/_/g, " ")}</label>
                  {key === "description" ? (
                    <textarea
                      rows={3}
                      value={val}
                      onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                      className="w-full border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                  ) : (
                    <input
                      value={val}
                      onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                      className="w-full border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                  )}
                </div>
              ))}
              <div className="col-span-2 flex gap-2">
                <button type="submit" disabled={updateMutation.isPending}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50">
                  {updateMutation.isPending ? "Saving…" : "Save"}
                </button>
                <button type="button" onClick={() => setEditing(false)}
                  className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium">
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
              {[
                ["Brand", product.brand],
                ["Category", product.category],
                ["Price", product.price != null ? `₹${product.price.toLocaleString()}` : null],
                ["MRP", product.mrp != null ? `₹${product.mrp.toLocaleString()}` : null],
                ["Color", product.color],
                ["Size", product.size],
                ["Material", product.material],
                ["Availability", product.availability ? "In Stock" : "Out of Stock"],
              ].map(([label, val]) => (
                <div key={label as string} className="flex gap-2">
                  <span className="text-muted-foreground w-24 shrink-0">{label}</span>
                  <span className="font-medium">{val ?? <span className="text-muted-foreground italic">—</span>}</span>
                </div>
              ))}
              {product.description && (
                <div className="col-span-2 flex gap-2 mt-2">
                  <span className="text-muted-foreground w-24 shrink-0">Description</span>
                  <span className="text-sm">{product.description}</span>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Listing Issues */}
      {product.issues.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Listing Issues ({product.issues.length})</CardTitle></CardHeader>
          <CardContent className="space-y-2 p-0 px-6 pb-4">
            {product.issues.map((issue) => (
              <div key={issue.id} className="flex items-start gap-3 py-2 border-b border-border last:border-0">
                <Badge variant={sevVariant[issue.severity]} className="mt-0.5 shrink-0">{issue.severity}</Badge>
                <div>
                  <p className="text-sm font-medium">{issue.message}</p>
                  {issue.suggested_fix && (
                    <p className="text-xs text-muted-foreground mt-0.5">Fix: {issue.suggested_fix}</p>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Enhanced Title */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Enhanced Title</CardTitle>
          <button
            onClick={() => enhanceMutation.mutate()}
            disabled={enhanceMutation.isPending}
            className="text-xs px-3 py-1.5 bg-primary text-primary-foreground rounded-md disabled:opacity-50"
          >
            {enhanceMutation.isPending ? "Generating…" : latestEnhanced ? "Regenerate" : "Generate"}
          </button>
        </CardHeader>
        <CardContent>
          {latestEnhanced ? (
            <div className="space-y-2">
              <div className="text-xs text-muted-foreground">Original: {latestEnhanced.original_title}</div>
              <div className="font-medium">{latestEnhanced.enhanced_title}</div>
              <div className="text-xs text-muted-foreground">{latestEnhanced.reason}</div>
              <div className="flex flex-wrap gap-1 mt-1">
                {latestEnhanced.keywords.map((kw) => (
                  <span key={kw} className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">{kw}</span>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No enhanced title yet. Click Generate to create one.</p>
          )}
        </CardContent>
      </Card>

      {/* Competitor Prices — Slice 4 */}
      <Card className="opacity-60">
        <CardHeader><CardTitle>Competitor Prices <span className="text-xs font-normal text-muted-foreground ml-1">(coming in next build)</span></CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Competitor price comparison will be available after Slice 4.</p>
        </CardContent>
      </Card>
    </div>
  );
}
