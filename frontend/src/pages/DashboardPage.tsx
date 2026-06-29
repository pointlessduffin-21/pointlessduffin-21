import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/Card";
import { apiGet } from "@/lib/api";
import { Send, Key, Activity, DollarSign, TrendingUp, Users } from "lucide-react";

interface DashboardStats {
  total_users: number;
  total_api_keys: number;
  active_api_keys: number;
  total_sms_sent: number;
  total_sms_today: number;
  total_cost_today: number;
  total_cost_month: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    apiGet<DashboardStats>("/analytics/dashboard").then(setStats).catch(console.error);
  }, []);

  if (!stats) return <div className="text-text-muted">Loading...</div>;

  const cards = [
    { icon: Users, label: "Total Users", value: stats.total_users, color: "text-blue-400" },
    { icon: Key, label: "Active API Keys", value: stats.active_api_keys, color: "text-green-400" },
    { icon: Send, label: "SMS Sent Today", value: stats.total_sms_today, color: "text-purple-400" },
    { icon: Activity, label: "Total SMS", value: stats.total_sms_sent, color: "text-orange-400" },
    { icon: DollarSign, label: "Cost Today", value: `$${stats.total_cost_today.toFixed(2)}`, color: "text-yellow-400" },
    { icon: TrendingUp, label: "Cost This Month", value: `$${stats.total_cost_month.toFixed(2)}`, color: "text-pink-400" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-text mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cards.map((card) => (
          <Card key={card.label}>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-text-muted">{card.label}</p>
                  <p className="text-2xl font-bold text-text mt-1">{card.value}</p>
                </div>
                <card.icon className={`w-8 h-8 ${card.color}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
