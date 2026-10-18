"use client";

import { ConnectionInfo } from "@/lib/types";
import { useCallback, useEffect, useState } from "react";
import { Skeleton } from "../ui/skeleton";
import { AlertCircle, CalendarDays, Link2, RefreshCcw } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "../ui/button";
import {
  connectCalendar,
  fetchCalendarConnection,
  refreshCalendarConnection,
} from "@/lib/connections";

const styles = {
  root: "space-y-2",
  title:
    "px-1 text-[11px] font-bold tracking-[0.08em] text-muted-foreground uppercase",
  errorRow:
    "flex items-start gap-2 rounded-lg bg-destructive/[0.06] px-3 py-2.5 text-xs text-destructive",
  errorIcon: "mt-px size-3.5 shrink-0",
  error: "min-w-0 flex-1 leading-relaxed",
  retryBtn: "h-6 shrink-0 px-2 text-xs text-destructive hover:text-destructive",
  skeleton: "h-[72px] w-full rounded-lg",
  card: "surface-2 rounded-lg p-3",
  row: "flex items-center gap-3",
  iconBox:
    "flex size-9 shrink-0 items-center justify-center rounded-md ring-1 ring-border",
  iconBoxConnected: "bg-success-soft text-success ring-success/20",
  iconBoxDisconnected: "bg-secondary text-muted-foreground",
  icon: "size-4",
  meta: "min-w-0 flex-1",
  label: "truncate text-sm font-semibold leading-tight",
  pill: "mt-1 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold",
  pillConnected: "bg-success-soft text-success",
  pillPending: "bg-accent text-primary",
  pillDisconnected: "bg-secondary text-muted-foreground ring-1 ring-border",
  dot: "relative size-1.5 rounded-full",
  refreshBtn: "shrink-0 text-muted-foreground",
  refreshIcon: "size-3.5",
  actions: "mt-3 flex",
  actionBtn: "h-8 w-full gap-1.5 text-xs font-semibold",
} as const;

function errorMessage(err: unknown, fallback: string) {
  return err instanceof Error && err.message ? err.message : fallback;
}

function statusLabel(status: ConnectionInfo["status"]) {
  if (status === "connected") return "Live sync active";
  if (status === "pending") return "Awaiting approval";

  return "Not connected";
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
  const pending = connection?.status === "pending";

  return (
    <div className={styles.root}>
      <p className={styles.title}>Calendar</p>

      {error && (
        <div className={styles.errorRow} role="alert">
          <AlertCircle className={styles.errorIcon} />
          <p className={styles.error}>{error}</p>
          <Button
            size="sm"
            variant="ghost"
            className={styles.retryBtn}
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
        <div className={styles.card}>
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
              <span
                className={cn(
                  styles.pill,
                  connected
                    ? styles.pillConnected
                    : pending
                      ? styles.pillPending
                      : styles.pillDisconnected,
                )}
              >
                <span
                  className={cn(
                    styles.dot,
                    connected ? "live-beacon bg-success" : pending ? "bg-primary" : "bg-muted-foreground/50",
                  )}
                />
                {statusLabel(connection.status)}
              </span>
            </div>
            <Button
              size="icon-sm"
              variant="ghost"
              className={styles.refreshBtn}
              disabled={busy}
              onClick={() => handleCalendarRefresh()}
              aria-label="Refresh connection status"
            >
              <RefreshCcw className={cn(styles.refreshIcon, busy && "animate-spin")} />
            </Button>
          </div>

          {!connected && (
            <div className={styles.actions}>
              <Button
                size="sm"
                className={styles.actionBtn}
                disabled={busy}
                onClick={() => handleCalendarConnect()}
              >
                <Link2 className="size-3.5" />
                Connect Google Calendar
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ConnectionsPanel;
