---
title: Hermes Pipeline Flowchart
description: Text-based flowchart illustrating the complete Hermes HHE-200 processing pipeline from form intake to email delivery.
created: 2026-05-03
updated: 2026-05-03
tags: [hermes, flowchart, pipeline]
---

# Hermes Pipeline Flowchart

## Complete HHE-200 Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                        START                                 │
│              Site Evaluator Submits Form                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: GOOGLE FORM INTAKE                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Site Evaluator fills out Google Form               │   │
│  │  - Property information                              │   │
│  │  - Owner/applicant details                          │   │
│  │  - System type and components                       │   │
│  │  - Sketch uploaded (Drive attachment)               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: GOOGLE SHEET POPULATED                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Form response creates new row in Google Sheet       │   │
│  │  - All form fields mapped to columns                │   │
│  │  - Sketch file reference stored                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: HERMES TRIGGERED                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Trigger Method:                                    │   │
│  │  - Form submission webhook (preferred), OR          │   │
│  │  - Scheduled cron check for new rows                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: READ SHEET ROW                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Hermes reads the new/pending row from Google Sheet  │   │
│  │  - Parse all form field values                       │   │
│  │  - Extract system type and component selections      │   │
│  │  - Identify conditional document triggers           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: RETRIEVE SKETCH FROM DRIVE                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Access: bouchlesshay@gmail.com Drive               │   │
│  │  - Locate uploaded sketch from form attachment      │   │
│  │  - Download sketch file                             │   │
│  │  - Parse hand-drawn elements                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
              ┌───────────┴───────────┐
              │   Hermes Processing   │
              └───────────┬───────────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
           ▼              ▼              ▼
    ┌────────────┐ ┌───────────┐ ┌──────────────┐
    │  STEP 6a   │ │  STEP 6b  │ │  STEP 6c     │
    │  Fill PDF  │ │  Generate │ │  Page        │
    │  Form      │ │  Drawing  │ │  Selection   │
    │  Fields   │ │           │ │  Logic       │
    └─────┬──────┘ └─────┬─────┘ └──────┬───────┘
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  SYSTEM TYPE CHECK   │
              └──────────┬──────────┘
                         │
          ┌──────────────┴──────────────┐
          │                              │
          ▼                              ▼
   ┌─────────────────┐    ┌─────────────────────────┐
   │  STANDARD SYSTEM │    │  ENGINEERED/ALTERNATIVE │
   │  ─────────────── │    │  (Components 7/8/9)    │
   │                  │    │                         │
   │  Use Pages 3+4   │    │  Use Pages 7+8          │
   │  GRID variant    │    │  BLANK variant          │
   │  (hand-fill)     │    │  (AutoCAD)              │
   │                  │    │                         │
   │  Page 3: Site    │    │  Page 7: Disposal Plan  │
   │       Plan +      │    │  Page 8: Cross-Section  │
   │       Soil Grid   │    │                         │
   │                  │    │  Replaces Pages 3+4     │
   │  Page 4: Disposal │    │                         │
   │       Plan +       │    │                         │
   │       Cross-Sect.  │    │                         │
   └──────────────────┘    └─────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  STEP 6d            │
              │  Conditional Docs    │
              │  ─────────────────   │
              │  Check triggers:     │
              │                      │
              │  ┌────────────────┐  │
              │  │ Variance?      │──┼──► Generate HHE-204
              │  └────────────────┘  │
              │  ┌────────────────┐  │
              │  │ Soil Notes     │──┼──► Generate GSB Soil
              │  │ Referenced?    │  │   Notes
              │  └────────────────┘  │
              │  ┌────────────────┐  │
              │  │ Pre-treatment  │──┼──► Generate HHE-300A
              │  │ System?        │  │
              │  └────────────────┘  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  STEP 6e            │
              │  MERGE PDFs          │
              │  ─────────────────   │
              │  Assemble all pages  │
              │  into single merged  │
              │  document           │
              └──────────┬───────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  STEP 7             │
              │  DRAFT + SEND EMAIL │
              │  ─────────────────   │
              │  To: Site Evaluator │
              │                      │
              │  Attachments:        │
              │  ┌────────────────┐  │
              │  │ 1. Merged PDF  │  │
              │  │ 2. Page 1 PDF  │  │
              │  │ 3. Page 2 PDF  │  │
              │  │ 4. Page 3/7 PDF│  │
              │  │ 5. Page 4/8 PDF│  │
              │  │ 6. AutoCAD DWG │  │
              │  │ 7. HHE-204     │  │ (if variance)
              │  │ 8. GSB Notes    │  │ (if referenced)
              │  │ 9. HHE-300A    │  │ (if pre-treat)
              │  └────────────────┘  │
              │                      │
              │  + Correction form   │
              │    link note         │
              └──────────┬───────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │        END          │
              │   Email Delivered   │
              └─────────────────────┘
```

---

## Conditional Document Logic

```
                    ┌────────────────────┐
                    │  Check Application │
                    │  Data for Triggers │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │  VARIANCE   │    │  SOIL      │    │  PRE-       │
   │  REQUESTED? │    │  NOTES     │    │  TREATMENT?  │
   └──────┬──────┘    │  REFERENCED?│    └──────┬──────┘
          │           └──────┬──────┘           │
          │                  │                  │
          ▼                  ▼                  ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │  YES ──►    │    │  YES ──►    │    │  YES ──►    │
   │  Generate   │    │  Generate   │    │  Generate   │
   │  HHE-204    │    │  GSB Soil   │    │  HHE-300A   │
   │             │    │  Notes      │    │             │
   └─────────────┘    └─────────────┘    └─────────────┘
          │                   │                  │
          └───────────────────┼──────────────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  Include in Email │
                    │  Package           │
                    └────────────────────┘
```

---

## Page Variant Selection

```
┌─────────────────────────────────────────────────────────┐
│              SYSTEM TYPE DECISION                        │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
   ┌─────────────────┐          ┌─────────────────────────┐
   │    STANDARD     │          │    ENGINEERED /         │
   │                 │          │    ALTERNATIVE          │
   │  Components:    │          │                         │
   │  1-6 only       │          │  Components:            │
   │                 │          │  7, 8, or 9 selected    │
   │  Page 3: GRID   │          │                         │
   │    (hand-fill)  │          │  Page 7: BLANK          │
   │                 │          │    (AutoCAD)            │
   │  Page 4: GRID    │          │                         │
   │    (hand-fill)  │          │  Page 8: BLANK          │
   │                 │          │    (AutoCAD)            │
   └─────────────────┘          └─────────────────────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Drawing placed │
                 │  on correct     │
                 │  pages          │
                 └─────────────────┘
```

---

## Trigger Summary

| Step | Action | Condition |
|------|--------|-----------|
| 1 | Form submitted | Manual |
| 2 | Row created in sheet | Automatic |
| 3 | Hermes triggered | Webhook or cron |
| 4 | Read row data | On trigger |
| 5 | Get sketch from Drive | On trigger |
| 6a | Fill PDF fields | Always |
| 6b | Generate AutoCAD | Always |
| 6c | Select pages | Based on system type |
| 6d | Generate HHE-204 | Variance requested |
| 6d | Generate GSB Notes | Soil notes referenced |
| 6d | Generate HHE-300A | Pre-treatment system |
| 6e | Merge PDFs | Always |
| 7 | Send email | Always |
