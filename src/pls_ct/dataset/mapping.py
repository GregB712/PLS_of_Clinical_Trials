"""Static mapping data carried over from the thesis (``finalDataset.ipynb``).

Kept as data (not buried in a notebook cell) so the dataset build is inspectable
and testable. These are the thesis's own choices, preserved verbatim.
"""

from __future__ import annotations

# The 8 canonical patient-summary questions, each mapped to the clinical-report
# section(s) used as its context. Source: finalDataset.ipynb "Database Mapping".
QUESTION_TO_SECTIONS: dict[str, list[str]] = {
    "Why was the research needed?": ["Objectives"],
    "How long was the trial?": ["Study Start/End Dates", "Reason for Termination"],
    "Who was in this clinical trial?": ["Study Population: Key Inclusion/Exclusion Criteria"],
    "What treatments did the participants take?": ["Statistical Methods", "Trial Analysis"],
    "What happened during the trial?": ["Study Design/Methodology"],
    "What were the results of the trial?": ["Trial Analysis", "Conclusion"],
    "What adverse events did participants report?": ["Trial Analysis"],
    "How has this trial helped?": ["Conclusion"],
}

# Novartis boilerplate stripped from both report and summary text during cleaning.
# Source: finalDataset.ipynb "Clean up Database" (contact URLs/phones + page footers).
NOVARTIS_BOILERPLATE: tuple[str, ...] = (
    "www.novartisclinicaltrials.com",
    "1-888-669-6682 (US);",
    "1-888-669-6682 (US)",
    "1-888-669-6682  (US)",
    "+41-61-324-1111 (EU);",
    "+41-61-324-1111 (EU)",
    "+41-61-324 1111 (EU);",
    "+41-61-324 1111 (EU)",
    "www.novctrd.com",
    "www.clinicaltrials.gov",
    "https://www.clinicaltrialsregister.eu/ctr-search/search",
    "www.clinicaltrialsregister.eu",
    "http://www.novartis.com/clinicaltrials",
    "Clinical Trial Results Website",
)

# Repeated page-footer templates ("| Trial Results Summary | <page>", with variants).
# Generated rather than hand-listed (the notebook enumerated pages 1..18 by hand).
_FOOTER_TEMPLATES: tuple[str, ...] = (
    "| Adults and Adolescent version |Trial Results Summary | {n}",
    "| Trial Results Summary | {n}",
    "| Trial Results Summary | Parent Version | {n}",
    "| Trial Results Summary | Adult Version | {n}",
)


def footer_boilerplate(max_page: int = 18) -> list[str]:
    """All page-footer strings to strip, longest first (so partial matches don't shadow)."""
    out = [tpl.format(n=n) for tpl in _FOOTER_TEMPLATES for n in range(max_page, 0, -1)]
    return sorted(out, key=len, reverse=True)
