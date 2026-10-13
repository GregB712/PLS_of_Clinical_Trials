"""Model pricing registry for cost estimates.

Prices are USD per 1,000,000 tokens as ``(input, output)``. This registry is
intentionally **empty by default**: provider prices change often and fabricating them
would be dishonest. Populate it from each provider's official pricing page (and note the
date) to enable cost estimates; unknown models return ``None`` ("cost unknown") rather
than a guess.

Last reviewed: 2026-10-13 (no prices asserted).
"""

from __future__ import annotations

# Example of the expected shape (commented out — fill in with verified current prices):
#   "claude-sonnet-5-5": (3.00, 15.00),
#   "gpt-4o-mini":       (0.15, 0.60),
#   "gemini-2.5-flash":  (0.30, 2.50),
PRICING: dict[str, tuple[float, float]] = {}


def estimate_cost(model: str, input_tokens: int | None, output_tokens: int | None) -> float | None:
    """Estimated USD cost, or ``None`` if pricing or token counts are unavailable."""
    price = PRICING.get(model)
    if price is None or input_tokens is None or output_tokens is None:
        return None
    in_rate, out_rate = price
    return input_tokens / 1_000_000 * in_rate + output_tokens / 1_000_000 * out_rate
