import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { apiPost } from "@/lib/api";
import { Send, CheckCircle, XCircle } from "lucide-react";

interface SMSResult {
  id: number;
  destination: string;
  content: string;
  status: string;
  gateway_response: string | null;
  credits_used: number;
  cost: number;
  created_at: string;
}

export default function SendSmsPage() {
  const [destination, setDestination] = useState("");
  const [content, setContent] = useState("");
  const [port, setPort] = useState(1);
  const [result, setResult] = useState<SMSResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const res = await apiPost<SMSResult>("/sms/send", {
        destination,
        content,
        port,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-text mb-6">Send SMS</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>New Message</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSend} className="space-y-4">
              <Input
                label="Destination Number"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="09993511225"
                required
              />
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-text">Message Content</label>
                <textarea
                  className="flex w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                  rows={4}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Your message here..."
                  maxLength={500}
                  required
                />
                <p className="text-xs text-text-muted text-right">{content.length}/500</p>
              </div>
              <Input
                label="Port"
                type="number"
                value={port}
                onChange={(e) => setPort(Number(e.target.value))}
                min={1}
                max={32}
              />
              {error && (
                <p className="text-sm text-danger bg-red-900/20 rounded-md p-2">{error}</p>
              )}
              <Button type="submit" className="w-full" disabled={loading}>
                <Send className="w-4 h-4 mr-2" />
                {loading ? "Sending..." : "Send Message"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Result</CardTitle>
          </CardHeader>
          <CardContent>
            {!result && !loading && (
              <p className="text-text-muted text-center py-8">
                Send a message to see the result here
              </p>
            )}
            {loading && (
              <p className="text-text-muted text-center py-8">Sending...</p>
            )}
            {result && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant={result.status === "sent" ? "success" : "danger"}>
                    {result.status === "sent" ? (
                      <CheckCircle className="w-3 h-3 mr-1 inline" />
                    ) : (
                      <XCircle className="w-3 h-3 mr-1 inline" />
                    )}
                    {result.status.toUpperCase()}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-text-muted">Destination</p>
                    <p className="text-text font-medium">{result.destination}</p>
                  </div>
                  <div>
                    <p className="text-text-muted">Credits Used</p>
                    <p className="text-text font-medium">{result.credits_used}</p>
                  </div>
                  <div>
                    <p className="text-text-muted">Cost</p>
                    <p className="text-text font-medium">${result.cost.toFixed(4)}</p>
                  </div>
                  <div>
                    <p className="text-text-muted">Time</p>
                    <p className="text-text font-medium">
                      {new Date(result.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                {result.gateway_response && (
                  <div>
                    <p className="text-sm text-text-muted mb-1">Gateway Response</p>
                    <pre className="text-xs bg-bg rounded-md p-2 text-text-muted whitespace-pre-wrap break-all max-h-32 overflow-auto">
                      {result.gateway_response}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
