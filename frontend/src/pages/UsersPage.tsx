import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Badge } from "@/components/ui/Badge";
import { apiGet, apiPost, apiPut, apiDelete } from "@/lib/api";
import { Trash2, UserPlus } from "lucide-react";

interface UserData {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export default function UsersPage() {
  const [users, setUsers] = useState<UserData[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ username: "", email: "", password: "", role: "user" });

  const loadUsers = () => {
    apiGet<UserData[]>("/users/").then(setUsers).catch(console.error);
  };

  useEffect(() => { loadUsers(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiPost("/users/", form);
    setShowCreate(false);
    setForm({ username: "", email: "", password: "", role: "user" });
    loadUsers();
  };

  const handleToggleActive = async (user: UserData) => {
    await apiPut(`/users/${user.id}`, { is_active: !user.is_active });
    loadUsers();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this user?")) return;
    await apiDelete(`/users/${id}`);
    loadUsers();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-text">Users</h1>
        <Button onClick={() => setShowCreate(true)}>
          <UserPlus className="w-4 h-4 mr-2" /> Add User
        </Button>
      </div>

      {showCreate && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Create User</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <Input
                label="Username"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
              />
              <Input
                label="Email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
              <Input
                label="Password"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                minLength={6}
              />
              <Select
                label="Role"
                options={[
                  { value: "admin", label: "Admin" },
                  { value: "manager", label: "Manager" },
                  { value: "user", label: "User" },
                  { value: "viewer", label: "Viewer" },
                ]}
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
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

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted text-left">
                  <th className="px-4 py-3 font-medium">ID</th>
                  <th className="px-4 py-3 font-medium">Username</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-border hover:bg-surface-light/50">
                    <td className="px-4 py-3 text-text-muted font-mono text-xs">{user.id}</td>
                    <td className="px-4 py-3 text-text font-medium">{user.username}</td>
                    <td className="px-4 py-3 text-text-muted">{user.email}</td>
                    <td className="px-4 py-3">
                      <Badge variant={user.role === "admin" ? "warning" : "default"}>
                        {user.role}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleToggleActive(user)}
                        className={`text-xs font-medium cursor-pointer ${
                          user.is_active ? "text-success" : "text-danger"
                        }`}
                      >
                        {user.is_active ? "Active" : "Disabled"}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-text-muted text-xs">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(user.id)}>
                        <Trash2 className="w-4 h-4 text-danger" />
                      </Button>
                    </td>
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
