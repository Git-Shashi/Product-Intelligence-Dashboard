import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function UploadPage() {
  const navigate = useNavigate();
  const csvRef = useRef<HTMLInputElement>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  const csvMutation = useMutation({
    mutationFn: (file: File) => api.uploadCsv(file),
    onSuccess: (data) => navigate(`/jobs/${data.job_id}`),
    onError: () => setError("Upload failed. Please check the file and try again."),
  });

  function handleCsvSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!csvFile) { setError("Please select a CSV file."); return; }
    csvMutation.mutate(csvFile);
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Upload Products</h1>
        <p className="text-muted-foreground mt-1">
          Upload a product CSV to validate listings, score quality, and generate alerts.
        </p>
      </div>

      {/* CSV Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Product CSV Upload</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCsvSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                CSV file <span className="text-muted-foreground font-normal">(sku_id, product_title, brand, category, price, mrp, …)</span>
              </label>
              <div
                className="border-2 border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
                onClick={() => csvRef.current?.click()}
              >
                {csvFile ? (
                  <p className="text-sm font-medium text-foreground">{csvFile.name}</p>
                ) : (
                  <p className="text-sm text-muted-foreground">Click to select a .csv file</p>
                )}
                <input
                  ref={csvRef}
                  type="file"
                  accept=".csv"
                  className="hidden"
                  onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
                />
              </div>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <button
              type="submit"
              disabled={csvMutation.isPending || !csvFile}
              className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary/90 transition-colors"
            >
              {csvMutation.isPending ? "Uploading…" : "Upload CSV"}
            </button>
          </form>
        </CardContent>
      </Card>

      {/* Video Upload — Slice 2 */}
      <Card className="opacity-60">
        <CardHeader>
          <CardTitle>Product Video Upload <span className="text-xs text-muted-foreground font-normal ml-2">(coming next)</span></CardTitle>
        </CardHeader>
        <CardContent>
          <div className="border-2 border-dashed border-border rounded-lg p-6 text-center">
            <p className="text-sm text-muted-foreground">
              Video upload with OCR extraction will be available in the next build.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Sample files hint */}
      <p className="text-xs text-muted-foreground text-center">
        No file? Use <code className="bg-gray-100 px-1 rounded">samples/sample_products.csv</code> from the repo.
      </p>
    </div>
  );
}
