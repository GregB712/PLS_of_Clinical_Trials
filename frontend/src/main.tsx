import React, { Suspense, lazy } from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Spinner } from "./components/ui";
import "./index.css";

// Lazy-load pages so each is its own chunk — keeps Recharts (Dashboard-only) and other
// page code out of the initial bundle.
const Landing = lazy(() => import("./pages/Landing").then((m) => ({ default: m.Landing })));
const Demo = lazy(() => import("./pages/Demo").then((m) => ({ default: m.Demo })));
const Dashboard = lazy(() => import("./pages/Dashboard").then((m) => ({ default: m.Dashboard })));
const Explorer = lazy(() => import("./pages/Explorer").then((m) => ({ default: m.Explorer })));
const Rag = lazy(() => import("./pages/Rag").then((m) => ({ default: m.Rag })));
const Research = lazy(() => import("./pages/Research").then((m) => ({ default: m.Research })));
const Settings = lazy(() => import("./pages/Settings").then((m) => ({ default: m.Settings })));

function page(element: React.ReactNode) {
  return <Suspense fallback={<Spinner />}>{element}</Suspense>;
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: page(<Landing />) },
      { path: "demo", element: page(<Demo />) },
      { path: "dashboard", element: page(<Dashboard />) },
      { path: "explorer", element: page(<Explorer />) },
      { path: "rag", element: page(<Rag />) },
      { path: "research", element: page(<Research />) },
      { path: "settings", element: page(<Settings />) },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
