"use client";

import ChatPanel from "@/components/dashboard/chat-panel";
import ConnectionsPanel from "@/components/dashboard/connection-panel";
import { Button } from "@/components/ui/button";
import { useDescope, useSession, useUser } from "@descope/nextjs-sdk/client";
import { LoaderCircle, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

const styles = {
  loadingShell:
    "app-shell-bg flex h-svh flex-col items-center justify-center gap-3 text-sm text-muted-foreground",
  loadingIcon: "size-5 animate-spin text-primary",
  shell: "app-shell-bg",
  account: "flex items-center gap-3",
  avatar:
    "flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold tracking-wide text-primary-foreground",
  accountText: "min-w-0 flex-1",
  accountName: "truncate text-sm font-semibold",
  accountEmail: "truncate text-xs text-muted-foreground",
  logoutBtn: "shrink-0 text-muted-foreground hover:text-foreground",
  logoutIcon: "size-4",
} as const;

function initials(nameOrEmail: string) {
  const base = nameOrEmail.split("@")[0];
  const parts = base.split(/[\s._-]+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase() || "?";
}

function DashboardPage() {
  const sdk = useDescope();
  const router = useRouter();
  const { isAuthenticated, sessionToken, isSessionLoading } = useSession();
  const { user, isUserLoading } = useUser();
  const [loggingOut, setLoggingout] = useState(false);

  const name = user?.name || user?.email?.split("@")[0] || "Signed in";
  const email = user?.email || "";

  useEffect(() => {
    if (!isSessionLoading && !isAuthenticated) {
      router.replace("/sign-in");
    }
  }, [isAuthenticated, isSessionLoading, router]);

  async function handleLogout() {
    if (loggingOut) return;
    setLoggingout(true);

    try {
      await sdk.logout();
      router.replace("/sign-in");
      router.refresh();
    } catch {
      setLoggingout(false);
    }
  }

  if (isSessionLoading || !isAuthenticated || !sessionToken) {
    return (
      <div className={styles.loadingShell}>
        <LoaderCircle className={styles.loadingIcon} />
        Preparing your workspace…
      </div>
    );
  }

  return (
    <div className={styles.shell}>
      <ChatPanel
        sessionToken={sessionToken}
        connections={<ConnectionsPanel sessionToken={sessionToken} />}
        footer={
          <div className={styles.account}>
            <div className={styles.avatar} aria-hidden="true">
              {isUserLoading ? "" : initials(user?.name || email || name)}
            </div>
            <div className={styles.accountText}>
              <p className={styles.accountName}>{isUserLoading ? "Loading…" : name}</p>
              {email && <p className={styles.accountEmail}>{email}</p>}
            </div>
            <Button
              variant="ghost"
              size="icon"
              className={styles.logoutBtn}
              disabled={loggingOut}
              onClick={() => handleLogout()}
              aria-label="Log out"
              title="Log out"
            >
              {loggingOut ? (
                <LoaderCircle className={`${styles.logoutIcon} animate-spin`} />
              ) : (
                <LogOut className={styles.logoutIcon} />
              )}
            </Button>
          </div>
        }
      />
    </div>
  );
}

export default DashboardPage;
