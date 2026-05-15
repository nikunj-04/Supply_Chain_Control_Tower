"""PDF Invoice Generator for Accessorial Charges."""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os
from typing import Dict, Any


class InvoicePDFGenerator:
    """Generate PDF invoices for accessorial charges."""
    
    def __init__(self, output_dir: str = "invoices"):
        """Initialize PDF generator with output directory."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#27ae60'),
            fontName='Helvetica-Bold',
            spaceAfter=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            fontName='Helvetica-Bold',
            spaceAfter=10,
            spaceBefore=15
        ))
    
    def generate_accessorial_invoice(self, charge_data: Dict[str, Any], invoice_number: str) -> str:
        """
        Generate PDF invoice for accessorial charge.
        
        Args:
            charge_data: Dictionary containing charge information
            invoice_number: Unique invoice number
            
        Returns:
            Path to generated PDF file
        """
        filename = f"{invoice_number}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Add company header
        elements.extend(self._create_header())
        elements.append(Spacer(1, 0.3*inch))
        
        # Add invoice title and number
        elements.append(Paragraph("INVOICE", self.styles['InvoiceTitle']))
        elements.append(Paragraph(f"Invoice #: {invoice_number}", self.styles['Normal']))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Add billing information
        elements.extend(self._create_billing_info(charge_data))
        elements.append(Spacer(1, 0.3*inch))
        
        # Add charge details table
        elements.extend(self._create_charge_table(charge_data))
        elements.append(Spacer(1, 0.3*inch))
        
        # Add payment terms
        elements.extend(self._create_payment_terms(charge_data))
        elements.append(Spacer(1, 0.3*inch))
        
        # Add footer
        elements.extend(self._create_footer())
        
        # Build PDF
        doc.build(elements)
        
        return filepath
    
    def _create_header(self):
        """Create company header section."""
        elements = []
        
        elements.append(Paragraph("Ecommerce Supply Chain Control Tower", self.styles['CompanyName']))
        elements.append(Paragraph("123 Logistics Avenue, Suite 500", self.styles['Normal']))
        elements.append(Paragraph("Chicago, IL 60601", self.styles['Normal']))
        elements.append(Paragraph("Phone: (555) 123-4567 | Email: billing@ecommerce.com", self.styles['Normal']))
        
        return elements
    
    def _create_billing_info(self, charge_data: Dict[str, Any]):
        """Create billing information section."""
        elements = []
        
        # Create two-column layout for Bill To and Charge Details
        data = [
            [Paragraph("<b>BILL TO:</b>", self.styles['Normal']), 
             Paragraph("<b>CHARGE DETAILS:</b>", self.styles['Normal'])],
            [Paragraph(f"{charge_data.get('carrier', 'N/A')}", self.styles['Normal']),
             Paragraph(f"Charge ID: {charge_data.get('charge_id', 'N/A')}", self.styles['Normal'])],
            [Paragraph("123 Carrier Street", self.styles['Normal']),
             Paragraph(f"Shipment: {charge_data.get('shipment_id', 'N/A')}", self.styles['Normal'])],
            [Paragraph("City, ST 12345", self.styles['Normal']),
             Paragraph(f"Occurrence: {charge_data.get('occurrence_date', 'N/A')}", self.styles['Normal'])],
        ]
        
        table = Table(data, colWidths=[3*inch, 3*inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_charge_table(self, charge_data: Dict[str, Any]):
        """Create charge details table."""
        elements = []
        
        elements.append(Paragraph("CHARGES", self.styles['SectionHeader']))
        
        # Format charge type
        charge_type = charge_data.get('charge_type', 'N/A')
        charge_type_display = charge_type.replace('_', ' ').title()
        
        # Table data
        data = [
            ['Description', 'Quantity', 'Rate', 'Amount'],
            [
                f"{charge_type_display} Charge\n{charge_data.get('reason', 'Delay/service issue')}",
                '1',
                f"${charge_data.get('amount', 0):.2f}",
                f"${charge_data.get('amount', 0):.2f}"
            ]
        ]
        
        # Add subtotal and total
        amount = charge_data.get('amount', 0)
        data.append(['', '', 'Subtotal:', f"${amount:.2f}"])
        data.append(['', '', 'Tax (0%):', '$0.00'])
        data.append(['', '', 'TOTAL:', f"${amount:.2f}"])
        
        table = Table(data, colWidths=[3*inch, 1*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('GRID', (0, 0), (-1, -4), 1, colors.grey),
            ('LINEBELOW', (0, -3), (-1, -3), 1, colors.grey),
            
            # Total row
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('LINEABOVE', (2, -1), (-1, -1), 2, colors.HexColor('#2c3e50')),
            ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor('#ecf0f1')),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_payment_terms(self, charge_data: Dict[str, Any]):
        """Create payment terms section."""
        elements = []
        
        elements.append(Paragraph("PAYMENT TERMS", self.styles['SectionHeader']))
        elements.append(Paragraph("• Payment Due: Net 30 days from invoice date", self.styles['Normal']))
        elements.append(Paragraph("• Please include invoice number with payment", self.styles['Normal']))
        elements.append(Paragraph("• Wire transfer or ACH payment accepted", self.styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Add notes if charge has additional details
        if charge_data.get('age_days', 0) > 30:
            elements.append(Paragraph(
                f"<b>Note:</b> This charge has been outstanding for {charge_data.get('age_days')} days.",
                self.styles['Normal']
            ))
        
        return elements
    
    def _create_footer(self):
        """Create invoice footer."""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph(
            "Thank you for your business! Questions? Contact us at billing@ecommerce.com or (555) 123-4567",
            footer_style
        ))
        
        return elements
