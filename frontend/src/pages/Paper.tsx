import { useEffect, useRef, useState } from "react";
import paper from "../content/paper.json";

// Generated from paper/ by paper/web/build_web.py. Regenerate after editing the LaTeX.

const REPO = "https://github.com/GregB712/PLS_of_Clinical_Trials";
const PDF_ON_GITHUB = `${REPO}/blob/main/${paper.meta.pdfPath}`;
const PDF_DOWNLOAD = `${REPO}/raw/main/${paper.meta.pdfPath}`;
const SOURCE_ON_GITHUB = `${REPO}/tree/main/paper`;

const published = new Date(`${paper.meta.date}T12:00:00`).toLocaleDateString("en-US", {
  year: "numeric",
  month: "long",
  day: "numeric",
});

const TOC_IDS = paper.toc.map((t) => t.id);

const initials = paper.meta.author
  .split(" ")
  .map((w) => w[0])
  .join("");

export function Paper() {
  const active = useActiveSection(TOC_IDS);
  const tocRef = useRef<HTMLElement>(null);

  // Keep the current section visible in the sidebar list (it scrolls on its own).
  useEffect(() => {
    const nav = tocRef.current;
    const link = nav?.querySelector<HTMLElement>('[aria-current="location"]');
    if (!nav || !link) return;
    const top = link.getBoundingClientRect().top - nav.getBoundingClientRect().top + nav.scrollTop;
    if (top < nav.scrollTop + 40 || top > nav.scrollTop + nav.clientHeight - 80) {
      nav.scrollTop = Math.max(0, top - nav.clientHeight / 3);
    }
  }, [active]);

  // The article mounts after the route chunk loads, so the browser's own jump to
  // #fragment has already happened against an empty page. Redo it once.
  useEffect(() => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (id) document.getElementById(id)?.scrollIntoView();
  }, []);

  return (
    <div className="relative">
      <ReadingProgress />

      <div className="xl:grid xl:grid-cols-[15rem_minmax(0,42.5rem)_minmax(0,1fr)] xl:gap-12">
        <aside className="hidden xl:block" aria-label="Contents">
          <nav
            ref={tocRef}
            className="sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pb-8 pr-2 [scrollbar-width:thin]"
          >
            <p className="mb-3 text-sm font-semibold text-ink">Contents</p>
            <Toc active={active} />
          </nav>
        </aside>

        <article className="mx-auto w-full max-w-[42.5rem]">
          <header className="space-y-6">
            <p className="text-sm font-medium text-accent">
              {paper.meta.degree} thesis, {paper.meta.university}
            </p>
            <h1 className="font-serif text-[2.5rem] font-bold leading-[1.1] tracking-[-0.02em] text-ink text-balance sm:text-[3rem]">
              {paper.meta.title}
            </h1>

            <div className="flex items-center gap-3">
              <span
                aria-hidden="true"
                className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-accent-soft text-sm font-semibold text-accent-strong dark:text-accent"
              >
                {initials}
              </span>
              <div className="text-sm leading-snug">
                <div className="font-medium text-ink">{paper.meta.author}</div>
                <div className="flex flex-wrap gap-x-3 text-ink-3">
                  <span>Supervised by {paper.meta.supervisor}</span>
                  <time dateTime={paper.meta.date}>{published}</time>
                  <span>{paper.readingMinutes} min read</span>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 border-y border-line py-3">
              <a href={PDF_ON_GITHUB} className="btn btn-secondary btn-small" target="_blank" rel="noreferrer">
                <GitHubIcon />
                View PDF on GitHub
              </a>
              <a href={PDF_DOWNLOAD} className="btn btn-secondary btn-small">
                Download PDF
              </a>
              <a
                href={SOURCE_ON_GITHUB}
                className="btn btn-small ml-auto text-ink-2 hover:text-ink"
                target="_blank"
                rel="noreferrer"
              >
                LaTeX source
              </a>
            </div>
          </header>

          <details className="mt-6 rounded-xl border border-line bg-surface xl:hidden">
            <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-ink">
              Contents
            </summary>
            <div className="border-t border-line px-4 py-3">
              <Toc active={active} />
            </div>
          </details>

          <section aria-labelledby="abstract" className="article mt-10">
            <h2 id="abstract" className="article-kicker">
              Abstract
            </h2>
            <div className="standfirst" dangerouslySetInnerHTML={{ __html: paper.abstract }} />
            <details className="greek mt-6">
              <summary>Περίληψη στα Ελληνικά</summary>
              <div lang="el" dangerouslySetInnerHTML={{ __html: paper.abstractGreek }} />
            </details>
          </section>

          <div className="article" dangerouslySetInnerHTML={{ __html: paper.body }} />

          <section aria-labelledby="acknowledgements" className="article">
            <h2 id="acknowledgements">Acknowledgements</h2>
            <div dangerouslySetInnerHTML={{ __html: paper.acknowledgements }} />
          </section>

          <section aria-labelledby="references" className="article">
            <h2 id="references">References</h2>
            <ol className="references">
              {paper.references.map((r) => (
                <li key={r.id} id={r.id} dangerouslySetInnerHTML={{ __html: r.html }} />
              ))}
            </ol>
          </section>

          <footer className="mt-16 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6 text-sm text-ink-2">
            <span>Prefer the typeset version?</span>
            <a href={PDF_ON_GITHUB} className="btn btn-primary" target="_blank" rel="noreferrer">
              View PDF on GitHub
            </a>
          </footer>
        </article>
      </div>
    </div>
  );
}

function Toc({ active }: { active: string | null }) {
  return (
    <ol className="space-y-0.5 text-[0.8125rem] leading-snug">
      {paper.toc.map((t) => (
        <li key={t.id} className={t.level === 1 ? "pt-2 first:pt-0" : "pl-6"}>
          <a
            href={`#${t.id}`}
            aria-current={active === t.id ? "location" : undefined}
            className={`flex gap-2 rounded-md px-2 py-1 transition-colors duration-150 ${
              active === t.id
                ? "bg-accent-soft font-semibold text-accent-strong dark:text-accent"
                : t.level === 1
                  ? "font-medium text-ink hover:bg-sunken"
                  : "text-ink-2 hover:bg-sunken hover:text-ink"
            }`}
          >
            <span className="w-6 shrink-0 tabular-nums text-ink-3">{t.number}</span>
            <span>{t.title}</span>
          </a>
        </li>
      ))}
    </ol>
  );
}

/** Thin bar under the navigation that fills as the article is read. */
function ReadingProgress() {
  const bar = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      const el = document.documentElement;
      const max = el.scrollHeight - el.clientHeight;
      const p = max > 0 ? Math.min(1, el.scrollTop / max) : 0;
      if (bar.current) bar.current.style.transform = `scaleX(${p})`;
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      cancelAnimationFrame(frame);
    };
  }, []);
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-x-0 top-12 z-30 h-0.5">
      <div ref={bar} className="h-full origin-left scale-x-0 bg-accent" />
    </div>
  );
}

/** Id of the last contents heading above the reading line (a quarter down the viewport). */
function useActiveSection(ids: string[]) {
  const [active, setActive] = useState<string | null>(null);
  useEffect(() => {
    const els = ids.map((id) => document.getElementById(id)).filter(Boolean) as HTMLElement[];
    let frame = 0;
    const update = () => {
      frame = 0;
      const line = window.innerHeight * 0.25;
      let current: string | null = null;
      for (const el of els) {
        if (el.getBoundingClientRect().top > line) break;
        current = el.id;
      }
      setActive(current);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(frame);
    };
  }, [ids]);
  return active;
}

function GitHubIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}
