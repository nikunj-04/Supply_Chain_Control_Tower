"""
Data Indexer - Indexes data from databases and PDFs into vector store.
Supports all 7 database systems + PDF documents.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import pdfplumber

from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .kpi_indexer import KPIIndexer
from models.billing_models import Invoice
from models.oms_models import Order
from models.tms_models import Shipment
from models.wms_models import Inventory, PickingTask
from models.returns_models import Return
from models.yard_models import DockAppointment
from config import settings

logger = logging.getLogger(__name__)


class DataIndexer:
    """
    Indexes data from all sources into the vector store.
    """
    
    def __init__(self):
        self.embedder = EmbeddingService()
        self.vector_store = VectorStore(dimension=self.embedder.get_dimension())
        
        # Initialize KPI indexer
        self.kpi_indexer = KPIIndexer(self.vector_store, self.embedder)
        
        # Create database engines
        self.engines = {
            'billing': create_engine(f'sqlite:///{settings.billing_db_path}'),
            'oms': create_engine(f'sqlite:///{settings.oms_db_path}'),
            'tms': create_engine(f'sqlite:///{settings.tms_db_path}'),
            'wms': create_engine(f'sqlite:///{settings.wms_db_path}'),
            'returns': create_engine(f'sqlite:///{settings.returns_db_path}'),
            'yard': create_engine(f'sqlite:///{settings.yard_db_path}')
        }
        
        # Create sessions
        self.sessions = {
            name: sessionmaker(bind=engine)()
            for name, engine in self.engines.items()
        }
        
        logger.info("✅ Data indexer initialized")
    
    def index_all(self, load_existing: bool = True):
        """
        Index all data sources.
        
        Args:
            load_existing: Try to load existing index first
        """
        if load_existing and self.vector_store.load("supplychain_full"):
            logger.info("Loaded existing index from disk")
            return
        
        logger.info("Starting full data indexing...")
        
        # Clear existing index
        self.vector_store.clear()
        
        # Index all databases (raw transaction data)
        self.index_billing()
        self.index_oms()
        self.index_tms()
        self.index_wms()
        self.index_returns()
        self.index_yard()
        
        # Index PDFs
        self.index_pdfs()
        
        # *** NEW: Index pre-calculated KPI metrics from dashboards ***
        # This ensures chatbot answers match dashboard displays exactly
        logger.info("Indexing KPI metrics from dashboard service...")
        self.kpi_indexer.index_kpi_metrics()
        
        # Index operational scorecard data
        logger.info("Indexing operational scorecard data...")
        self.kpi_indexer.index_operational_scorecard()
        
        # Index exception management data
        logger.info("Indexing exception management data...")
        self.kpi_indexer.index_exceptions()
        
        # Index additional dashboard summaries
        try:
            self.kpi_indexer.index_dashboard_summaries()
        except Exception as e:
            logger.warning(f"Could not index dashboard summaries: {e}")
        
        # Save to disk
        self.vector_store.save("supplychain_full")
        
        logger.info(f"✅ Full indexing complete ({len(self.vector_store)} documents)")
    
    def index_billing(self):
        """Index all invoices from billing database."""
        logger.info("Indexing billing data...")
        
        db = self.sessions['billing']
        try:
            # Get all invoices
            invoices = db.execute(select(Invoice)).scalars().all()
            
            if not invoices:
                logger.warning("No invoices found")
                return
            
            # Prepare documents
            documents = []
            metadata = []
            
            for invoice in invoices:
                # Create searchable text
                text = f"""
                Invoice {invoice.invoice_id}
                Customer: {invoice.customer_name}
                Amount: ${invoice.total:.2f}
                Status: {invoice.status}
                Due Date: {invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'N/A'}
                Date: {invoice.invoice_date.strftime('%Y-%m-%d')}
                Balance: ${invoice.balance:.2f}
                """
                
                documents.append(text.strip())
                metadata.append({
                    'source': 'billing',
                    'type': 'invoice',
                    'id': invoice.id,
                    'invoice_number': invoice.invoice_id,
                    'client_name': invoice.customer_name,
                    'amount': float(invoice.total),
                    'status': invoice.status,
                    'date': invoice.invoice_date.isoformat(),
                    'content': text.strip()
                })
            
            # Generate embeddings and store
            embeddings = self.embedder.encode(documents, show_progress=True)
            self.vector_store.add(embeddings, metadata)
            
            logger.info(f"✅ Indexed {len(documents)} invoices")
        except Exception as e:
            logger.error(f"Error indexing billing: {e}")
    
    def index_oms(self):
        """Index orders from OMS database."""
        logger.info("Indexing OMS data...")
        
        db = self.sessions['oms']
        try:
            # Index orders
            orders = db.execute(select(Order)).scalars().all()
            
            documents = []
            metadata = []
            
            for order in orders:
                text = f"""
                Order {order.order_id}
                Customer: {order.customer_name}
                Status: {order.status}
                Total: ${order.total_value:.2f}
                Items: {order.total_items} units
                Date: {order.order_date.strftime('%Y-%m-%d')}
                Priority: {order.priority}
                """
                
                documents.append(text.strip())
                metadata.append({
                    'source': 'oms',
                    'type': 'order',
                    'id': order.id,
                    'order_number': order.order_id,
                    'customer': order.customer_name,
                    'status': order.status,
                    'total': float(order.total_value),
                    'content': text.strip()
                })
            
            embeddings = self.embedder.encode(documents, show_progress=True)
            self.vector_store.add(embeddings, metadata)
            
            logger.info(f"✅ Indexed {len(documents)} OMS records")
        except Exception as e:
            logger.error(f"Error indexing OMS: {e}")
    
    def index_tms(self):
        """Index shipments from TMS database."""
        logger.info("Indexing TMS data...")
        
        db = self.sessions['tms']
        try:
            # Index shipments
            shipments = db.execute(select(Shipment)).scalars().all()
            
            documents = []
            metadata = []
            
            for shipment in shipments:
                text = f"""
                Shipment {shipment.shipment_id}
                Carrier: {shipment.carrier}
                Route: {shipment.origin} to {shipment.destination}
                Status: {shipment.status}
                Tracking: {shipment.tracking_number}
                Cost: ${shipment.cost:.2f}
                Date: {shipment.scheduled_pickup.strftime('%Y-%m-%d')}
                """
                
                documents.append(text.strip())
                metadata.append({
                    'source': 'tms',
                    'type': 'shipment',
                    'id': shipment.id,
                    'shipment_id': shipment.shipment_id,
                    'carrier': shipment.carrier,
                    'status': shipment.status,
                    'cost': float(shipment.cost),
                    'content': text.strip()
                })
            
            embeddings = self.embedder.encode(documents, show_progress=True)
            self.vector_store.add(embeddings, metadata)
            
            logger.info(f"✅ Indexed {len(documents)} TMS records")
        except Exception as e:
            logger.error(f"Error indexing TMS: {e}")
    
    def index_wms(self):
        """Index warehouse inventory and picking tasks from WMS database."""
        logger.info("Indexing WMS data...")
        
        db = self.sessions['wms']
        try:
            documents = []
            metadata = []
            
            # Index inventory
            inventory = db.execute(select(Inventory)).scalars().all()
            
            for inv in inventory:
                text = f"""
                Inventory: {inv.product_name}
                SKU: {inv.sku}
                Warehouse: {inv.warehouse_location}
                Quantity: {inv.quantity_on_hand} units
                Reserved: {inv.quantity_reserved} units
                Available: {inv.quantity_available} units
                """
                
                documents.append(text.strip())
                metadata.append({
                    'source': 'wms',
                    'type': 'inventory',
                    'sku': inv.sku,
                    'product': inv.product_name,
                    'warehouse': inv.warehouse_location,
                    'quantity': inv.quantity_on_hand,
                    'content': text.strip()
                })
            
            # Index picking tasks (labor data)
            tasks = db.execute(select(PickingTask)).scalars().all()
            
            for task in tasks:
                text = f"""
                Picking Task for Order {task.order_id}
                SKU: {task.sku}
                Quantity: {task.quantity} units
                Location: {task.location}
                Status: {task.status}
                Assigned to: {task.assigned_to or 'Unassigned'}
                Priority: {task.priority}
                Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}
                Completed: {task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else 'Pending'}
                """
                
                documents.append(text.strip())
                metadata.append({
                    'source': 'wms',
                    'type': 'picking_task',
                    'order_id': task.order_id,
                    'sku': task.sku,
                    'status': task.status,
                    'assigned_to': task.assigned_to,
                    'priority': task.priority,
                    'created_date': task.created_at.isoformat(),
                    'content': text.strip()
                })
            
            embeddings = self.embedder.encode(documents, show_progress=True)
            self.vector_store.add(embeddings, metadata)
            
            logger.info(f"✅ Indexed {len(documents)} WMS records ({len(inventory)} inventory + {len(tasks)} tasks)")
        except Exception as e:
            logger.error(f"Error indexing WMS: {e}")
    
    def index_returns(self):
        """Index return orders from returns database."""
        logger.info("Indexing returns data...")
        
        db = self.sessions['returns']
        try:
            returns = db.execute(select(Return)).scalars().all()
            
            documents = []
            metadata = []
            
            for ret in returns:
                text = f"""
                Return {ret.return_id}
                Customer: {ret.customer_name}
                Original Order: {ret.order_id}
                Reason: {ret.reason}
                Status: {ret.status}
                Total: ${ret.refund_amount:.2f}
                Date: {ret.return_date.strftime('%Y-%m-%d')}
                """
                
                documents.append(text.strip())
                metadata.append({
                    'source': 'returns',
                    'type': 'return_order',
                    'rma_number': ret.return_id,
                    'customer': ret.customer_name,
                    'reason': ret.reason,
                    'status': ret.status,
                    'amount': float(ret.refund_amount),
                    'content': text.strip()
                })
            
            embeddings = self.embedder.encode(documents, show_progress=True)
            self.vector_store.add(embeddings, metadata)
            
            logger.info(f"✅ Indexed {len(documents)} returns")
        except Exception as e:
            logger.error(f"Error indexing returns: {e}")
    
    def index_yard(self):
        """Index yard dock appointments."""
        logger.info("Indexing yard data...")
        
        db = self.sessions['yard']
        try:
            appointments = db.execute(select(DockAppointment)).scalars().all()
            
            documents = []
            metadata = []
            
            for appt in appointments:
                text = f"""
                Dock Appointment: {appt.appointment_id}
                Carrier: {appt.carrier}
                Trailer: {appt.trailer_number}
                Dock: {appt.dock_door}
                Type: {appt.appointment_type}
                Status: {appt.status}
                Scheduled: {appt.scheduled_time.strftime('%Y-%m-%d %H:%M')}
                """
                
                documents.append(text.strip())
                metadata.append({
                    'source': 'yard',
                    'type': 'dock_appointment',
                    'trailer': appt.trailer_number,
                    'carrier': appt.carrier,
                    'status': appt.status,
                    'content': text.strip()
                })
            
            embeddings = self.embedder.encode(documents, show_progress=True)
            self.vector_store.add(embeddings, metadata)
            
            logger.info(f"✅ Indexed {len(documents)} yard records")
        except Exception as e:
            logger.error(f"Error indexing yard: {e}")
    
    def index_pdfs(self, pdf_dir: str = "invoices"):
        """
        Index PDF documents.
        
        Args:
            pdf_dir: Directory containing PDFs
        """
        logger.info(f"Indexing PDFs from {pdf_dir}...")
        
        pdf_path = Path(pdf_dir)
        if not pdf_path.exists():
            logger.warning(f"PDF directory not found: {pdf_dir}")
            return
        
        pdf_files = list(pdf_path.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_dir}")
            return
        
        documents = []
        metadata = []
        
        for pdf_file in pdf_files:
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    
                    if text.strip():
                        documents.append(text.strip())
                        metadata.append({
                            'source': 'pdf',
                            'type': 'document',
                            'filename': pdf_file.name,
                            'path': str(pdf_file),
                            'content': text.strip()[:1000]  # Store first 1000 chars
                        })
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
        
        if documents:
            embeddings = self.embedder.encode(documents, show_progress=True)
            self.vector_store.add(embeddings, metadata)
            logger.info(f"✅ Indexed {len(documents)} PDFs")
        else:
            logger.warning("No PDF content extracted")
    
    def get_vector_store(self) -> VectorStore:
        """Get the vector store instance."""
        return self.vector_store
    
    def refresh_kpi_data(self):
        """
        Refresh only the KPI metrics without rebuilding entire index.
        Useful for keeping KPI data current without long rebuild times.
        """
        logger.info("Refreshing KPI and dashboard metrics only...")
        
        try:
            # Load existing index
            if not self.vector_store.load("supplychain_full"):
                logger.warning("No existing index found, performing full index")
                self.index_all(load_existing=False)
                return
            
            # Remove old KPI documents (by filtering out kpi_dashboard source)
            # Note: This is a simplified approach. For production, you'd want
            # to track document IDs and remove specific documents.
            logger.info("Removing old KPI data...")
            
            # Re-index KPI metrics
            self.kpi_indexer.index_kpi_metrics()
            
            # Re-index operational scorecard
            self.kpi_indexer.index_operational_scorecard()
            
            # Re-index exception management data
            self.kpi_indexer.index_exceptions()
            
            # Re-index dashboard summaries
            try:
                self.kpi_indexer.index_dashboard_summaries()
            except Exception as e:
                logger.warning(f"Could not index dashboard summaries: {e}")
            
            # Save updated index
            self.vector_store.save("supplychain_full")
            
            logger.info(f"✅ KPI and dashboard data refresh complete ({len(self.vector_store)} total documents)")
            
        except Exception as e:
            logger.error(f"Error refreshing KPI data: {e}", exc_info=True)
            raise
