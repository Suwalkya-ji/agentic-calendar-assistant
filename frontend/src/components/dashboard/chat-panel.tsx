"use client";

import {
  ArrowUp,
  CalendarCheck,
  CalendarClock,
  CalendarDays,
  CalendarPlus,
  CalendarSearch,
  CalendarX,
  Clock,
  LoaderCircle,
  Menu,
  MessageSquare,
  NotebookPen,
  Plus,
  Sparkles,
  X,
  type LucideIcon,
} from "lucide-react";
import {
  FormEvent,
  KeyboardEvent,
  ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { Button } from "../ui/button";
import {
  listThreads,
  loadThread,
  streamAgentChat,
  ThreadSummary,
} from "@/lib/agent";
import { ScrollArea } from "../ui/scroll-area";
import { Textarea } from "../ui/textarea";
import { cn } from "@/lib/utils";
import { MarkdownMessage, formatErrorMessage } from "./markdown-message";

const styles = {
  root: "flex h-svh overflow-hidden bg-background",

  // Left rail: fixed 300px on desktop, off-canvas drawer below lg.
  overlay: "fixed inset-0 z-30 bg-foreground/25 backdrop-blur-[2px] lg:hidden",
  aside:
    "fixed inset-y-0 left-0 z-40 flex w-[300px] max-w-[85vw] flex-col border-r border-sidebar-border bg-sidebar transition-transform duration-300 ease-out lg:static lg:max-w-none lg:translate-x-0 lg:shadow-none",
  asideOpen: "translate-x-0 surface-3",
  asideClosed: "-translate-x-full",
  brandRow: "flex items-center justify-between gap-2 px-5 pt-5 pb-4",
  brandLeft: "flex min-w-0 items-center gap-3",
  brandMark:
    "flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground",
  brandMarkIcon: "size-4",
  brandTitle: "font-heading text-[22px] leading-none font-medium tracking-tight",
  brandSub:
    "mt-1 text-[11px] font-bold tracking-[0.08em] text-muted-foreground uppercase",
  closeBtn: "lg:hidden",
  topActions: "space-y-4 px-4 pb-4",
  newChatBtn: "h-10 w-full justify-start gap-2 rounded-lg px-3 text-sm font-semibold",
  sectionLabel:
    "px-1 text-[11px] font-bold tracking-[0.08em] text-muted-foreground uppercase",
  chatsSection: "flex min-h-0 flex-1 flex-col border-t border-sidebar-border pt-4",
  chatsHeader: "mb-2 px-5",
  chatsScroll: "min-h-0 flex-1 px-3 pb-3",
  chatsEmpty:
    "mx-2 rounded-lg border border-dashed border-border px-3 py-4 text-[13px] leading-relaxed text-muted-foreground",
  chatsError:
    "mx-2 rounded-lg bg-destructive/[0.06] px-3 py-2.5 text-xs text-destructive",
  threadList: "space-y-0.5",
  threadBtn:
    "group relative flex w-full items-start gap-2.5 rounded-lg px-3 py-2.5 text-left transition-colors disabled:opacity-50",
  threadBtnActive: "bg-card ring-1 ring-border",
  threadBtnIdle: "hover:bg-card/70",
  threadActiveBar: "absolute top-2.5 bottom-2.5 left-0 w-0.5 rounded-full bg-primary",
  threadIcon: "mt-0.5 size-4 shrink-0 text-muted-foreground",
  threadIconActive: "text-primary",
  threadText: "min-w-0 flex-1",
  threadTitle: "line-clamp-1 text-sm font-medium leading-snug",
  threadTime: "mt-0.5 block text-xs text-muted-foreground tabular-nums",
  footer: "border-t border-sidebar-border p-4",

  // Main canvas
  main: "relative flex min-w-0 flex-1 flex-col",
  topBar:
    "flex h-14 shrink-0 items-center gap-3 border-b border-border bg-background/90 px-3 backdrop-blur-md sm:px-6 lg:px-8",
  menuBtn: "lg:hidden",
  topTitle: "min-w-0 flex-1",
  topTitleText: "truncate font-heading text-lg leading-tight font-medium",
  topSub: "hidden truncate text-xs text-muted-foreground sm:block",
  newChatIconBtn: "lg:hidden",

  messagesScroll: "min-h-0 flex-1",
  messagesInner: "mx-auto w-full max-w-[820px] px-4 py-8 sm:px-6 lg:py-12",

  emptyState: "flex min-h-[55vh] flex-col justify-center py-6",
  eyebrow:
    "inline-flex items-center gap-2 text-[11px] font-bold tracking-[0.08em] text-primary uppercase",
  emptyTitle:
    "mt-4 font-heading text-[32px] leading-10 font-normal tracking-[-0.01em] sm:text-[40px] sm:leading-[48px] sm:tracking-[-0.02em]",
  emptyCopy: "mt-3 max-w-lg text-base leading-[26px] text-muted-foreground",
  suggestions: "mt-8 grid gap-2.5 sm:grid-cols-2",
  suggestionBtn:
    "group flex items-start gap-3 rounded-lg border border-border bg-secondary px-4 py-3.5 text-left transition-all hover:-translate-y-px hover:border-rose hover:bg-card disabled:pointer-events-none disabled:opacity-50",
  suggestionIcon:
    "mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-card text-primary ring-1 ring-border transition-colors group-hover:bg-accent",
  suggestionLabel: "text-sm font-semibold",
  suggestionHint: "mt-0.5 block text-xs text-muted-foreground",

  messageList: "space-y-6",
  statusRow: "flex items-center gap-2 text-sm text-muted-foreground",
  spin: "size-4 animate-spin",
  spinSm: "size-3.5 animate-spin",
  messageRow: "message-enter flex w-full min-w-0 gap-3",
  messageRowUser: "justify-end",
  messageRowAssistant: "justify-start",
  avatar:
    "mt-0.5 hidden size-7 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground sm:flex",
  avatarIcon: "size-3.5",
  bubble:
    "min-w-0 max-w-[min(100%,40rem)] overflow-hidden break-words [overflow-wrap:anywhere]",
  bubbleUser:
    "rounded-lg rounded-br-sm bg-primary px-4 py-2.5 text-primary-foreground",
  bubbleAssistant:
    "rounded-lg rounded-tl-sm border border-border bg-secondary px-4 py-3 text-foreground",
  bubbleSystem:
    "rounded-lg border border-destructive/20 bg-destructive/[0.05] px-4 py-2.5 text-sm text-destructive",
  thinking: "inline-flex items-center gap-2 text-sm text-muted-foreground",
  userText: "whitespace-pre-wrap text-[15px] leading-7",

  // Tool execution live status feed
  feed: "border-l border-dashed border-border pl-4 sm:ml-[13px]",
  feedItem: "flex items-center gap-2.5 text-[13px] text-muted-foreground",
  feedIcon:
    "flex size-6 items-center justify-center rounded-md bg-card text-primary ring-1 ring-border",
  feedIconSvg: "size-3.5",

  composerWrap:
    "pb-safe shrink-0 border-t border-border bg-background/95 px-3 pt-3 backdrop-blur-md sm:px-6",
  composerForm:
    "surface-2 mx-auto flex w-full max-w-[820px] items-end gap-2 rounded-xl p-2 transition-colors focus-within:border-primary",
  composerInput:
    "max-h-40 min-h-[44px] flex-1 resize-none border-0 bg-transparent px-3 py-2.5 text-[15px] shadow-none focus-visible:ring-0",
  sendBtn: "mb-0.5 size-10 shrink-0 rounded-lg",
  sendIcon: "size-4",
  composerHint:
    "mx-auto mt-2 hidden max-w-[820px] text-center text-[11px] text-muted-foreground sm:block",
} as const;

type Props = {
  sessionToken: string;
  connections?: ReactNode;
  footer?: ReactNode;
};

type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
};

const WELCOME =
  "Connect Google Calendar, then ask about today's agenda, create a Meet, or reschedule something.";

const SUGGESTIONS: { prompt: string; label: string; hint: string; icon: LucideIcon }[] = [
  {
    prompt: "What's on today?",
    label: "Today's agenda",
    hint: "A short brief of your day",
    icon: CalendarDays,
  },
  {
    prompt: "What's on tomorrow?",
    label: "Tomorrow at a glance",
    hint: "Prepare for what's next",
    icon: CalendarClock,
  },
  {
    prompt: "Find a free slot tomorrow morning",
    label: "Find a free slot",
    hint: "Check availability before you book",
    icon: Clock,
  },
  {
    prompt:
      "Schedule a 30 minute meeting tomorrow at 10am with a Google Meet link and invite dineshsuwalkya31@gmail.com",
    label: "Schedule a meeting",
    hint: "Invites dineshsuwalkya31@gmail.com with a Meet link",
    icon: CalendarPlus,
  },
];

// Backend progress events look like "Running <tool_name>".
const TOOL_LABELS: Record<string, { label: string; icon: LucideIcon }> = {
  list_upcoming_meetings: { label: "Reviewing your calendar", icon: CalendarSearch },
  check_calendar_busy: { label: "Checking availability", icon: Clock },
  create_meeting: { label: "Creating the meeting", icon: CalendarPlus },
  reschedule_meeting: { label: "Rescheduling the meeting", icon: CalendarCheck },
  cancel_meeting: { label: "Cancelling the meeting", icon: CalendarX },
  update_working_memory: { label: "Saving your preference", icon: NotebookPen },
};

function describeProgress(message: string) {
  const tool = message.replace(/^Running\s+/i, "").trim();
  return TOOL_LABELS[tool] ?? { label: message, icon: Sparkles };
}

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function formatThreadTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  const sameDay = date.toDateString() === new Date().toDateString();
  return sameDay
    ? date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })
    : date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function WelcomeMessage(): Message {
  return {
    id: "welcome",
    role: "assistant",
    content: WELCOME,
  };
}

function ChatPanel({ sessionToken, connections, footer }: Props) {
  const [threadId, setThreadId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([WelcomeMessage()]);
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [threadsError, setThreadsError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [running, setRunning] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const showEmpty =
    messages.length === 1 && messages[0]?.id === "welcome" && !running;

  const bottomRef = useRef<HTMLDivElement>(null);

  const refreshThreads = useCallback(async () => {
    try {
      const data = await listThreads(sessionToken);
      setThreads(data.threads);
      setThreadsError(null);
    } catch (error) {
      setThreadsError(
        error instanceof Error ? error.message : "Could not load chats",
      );
    }
  }, [sessionToken]);

  useEffect(() => {
    refreshThreads();
  }, [refreshThreads]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, progress]);

  // Close the drawer with Escape.
  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") setDrawerOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  function startNewChat() {
    if (running) return;
    setThreadId(crypto.randomUUID());
    setMessages([WelcomeMessage()]);
    setPrompt("");
    setDrawerOpen(false);
  }

  async function resumeThread(nextThreadId: string) {
    setDrawerOpen(false);
    if (running || loadingThread || nextThreadId === threadId) return;
    setLoadingThread(true);
    setProgress(null);

    try {
      const data = await loadThread(sessionToken, nextThreadId);
      setThreadId(data.threadId);
      setMessages(
        data.messages.length > 0 ? data.messages : [WelcomeMessage()],
      );
      setPrompt("");
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "system",
          content: "Could not load the chat",
        },
      ]);
    } finally {
      setLoadingThread(false);
    }
  }

  async function sendMessage(text: string) {
    const trimmed = text.trim();

    if (!trimmed || running || loadingThread) return;
    const assistantId = crypto.randomUUID();

    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
      },
      {
        id: assistantId,
        role: "assistant",
        content: "",
      },
    ]);

    setPrompt("");
    setRunning(true);
    setProgress(null);

    try {
      await streamAgentChat(
        sessionToken,
        {
          message: trimmed,
          threadId,
        },
        (event) => {
          if (event.type === "progress" && event.message) {
            setProgress(event.message);
          }
          if (event.type === "token" && event.token) {
            setProgress(null);
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: message.content + event.token,
                    }
                  : message,
              ),
            );
          }

          if (event.type === "error") {
            setProgress(null);
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      content: formatErrorMessage(event.message ?? "Agent failed"),
                    }
                  : message,
              ),
            );
          }
        },
      );

      refreshThreads();
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "system",
          content: "Could not reach the agent API",
        },
      ]);
    } finally {
      setRunning(false);
      setProgress(null);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    sendMessage(prompt);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(prompt);
    }
  }

  const activeTitle = threads.find((thread) => thread.id === threadId)?.title;
  const step = progress ? describeProgress(progress) : null;
  const StepIcon = step?.icon;

  return (
    <div className={styles.root}>
      {drawerOpen && (
        <div
          className={styles.overlay}
          onClick={() => setDrawerOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(styles.aside, drawerOpen ? styles.asideOpen : styles.asideClosed)}
        aria-label="Conversations and account"
      >
        <div className={styles.brandRow}>
          <div className={styles.brandLeft}>
            <div className={styles.brandMark}>
              <Sparkles className={styles.brandMarkIcon} />
            </div>
            <div className="min-w-0">
              <p className={styles.brandTitle}>Concierge</p>
              <p className={styles.brandSub}>Meeting assistant</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className={styles.closeBtn}
            onClick={() => setDrawerOpen(false)}
            aria-label="Close menu"
          >
            <X />
          </Button>
        </div>

        <div className={styles.topActions}>
          <Button onClick={startNewChat} className={styles.newChatBtn} disabled={running}>
            <Plus className="size-4" />
            New conversation
          </Button>
          {connections}
        </div>

        <div className={styles.chatsSection}>
          <div className={styles.chatsHeader}>
            <p className={styles.sectionLabel}>Recent</p>
          </div>
          <ScrollArea className={styles.chatsScroll}>
            {threadsError ? (
              <p className={styles.chatsError}>
                Could not load chats: {threadsError}
              </p>
            ) : threads.length === 0 ? (
              <p className={styles.chatsEmpty}>
                No conversations yet. Your threads will appear here.
              </p>
            ) : (
              <div className={styles.threadList}>
                {threads.map((thread) => {
                  const active = thread.id === threadId;
                  return (
                    <button
                      key={thread.id}
                      type="button"
                      disabled={running || loadingThread}
                      onClick={() => resumeThread(thread.id)}
                      className={cn(
                        styles.threadBtn,
                        active ? styles.threadBtnActive : styles.threadBtnIdle,
                      )}
                      aria-current={active ? "true" : undefined}
                    >
                      {active && <span className={styles.threadActiveBar} />}
                      <MessageSquare
                        className={cn(styles.threadIcon, active && styles.threadIconActive)}
                      />
                      <span className={styles.threadText}>
                        <span className={styles.threadTitle}>{thread.title}</span>
                        <span className={styles.threadTime}>
                          {formatThreadTime(thread.updatedAt)}
                        </span>
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </ScrollArea>
        </div>

        <div className={styles.footer}>{footer}</div>
      </aside>

      <section className={styles.main}>
        <header className={styles.topBar}>
          <Button
            variant="ghost"
            size="icon"
            className={styles.menuBtn}
            onClick={() => setDrawerOpen(true)}
            aria-label="Open menu"
          >
            <Menu />
          </Button>
          <div className={styles.topTitle}>
            <p className={styles.topTitleText}>
              {showEmpty ? "New conversation" : activeTitle || "Conversation"}
            </p>
            <p className={styles.topSub}>Schedule, reschedule, and brief your day</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className={styles.newChatIconBtn}
            onClick={startNewChat}
            disabled={running}
            aria-label="New conversation"
          >
            <Plus />
          </Button>
        </header>

        <ScrollArea className={styles.messagesScroll}>
          <div className={styles.messagesInner}>
            {showEmpty ? (
              <div className={styles.emptyState}>
                <p className={styles.eyebrow}>
                  <Sparkles className="size-3.5" />
                  Your calendar concierge
                </p>
                <h1 className={styles.emptyTitle}>
                  {greeting()}. How may I help with your day?
                </h1>
                <p className={styles.emptyCopy}>{WELCOME}</p>
                <div className={styles.suggestions}>
                  {SUGGESTIONS.map((suggestion) => {
                    const Icon = suggestion.icon;
                    return (
                      <button
                        key={suggestion.prompt}
                        type="button"
                        onClick={() => sendMessage(suggestion.prompt)}
                        className={styles.suggestionBtn}
                        disabled={running || loadingThread}
                      >
                        <span className={styles.suggestionIcon}>
                          <Icon className="size-4" />
                        </span>
                        <span>
                          <span className={styles.suggestionLabel}>{suggestion.label}</span>
                          <span className={styles.suggestionHint}>{suggestion.hint}</span>
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className={styles.messageList}>
                {loadingThread ? (
                  <div className={styles.statusRow}>
                    <LoaderCircle className={styles.spin} />
                    Loading conversation…
                  </div>
                ) : (
                  messages.map((message) => {
                    if (message.id === "welcome" && messages.length > 1) {
                      return null;
                    }

                    const isUser = message.role === "user";

                    return (
                      <div
                        key={message.id}
                        className={cn(
                          styles.messageRow,
                          isUser ? styles.messageRowUser : styles.messageRowAssistant,
                        )}
                      >
                        {message.role === "assistant" && (
                          <div className={styles.avatar} aria-hidden="true">
                            <Sparkles className={styles.avatarIcon} />
                          </div>
                        )}
                        <div
                          className={cn(
                            styles.bubble,
                            isUser && styles.bubbleUser,
                            message.role === "assistant" && styles.bubbleAssistant,
                            message.role === "system" && styles.bubbleSystem,
                          )}
                        >
                          {!message.content && running ? (
                            <span className={styles.thinking}>
                              <LoaderCircle className={styles.spinSm} />
                              Thinking…
                            </span>
                          ) : isUser ? (
                            <p className={styles.userText}>{message.content}</p>
                          ) : (
                            <MarkdownMessage
                              content={message.content}
                              tone={message.role === "system" ? "system" : "assistant"}
                            />
                          )}
                        </div>
                      </div>
                    );
                  })
                )}

                {step && StepIcon ? (
                  <div className={styles.feed} role="status">
                    <div className={styles.feedItem}>
                      <span className={styles.feedIcon}>
                        <StepIcon className={styles.feedIconSvg} />
                      </span>
                      {step.label}
                      <LoaderCircle className={styles.spinSm} />
                    </div>
                  </div>
                ) : null}
                <div ref={bottomRef} />
              </div>
            )}
          </div>
        </ScrollArea>

        <div className={styles.composerWrap}>
          <form onSubmit={onSubmit} className={styles.composerForm}>
            <Textarea
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              rows={1}
              onKeyDown={onKeyDown}
              disabled={running}
              placeholder="Ask about your calendar…"
              className={styles.composerInput}
              aria-label="Message"
            />
            <Button
              type="submit"
              size="icon"
              disabled={!prompt.trim() || running}
              className={styles.sendBtn}
              aria-label="Send message"
            >
              {running ? (
                <LoaderCircle className={cn(styles.sendIcon, "animate-spin")} />
              ) : (
                <ArrowUp className={styles.sendIcon} />
              )}
            </Button>
          </form>
          <p className={styles.composerHint}>
            Enter to send · Shift + Enter for a new line
          </p>
        </div>
      </section>
    </div>
  );
}

export default ChatPanel;
