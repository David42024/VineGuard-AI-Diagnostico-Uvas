"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Search,
  History,
  Brain,
  GitBranch,
  BarChart3,
  FileText,
  Users,
  Info,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Sun,
  Moon,
  Languages,
  Sprout,
  Gauge,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth-store";
import { useThemeStore } from "@/store/theme-store";
import { useTheme } from "next-themes";
import { t } from "@/i18n";
import { logout as authLogout } from "@/lib/auth";
import { useRouter } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  // Admin section
  { label: "nav.adminDashboard", href: "/admin", icon: Gauge, adminOnly: true },
  { label: "nav.models", href: "/admin/models", icon: Brain, adminOnly: true },
  { label: "nav.pipeline", href: "/admin/pipeline", icon: GitBranch, adminOnly: true },
  { label: "nav.statistics", href: "/admin/statistics", icon: BarChart3, adminOnly: true },
  { label: "nav.reports", href: "/admin/reports", icon: FileText, adminOnly: true },
  { label: "nav.users", href: "/admin/users", icon: Users, adminOnly: true },
  // Client section
  { label: "nav.dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "nav.diagnosis", href: "/dashboard/diagnosis", icon: Search },
  { label: "nav.history", href: "/dashboard/history", icon: History },
  { label: "nav.info", href: "/dashboard/diseases", icon: Info },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { role } = useAuthStore();
  const { sidebarCollapsed, toggleSidebar, language, setLanguage } =
    useThemeStore();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const isAdmin = role === "admin";
  const adminItems = navItems.filter((item) => item.adminOnly && isAdmin);
  const clientItems = navItems.filter((item) => !item.adminOnly);

  const handleLogout = async () => {
    await authLogout();
    useAuthStore.getState().logout();
    router.push("/login");
  };

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r bg-card transition-all duration-300",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex h-14 items-center border-b px-4">
        <Link href={isAdmin ? "/admin" : "/dashboard"} className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Sprout className="h-5 w-5 text-primary-foreground" />
          </div>
          {!sidebarCollapsed && (
            <span className="font-bold text-foreground">{t("app.name")}</span>
          )}
        </Link>
        <Button
          variant="ghost"
          size="icon"
          className="ml-auto hidden h-6 w-6 lg:flex"
          onClick={toggleSidebar}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2 space-y-1">
        {isAdmin && (
          <>
            {!sidebarCollapsed && (
              <div className="flex items-center gap-2 px-3 py-1.5">
                <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {t("nav.adminSection")}
                </span>
              </div>
            )}
            {adminItems.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {!sidebarCollapsed && <span>{t(item.label)}</span>}
                </Link>
              );
            })}
            <div className={cn("border-t my-2", sidebarCollapsed ? "mx-2" : "mx-3")} />
          </>
        )}
        {!sidebarCollapsed && (
          <div className="flex items-center gap-2 px-3 py-1.5">
            <LayoutDashboard className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              {t("nav.clientSection")}
            </span>
          </div>
        )}
        {clientItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && <span>{t(item.label)}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t p-2 space-y-1">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size={sidebarCollapsed ? "icon" : "default"}
              className={cn(
                "w-full justify-start gap-3",
                sidebarCollapsed && "justify-center"
              )}
            >
              <Languages className="h-4 w-4 shrink-0" />
              {!sidebarCollapsed && (
                <span className="text-sm">
                  {language === "es"
                    ? "Español"
                    : language === "en"
                    ? "English"
                    : "Português"}
                </span>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setLanguage("es")}>
              Español
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setLanguage("en")}>
              English
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setLanguage("pt")}>
              Português
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        {mounted && (
          <Button
            variant="ghost"
            size={sidebarCollapsed ? "icon" : "default"}
            className={cn(
              "w-full justify-start gap-3",
              sidebarCollapsed && "justify-center"
            )}
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4 shrink-0" />
            ) : (
              <Moon className="h-4 w-4 shrink-0" />
            )}
            {!sidebarCollapsed && (
              <span className="text-sm">
                {theme === "dark" ? t("common.theme.light") : t("common.theme.dark")}
              </span>
            )}
          </Button>
        )}

        <Button
          variant="ghost"
          size={sidebarCollapsed ? "icon" : "default"}
          className={cn(
            "w-full justify-start gap-3 text-destructive hover:text-destructive",
            sidebarCollapsed && "justify-center"
          )}
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!sidebarCollapsed && <span className="text-sm">{t("common.logout")}</span>}
        </Button>
      </div>
    </aside>
  );
}
