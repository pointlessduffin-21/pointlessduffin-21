import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { apiGet, apiPut, apiPost } from "@/lib/api";
import { Settings, Send, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface AppSettings {
  id: number;
  gateway_url: string;
  gateway_account: string;
  gateway_password: string;
  default_port: number;
  sms_cost_per_message: number;
  test_destination: string;
  updated_at: string | null;
}

interface TestResult {
  success: boolean;
  destination: string;
  gateway_response: string;
  credits_used: number;
  cost: number;
}

export default function SettingsPage() {
  const [cfg, setCfg] = useState<AppSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testError, setTestError] = useState("");

  useEffect(() => {
    apiGet<AppSettings>("/settings/").then(setCfg).catch(console.error);
  }, []);

  const handleSave = async () => {
    if (!cfg) return;
    setSaving(true);
    try {
      const updated = await apiPut<AppSettings>("/settings/", cfg);
      setCfg(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e: any) {
      alert(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!cfg) return;
    setTesting(true);
    setTestResult(null);
    setTestError("");
    try {
      const body: any = {
        test_destination: cfg.test_destination,
        gateway_url: cfg.gateway_url,
        gateway_account: cfg.gateway_account,
        gateway_password: cfg.gateway_password,
        default_port: cfg.default_port,
        sms_cost_per_message: cfg.sms_cost_per_message,
      };
      const result = await apiPost<TestResult>("/settings/test", body);
      setTestResult(result);
    } catch (e: any) {
      setTestError(e.message || "Test failed");
    } finally {
      setTesting(false);
    }
  };

  if (!cfg) return <div className="text-text-muted p-8">Loading settings...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text flex items-center gap-2">
          <Settings className="w-6 h-6" /> Settings
        </h1>
        <div className="flex gap-2">
          <Button onClick={handleTest} variant="outline" disabled={testing}>
            {testing ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Send className="w-4 h-4 mr-2" />
            )}
            {testing ? "Testing..." : "Test Connection"}
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saved ? "Saved!" : saving ? "Saving..." : "Save Settings"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gateway Settings */}
        <Card>
          <CardHeader>
            <CardTitle>T200 Gateway Configuration</CardTitle>
            <p className="text-sm text-text-muted mt-1">
              Configure the SMS gateway connection. Changes take effect immediately.
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              label="Gateway URL"
              value={cfg.gateway_url}
              onChange={(e) => setCfg({ ...cfg, gateway_url: e.target.value })}
              placeholder="http://192.168.5.150/cgi/WebCGI"
            />
            <Input
              label="Account / Username"
              value={cfg.gateway_account}
              onChange={(e) => setCfg({ ...cfg, gateway_account: e.target.value })}
              placeholder="apiuser"
            />
            <Input
              label="Password"
              type="password"
              value={cfg.gateway_password}
              onChange={(e) => setCfg({ ...cfg, gateway_password: e.target.value })}
              placeholder="apipass"
            />
            <Input
              label="Default Port"
              type="number"
              value={cfg.default_port}
              onChange={(e) => setCfg({ ...cfg, default_port: Number(e.target.value) })}
              min={1}
              max={32}
            />
          </CardContent>
        </Card>

        {/* Billing & Test */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Billing & Test</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                label="Cost per SMS (USD)"
                type="number"
                step="0.001"
                value={cfg.sms_cost_per_message}
                onChange={(e) =>
                  setCfg({ ...cfg, sms_cost_per_message: Number(e.target.value) })
                }
              />
              <Input
                label="Test Destination Number"
                value={cfg.test_destination}
                onChange={(e) =>
                  setCfg({ ...cfg, test_destination: e.target.value })
                }
                placeholder="09993511225"
              />
              <p className="text-xs text-text-muted">
                This number is used when you click "Test Connection" — a test message
                will be sent to verify the gateway is working.
              </p>
            </CardContent>
          </Card>

          {/* Test Result */}
          {(testResult || testError) && (
            <Card className={testResult?.success ? "border-success" : "border-danger"}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {testResult?.success ? (
                    <>
                      <CheckCircle className="w-5 h-5 text-success" />
                      Test Successful
                    </>
                  ) : (
                    <>
                      <XCircle className="w-5 h-5 text-danger" />
                      Test Failed
                    </>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {testResult && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <p className="text-text-muted">Destination</p>
                        <p className="text-text font-mono">{testResult.destination}</p>
                      </div>
                      <div>
                        <p className="text-text-muted">Credits Used</p>
                        <p className="text-text">{testResult.credits_used}</p>
                      </div>
                      <div>
                        <p className="text-text-muted">Cost</p>
                        <p className="text-text">${testResult.cost.toFixed(4)}</p>
                      </div>
                      <div>
                        <p className="text-text-muted">Status</p>
                        <Badge variant={testResult.success ? "success" : "danger"}>
                          {testResult.success ? "SENT" : "FAILED"}
                        </Badge>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-text-muted mb-1">Gateway Response</p>
                      <pre className="text-xs bg-bg rounded-md p-2 text-text-muted whitespace-pre-wrap break-all max-h-32 overflow-auto">
                        {testResult.gateway_response || "(empty)"}
                      </pre>
                    </div>
                  </div>
                )}
                {testError && (
                  <p className="text-sm text-danger">{testError}</p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
