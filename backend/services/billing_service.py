"""Billing service for processing accessorial charges."""
from datetime import datetime, timedelta
from typing import Dict, Any
import os

from logger import setup_logger
from utils.pdf_generator import InvoicePDFGenerator
from models.billing_models import get_billing_session, Invoice, BillingLineItem
from services.dashboard_service import dashboard_service

logger = setup_logger(__name__)


class BillingService:
    """Service for processing billing operations."""
    
    def __init__(self):
        """Initialize billing service."""
        self.pdf_generator = InvoicePDFGenerator(output_dir="invoices")
        self.invoice_counter = 10000  # Start invoice numbers at 10000
    
    def _generate_invoice_number(self) -> str:
        """Generate unique invoice number."""
        self.invoice_counter += 1
        return f"INV-{datetime.now().strftime('%Y%m')}-{self.invoice_counter}"
    
    async def process_accessorial_charge(self, charge_id: str) -> Dict[str, Any]:
        """
        Process an accessorial charge by creating invoice and generating PDF.
        
        Args:
            charge_id: The ID of the charge to process
            
        Returns:
            Dictionary containing invoice details and download URL
        """
        logger.info(f"Processing accessorial charge: {charge_id}")
        
        # Get all accessorial charges from dashboard service
        charges_data = dashboard_service.get_accessorial_charges()
        
        # Find the specific charge
        charge = None
        for opp in charges_data.get('opportunities', []):
            if opp.get('charge_id') == charge_id:
                charge = opp
                break
        
        if not charge:
            raise ValueError(f"Charge {charge_id} not found")
        
        # Check if already has an invoice (even if status is billed)
        if charge.get('invoice_number') and charge.get('download_url'):
            # Already has an invoice, return existing invoice info
            return {
                'success': True,
                'invoice_number': charge.get('invoice_number'),
                'charge_id': charge_id,
                'amount': charge.get('amount'),
                'invoice_date': None,
                'due_date': None,
                'download_url': charge.get('download_url'),
                'status': 'billed',
                'message': f"Invoice {charge.get('invoice_number')} already exists"
            }
        
        # Check if status is not pending (but no invoice exists)
        if charge.get('status') not in ['pending', 'billed', 'under_review']:
            raise ValueError(f"Charge {charge_id} cannot be billed with status: {charge.get('status')}")
        
        # Generate invoice number
        invoice_number = self._generate_invoice_number()
        
        # Prepare charge data for PDF
        charge_data = {
            'charge_id': charge.get('charge_id'),
            'charge_type': charge.get('charge_type'),
            'amount': charge.get('amount'),
            'carrier': charge.get('carrier', 'N/A'),
            'shipment_id': charge.get('shipment_id', 'N/A'),
            'occurrence_date': charge.get('occurrence_date'),
            'age_days': charge.get('age_days'),
            'reason': charge.get('reason', 'Service delay or detention')
        }
        
        # Generate PDF invoice
        logger.info(f"Generating PDF invoice: {invoice_number}")
        pdf_path = self.pdf_generator.generate_accessorial_invoice(
            charge_data=charge_data,
            invoice_number=invoice_number
        )
        
        # Create invoice record in database
        logger.info(f"Creating invoice record in database: {invoice_number}")
        invoice_record = self._create_invoice_record(
            invoice_number=invoice_number,
            charge_data=charge_data
        )
        
        # Update charge status (in memory for now - would update database in production)
        charge['status'] = 'billed'
        charge['invoice_number'] = invoice_number
        charge['billed_date'] = datetime.now().isoformat()
        
        # Get filename from path
        filename = os.path.basename(pdf_path)
        
        # Return response
        return {
            'success': True,
            'invoice_number': invoice_number,
            'charge_id': charge_id,
            'amount': charge_data['amount'],
            'invoice_date': datetime.now().isoformat(),
            'due_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'download_url': f"/invoices/{filename}",
            'status': 'billed',
            'message': f'Invoice {invoice_number} created successfully'
        }
    
    def _create_invoice_record(self, invoice_number: str, charge_data: Dict[str, Any]) -> Invoice:
        """
        Create invoice record in billing database.
        
        Args:
            invoice_number: Generated invoice number
            charge_data: Charge information
            
        Returns:
            Created Invoice object
        """
        from config import settings
        
        session = get_billing_session(settings.billing_db_path)
        
        try:
            # Create invoice record
            invoice = Invoice(
                invoice_id=invoice_number,
                customer_id=charge_data.get('carrier', 'UNKNOWN').replace(' ', '_').upper(),
                customer_name=charge_data.get('carrier', 'Unknown Carrier'),
                order_id=charge_data.get('shipment_id', 'N/A'),
                invoice_date=datetime.now(),
                due_date=datetime.now() + timedelta(days=30),
                status='pending',
                subtotal=charge_data.get('amount', 0),
                tax=0.0,
                total=charge_data.get('amount', 0),
                amount_paid=0.0,
                balance=charge_data.get('amount', 0)
            )
            
            session.add(invoice)
            
            # Create line item
            line_item = BillingLineItem(
                invoice_id=invoice_number,
                service_type='accessorial_charge',
                description=f"{charge_data.get('charge_type', '').replace('_', ' ').title()} - {charge_data.get('charge_id')}",
                quantity=1.0,
                unit_price=charge_data.get('amount', 0),
                line_total=charge_data.get('amount', 0)
            )
            
            session.add(line_item)
            session.commit()
            
            logger.info(f"Invoice record created successfully: {invoice_number}")
            return invoice
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating invoice record: {e}")
            raise
        finally:
            session.close()
