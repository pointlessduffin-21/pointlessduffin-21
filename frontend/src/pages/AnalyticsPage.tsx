import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { apiGet } from "@/lib/api";
import { Download, BarChart3 } from "lucide-react";

interface CostBreakdownItem {
  api_key_id: number;
  api_key_name: string;
  username: string;
  total_messages: number;
  total_cost: number;
  sent_count: number;
  failed_count: number;
}

export default function AnalyticsPage() {
  const [breakdown, setBreakdown] = useState<CostBreakdownItem[]>([]);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(false);

  const loadBreakdown = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    try {
      const data = await apiGet<CostBreakdownItem[]>(
        `/analytics/cost-breakdown?${params.toString()}`
      );
      setBreakdown(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadBreakdown(); }, []);

  const handleExport = () => {
    const params = new URLSearchParams();
    params.set("export_type", "cost_breakdown");
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    window.open(`/api/analytics/export/csv?${params.toString()}`, "_blank");
  };

  const totalCost = breakdown.reduce((s, i) => s + i.total_cost, 0);
  const totalMessages = breakdown.reduce((s, i) => s + i.total_messages, 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">Analytics & Reports</h1>
        <Button onClick={handleExport}>
          <Download className="w-4 h-4 mr-2" /> Export CSV
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-text-muted">Total Cost</p>
            <p className="text-2xl font-bold text-text">${totalCost.toFixed(2)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-text-muted">Total Messages</p>
            <p className="text-2xl font-bold text-text">{totalMessages}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-text-muted">API Keys</p>
            <p className="text-2xl font-bold text-text">{breakdown.length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-4">
        <CardContent className="py-3 flex items-center gap-4 flex-wrap">
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
          <Button variant="outline" size="sm" onClick={loadBreakdown} disabled={loading}>
            {loading ? "Loading..." : "Apply"}
          </Button>
        </CardContent>
      </Card>

      {/* Cost Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Cost Breakdown by API Key
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted text-left">
                  <th className="px-4 py-3 font-medium">API Key</th>
                  <th className="px-4 py-3 font-medium">Owner</th>
                  <th className="px-4 py-3 font-medium text-right">Messages</th>
                  <th className="px-4 py-3 font-medium text-right">Sent</th>
                  <th className="px-4 py-3 font-medium text-right">Failed</th>
                  <th className="px-4 py-3 font-medium text-right">Cost</th>
                </tr>
              </thead>
              <tbody>
                {breakdown.length === 0 && (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-text-muted">
                      No data available
                    </td>
                  </tr>
                )}
                {breakdown.map((item) => (
                  <tr key={item.api_key_id} className="border-b border-border hover:bg-surface-light/50">
                    <td className="px-4 py-3 text-text font-medium">{item.api_key_name}</td>
                    <td className="px-4 py-3 text-text-muted">{item.username}</td>
                    <td className="px-4 py-3 text-text text-right">{item.total_messages}</td>
                    <td className="px-4 py-3 text-success text-right">{item.sent_count}</td>
                    <td className="px-4 py-3 text-danger text-right">{item.failed_count}</td>
                    <td className="px-4 py-3 text-text font-mono text-right">${item.total_cost.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
