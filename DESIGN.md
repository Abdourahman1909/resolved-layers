---
name: "Resolved Layers"
description: "A calm, evidence-first desktop system for transparent computational-health inference."
colors:
  laboratory-blue: "#0B42E7"
  laboratory-blue-hover: "#0B35C5"
  ink: "#101522"
  evidence-ink: "#303847"
  secondary-text: "#566176"
  muted-text: "#7E8798"
  small-muted-text: "#626C7F"
  pathogenic: "#263B72"
  benign: "#6D9B91"
  threshold-amber: "#8A590E"
  success: "#14804A"
  error: "#B52921"
  rule: "#D8DEE8"
  control-rule: "#CCD3DE"
  soft-rule: "#E8ECF2"
  selected-blue: "#EEF3FF"
  disabled-surface: "#E9EDF3"
  quiet-surface: "#F1F4F8"
  header-surface: "#F8FAFC"
  alternate-row: "#FBFCFE"
  canvas: "#FFFFFF"
typography:
  headline:
    fontFamily: "Arial, sans-serif"
    fontSize: "28px"
    fontWeight: 500
  title:
    fontFamily: "Arial, sans-serif"
    fontSize: "20px"
    fontWeight: 500
  body:
    fontFamily: "Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.15
  label:
    fontFamily: "Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    letterSpacing: "0.45px"
rounded:
  compact: "3px"
  control: "4px"
  standard: "5px"
  pill: "999px"
spacing:
  hairline: "1px"
  xs: "4px"
  sm: "8px"
  control-inset: "12px"
  md: "16px"
  section: "24px"
  gutter: "34px"
components:
  button-primary:
    backgroundColor: "{colors.laboratory-blue}"
    textColor: "{colors.canvas}"
    typography: "{typography.body}"
    rounded: "{rounded.standard}"
    padding: "0 15px"
    height: "42px"
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.standard}"
    padding: "0 15px"
    height: "42px"
  select-field:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 34px 0 12px"
    height: "38px"
  filter-chip:
    backgroundColor: "{colors.selected-blue}"
    textColor: "{colors.laboratory-blue}"
    rounded: "{rounded.pill}"
    padding: "0 11px"
    height: "27px"
---

# Design System: Resolved Layers

## Overview

**Creative North Star: "The Evidence Desk"**

Resolved Layers is a light-first computational-health desktop workspace. Its visual language resembles an orderly evidence desk: source material, model fit, transformation details, and results remain visible as connected layers separated by fine rules rather than decorative containers. The system is calm, professional, compact, and explicit about state.

The interface earns trust through alignment, restrained laboratory blue, near-flat tonal surfaces, and evidence-bearing language. It avoids generic dashboard theater: hierarchy comes from type, dividers, and spatial grouping rather than gradients, large metric cards, heavy shadows, or ornamental data graphics. Selected-record work preserves the active Records table beside a resizable, Source Row-anchored evidence pane instead of replacing context with a modal. Surface-specific workflows may compose these primitives differently; the design system does not make any single page layout universal.

**Key Characteristics:**

- Light-first white canvas with cool, nearly neutral supporting surfaces.
- Thin rules and tonal shifts organize dense evidence without visual clutter.
- Laboratory blue is reserved for interaction, focus, selection, and section signals.
- Compact Arial/native-sans typography supports scanning at desktop density.
- Small radii soften controls without turning the workspace into a card grid.
- Status and evidence are named directly; color supports meaning but never carries it alone.
- Label-dependent performance remains authorization-, denominator-, and source-led rather than card-led.
- Record detail preserves table context and follows immutable Source Row identity.

## Colors

The palette combines crisp paper whites, cool slate neutrals, and one restrained laboratory-blue interaction voice, with semantic colors used sparingly for evidence states.

### Primary

- **Laboratory Blue:** The sole recurring interaction accent for primary actions, active navigation rules, focus borders, selected text, and section labels.
- **Laboratory Blue Hover:** The darker primary-button hover state; it signals response without adding elevation.

### Secondary

- **Pathogenic Navy:** Identifies Pathogenic prediction evidence and distribution segments.
- **Benign Sage:** Identifies Benign prediction evidence and composition segments.
- **Threshold Amber:** Provides the readable foreground for Release Threshold values, warning text, and modified-source evidence; it also marks the threshold line and is never general decoration.

### Neutral

- **Evidence Ink:** Primary text and high-emphasis values use ink; evidence labels use the slightly softer evidence-ink role.
- **Secondary, Muted, and Small Muted Text:** Supporting explanations use secondary-text; disabled button labels use muted-text; very small field-type, missing-value, and disabled-field text uses the stronger small-muted-text role so compact copy remains readable.
- **Canvas and Quiet Surfaces:** Canvas remains white. Quiet, header, selected, disabled, and alternating-row surfaces provide shallow tonal grouping.
- **Rule Family:** Rule, control-rule, and soft-rule create the system's structural hierarchy, from section boundaries to dense table grids.

### Named Rules

**The One Blue Voice Rule.** Laboratory blue communicates action, focus, selection, or structural emphasis; it is not a decorative fill.

**The Evidence Color Rule.** Pathogenic, Benign, threshold, success, and error colors accompany explicit labels or values and never substitute for them.

## Typography

**Display Font:** Arial (with native sans-serif fallback)

**Body Font:** Arial (with native sans-serif fallback)

**Character:** One practical sans-serif family keeps the application neutral and legible. Hierarchy comes from a compact size range and restrained Medium/DemiBold emphasis rather than dramatic font changes.

### Hierarchy

- **Headline** (Medium, 27–28px): Top-level workspace titles.
- **Title** (Medium/DemiBold, 18–20px): Product naming, archive headings, and major local headings.
- **Body** (Regular/Medium, 13–14px, approximately 1.15 line-height when wrapping): Controls, navigation, evidence rows, and explanatory copy.
- **Label** (DemiBold, 10–12px): Table headers, metadata, compact captions, and section markers. Section markers are uppercase at 12px with 0.45px letter spacing.

### Named Rules

**The Working-Type Rule.** Most operational information stays within 10–14px; only page and major local titles rise above that compact evidence scale.

## Layout

The incumbent desktop frame is designed at 1536 × 980 with a 1120 × 720 minimum and a fixed 70px application bar. Major workspace content uses 34px horizontal gutters and 16–25px vertical section intervals. The Source Review evidence pane is responsive within a bounded 398–468px width, while primary content receives the remaining space.

Screens use split workspaces, ruled bands, tables, and focused panes rather than a universal card grid. Repeated internal spacing centers on 8, 12, 16, and 24px; 34px is the outer workspace gutter. Dense tables use approximately 35–41px body rows and 47–58px headers. Navigation and evidence remain compact so source context survives beside active work.

In Records, selecting a prediction opens the Variant Inspector as a resizable right pane while the table remains visible and active. The Inspector is bounded to 360–650px with a preferred width of roughly 39% and the table retains at least 500px while detail is open. The 9px separator supports pointer resizing and Left/Right Arrow resizing in 24px steps.

Observed Evaluation is a single scrollable evidence ledger. A compact run-identity band leads into a full-width authorization gate; once labels are authorized, the calculated evidence uses an evaluation-specific 64/34 split between metrics, confusion evidence, and denominator coverage on the left and inspectable cohorts plus calculation provenance on the right. This ratio belongs to the Evaluation Workspace and does not establish a global dashboard grid.

**The Surface Boundary Rule.** Split panes, cohort charts, records tables, and evidence bands are valid compositions for their respective tasks, not mandatory templates for every new surface.

**The Table-Context Rule.** Record detail opens beside the Records table, never over it; selection, resizing, and dismissal preserve the immutable Source Row as the shared reference.

## Elevation & Depth

The system is flat by default and defines depth through tonal surface changes, 1px rules, clipping, and adjacency. The observed QML does not use drop shadows. Popups and bounded containers remain visually attached to the workspace through a border and small radius rather than floating dramatically above it.

### Named Rules

**The Flat Evidence Rule.** Use borders and restrained tonal layering before considering elevation; heavy shadows and glass effects do not belong in this system.

## Shapes

The form language is gently squared. Dense containers and selection rows use 3px corners, select fields and popups use 4px, and standard buttons and source containers use 5px. Pills are reserved for compact status and removable-filter chips. Most structural boundaries remain straight 1px rules.

**The Small-Radius Rule.** Corners support clarity at desktop density; they do not turn every section into a soft standalone card.

## Components

### Buttons

- **Shape:** Compact rectangular controls with a 5px radius and a 42px default height; bounded contexts may use observed 29–38px compact heights.
- **Primary:** Laboratory-blue fill, white Medium label, and 15px horizontal inset. Hover darkens the fill without lifting the control.
- **Secondary:** White fill, ink label, and a 1px control-rule border. Hover moves to the quiet surface; keyboard focus turns the border laboratory blue.
- **Quiet:** Borderless white/transparent-adjacent command treatment for low-emphasis actions such as archive, back, and Inspector Close controls. Quiet appearance never suppresses keyboard operation or the visible 2px laboratory-blue focus boundary.
- **Disabled:** Disabled-surface fill, muted label, and reduced opacity; state remains legible without relying on opacity alone.

### Chips

- **Style:** Removable filters use a 27–30px pill silhouette, pale semantic surface, matching semantic text, and compact 10–11px labels.
- **State:** Selection is explicit in both text and tonal fill. Chips represent active filters or verified status, not decorative categories.

### Cards / Containers

- **Corner Style:** 3–5px depending on density.
- **Background:** White at rest, with pale cool surfaces for headers, alternating rows, selections, and hover.
- **Shadow Strategy:** None; use the flat evidence philosophy.
- **Border:** A 1px rule or soft-rule boundary.
- **Internal Padding:** Commonly 12–20px; larger workspace offsets use the 34px gutter.

### Inputs / Fields

- **Style:** White background, 1px control-rule border, 4–5px radius, 12–14px text, and compact 38–40px height.
- **Focus:** Border changes to laboratory blue. Select menus use a pale-blue highlighted option.
- **Error / Disabled:** Disabled fields use quiet surfaces and muted text; error states pair semantic color with explicit evidence copy.

### Navigation

Top-level navigation sits in the 70px application bar. Labels are 13px, active items become DemiBold ink, and a 2px laboratory-blue rule marks the current surface. Unavailable destinations remain visible at reduced opacity so the application structure stays understandable.

### Evidence Rows

Evidence rows use a stable 46/52 label-to-value split, 13px type, right-aligned Medium values, and approximately 7px of vertical breathing room. Long checksums and contract values may wrap; otherwise values elide in the middle to preserve identifying ends.

### Tables

Tables are framed by a 1px rule with clipped 3px corners. Header surfaces are pale and centered; body rows alternate white and the alternate-row surface. Fine soft-rule cell boundaries and 10–12px text support exact record inspection at high density. A selected row receives selected-blue fill and a selected border while the focused table receives a visible laboratory-blue perimeter.

Prediction tables expose table semantics and accessible cell semantics. Each cell names its column, immutable Source Row, and value, carries selected state, and supports an accessible press action. Up/Down and Home/End move row selection; Return, Enter, or Space establishes a selection when none exists; Escape closes the Inspector without losing the table.

### Observed Evaluation Evidence Ledger

The Evaluation Workspace uses one signature authorization-led ledger rather than independent KPI cards. It begins with Source Dataset, Model Package, Inference Contract, fixed Release Threshold, and Evaluated Denominator in one ruled traceability band. Ground-Truth Authorization then requires an explicit label column plus exact raw-value mappings for Pathogenic and Benign before any observed metric appears; the authorization state and mapping remain visible after calculation.

The metric ledger is one compact contiguous row. F1 receives the strongest typographic emphasis because it is the primary competition metric, while Precision, Recall, MCC, and Accuracy remain supporting values separated by fine internal rules. Undefined formulas say `Undefined` instead of fabricating zero. The confusion matrix names its axes in full—rows are predictions and columns are authorized Ground Truth—then pairs TP, FP, FN, and TN counts with their explicit abbreviations and semantic color.

The operator reviews proposed valid, missing-label, and unrecognized-value counts before authorization; denominator coverage then discloses evaluated and excluded counts beside the observed results. Evaluation Cohorts use explicit `Inspect N` commands to open the exact FP, FN, TP, or TN Source Rows in Records, where the existing Variant Inspector remains the record-level evidence surface. Calculation Evidence keeps run, source checksum state, authorized mappings, fixed threshold, and contract checksum adjacent to the observed results. When the archived source is unavailable, checksum-invalid, or not authorized, the same surface withholds metrics and explains why.

**The Authorized Observation Rule.** Current-run metrics appear only after checksum-valid source access and explicit Ground-Truth Authorization; they never stand in for saved release validation or external Organizer Scoring.

### Variant Inspector

The Inspector is a table-visible, resizable right pane rather than a modal. Its evidence order is stable: selected Source Row with prediction and ensemble score; score, Release Threshold, threshold relationship, and disagreement; separate CatBoost and LightGBM component-model scores; immutable run, package, and contract identity; then checksum state and the complete original Source Row.

The Inspector's evidence scroll and its Close and search controls participate in the tab sequence. The evidence scroll supports Up/Down, Page Up/Page Down, Home, and End. The splitter is an accessible separator with a visible blue focus line and Left/Right Arrow resizing.

**The Evidence-Lane Rule.** Component-model outputs are model-output evidence only; keep them explicitly separate from biological causation, clinical evidence, and model explainability.

## Do's and Don'ts

### Do:

- **Do** use thin rules, alignment, and subtle tonal surfaces to make relationships inspectable.
- **Do** preserve compact evidence density with the observed 10–14px working type and small radii.
- **Do** reserve laboratory blue for interaction, focus, selection, and structural emphasis.
- **Do** pair every semantic color with explicit status, evidence, or category language.
- **Do** reuse the same shell, type, color, control, and rule vocabulary across Source Review, Dataset Profile, Overview, Records, Evaluation, and Run Archive.
- **Do** keep the Evaluation traceability band, exact label mapping, evaluated denominator, confusion evidence, and calculation provenance visible as one connected ledger.
- **Do** route Evaluation Cohorts into filtered Records with an explicit `Inspect N` action so exact error rows and the Variant Inspector remain available.
- **Do** keep the Records table visible while selected Source Row evidence opens, resizes, scrolls, or closes beside it.
- **Do** preserve visible focus and accessible names, roles, selected states, and keyboard actions for quiet controls, table cells, the Inspector, and its splitter.

### Don't:

- **Don't** introduce gradients, heavy shadows, glass effects, or decorative elevation.
- **Don't** turn every data group into a rounded card or build generic KPI-card grids.
- **Don't** use oversized decorative metrics or add charts without an evidence task.
- **Don't** split observed metrics into freestanding KPI cards or separate them from authorization, denominator, confusion, and calculation evidence.
- **Don't** show current-run F1, confusion counts, or other observed performance for an unlabeled run awaiting Organizer Scoring.
- **Don't** drift into generic AI-dashboard or generic medical-blue styling.
- **Don't** universalize a page-specific behavior or composition as a visual-system law.
- **Don't** describe component scores as biological causation, clinical evidence, or explainability.
