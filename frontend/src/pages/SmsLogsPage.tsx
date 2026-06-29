import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { apiGet } from "@/lib/api";
import { Download, ChevronLeft, ChevronRight } from "lucide-react";

interface SMSLogEntry {
  id: number;
  api_key_id: number;
  api_key_name: string | null;
  username: string | null;
  destination: string;
  content: string;
  port: number;
  status: string;
  gateway_response: string | null;
  credits_used: number;
  cost: number;
  ip_address: string | null;
  created_at: string;
}

export default function SmsLogsPage() {
  const [logs, setLogs] = useState<SMSLogEntry[]>([]);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const loadLogs = () => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", "50");
    if (statusFilter) params.set("status", statusFilter);
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);

    apiGet<SMSLogEntry[]>(`/sms/logs?${params.toString()}`)
      .then(setLogs)
      .catch(console.error);
  };

  useEffect(() => { loadLogs(); }, [page, statusFilter]);

  const handleExport = () => {
    const params = new URLSearchParams();
    params.set("export_type", "sms_logs");
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    window.open(`/api/analytics/export/csv?${params.toString()}`, "_blank");
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">SMS Logs</h1>
        <Button onClick={handleExport}>
          <Download className="w-4 h-4 mr-2" /> Export CSV
        </Button>
      </div>

      {/* Filters */}
      <Card className="mb-4">
        <CardContent className="py-3 flex items-center gap-4 flex-wrap">
          <Select
            options={[
              { value: "", label: "All Statuses" },
              { value: "sent", label: "Sent" },
              { value: "failed", label: "Failed" },
              { value: "pending", label: "Pending" },
            ]}
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="w-40"
          />
          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            placeholder="Start date"
            className="w-40"
          />
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            placeholder="End date"
            className="w-40"
          />
          <Button variant="outline" size="sm" onClick={() => { loadLogs(); }}>
            Apply
          </Button>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted text-left">
                  <th className="px-4 py-3 font-medium">ID</th>
                  <th className="px-4 py-3 font-medium">Key / User</th>
                  <th className="px-4 py-3 font-medium">Destination</th>
                  <th className="px-4 py-3 font-medium">Content</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Credits</th>
                  <th className="px-4 py-3 font-medium">Cost</th>
                  <th className="px-4 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 && (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-text-muted">
                      No logs found
                    </td>
                  </tr>
                )}
                {logs.map((log) => (
                  <tr key={log.id} className="border-b border-border hover:bg-surface-light/50">
                    <td className="px-4 py-3 text-text-muted font-mono text-xs">{log.id}</td>
                    <td className="px-4 py-3">
                      <span className="text-text">{log.api_key_name || "—"}</span>
                      <span className="text-text-muted text-xs block">{log.username || ""}</span>
                    </td>
                    <td className="px-4 py-3 text-text font-mono text-xs">{log.destination}</td>
                    <td className="px-4 py-3 text-text max-w-[200px] truncate" title={log.content}>
                      {log.content}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={log.status === "sent" ? "success" : "danger"}>
                        {log.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-text">{log.credits_used}</td>
                    <td className="px-4 py-3 text-text">${log.cost.toFixed(4)}</td>
                    <td className="px-4 py-3 text-text-muted text-xs">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <p className="text-sm text-text-muted">Page {page}</p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1}>
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage((p) => p + 1)} disabled={logs.length < 50}>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
