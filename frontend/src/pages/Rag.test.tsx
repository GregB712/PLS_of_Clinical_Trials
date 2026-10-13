import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Rag } from "./Rag";

vi.mock("../lib/api", () => ({
  api: {
    ask: vi.fn(async () => ({
      answer: "the grounded answer",
      sufficient: true,
      citations: [{ trial_name: "T1", section: "Objectives", start: 0, end: 5, score: 0.42 }],
    })),
  },
  ApiError: class ApiError extends Error {},
}));

describe("Rag", () => {
  it("submits a query and shows the answer with citations", async () => {
    render(<Rag />);
    fireEvent.change(screen.getByPlaceholderText(/What adverse events/i), {
      target: { value: "What were the objectives?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /ask/i }));
    await waitFor(() => expect(screen.getByText("the grounded answer")).toBeInTheDocument());
    expect(screen.getByText(/Objectives/)).toBeInTheDocument();
  });
});
