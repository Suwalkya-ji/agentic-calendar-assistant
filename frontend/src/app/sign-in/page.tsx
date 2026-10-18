import { RedirectIfAuthenticated } from "@/components/auth/RedirectIfAuthenticated";
import SignInComponent from "@/components/auth/sign-in";
import { CalendarCheck, Clock, ShieldCheck, Sparkles, Video } from "lucide-react";

const styles = {
  shell: "app-shell-bg min-h-svh lg:grid lg:grid-cols-[1.1fr_1fr]",
  story:
    "relative hidden flex-col justify-between overflow-hidden border-r border-border bg-secondary px-12 py-12 lg:flex xl:px-16",
  brand: "flex items-center gap-3",
  brandMark:
    "flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground",
  brandTitle: "font-heading text-[22px] leading-none font-medium tracking-tight",
  storyBody: "max-w-md",
  eyebrow:
    "text-[11px] font-bold tracking-[0.08em] text-primary uppercase",
  storyTitle:
    "mt-4 font-heading text-[40px] leading-[48px] font-normal tracking-[-0.02em]",
  storyCopy: "mt-4 text-base leading-[26px] text-muted-foreground",
  features: "mt-10 space-y-4",
  feature: "flex items-start gap-3",
  featureIcon:
    "flex size-8 shrink-0 items-center justify-center rounded-md bg-card text-primary ring-1 ring-border",
  featureTitle: "text-sm font-semibold",
  featureCopy: "text-[13px] leading-[18px] text-muted-foreground",
  storyFoot: "flex items-center gap-2 text-xs text-muted-foreground",
  rule: "absolute inset-x-0 top-0 h-0.5 bg-primary",

  formSide: "flex min-h-svh items-center justify-center px-4 py-10 sm:px-8",
  formWrap: "w-full max-w-md",
  mobileBrand: "mb-8 flex items-center justify-center gap-3 lg:hidden",
  card: "surface-2 rounded-xl px-5 py-8 sm:px-8",
  cardHeader: "mb-6 text-center",
  cardTitle:
    "font-heading text-[30px] leading-[38px] font-normal tracking-[-0.015em]",
  cardCopy: "mt-2 text-sm leading-[22px] text-muted-foreground",
  legal: "mt-6 text-center text-xs text-muted-foreground",
} as const;

const FEATURES = [
  {
    icon: CalendarCheck,
    title: "Your agenda, briefed",
    copy: "Ask what's on today and get a concise, scannable summary.",
  },
  {
    icon: Clock,
    title: "Conflict-free scheduling",
    copy: "Availability is checked before anything is booked.",
  },
  {
    icon: Video,
    title: "Meet links and invites",
    copy: "Google Meet and attendee invitations, handled for you.",
  },
];

function Brand() {
  return (
    <div className={styles.brand}>
      <div className={styles.brandMark}>
        <Sparkles className="size-4" />
      </div>
      <span className={styles.brandTitle}>Concierge</span>
    </div>
  );
}

function SignInPage() {
  return (
    <main className={styles.shell}>
      <section className={styles.story}>
        <span className={styles.rule} />
        <Brand />
        <div className={styles.storyBody}>
          <p className={styles.eyebrow}>Private calendar concierge</p>
          <h1 className={styles.storyTitle}>Composure for every hour of your day.</h1>
          <p className={styles.storyCopy}>
            Schedule, reschedule and brief your day in plain language. Your
            assistant works directly with Google Calendar.
          </p>
          <ul className={styles.features}>
            {FEATURES.map(({ icon: Icon, title, copy }) => (
              <li key={title} className={styles.feature}>
                <span className={styles.featureIcon}>
                  <Icon className="size-4" />
                </span>
                <span>
                  <span className={styles.featureTitle}>{title}</span>
                  <span className={`block ${styles.featureCopy}`}>{copy}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <p className={styles.storyFoot}>
          <ShieldCheck className="size-3.5" />
          Secured by Descope. Your Google tokens are never stored by this app.
        </p>
      </section>

      <section className={styles.formSide}>
        <div className={styles.formWrap}>
          <div className={styles.mobileBrand}>
            <Brand />
          </div>
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <h2 className={styles.cardTitle}>Welcome back</h2>
              <p className={styles.cardCopy}>
                Sign in to connect your calendar and start scheduling.
              </p>
            </div>
            <RedirectIfAuthenticated>
              <SignInComponent />
            </RedirectIfAuthenticated>
          </div>
          <p className={styles.legal}>
            By continuing you agree to let the assistant manage events you ask it to.
          </p>
        </div>
      </section>
    </main>
  );
}

export default SignInPage;
