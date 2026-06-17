# Hermes Quality Gate System

## Overview

The Hermes Quality Gate ensures HHE-200 PDFs meet production standards before delivery. It uses a **self-correcting loop** that:

1. **Compares** generated output against pinnacle example PDFs
2. **Scores** quality across form filling, drawing accuracy, and positioning
3. **Iterates** with refinement instructions until quality ≥ 85/100
4. **Alerts** via Telegram if iteration exceeds 2 hours
5. **Pauses** automation for manual review if timeout is reached

## Pinnacle Examples

The quality standard is defined by the **26-018** example PDFs in `/OpenEvaluator/example/`:

```
26-018 PG1 (1).pdf  - Applicant Information (filled correctly)
26-018 PG2 (1).pdf  - Site Conditions & Soil Data (filled correctly)
26-018 PG3 (1).pdf  - Site Plan with CAD drawing (accurate positioning)
26-018 PG4 (1).pdf  - Cross-Section with CAD drawing (accurate positioning)
```

## Quality Scoring

### Pages 1-2 (Form Fields)
- **Expected Fields**: NAME, ADDRESS, CITY, STATE, ZIP, PHONE, EMAIL, SITE EVALUATOR, SOIL TYPE, SLOPE, etc.
- **Scoring**: % of fields correctly filled
- **Weight**: 70% of page score

### Pages 3-4 (CAD Drawings)
- **Drawing Accuracy**: Lines, dimensions, grid positioning match example (0-100)
- **Positioning**: Elements aligned to grid reference points (0-100)
- **Weight**: 70% of page score

### Overall Score
- **Threshold**: ≥ 95/100 = PASS
- **85-94/100** = Minor gaps, acceptable with review
- **70-84/100** = Significant rework needed
- **< 60/100** = Full revision required

## Self-Correction Loop

```
Iteration 1
├─ Generate HHE-200 PDF
├─ Assess quality (compare to examples)
├─ Score: 72/100 (below threshold)
├─ Identify gaps:
│  ├─ Page 1: Missing 2 form fields
│  ├─ Page 3: Drawing positioning off by 0.5 inches
│  └─ Page 4: Cross-section lines misaligned
└─ Pass refinement feedback to Hermes

Iteration 2
├─ Hermes refines form filling logic
├─ Regenerate CAD drawings with corrected positioning
├─ Assess quality again
├─ Score: 88/100 ✅ PASS
└─ Proceed to PDF output

✅ SUCCESS after 2 iterations (8 minutes)
```

## Timeout & Alerts

**If iterations exceed 2 hours:**

1. Automation pauses immediately
2. Telegram alert sent:
   ```
   ⏱️ HHE-200 Quality Gate Timeout
   Project: 26-018
   Time Elapsed: 2h 0min
   Iterations: 15
   Last Score: 78/100
   Status: PAUSED FOR MANUAL REVIEW
   ```
3. Manual review required before proceeding

## Integration with OpenEvaluator

### Step-by-Step Flow

```
1. Google Sheet Submission (Row 2)
   ↓
2. Extract data → Pass to Hermes_output
   ↓
3. [HERMES QUALITY GATE CHECKPOINT]
   ├─ Run self-correction loop
   ├─ Assess quality vs examples
   ├─ Iterate with feedback (max 2 hours)
   └─ Return: Score ≥85 or TIMEOUT
   ↓
4. If PASS: Generate CAD drawings
   ↓
5. Fill HHE-200 form (all 4 pages)
   ↓
6. Output PDF + supporting documents
   ↓
7. Email to site evaluator
```

## Running the Test

```bash
cd /home/workspace/OpenEvaluator
python3 test_harness_with_quality_gate.py
```

### Expected Output

```
📋 Step 1: Loading test data from Google Sheet
✓ Loaded project: 26-018

🤖 Step 2: Running Hermes with Quality Gate
✓ Iteration 1: Score 72/100 (gap: Page 1 - Missing 2 fields)
✓ Iteration 2: Score 88/100 ✅ PASS

📐 Step 3: Generating CAD Drawings
✓ Site Plan Generated
✓ Cross-Section Generated

📝 Step 4: Filling HHE-200 Form
✓ Pages 1-4 complete

✨ Step 5: Final Quality Assessment
✓ Score: 88/100

✅ TEST COMPLETE
```

## Configuring Alerts

Telegram alerts are sent via Zo's integration:

1. Go to [Zo Settings > Channels](/?t=settings&s=channels)
2. Ensure Telegram is connected to your account
3. Hermes will automatically send timeout alerts to your Telegram

## Files

- `hermes_quality_assessment.py` - Quality scoring engine
- `hermes_self_correction.py` - Self-correction loop with timeout
- `test_harness_with_quality_gate.py` - Full end-to-end test

## Debugging

### If quality is stuck < 85/100

1. Check `/home/workspace/OpenEvaluator/example/` for pinnacle PDFs
2. Review `hermes_quality_assessment.py` gap analysis
3. Verify Hermes data extraction is correct
4. Consider manual refinement of pinnacle examples if standard is too strict

### If timeout is triggered too often

1. Increase `TIMEOUT_HOURS` in `hermes_self_correction.py` (default: 2)
2. Increase `max_iterations` in loop (default: 10)
3. Review Hermes generation time per iteration

## Production Readiness

✅ Quality gate system ready for production when:
- ✓ All pinnacle example PDFs are in `/OpenEvaluator/example/`
- ✓ Telegram alerts are configured
- ✓ Test harness passes with score ≥ 85/100
- ✓ Hermes integration is complete

---
**Last Updated**: May 31, 2026
**Status**: Ready for Integration
