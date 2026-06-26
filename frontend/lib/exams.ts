/**
 * The six exam types covered by Scintia (docs/01_SPECIFICATIONS.md §4).
 * `value` matches the backend `exam_type` enum (docs/04_MODELE_DONNEES.md).
 */
export type ExamType =
  | "bone"
  | "myocardial_spect"
  | "mibg"
  | "octreotide"
  | "parathyroid"
  | "lung_vq";

export interface ExamOption {
  value: ExamType;
  /** User-facing label (FR). */
  label: string;
  /** Short radiopharmaceutical hint. */
  tracer: string;
}

export const EXAM_OPTIONS: ExamOption[] = [
  { value: "bone", label: "Scintigraphie osseuse", tracer: "Tc-99m HMDP/HDP" },
  { value: "myocardial_spect", label: "SPECT myocardique", tracer: "Tc-99m MIBI · Tl-201" },
  { value: "mibg", label: "MIBG", tracer: "I-123 · I-131 MIBG" },
  { value: "octreotide", label: "Octréotide / SSTR", tracer: "In-111 octréotide" },
  { value: "parathyroid", label: "Parathyroïde", tracer: "Tc-99m sestamibi" },
  { value: "lung_vq", label: "Poumon V/P", tracer: "Tc-99m MAA · Technegas" },
];
