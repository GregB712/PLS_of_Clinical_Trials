import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Dashboard } from "./Dashboard";

vi.mock("../lib/api", () => ({
  api: { experiments: vi.fn(async () => []) },
  ApiError: class ApiError extends Error {},
}));

describe("Dashboard", () => {
  it("shows an empty state when no benchmarks exist", async () => {
    render(<Dashboard />);
    await waitFor(() =>
      expect(screen.getByText(/No benchmarks recorded yet/i)).toBeInTheDocument(),
    );
  });
});
