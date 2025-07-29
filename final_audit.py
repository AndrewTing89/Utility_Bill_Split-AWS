#!/usr/bin/env python3
"""
Final comprehensive audit - excluding correct Flask route parameters
"""

import os
import re
from pathlib import Path

def final_audit():
    """Final audit excluding correct Flask route patterns"""
    
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
    
    # Wrong patterns (excluding correct Flask route params)
    wrong_patterns = [
        'bill.bill_amount',  # should be bill.amount
        'bill.bill_id',      # should be bill.id  
    ]
    
    # Patterns that are OK in specific contexts
    ok_in_context = [
        'bill_id=bill.id',   # Flask route parameter - OK
        'bill_amount',       # only wrong in Jinja filters/templates
    ]
    
    templates_dir = Path('/Users/ndting/Desktop/PGE Split AWS/web-ui/templates')
    real_issues = []
    
    print("🔍 FINAL COMPREHENSIVE AUDIT")
    print("=" * 40)
    
    for template_file in templates_dir.glob('*.html'):
        print(f"\n📄 {template_file.name}")
        
        with open(template_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for definite wrong patterns
        for pattern in wrong_patterns:
            matches = []
            for i, line in enumerate(lines, 1):
                if pattern in line:
                    matches.append((i, line.strip()))
            
            if matches:
                real_issues.append({
                    'file': template_file.name,
                    'pattern': pattern,
                    'matches': matches
                })
                print(f"  ❌ {pattern}:")
                for line_num, line_content in matches:
                    print(f"    Line {line_num}: {line_content}")
        
        # Check for bill_amount in wrong contexts (not in Flask routes)
        for i, line in enumerate(lines, 1):
            if 'bill_amount' in line and 'bill_id=' not in line:
                # This is likely a Jinja template issue
                if 'sum(attribute=' in line or 'format(' in line:
                    real_issues.append({
                        'file': template_file.name,
                        'pattern': 'bill_amount (in Jinja)',
                        'matches': [(i, line.strip())]
                    })
                    print(f"  ❌ bill_amount in Jinja:")
                    print(f"    Line {i}: {line.strip()}")
        
        # Check for unknown bill.* patterns
        bill_patterns = re.findall(r'bill\.[a-zA-Z_]+', content)
        unknown_patterns = set(bill_patterns) - master_schema
        
        if unknown_patterns:
            print(f"  ⚠️  Unknown: {unknown_patterns}")
            for pattern in unknown_patterns:
                real_issues.append({
                    'file': template_file.name,
                    'pattern': f'UNKNOWN: {pattern}',
                    'matches': [(0, 'Found in file')]
                })
        else:
            print("  ✅ All bill.* patterns match schema")
    
    print(f"\n📊 FINAL RESULTS")
    print(f"Real issues requiring fixes: {len(real_issues)}")
    
    if real_issues:
        print("\n🔧 REMAINING FIXES NEEDED:")
        for issue in real_issues:
            print(f"  {issue['file']}: {issue['pattern']}")
            return False
    else:
        print("✅ ALL TEMPLATES ARE CONSISTENT WITH MASTER SCHEMA!")
        return True

if __name__ == "__main__":
    success = final_audit()
    exit(0 if success else 1)