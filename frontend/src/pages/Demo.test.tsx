import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Demo } from "./Demo";

vi.mock("../lib/api", () => ({
  api: {
    trials: vi.fn(async () => ({
      items: [{ protocol_id: "SYN001A2101", source: "synthetic", document_kinds: ["report"] }],
      total: 1,
      limit: 200,
      offset: 0,
    })),
    backends: vi.fn(async () => ({
      backends: [{ spec: "lead", kind: "baseline", available: true }],
      uploads_enabled: false,
    })),
    trial: vi.fn(async () => ({
      protocol_id: "SYN001A2101",
      source: "synthetic",
      documents: [],
      report_sections: { Objectives: "the technical objective" },
      summary_sections: { "Why was the research needed?": "the plain answer" },
    })),
  },
  ApiError: class ApiError extends Error {},
}));

describe("Demo", () => {
  it("shows the original document and the synthetic notice for a selected trial", async () => {
    render(<Demo />);
    expect(await screen.findByText(/synthetic samples made for this showcase/i)).toBeInTheDocument();
    expect(screen.getByText(/PDF upload is turned off/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Clinical trial"), { target: { value: "SYN001A2101" } });
    expect(await screen.findByText("the technical objective")).toBeInTheDocument();
    expect(screen.getByText(/nothing here describes a real trial/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: "Patient summary" }));
    expect(screen.getByText("the plain answer")).toBeInTheDocument();
  });
});
