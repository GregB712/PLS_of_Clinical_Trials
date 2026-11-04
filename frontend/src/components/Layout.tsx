import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  { to: "/demo", label: "Live demo" },
  { to: "/dashboard", label: "Model comparison" },
  { to: "/explorer", label: "Dataset" },
  { to: "/rag", label: "Research assistant" },
  { to: "/paper", label: "Paper" },
  { to: "/research", label: "Methodology" },
  { to: "/settings", label: "Settings" },
];

export function Layout() {
  return (
    <div className="min-h-screen">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-full focus:bg-accent focus:px-4 focus:py-2 focus:text-white"
      >
        Skip to content
      </a>
      <header className="nav-material sticky top-0 z-40">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 sm:px-6">
          <NavLink
            to="/"
            className="flex shrink-0 items-center gap-2 py-3 text-[0.9375rem] font-semibold tracking-[-0.01em] text-ink"
          >
            <Logo />
            <span className="hidden sm:inline">Plain-language trials</span>
          </NavLink>
          <nav
            aria-label="Primary"
            className="-mr-4 flex min-w-0 flex-1 gap-0.5 overflow-x-auto py-2 pr-4 text-sm [mask-image:linear-gradient(to_right,black_85%,transparent)] [scrollbar-width:none] sm:justify-end sm:[mask-image:none]"
          >
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `shrink-0 rounded-full px-3 py-1.5 transition-colors duration-150 ${
                    isActive
                      ? "bg-accent-soft font-semibold text-accent-strong dark:text-accent"
                      : "text-ink-2 hover:bg-sunken hover:text-ink"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-6xl px-4 pb-20 pt-10 sm:px-6 sm:pt-14">
        <Outlet />
      </main>
    </div>
  );
}

/** A dense block of lines resolving into one highlighted line: the project in one glyph. */
function Logo() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
      <rect width="22" height="22" rx="6" className="fill-accent" />
      <g className="stroke-white dark:stroke-[#06201b]" strokeWidth="1.6" strokeLinecap="round">
        <path d="M5.5 6.5h11M5.5 9.5h9M5.5 12.5h11" opacity="0.55" />
        <path d="M5.5 16h7" strokeWidth="2.4" />
      </g>
    </svg>
  );
}
