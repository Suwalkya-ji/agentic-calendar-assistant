"use client";

import { ConnectionInfo } from "@/lib/types";
import { useCallback, useEffect, useState } from "react";
import { Skeleton } from "../ui/skeleton";
import { CalendarDays, RefreshCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "../ui/button";
import {
  connectCalendar,
  fetchCalendarConnection,
  refreshCalendarConnection,
} from "@/lib/connections";

const styles = {
  root: "space-y-1.5",
  title: "px-0.5 text-sm font-semibold text-sidebar-foreground",
  error: "min-w-0 flex-1 text-xs text-destructive",
  errorRow: "flex items-center gap-2 px-0.5",
  skeleton: "h-11 w-full rounded-xl",
  row: "flex items-center gap-2 rounded-xl bg-sidebar-accent/50 px-2 py-2",
  iconBox: "flex size-8 shrink-0 items-center justify-center rounded-lg",
  iconBoxConnected: "bg-primary text-primary-foreground",
  iconBoxDisconnected: "bg-card text-muted-foreground ring-1 ring-border",
  icon: "size-4",
  meta: "min-w-0 flex-1",
  label: "truncate text-sm font-semibold leading-tight",
  status: "mt-0.5 text-xs font-medium",
  statusConnected: "text-primary",
  statusDisconnected: "text-muted-foreground",
  actionBtn: "h-8 shrink-0 px-2.5",
  refreshBtn: "shrink-0",
  refreshIcon: "size-3.5",
} as const;

function errorMessage(err: unknown, fallback: string) {
  return err instanceof Error && err.message ? err.message : fallback;
}

function statusLabel(status: ConnectionInfo["status"]) {
  if (status === "connected") return "Connected";
  if (status === "pending") return "Pending";

  return "Not Connected";
}

function ConnectionsPanel({ sessionToken }: { sessionToken: string }) {
  const [connection, setConnection] = useState<ConnectionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoadCalendarConnection = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      let next = await fetchCalendarConnection(sessionToken);

      // Coming back from Google, the status is still "pending" until we ask
      // the backend to check with Descope, so do that automatically.
      if (next.status === "pending") {
        await refreshCalendarConnection(sessionToken);
        next = await fetchCalendarConnection(sessionToken);
      }

      setConnection(next);
    } catch (err) {
      setError(errorMessage(err, "Could not load the calendar connection"));
    } finally {
      setLoading(false);
    }
  }, [sessionToken]);

  useEffect(() => {
    handleLoadCalendarConnection();
  }, [handleLoadCalendarConnection]);

  async function handleCalendarConnect() {
    setBusy(true);
    setError(null);

    try {
      // On success this navigates away to Google, so busy stays on.
      await connectCalendar(sessionToken);
    } catch (err) {
      setError(errorMessage(err, "Could not start the Google connection"));
      setBusy(false);
    }
  }

  async function handleCalendarRefresh() {
    setBusy(true);
    setError(null);

    try {
      await refreshCalendarConnection(sessionToken);
      await handleLoadCalendarConnection();
    } catch (err) {
      setError(errorMessage(err, "Could not refresh the connection"));
    } finally {
      setBusy(false);
    }
  }

  const connected = connection?.status === "connected";

  return (
    <div className={styles.root}>
      <p className={styles.title}>Connections</p>

      {error && (
        <div className={styles.errorRow}>
          <p className={styles.error}>{error}</p>
          <Button
            size="sm"
            variant="ghost"
            className={styles.actionBtn}
            disabled={loading || busy}
            onClick={() => handleLoadCalendarConnection()}
          >
            Retry
          </Button>
        </div>
      )}

      {loading ? (
        <Skeleton className={styles.skeleton} />
      ) : !connection ? null : (
        <div className={styles.row}>
          <div
            className={cn(
              styles.iconBox,
              connected ? styles.iconBoxConnected : styles.iconBoxDisconnected,
            )}
          >
            <CalendarDays className={styles.icon} />
          </div>
          <div className={styles.meta}>
            <p className={styles.label}>{connection.label}</p>

            <p
              className={cn(
                styles.status,
                connected ? styles.statusConnected : styles.statusDisconnected,
              )}
            >
              {statusLabel(connection.status)}
            </p>
          </div>
          <Button
            size="sm"
            variant={connected ? "ghost" : "default"}
            className={styles.actionBtn}
            disabled={busy}
            onClick={() => handleCalendarConnect()}
          >
            {connected ? "Reconnect" : "Connect"}
          </Button>

          <Button
            size="icon-sm"
            variant={"ghost"}
            className={styles.refreshBtn}
            disabled={busy}
            onClick={() => handleCalendarRefresh()}
          >
            <RefreshCcw className={styles.refreshIcon} />
          </Button>
        </div>
      )}
    </div>
  );
}

export default ConnectionsPanel;
