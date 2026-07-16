"use client";

import { AppShell } from "@/components/layout/app-shell";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";
import { getSession } from "@/lib/auth";
import { Skeleton } from "@/components/ui/skeleton";

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { user, setUser } = useAuthStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await getSession();
        setUser(userData);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };
    if (!user) {
      checkAuth();
    } else {
      setLoading(false);
    }
  }, [user, setUser, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="space-y-4 w-64">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-8 w-1/2" />
        </div>
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
