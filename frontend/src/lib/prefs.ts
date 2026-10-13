// Per-viewer UI preferences (localStorage; never required, always safe to lose).

export interface Prefs {
  backend: string;
  maxTokens: number;
}

const KEY = "pls_prefs";
const DEFAULTS: Prefs = { backend: "lead", maxTokens: 256 };

export function loadPrefs(): Prefs {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    /* private mode / blocked storage — fall back to defaults */
  }
  return DEFAULTS;
}

export function savePrefs(prefs: Prefs): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(prefs));
  } catch {
    /* ignore */
  }
}
