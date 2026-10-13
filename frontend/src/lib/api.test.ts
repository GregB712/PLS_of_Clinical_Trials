import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "./api";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

describe("api client", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("parses JSON on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        jsonResponse({ trials: 6, documents: 12, sections: 96, chunks: 0, experiments: 1 }),
      ),
    );
    const stats = await api.stats();
    expect(stats.trials).toBe(6);
    expect(stats.experiments).toBe(1);
  });

  it("throws ApiError carrying error + detail on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse({ error: "provider_config", detail: "no key" }, 400)),
    );
    await expect(api.summarize({ backend: "anthropic", context: "x" })).rejects.toMatchObject({
      status: 400,
      message: "provider_config",
      detail: "no key",
    });
  });

  it("wraps network failures as ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("connection refused");
      }),
    );
    await expect(api.stats()).rejects.toBeInstanceOf(ApiError);
  });

  it("builds trial query strings", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({ items: [], total: 0, limit: 10, offset: 0 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await api.trials({ q: "SYN", limit: 10, offset: 5 });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("/trials?");
    expect(url).toContain("q=SYN");
    expect(url).toContain("limit=10");
    expect(url).toContain("offset=5");
  });
});
