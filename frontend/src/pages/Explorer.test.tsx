import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Explorer } from "./Explorer";

vi.mock("../lib/api", () => ({
  api: {
    trials: vi.fn(async () => ({
      items: [{ protocol_id: "SYN001A2101", source: "synthetic", document_kinds: ["report"] }],
      total: 1,
      limit: 20,
      offset: 0,
    })),
    trial: vi.fn(async () => ({
      protocol_id: "SYN001A2101",
      source: "synthetic",
      documents: [],
      report_sections: { Objectives: "the stated objective" },
      summary_sections: {},
    })),
  },
  ApiError: class ApiError extends Error {},
}));

describe("Explorer", () => {
  it("lists trials and loads detail on click", async () => {
    render(<Explorer />);
    const item = await screen.findByText("SYN001A2101");
    fireEvent.click(item);
    await waitFor(() => expect(screen.getByText("the stated objective")).toBeInTheDocument());
  });
});
