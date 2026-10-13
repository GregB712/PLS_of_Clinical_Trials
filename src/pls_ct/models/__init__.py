"""Model backends behind one unified interface (:class:`SummarizerBackend`)."""

from pls_ct.models.base import GenConfig, SummarizerBackend, SummaryResult
from pls_ct.models.baseline import LeadSentencesBackend

__all__ = ["GenConfig", "SummaryResult", "SummarizerBackend", "LeadSentencesBackend"]
