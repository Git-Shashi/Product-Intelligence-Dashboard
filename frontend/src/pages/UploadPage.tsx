import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/api";
import { apiClient } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function UploadPage() {
  const navigate = useNavigate();

  // Video state
  const videoRef = useRef<HTMLInputElement>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [skuId, setSkuId] = useState("");
  const [enhanceTitle, setEnhanceTitle] = useState(false);
  const [videoError, setVideoError] = useState("");

  // CSV state
  const csvRef = useRef<HTMLInputElement>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvError, setCsvError] = useState("");

  const videoMutation = useMutation({
    mutationFn: (vars: { file: File; sku: string; enhance: boolean }) => {
      const fd = new FormData();
      fd.append("file", vars.file);
      fd.append("enhance_title", String(vars.enhance));
      if (vars.sku) fd.append("sku_id", vars.sku);
      return apiClient.post<{ job_id: number }>("/upload-video", fd).then((r) => r.data);
    },
    onSuccess: (data) => navigate(`/jobs/${data.job_id}`),
    onError: () => setVideoError("Upload failed. Check file format and try again."),
  });

  const csvMutation = useMutation({
    mutationFn: (file: File) => api.uploadCsv(file),
    onSuccess: (data) => navigate(`/jobs/${data.job_id}`),
    onError: () => setCsvError("Upload failed. Please check the file and try again."),
  });

  function handleVideoSubmit(e: React.FormEvent) {
    e.preventDefault();
    setVideoError("");
    if (!videoFile) { setVideoError("Please select a video file."); return; }
    videoMutation.mutate({ file: videoFile, sku: skuId, enhance: enhanceTitle });
  }

  function handleCsvSubmit(e: React.FormEvent) {
    e.preventDefault();
    setCsvError("");
    if (!csvFile) { setCsvError("Please select a CSV file."); return; }
    csvMutation.mutate(csvFile);
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Upload Products</h1>
        <p className="text-muted-foreground mt-1">
          Upload a product video (primary) or CSV feed (fallback) to validate listings and generate alerts.
        </p>
      </div>

      {/* Video Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Product Video Upload</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleVideoSubmit} className="space-y-4">
            <div
              className="border-2 border-dashed border-border rounded-lg p-6 text-center cursor-pointer hover:border-primary/50 transition-colors"
              onClick={() => videoRef.current?.click()}
            >
              {videoFile ? (
                <div>
                  <p className="text-sm font-medium text-foreground">{videoFile.name}</p>
                  <p className="text-xs text-muted-foreground mt-1">{(videoFile.size / 1024 / 1024).toFixed(1)} MB</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm text-muted-foreground">Click to select a video file</p>
                  <p className="text-xs text-muted-foreground mt-1">MP4, MOV, AVI, WebM</p>
                </div>
              )}
              <input
                ref={videoRef}
                type="file"
                accept="video/mp4,video/quicktime,video/x-msvideo,video/webm,.mp4,.mov,.avi,.webm"
                className="hidden"
                onChange={(e) => setVideoFile(e.target.files?.[0] ?? null)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                SKU ID <span className="text-muted-foreground font-normal">(optional — auto-generated if blank)</span>
              </label>
              <input
                value={skuId}
                onChange={(e) => setSkuId(e.target.value)}
                placeholder="e.g. SHOE001"
                className="w-full border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <label className="flex items-center gap-3 cursor-pointer select-none">
              <div
                onClick={() => setEnhanceTitle((v) => !v)}
                className={`relative w-10 h-6 rounded-full transition-colors ${enhanceTitle ? "bg-primary" : "bg-gray-200"}`}
              >
                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${enhanceTitle ? "translate-x-5" : "translate-x-1"}`} />
              </div>
              <div>
                <p className="text-sm font-medium">Enhance product title</p>
                <p className="text-xs text-muted-foreground">Generates an improved title using extracted attributes and trending keywords</p>
              </div>
            </label>

            {videoError && <p className="text-sm text-destructive">{videoError}</p>}

            <button
              type="submit"
              disabled={videoMutation.isPending || !videoFile}
              className="w-full py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-primary/90 transition-colors"
            >
              {videoMutation.isPending ? "Uploading…" : "Upload Video"}
            </button>

            <p className="text-xs text-muted-foreground text-center">
              OCR runs on video frames. Falls back to simulated data if text is unreadable.
            </p>
          </form>
        </CardContent>
      </Card>

      {/* CSV Upload */}
      <Card>
        <CardHeader>
          <CardTitle>CSV Fallback Upload</CardTitle>
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

            {csvError && <p className="text-sm text-destructive">{csvError}</p>}

            <button
              type="submit"
              disabled={csvMutation.isPending || !csvFile}
              className="w-full py-2.5 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium disabled:opacity-50 hover:bg-secondary/80 transition-colors"
            >
              {csvMutation.isPending ? "Uploading…" : "Upload CSV"}
            </button>
          </form>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-center">
        Sample files: <code className="bg-gray-100 px-1 rounded">samples/sample_products.csv</code> and <code className="bg-gray-100 px-1 rounded">samples/sample_competitor_prices.csv</code>
      </p>
    </div>
  );
}
