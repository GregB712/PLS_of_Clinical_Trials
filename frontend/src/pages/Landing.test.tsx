import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { Landing } from "./Landing";

vi.mock("../lib/api", () => ({
  api: {
    stats: vi.fn(async () => ({
      trials: 6,
      documents: 12,
      sections: 96,
      chunks: 3,
      experiments: 1,
    })),
  },
  ApiError: class ApiError extends Error {},
}));

describe("Landing", () => {
  it("renders real dataset stats once loaded", async () => {
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("6")).toBeInTheDocument());
    expect(screen.getByText("Trials")).toBeInTheDocument();
    expect(screen.getByText("Indexed chunks")).toBeInTheDocument();
  });
});
