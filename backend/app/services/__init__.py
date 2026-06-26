"""Business-logic services (pipeline stages).

One service = one role (docs/02_ARCHITECTURE.md §3): IngestionService,
AnonymizationService, SeparationService, ConversionService, SegmentationService,
RegistrationService, QuantificationService, DosimetryService, ExamAnalysisService,
ReportService, ExportService. Implemented incrementally from Phase 1.
"""
