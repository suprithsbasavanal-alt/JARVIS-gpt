from backend.app.services.research.collector import MultiSourceCollector, DuplicateDetectionEngine
from backend.app.services.research.scorer import SourceCredibilityScorer, ConfidenceScoringEngine
from backend.app.services.research.verifier import FactExtractionEngine, ContradictionDetectionEngine, CitationGenerator
from backend.app.services.research.service import ResearchService
