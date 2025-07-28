"""
PDF Generator adapted for AWS Lambda

This module generates professional-looking PDF bills using ReportLab
optimized for the Lambda environment with S3 integration.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

class PDFGeneratorAWS:
    """PDF generator optimized for AWS Lambda"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.darkgreen
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8
        ))
        
        # Small text style
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey
        ))
    
    def generate_pdf(self, bill_data: Dict) -> Optional[bytes]:
        """
        Generate PDF from bill data
        
        Args:
            bill_data: Dictionary containing bill information
            
        Returns:
            PDF content as bytes or None if failed
        """
        try:
            # Create BytesIO buffer for PDF
            buffer = BytesIO()
            
            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build PDF content
            story = []
            
            # Title
            title = Paragraph("PG&E Bill Split Summary", self.styles['CustomTitle'])
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Email header information (to make it look official)
            story.extend(self._create_email_header(bill_data))
            story.append(Spacer(1, 15))
            
            # Bill summary section
            story.extend(self._create_bill_summary(bill_data))
            story.append(Spacer(1, 15))
            
            # Split calculation section
            story.extend(self._create_split_calculation(bill_data))
            story.append(Spacer(1, 15))
            
            # Payment instructions
            story.extend(self._create_payment_instructions(bill_data))
            story.append(Spacer(1, 15))
            
            # Verification section
            story.extend(self._create_verification_section(bill_data))
            
            # Footer
            story.append(Spacer(1, 20))
            story.extend(self._create_footer())
            
            # Build the PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated PDF for bill due {bill_data.get('due_date', 'unknown')}")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return None
    
    def _create_email_header(self, bill_data: Dict) -> list:
        """Create email header section to make it look official"""
        elements = []
        
        # Create email header table
        header_data = [
            ['From:', 'DoNotReply@billpay.pge.com'],
            ['To:', bill_data.get('recipient_email', 'your-email@example.com')],
            ['Subject:', 'Your PG&E bill is ready'],
            ['Date:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Bill Period:', self._get_bill_period(bill_data)]
        ]
        
        header_table = Table(header_data, colWidths=[1*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        
        return elements
    
    def _create_bill_summary(self, bill_data: Dict) -> list:
        """Create bill summary section"""
        elements = []
        
        # Section header
        header = Paragraph("📧 PG&E Bill Summary", self.styles['CustomHeader'])
        elements.append(header)
        
        # Bill details table
        bill_details = [
            ['Bill Amount:', f"${bill_data.get('amount', 0):.2f}"],
            ['Due Date:', bill_data.get('due_date', 'Unknown')],
            ['Account:', 'Pacific Gas & Electric'],
            ['Bill Date:', self._get_bill_date(bill_data)],
            ['Status:', 'Ready for Payment']
        ]
        
        details_table = Table(bill_details, colWidths=[2*inch, 2*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        elements.append(details_table)
        
        return elements
    
    def _create_split_calculation(self, bill_data: Dict) -> list:
        """Create split calculation section"""
        elements = []
        
        # Section header
        header = Paragraph("💰 Roommate Split Calculation", self.styles['CustomHeader'])
        elements.append(header)
        
        # Split details
        roommate_portion = bill_data.get('roommate_portion', 0)
        my_portion = bill_data.get('my_portion', 0)
        total_amount = bill_data.get('amount', 0)
        
        # Calculate percentages
        roommate_pct = (roommate_portion / total_amount * 100) if total_amount > 0 else 0
        my_pct = (my_portion / total_amount * 100) if total_amount > 0 else 0
        
        split_data = [
            ['Description', 'Amount', 'Percentage'],
            ['Roommate Portion', f"${roommate_portion:.2f}", f"{roommate_pct:.1f}%"],
            ['My Portion', f"${my_portion:.2f}", f"{my_pct:.1f}%"],
            ['', '', ''],
            ['Total Bill', f"${total_amount:.2f}", '100.0%']
        ]
        
        split_table = Table(split_data, colWidths=[2.5*inch, 1*inch, 1*inch])
        split_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('GRID', (0, -1), (-1, -1), 1, colors.darkgreen),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(split_table)
        
        return elements
    
    def _create_payment_instructions(self, bill_data: Dict) -> list:
        """Create payment instructions section"""
        elements = []
        
        # Section header
        header = Paragraph("💳 Payment Instructions", self.styles['CustomHeader'])
        elements.append(header)
        
        # Instructions text
        roommate_portion = bill_data.get('roommate_portion', 0)
        
        instructions = [
            f"• Request ${roommate_portion:.2f} from your roommate via Venmo",
            "• Use the Venmo link that was sent to your phone",
            "• Include 'PG&E bill split' in the payment note",
            "• Pay your portion directly to PG&E",
            "• Keep this PDF for your records"
        ]
        
        for instruction in instructions:
            p = Paragraph(instruction, self.styles['CustomBody'])
            elements.append(p)
        
        return elements
    
    def _create_verification_section(self, bill_data: Dict) -> list:
        """Create verification section"""
        elements = []
        
        # Section header
        header = Paragraph("✅ Verification", self.styles['CustomHeader'])
        elements.append(header)
        
        # Verification details
        verification_text = f"""
        This document was automatically generated from your PG&E email notification.
        The original email was received on {datetime.now().strftime('%B %d, %Y')} and 
        processed by the PG&E Bill Split Automation system.
        """
        
        p = Paragraph(verification_text, self.styles['CustomBody'])
        elements.append(p)
        
        # Processing details table
        processing_data = [
            ['Email ID:', bill_data.get('email_id', 'N/A')[:20] + '...'],
            ['Processed:', datetime.now().strftime('%m/%d/%Y %I:%M %p')],
            ['System:', 'PG&E Bill Split Automation v2.0'],
            ['Split Ratio:', '1/3 roommate, 2/3 me']
        ]
        
        proc_table = Table(processing_data, colWidths=[1.5*inch, 3*inch])
        proc_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        elements.append(Spacer(1, 10))
        elements.append(proc_table)
        
        return elements
    
    def _create_footer(self) -> list:
        """Create footer section"""
        elements = []
        
        # Footer line
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        elements.append(Spacer(1, 5))
        
        footer_text = """
        This is an automated summary generated for convenience. 
        Please refer to your original PG&E bill for official payment instructions.
        """
        
        footer = Paragraph(footer_text, self.styles['SmallText'])
        elements.append(footer)
        
        return elements
    
    def _get_bill_period(self, bill_data: Dict) -> str:
        """Get bill period from due date"""
        try:
            due_date = datetime.strptime(bill_data.get('due_date', ''), '%m/%d/%Y')
            # Assume bill period is previous month
            if due_date.month == 1:
                period_month = 12
                period_year = due_date.year - 1
            else:
                period_month = due_date.month - 1
                period_year = due_date.year
            
            period_date = datetime(period_year, period_month, 1)
            return period_date.strftime('%B %Y')
            
        except:
            return "Current Period"
    
    def _get_bill_date(self, bill_data: Dict) -> str:
        """Get bill date (usually a few days before due date)"""
        try:
            due_date = datetime.strptime(bill_data.get('due_date', ''), '%m/%d/%Y')
            # Assume bill date is 10 days before due date
            bill_date = due_date.replace(day=max(1, due_date.day - 10))
            return bill_date.strftime('%m/%d/%Y')
            
        except:
            return datetime.now().strftime('%m/%d/%Y')