"use client";

import { usePathname } from "next/navigation";
import { Menu, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuthStore } from "@/store/auth-store";
import { useThemeStore } from "@/store/theme-store";
import { useTranslation } from "@/i18n";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { logout as authLogout } from "@/lib/auth";
import { useRouter } from "next/navigation";

const pageTitles: Record<string, string> = {
  "/dashboard": "nav.dashboard",
  "/dashboard/diagnosis": "diagnosis.title",
  "/dashboard/history": "history.title",
  "/dashboard/diseases": "nav.info",
  "/admin/models": "models.title",
  "/admin/statistics": "statistics.title",
  "/admin/reports": "reports.title",
  "/admin/users": "nav.users",
};

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuthStore();
  const { sidebarCollapsed, setSidebarCollapsed, language, setLanguage } = useThemeStore();
  const t = useTranslation();

  const title = Object.entries(pageTitles).find(([path]) =>
    pathname.startsWith(path)
  );
  const pageTitle = title ? t(title[1]) : t("nav.dashboard");

  const handleLogout = async () => {
    await authLogout();
    useAuthStore.getState().logout();
    router.push("/login");
  };

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "VG";

  const languages = [
    { code: "es", label: "common.language.es" },
    { code: "en", label: "common.language.en" },
    { code: "pt", label: "common.language.pt" },
  ];

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 lg:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
      >
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex-1">
        <h1 className="text-lg font-semibold">{pageTitle}</h1>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <Globe className="h-5 w-5" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>{t("common.language")}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {languages.map((lang) => (
            <DropdownMenuItem
              key={lang.code}
              onClick={() => setLanguage(lang.code as "es" | "en" | "pt")}
              className={language === lang.code ? "bg-accent" : ""}
            >
              {t(lang.label)}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="relative h-8 w-8 rounded-full">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                {initials}
              </AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="w-56" align="end" forceMount>
          <DropdownMenuLabel className="font-normal">
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium leading-none">{user?.name}</p>
              <p className="text-xs leading-none text-muted-foreground">
                {user?.username}
              </p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout}>
            {t("common.logout")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
