"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import Link from "next/link";

const styles = {
  root: "markdown-body min-w-0 max-w-full overflow-hidden text-[15px] leading-7 [&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
  rootUser:
    "[&_a]:text-primary-foreground [&_a]:decoration-primary-foreground/50",
  p: "mb-3 last:mb-0",
  ul: "mb-3 list-disc space-y-1.5 pl-5 last:mb-0",
  ol: "mb-3 list-decimal space-y-1.5 pl-5 last:mb-0",
  li: "leading-7",
  strong: "font-semibold text-foreground",
  em: "italic",
  codeBlock:
    "block overflow-x-auto rounded-lg bg-muted px-3 py-2 text-[13px] leading-6",
  codeInline: "rounded-md bg-muted px-1.5 py-0.5 text-[13px] font-medium",
  pre: "mb-3 max-w-full overflow-x-auto rounded-xl bg-muted p-3 last:mb-0",
  h1: "mb-2 font-heading text-xl font-semibold",
  h2: "mb-2 font-heading text-lg font-semibold",
  h3: "mb-2 text-base font-semibold",
  blockquote: "mb-3 border-l-2 border-primary/40 pl-3 text-muted-foreground",
} as const;

export function formatErrorMessage(content: string): string {
  if (!content) return content;
  const lower = content.toLowerCase();

  if (
    lower.includes("resource_exhausted") ||
    lower.includes("quota exceeded") ||
    lower.includes("code: 429") ||
    (lower.includes("429") && lower.includes("quota"))
  ) {
    const retryMatch = content.match(/retry\s+(?:in|after)\s+([0-9a-zA-Z\.]+)/i);
    if (retryMatch) {
      const raw = retryMatch[1].replace(/\.$/, "");
      const hMatch = raw.match(/(\d+)\s*h/);
      const mMatch = raw.match(/(\d+)\s*m/);
      const sMatch = raw.match(/(\d+)(?:\.\d+)?\s*s/);

      const parts: string[] = [];
      if (hMatch) parts.push(`${hMatch[1]} hour${hMatch[1] !== "1" ? "s" : ""}`);
      if (mMatch) parts.push(`${mMatch[1]} minute${mMatch[1] !== "1" ? "s" : ""}`);
      if (!hMatch && !mMatch && sMatch) parts.push(`${sMatch[1]} second${sMatch[1] !== "1" ? "s" : ""}`);

      if (parts.length > 0) {
        return `⏳ **Daily Request Limit Reached**\n\nYou have reached the free tier quota for this AI model. Please retry in **${parts.join(" and ")}**.`;
      }
      if (raw) {
        return `⏳ **Daily Request Limit Reached**\n\nYou have reached the free tier quota for this AI model. Please retry in **${raw}**.`;
      }
    }

    return "⏳ **Daily Request Limit Reached**\n\nYou have reached the daily free quota for the AI model. Please wait a while before sending another message.";
  }

  return content;
}

type Props = {
  content: string;
  className?: string;
  tone?: "assistant" | "user" | "system";
};

export function MarkdownMessage({
  content,
  className,
  tone = "assistant",
}: Props) {
  const displayContent = tone === "user" ? content : formatErrorMessage(content);

  return (
    <div
      className={cn(styles.root, tone === "user" && styles.rootUser, className)}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => <Link href={href ?? "#"}>{children}</Link>,
          p: ({ children }) => <p className={styles.p}>{children}</p>,
          ul: ({ children }) => <ul className={styles.ul}>{children}</ul>,
          ol: ({ children }) => <ol className={styles.ol}>{children}</ol>,
          li: ({ children }) => <li className={styles.li}>{children}</li>,
          strong: ({ children }) => (
            <strong className={styles.strong}>{children}</strong>
          ),
          em: ({ children }) => <em className={styles.em}>{children}</em>,
          code: ({ children, className: codeClassName }) => {
            const isBlock = Boolean(codeClassName);
            return (
              <code className={isBlock ? styles.codeBlock : styles.codeInline}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => <pre className={styles.pre}>{children}</pre>,
          h1: ({ children }) => <h3 className={styles.h1}>{children}</h3>,
          h2: ({ children }) => <h3 className={styles.h2}>{children}</h3>,
          h3: ({ children }) => <h3 className={styles.h3}>{children}</h3>,
          blockquote: ({ children }) => (
            <blockquote className={styles.blockquote}>{children}</blockquote>
          ),
        }}
      >
        {displayContent}
      </ReactMarkdown>
    </div>
  );
}
