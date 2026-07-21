"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search,
  UserPlus,
  Shield,
  User as UserIcon,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Edit,
  Trash2,
} from "lucide-react";
import { ErrorState } from "@/components/feedback/error-state";
import { toast } from "sonner";
import api from "@/lib/api";
import { useTranslation } from "@/i18n";

interface UserRow {
  id: number;
  name: string;
  username: string;
  role: "admin" | "client";
  active: boolean;
}

export default function UsersPage() {
  const t = useTranslation();
  const [search, setSearch] = useState("");
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/users");
      setUsers((res.data || []).map((u: { id: number; name: string; username: string; role: string; active: boolean }) => ({
        id: u.id,
        name: u.name,
        username: u.username,
        role: u.role as "admin" | "client",
        active: u.active,
      })));
    } catch {
      setError(t("common.error"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Create user state
  const [showNewUser, setShowNewUser] = useState(false);
  const [newUserName, setNewUserName] = useState("");
  const [newUserUsername, setNewUserUsername] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");

  const handleCreateUser = async () => {
    try {
      await api.post("/users", {
        name: newUserName,
        username: newUserUsername,
        password: newUserPassword,
      });
      toast.success(t("users.toastCreateSuccess"));
      setShowNewUser(false);
      setNewUserName("");
      setNewUserUsername("");
      setNewUserPassword("");
      fetchData();
    } catch {
      toast.error(t("users.toastCreateError"));
    }
  };

  // Edit user state
  const [showEditUser, setShowEditUser] = useState(false);
  const [editUser, setEditUser] = useState<UserRow | null>(null);
  const [editUserName, setEditUserName] = useState("");
  const [editUserUsername, setEditUserUsername] = useState("");
  const [editUserRole, setEditUserRole] = useState<"admin" | "client">("client");
  const [editUserActive, setEditUserActive] = useState(true);

  const handleEditUser = async () => {
    if (!editUser) return;
    try {
      await api.patch(`/users/${editUser.id}`, {
        name: editUserName,
        username: editUserUsername,
        role: editUserRole,
        active: editUserActive,
      });
      toast.success(t("users.toastEditSuccess"));
      setShowEditUser(false);
      fetchData();
    } catch {
      toast.error(t("users.toastEditError"));
    }
  };

  // Delete user state
  const [showDeleteUser, setShowDeleteUser] = useState(false);
  const [deleteUser, setDeleteUser] = useState<UserRow | null>(null);

  const handleDeleteUser = async () => {
    if (!deleteUser) return;
    try {
      await api.delete(`/users/${deleteUser.id}`);
      toast.success(t("users.toastDeleteSuccess"));
      setShowDeleteUser(false);
      fetchData();
    } catch {
      toast.error(t("users.toastDeleteError"));
    }
  };

  // Toggle active
  const handleToggleActive = async (user: UserRow) => {
    try {
      await api.patch(`/users/${user.id}`, { active: !user.active });
      toast.success(user.active ? t("users.toastDeactivate") : t("users.toastActivate"));
      fetchData();
    } catch {
      toast.error(t("users.toastEditError"));
    }
  };

  if (error && users.length === 0) return <ErrorState message={error} onRetry={fetchData} />;

  const filtered = users.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.username.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {t("users.title")}
          </h2>
          <p className="text-muted-foreground">
            {t("users.subtitle")}
          </p>
        </div>
        <Dialog open={showNewUser} onOpenChange={setShowNewUser}>
          <DialogTrigger asChild>
            <Button>
              <UserPlus className="mr-2 h-4 w-4" />
              {t("users.newUser")}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("users.createUserTitle")}</DialogTitle>
              <DialogDescription>
                {t("users.createUserDesc")}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("users.name")}</label>
                <Input value={newUserName} onChange={(e) => setNewUserName(e.target.value)} placeholder={t("users.namePlaceholder")} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("users.username")}</label>
                <Input value={newUserUsername} onChange={(e) => setNewUserUsername(e.target.value)} placeholder={t("users.usernamePlaceholder")} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("users.password")}</label>
                <Input type="password" value={newUserPassword} onChange={(e) => setNewUserPassword(e.target.value)} placeholder="••••••••" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewUser(false)}>{t("common.cancel")}</Button>
              <Button onClick={handleCreateUser} disabled={!newUserName || !newUserUsername || !newUserPassword}>{t("users.createBtn")}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        <Button variant="outline" size="icon" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t("users.searchPlaceholder")}
            className="pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("users.registered")}</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("users.columnUser")}</TableHead>
                <TableHead>{t("users.columnName")}</TableHead>
                <TableHead>{t("users.columnRole")}</TableHead>
                <TableHead>{t("users.columnStatus")}</TableHead>
                <TableHead>{t("users.columnActions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-primary/10 text-primary text-xs">
                          {user.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </AvatarFallback>
                      </Avatar>
                      <span className="font-medium">{user.username}</span>
                    </div>
                  </TableCell>
                  <TableCell>{user.name}</TableCell>
                  <TableCell>
                    <Badge
                      variant={user.role === "admin" ? "default" : "secondary"}
                      className="gap-1"
                    >
                      {user.role === "admin" ? (
                        <Shield className="h-3 w-3" />
                      ) : (
                        <UserIcon className="h-3 w-3" />
                      )}
                      {user.role === "admin" ? t("users.roleAdmin") : t("users.roleClient")}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {user.active ? (
                      <Badge variant="success" className="gap-1">
                        <CheckCircle2 className="h-3 w-3" />
                        {t("users.active")}
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="gap-1">
                        <XCircle className="h-3 w-3" />
                        {t("users.inactive")}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditUser(user);
                          setEditUserName(user.name);
                          setEditUserUsername(user.username);
                          setEditUserRole(user.role);
                          setEditUserActive(user.active);
                          setShowEditUser(true);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive"
                        onClick={() => {
                          setDeleteUser(user);
                          setShowDeleteUser(true);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleActive(user)}
                      >
                        {user.active ? t("users.btnDeactivate") : t("users.btnActivate")}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Edit User Dialog */}
      <Dialog
        open={showEditUser}
        onOpenChange={(open) => {
          if (!open) {
            setShowEditUser(false);
            setEditUser(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("users.editUserTitle")}</DialogTitle>
            <DialogDescription>
              {t("users.editUserDesc")}
            </DialogDescription>
          </DialogHeader>
          {editUser && (
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("users.name")}</label>
                <Input
                  value={editUserName}
                  onChange={(e) => setEditUserName(e.target.value)}
                  placeholder={t("users.namePlaceholder")}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("users.username")}</label>
                <Input
                  value={editUserUsername}
                  onChange={(e) => setEditUserUsername(e.target.value)}
                  placeholder={t("users.usernamePlaceholder")}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("users.role")}</label>
                <Select
                  value={editUserRole}
                  onValueChange={(v) => setEditUserRole(v as "admin" | "client")}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">{t("users.roleAdmin")}</SelectItem>
                    <SelectItem value="client">{t("users.roleClient")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">{t("users.status")}</label>
                <Select
                  value={editUserActive ? "active" : "inactive"}
                  onValueChange={(v) => setEditUserActive(v === "active")}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">{t("users.statusActive")}</SelectItem>
                    <SelectItem value="inactive">{t("users.statusInactive")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditUser(false)}>{t("common.cancel")}</Button>
            <Button onClick={handleEditUser} disabled={!editUserName || !editUserUsername}>{t("users.saveBtn")}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog
        open={showDeleteUser}
        onOpenChange={(open) => {
          if (!open) {
            setShowDeleteUser(false);
            setDeleteUser(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("users.deleteUserTitle")}</DialogTitle>
            <DialogDescription>
              {t("users.deleteUserDesc")}
            </DialogDescription>
          </DialogHeader>
          {deleteUser && (
            <div className="py-4">
              <p className="text-sm text-muted-foreground">
                Usuario: <span className="font-medium">{deleteUser.username}</span>
              </p>
              <p className="text-sm text-muted-foreground">
                Nombre: <span className="font-medium">{deleteUser.name}</span> 
              </p>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteUser(false)}>{t("common.cancel")}</Button>
            <Button variant="destructive" onClick={handleDeleteUser}>{t("common.delete")}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
