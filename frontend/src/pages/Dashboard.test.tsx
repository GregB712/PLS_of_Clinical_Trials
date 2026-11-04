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

  it("shows the full-study results from the thesis", () => {
    render(<Dashboard />);
    expect(screen.getByText(/Full study: held-out test set/i)).toBeInTheDocument();
    // Fine-tuned Flan-T5-small seed 44 has the best test ROUGE-L (Table 5.1).
    expect(screen.getByText("Flan-T5-small FT (seed 44)").closest("tr")).toHaveTextContent(
      "22.80 [20.76, 24.81]",
    );
  });
});
