"""
AWS Lambda Handler for PG&E Bill Split Automation

This function replaces the local automation script and runs on AWS Lambda
triggered by EventBridge on the 5th of each month at 9:00 AM PST.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler function
    
    Args:
        event: EventBridge event or manual trigger
        context: Lambda context object
        
    Returns:
        Response dictionary with status and results
    """
    
    logger.info("=== PG&E Bill Split Automation - AWS Lambda ===")
    logger.info(f"Request ID: {context.aws_request_id}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Event: {json.dumps(event, default=str)}")
    
    try:
        # Import our automation logic
        from bill_automation import run_monthly_automation
        
        # Check if this is a test run
        test_mode = event.get('test_mode', False)
        if test_mode:
            logger.info("Running in TEST MODE")
        
        # Run the automation
        result = run_monthly_automation(test_mode=test_mode)
        
        # Return success response
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Automation completed successfully',
                'timestamp': datetime.now().isoformat(),
                'request_id': context.aws_request_id,
                'result': result
            })
        }
        
        logger.info(f"Automation completed successfully: {result}")
        return response
        
    except Exception as e:
        error_msg = f"Automation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Return error response
        response = {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': error_msg,
                'timestamp': datetime.now().isoformat(),
                'request_id': context.aws_request_id
            })
        }
        
        return response


def health_check_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Health check endpoint for monitoring
    """
    return {
        'statusCode': 200,
        'body': json.dumps({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    }


def manual_trigger_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Manual trigger for testing automation outside of schedule
    """
    
    logger.info("Manual trigger received")
    
    # Force test mode for manual triggers unless explicitly disabled
    test_mode = event.get('test_mode', True)
    
    # Create modified event for main handler
    modified_event = {
        **event,
        'test_mode': test_mode,
        'manual_trigger': True
    }
    
    return lambda_handler(modified_event, context)