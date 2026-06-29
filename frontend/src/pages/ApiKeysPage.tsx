import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { apiGet, apiPost, apiDelete } from "@/lib/api";
import { Plus, Trash2, Copy, Check, Clock } from "lucide-react";

interface APIKeyData {
  id: number;
  name: string;
  key_prefix: string;
  is_active: boolean;
  expires_at: string | null;
  rate_limit_per_minute: number;
  allowed_ips: string | null;
  created_at: string;
  last_used_at: string | null;
  user_id: number;
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<APIKeyData[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newKey, setNewKey] = useState({ name: "", expires_at: "", rate_limit_per_minute: 30, allowed_ips: "" });
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const loadKeys = () => {
    apiGet<APIKeyData[]>("/keys/").then(setKeys).catch(console.error);
  };

  useEffect(() => { loadKeys(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const body: any = {
      name: newKey.name,
      rate_limit_per_minute: newKey.rate_limit_per_minute,
    };
    if (newKey.expires_at) body.expires_at = newKey.expires_at;
    if (newKey.allowed_ips) body.allowed_ips = newKey.allowed_ips;

    const result = await apiPost<any>("/keys/", body);
    setCreatedKey(result.full_key);
    setShowCreate(false);
    setNewKey({ name: "", expires_at: "", rate_limit_per_minute: 30, allowed_ips: "" });
    loadKeys();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this API key?")) return;
    await apiDelete(`/keys/${id}`);
    loadKeys();
  };

  const copyKey = () => {
    if (createdKey) {
      navigator.clipboard.writeText(createdKey);
      setCopied(true);
      setTimeout(() => { setCopied(false); setCreatedKey(null); }, 5000);
    }
  };

  const isExpired = (date: string | null) => {
    if (!date) return false;
    return new Date(date) < new Date();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">API Keys</h1>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4 mr-2" /> Create Key
        </Button>
      </div>

      {/* Created key banner */}
      {createdKey && (
        <Card className="mb-4 border-primary bg-primary/10">
          <CardContent className="py-4">
            <p className="text-sm font-medium text-text mb-2">🔑 New API Key Created — copy it now, it won't be shown again!</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 bg-surface rounded-md px-3 py-2 text-sm text-text font-mono break-all">
                {createdKey}
              </code>
              <Button size="sm" onClick={copyKey}>
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create form */}
      {showCreate && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Create New API Key</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <Input
                label="Key Name"
                value={newKey.name}
                onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
                placeholder="e.g. Production App"
                required
              />
              <Input
                label="Expires At (optional)"
                type="datetime-local"
                value={newKey.expires_at}
                onChange={(e) => setNewKey({ ...newKey, expires_at: e.target.value })}
              />
              <Input
                label="Rate Limit (per minute)"
                type="number"
                value={newKey.rate_limit_per_minute}
                onChange={(e) => setNewKey({ ...newKey, rate_limit_per_minute: Number(e.target.value) })}
              />
              <Input
                label="Allowed IPs (comma-separated, optional)"
                value={newKey.allowed_ips}
                onChange={(e) => setNewKey({ ...newKey, allowed_ips: e.target.value })}
                placeholder="192.168.1.1, 10.0.0.5"
              />
              <div className="flex gap-2">
                <Button type="submit">Create</Button>
                <Button variant="outline" type="button" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Keys list */}
      <div className="space-y-3">
        {keys.length === 0 && (
          <p className="text-text-muted text-center py-8">No API keys yet. Create one to get started.</p>
        )}
        {keys.map((key) => (
          <Card key={key.id}>
            <CardContent className="py-4 flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium text-text">{key.name}</p>
                  <Badge variant={key.is_active && !isExpired(key.expires_at) ? "success" : "danger"}>
                    {!key.is_active ? "Disabled" : isExpired(key.expires_at) ? "Expired" : "Active"}
                  </Badge>
                </div>
                <p className="text-sm text-text-muted font-mono">
                  {key.key_prefix}...
                </p>
                <div className="flex gap-4 mt-1 text-xs text-text-muted">
                  <span>Rate: {key.rate_limit_per_minute}/min</span>
                  {key.expires_at && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Expires: {new Date(key.expires_at).toLocaleDateString()}
                    </span>
                  )}
                  {key.last_used_at && (
                    <span>Last used: {new Date(key.last_used_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={() => handleDelete(key.id)}>
                <Trash2 className="w-4 h-4 text-danger" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
