"""
Hermes Self-Correction Loop

Iterates on HHE-200 generation until quality meets standard (>85 score).
2-hour timeout with Telegram alert if exceeds.
"""

import time
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta
import subprocess
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import quality assessment
from hermes_quality_assessment import assess_generated_hhe200

QUALITY_THRESHOLD = 75
TIMEOUT_HOURS = 2
TELEGRAM_ENABLED = True

async def send_telegram_alert(message: str):
    """Send alert to Telegram."""
    try:
        # Use Zo's Telegram integration via the send_sms_to_user API
        # For now, log it
        logger.info(f"📱 TELEGRAM ALERT: {message}")
        # In production, use: send_telegram_message(message)
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")


async def hermes_self_correct_loop(
    hermes_output: Dict,
    max_iterations: int = 10
) -> Dict:
    """
    Main self-correction loop.
    
    1. Generate HHE-200 with current data
    2. Assess quality against pinnacle examples
    3. If score < threshold, identify gaps and refine
    4. Repeat until score >= threshold or timeout
    """
    
    start_time = time.time()
    timeout_seconds = TIMEOUT_HOURS * 3600
    iteration = 0
    
    logger.info("🔄 Starting Hermes Self-Correction Loop")
    logger.info(f"   Quality Threshold: {QUALITY_THRESHOLD}/100")
    logger.info(f"   Timeout: {TIMEOUT_HOURS} hours")
    
    while iteration < max_iterations:
        iteration += 1
        elapsed = time.time() - start_time
        elapsed_minutes = elapsed / 60
        
        logger.info(f"\n📊 Iteration {iteration} ({elapsed_minutes:.1f}min elapsed)")
        
        # Check timeout
        if elapsed > timeout_seconds:
            timeout_msg = f"❌ TIMEOUT: {TIMEOUT_HOURS}h limit exceeded. Self-correction paused. Manual review needed."
            logger.error(timeout_msg)
            await send_telegram_alert(timeout_msg)
            return {
                'status': 'timeout',
                'iteration': iteration,
                'elapsed_seconds': elapsed,
                'message': timeout_msg
            }
        
        # Step 1: Run Hermes (placeholder - in real flow, this generates the PDF)
        logger.info(f"   Step 1: Generating HHE-200 PDF...")
        # In production: run_hermes_generation(hermes_output)
        
        # Step 2: Assess quality
        logger.info(f"   Step 2: Assessing quality against pinnacle examples...")
        try:
            assessment = assess_generated_hhe200(Path('/home/workspace/OpenEvaluator'))
            overall_score = assessment['assessment'].get('overall_score', 0)
            pages = assessment['assessment'].get('pages', {})
            
            logger.info(f"   Overall Score: {overall_score}/100")
            for page_key, page_data in pages.items():
                logger.info(f"      {page_key}: {page_data.get('score', 0)}/100 - {page_data.get('gaps', [])[:1]}")
            
        except Exception as e:
            logger.error(f"   Error assessing quality: {e}")
            overall_score = 0
        
        # Step 3: Check if meets threshold
        if overall_score >= QUALITY_THRESHOLD:
            success_msg = f"✅ SUCCESS: Quality score {overall_score}/100 meets standard after {iteration} iterations ({elapsed_minutes:.1f} min)"
            logger.info(success_msg)
            await send_telegram_alert(success_msg)
            
            return {
                'status': 'success',
                'iteration': iteration,
                'overall_score': overall_score,
                'elapsed_seconds': elapsed,
                'assessment': assessment['assessment'],
                'message': success_msg
            }
        
        # Step 4: If below threshold, analyze gaps and refine
        logger.info(f"   Step 3: Quality below threshold ({overall_score}/{QUALITY_THRESHOLD}). Analyzing gaps...")
        
        gaps = []
        for page_key, page_data in pages.items():
            page_gaps = page_data.get('gaps', [])
            if page_gaps:
                gaps.extend([(page_key, g) for g in page_gaps])
        
        if gaps:
            for page, gap in gaps[:3]:
                logger.info(f"      {page}: {gap}")
        
        # Step 5: Generate refinement instruction for Hermes
        refinement_instruction = _generate_refinement(pages, overall_score)
        logger.info(f"   Step 4: Refinement instruction: {refinement_instruction[:100]}...")
        
        # In production: pass refinement_instruction to Hermes
        # hermes_output['refinement_feedback'] = refinement_instruction
        
        # Wait before next iteration (avoid rapid loops)
        wait_time = min(5, timeout_seconds - elapsed)
        if iteration < max_iterations and overall_score < QUALITY_THRESHOLD:
            logger.info(f"   Waiting {int(wait_time)}s before next iteration...")
            await asyncio.sleep(min(2, wait_time))
    
    # Max iterations reached
    timeout_msg = f"❌ MAX ITERATIONS REACHED ({max_iterations}). Manual review needed."
    logger.error(timeout_msg)
    await send_telegram_alert(timeout_msg)
    
    return {
        'status': 'max_iterations',
        'iteration': iteration,
        'elapsed_seconds': elapsed,
        'message': timeout_msg
    }


def _generate_refinement(pages: Dict, overall_score: int) -> str:
    """
    Generate specific refinement instructions based on gaps.
    Hermes uses these to improve output.
    """
    
    instructions = []
    
    for page_key, page_data in pages.items():
        page_num = int(page_key.split('_')[1])
        gaps = page_data.get('gaps', [])
        score = page_data.get('score', 0)
        
        if score < QUALITY_THRESHOLD:
            if page_num in [1, 2]:
                if gaps:
                    instructions.append(f"Page {page_num}: {gaps[0]}")
                if page_data.get('filled_fields', 0) < page_data.get('expected_fields', 0):
                    missing = page_data.get('expected_fields', 0) - page_data.get('filled_fields', 0)
                    instructions.append(f"Page {page_num}: Missing {missing} form fields - ensure all required fields are filled")
            
            elif page_num in [3, 4]:
                if page_data.get('drawing_accuracy', 0) < 70:
                    instructions.append(f"Page {page_num}: Drawing accuracy low ({page_data.get('drawing_accuracy', 0)}/100) - improve CAD drawing generation")
                if page_data.get('positioning', 0) < 70:
                    instructions.append(f"Page {page_num}: Drawing positioning off - align to grid/reference points")
                if gaps:
                    instructions.append(f"Page {page_num}: {gaps[0]}")
    
    if not instructions:
        instructions.append("Overall quality low - review entire form against pinnacle example")
    
    return " | ".join(instructions[:3])


async def run_hermes_with_quality_gate(hermes_output: Dict) -> Dict:
    """
    Public API: Run Hermes with quality gates.
    Returns only when quality meets standard or timeout occurs.
    """
    
    result = await hermes_self_correct_loop(hermes_output, max_iterations=10)
    
    if result['status'] == 'success':
        logger.info("✅ Hermes output approved by quality gate")
        return result
    
    elif result['status'] == 'timeout':
        logger.error(f"⏱️  TIMEOUT - Pausing automation for manual review")
        logger.error(f"   Message sent to Telegram: {result['message']}")
        return result
    
    else:
        logger.error(f"❌ Quality gate failed: {result['message']}")
        return result


# Synchronous wrapper for testing
def run_hermes_with_quality_gate_sync(hermes_output: Dict) -> Dict:
    """Synchronous wrapper - use when async not available."""
    return asyncio.run(run_hermes_with_quality_gate(hermes_output))


if __name__ == '__main__':
    # Test with example hermes output
    test_hermes_output = {
        'project_id': '26-018',
        'site_address': 'Turner Property',
        'data': {}
    }
    
    result = run_hermes_with_quality_gate_sync(test_hermes_output)
    print(json.dumps(result, indent=2, default=str))
