import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Paper } from "./Paper";
import paper from "../content/paper.json";

describe("Paper", () => {
  it("renders the article with PDF links, contents and references", () => {
    const { container } = render(<Paper />);
    expect(screen.getByRole("heading", { level: 1, name: paper.meta.title })).toBeInTheDocument();

    const pdfLinks = screen.getAllByRole("link", { name: /View PDF on GitHub/i });
    expect(pdfLinks[0]).toHaveAttribute(
      "href",
      "https://github.com/GregB712/PLS_of_Clinical_Trials/blob/main/paper/main.pdf",
    );
    expect(screen.getByRole("link", { name: /Download PDF/i })).toBeInTheDocument();

    // Every chapter heading from the contents is present in the body.
    for (const t of paper.toc) {
      expect(container.querySelector(`#${t.id}`)).not.toBeNull();
    }
    // Every in-article link points at something that exists.
    container.querySelectorAll<HTMLAnchorElement>('.article a[href^="#"]').forEach((a) => {
      expect(container.querySelector(a.getAttribute("href")!)).not.toBeNull();
    });
    expect(container.querySelectorAll(".references li")).toHaveLength(paper.references.length);
  });
});
