import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Landing } from "./pages/Landing";
import { Demo } from "./pages/Demo";
import { Dashboard } from "./pages/Dashboard";
import { Explorer } from "./pages/Explorer";
import { Rag } from "./pages/Rag";
import { Research } from "./pages/Research";
import { Settings } from "./pages/Settings";
import "./index.css";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Landing /> },
      { path: "demo", element: <Demo /> },
      { path: "dashboard", element: <Dashboard /> },
      { path: "explorer", element: <Explorer /> },
      { path: "rag", element: <Rag /> },
      { path: "research", element: <Research /> },
      { path: "settings", element: <Settings /> },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
