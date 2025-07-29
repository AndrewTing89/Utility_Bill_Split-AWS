#!/usr/bin/env python3
"""
Comprehensive audit of template variables vs master schema
"""

import os
import re
from pathlib import Path

def audit_template_variables():
    """Audit all template files for variable consistency"""
    
    # Master schema from Flask app
    master_schema = {
        'bill.id',           # not bill.bill_id
        'bill.amount',       # not bill.bill_amount
        'bill.due_date',
        'bill.roommate_portion',
        'bill.my_portion', 
        'bill.processed_date',
        'bill.status',
        'bill.email_body',
        'bill.pdf_generated',
        'bill.pdf_sent',
        'bill.venmo_sent',
        'bill.email_subject',
        'bill.email_date',
        'bill.email_id',
        'bill.venmo_link',
        'bill.notes'
    }
    
    # Common wrong patterns to check for
    wrong_patterns = [
        'bill.bill_amount',  # should be bill.amount
        'bill.bill_id',      # should be bill.id  
        'bill_amount',       # in Jinja filters
        'bill_id'            # in loops etc
    ]
    
    templates_dir = Path('/Users/ndting/Desktop/PGE Split AWS/web-ui/templates')
    issues = []
    
    print("🔍 COMPREHENSIVE TEMPLATE VARIABLE AUDIT")
    print("=" * 50)
    
    for template_file in templates_dir.glob('*.html'):
        print(f"\n📄 Checking: {template_file.name}")
        
        with open(template_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for wrong patterns
        for pattern in wrong_patterns:
            matches = []
            for i, line in enumerate(lines, 1):
                if pattern in line:
                    matches.append((i, line.strip()))
            
            if matches:
                issues.append({
                    'file': template_file.name,
                    'pattern': pattern,
                    'matches': matches
                })
                print(f"  ❌ Found '{pattern}':")
                for line_num, line_content in matches:
                    print(f"    Line {line_num}: {line_content}")
        
        # Check for bill.* patterns to catch any we missed
        bill_patterns = re.findall(r'bill\.[a-zA-Z_]+', content)
        unknown_patterns = set(bill_patterns) - master_schema
        
        if unknown_patterns:
            print(f"  ⚠️  Unknown bill patterns: {unknown_patterns}")
            for pattern in unknown_patterns:
                issues.append({
                    'file': template_file.name,
                    'pattern': f'UNKNOWN: {pattern}',
                    'matches': [(0, 'Found in file')]
                })
    
    print(f"\n📊 SUMMARY")
    print(f"Total issues found: {len(issues)}")
    
    if issues:
        print("\n🔧 FIXES NEEDED:")
        for issue in issues:
            print(f"  {issue['file']}: {issue['pattern']} ({len(issue['matches'])} occurrences)")
    else:
        print("✅ All templates match master schema!")
    
    return issues

if __name__ == "__main__":
    audit_template_variables()