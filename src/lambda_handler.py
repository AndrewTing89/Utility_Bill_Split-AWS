"""
AWS Lambda handler for PG&E Bill Automation
"""

import json
import logging
import os
from bill_automation import run_monthly_automation

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Main Lambda handler function
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        Response with status and results
    """
    try:
        logger.info(f"Lambda invoked with event: {json.dumps(event)}")
        
        # Determine test mode from event or environment
        test_mode = event.get('test_mode', os.environ.get('TEST_MODE', 'false').lower() == 'true')
        
        # Run the automation
        results = run_monthly_automation(test_mode=test_mode)
        
        # Log results
        logger.info(f"Automation results: {json.dumps(results)}")
        
        # Return successful response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Automation completed successfully',
                'results': results
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Automation failed',
                'error': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }