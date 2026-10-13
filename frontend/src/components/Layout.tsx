import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  { to: "/", label: "Home", end: true },
  { to: "/demo", label: "Live demo" },
  { to: "/dashboard", label: "Model comparison" },
  { to: "/explorer", label: "Dataset" },
  { to: "/rag", label: "Research assistant" },
];

export function Layout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <NavLink to="/" className="text-lg font-semibold text-brand">
            PLS&nbsp;of&nbsp;Clinical&nbsp;Trials
          </NavLink>
          <nav className="flex flex-wrap gap-1 text-sm">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-md px-3 py-1.5 transition-colors ${
                    isActive ? "bg-brand text-white" : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
