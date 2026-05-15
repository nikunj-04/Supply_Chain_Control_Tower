"""
KPI Indexer - Indexes pre-calculated KPI metrics from dashboard service.
This ensures chatbot responses match dashboard displays exactly.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from .embeddings import EmbeddingService
from .vector_store import VectorStore
from services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)


class KPIIndexer:
    """
    Indexes pre-calculated KPI metrics from dashboard service into vector store.
    This ensures chatbot answers match dashboard data exactly.
    """
    
    def __init__(self, vector_store: VectorStore, embedder: EmbeddingService):
        """
        Initialize KPI indexer.
        
        Args:
            vector_store: Vector store instance to add KPIs to
            embedder: Embedding service for encoding
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.dashboard_service = DashboardService()
    
    def index_kpi_metrics(self):
        """
        Index all KPI metrics from dashboard service.
        This creates searchable documents that match what dashboards show.
        """
        logger.info("Indexing KPI metrics from dashboard service...")
        
        try:
            # Get the full KPI dashboard
            kpi_dashboard = self.dashboard_service.get_kpi_dashboard()
            
            documents = []
            metadata = []
            
            # Process each category
            for category in kpi_dashboard.get('categories', []):
                category_title = category.get('title', '')
                category_icon = category.get('icon', '')
                
                # Create a comprehensive document for the category
                category_doc = self._create_category_document(category, kpi_dashboard['last_updated'])
                documents.append(category_doc)
                metadata.append({
                    'source': 'kpi_dashboard',
                    'type': 'kpi_category',
                    'category': category_title,
                    'icon': category_icon,
                    'last_updated': kpi_dashboard['last_updated'],
                    'content': category_doc
                })
                
                # Create individual documents for each metric
                for metric in category.get('metrics', []):
                    metric_doc = self._create_metric_document(
                        category_title, 
                        metric, 
                        kpi_dashboard['last_updated']
                    )
                    documents.append(metric_doc)
                    metadata.append({
                        'source': 'kpi_dashboard',
                        'type': 'kpi_metric',
                        'category': category_title,
                        'metric_label': metric.get('label', ''),
                        'metric_value': metric.get('value', ''),
                        'metric_status': metric.get('status', ''),
                        'last_updated': kpi_dashboard['last_updated'],
                        'content': metric_doc
                    })
            
            # Add a summary document with all KPIs
            summary_doc = self._create_summary_document(kpi_dashboard)
            documents.append(summary_doc)
            metadata.append({
                'source': 'kpi_dashboard',
                'type': 'kpi_summary',
                'last_updated': kpi_dashboard['last_updated'],
                'total_categories': len(kpi_dashboard.get('categories', [])),
                'content': summary_doc
            })
            
            # Generate embeddings and add to vector store
            if documents:
                embeddings = self.embedder.encode(documents, show_progress=True)
                self.vector_store.add(embeddings, metadata)
                logger.info(f"✅ Indexed {len(documents)} KPI documents")
            else:
                logger.warning("No KPI documents to index")
                
        except Exception as e:
            logger.error(f"Error indexing KPI metrics: {e}", exc_info=True)
    
    def index_operational_scorecard(self):
        """
        Index operational scorecard data from all systems.
        This includes system health metrics and operational status.
        """
        logger.info("Indexing operational scorecard data...")
        
        try:
            # Get operational scorecard
            scorecard = self.dashboard_service.get_operational_scorecard()
            
            documents = []
            metadata = []
            
            timestamp = scorecard.get('timestamp').strftime('%b %d, %Y, %I:%M %p') if scorecard.get('timestamp') else 'Unknown'
            summary = scorecard.get('summary', {})
            
            # Create summary document
            summary_doc = f"""Operational Scorecard Summary
Last Updated: {timestamp}

System Health Overview:
- Total Systems: {summary.get('total_systems', 0)}
- Healthy: {summary.get('healthy', 0)} ✅
- Warning: {summary.get('warning', 0)} ⚠️
- Critical: {summary.get('critical', 0)} 🔴

This represents the overall health status across all operational systems.
"""
            
            documents.append(summary_doc)
            metadata.append({
                'source': 'operational_dashboard',
                'type': 'scorecard_summary',
                'last_updated': timestamp,
                'content': summary_doc
            })
            
            # Index each system's scorecard
            for system in scorecard.get('systems', []):
                system_name = system.get('system_name', '')
                overall_status = system.get('overall_status', 'unknown')
                metrics = system.get('metrics', [])
                
                # Create comprehensive system document
                system_doc = f"""System: {system_name}
Last Updated: {timestamp}
Overall Status: {overall_status.upper()} {self._get_status_emoji(overall_status)}

Current Metrics:
"""
                
                for metric in metrics:
                    name = metric.get('name', '')
                    value = metric.get('value', '')
                    unit = metric.get('unit', '')
                    status = metric.get('status', '')
                    trend = metric.get('trend', '')
                    
                    status_emoji = self._get_metric_status_emoji(status)
                    trend_arrow = self._get_trend_arrow(trend)
                    
                    system_doc += f"- {name}: {value} {unit} {status_emoji} {trend_arrow}\n"
                
                # Add query variations
                system_doc += f"""

Common queries:
- What is the status of {system_name}? Answer: {overall_status}
- How is {system_name} performing? Answer: {overall_status}
- {system_name} health? Answer: {overall_status}
"""
                
                documents.append(system_doc)
                metadata.append({
                    'source': 'operational_dashboard',
                    'type': 'system_scorecard',
                    'system_name': system_name,
                    'overall_status': overall_status,
                    'last_updated': timestamp,
                    'content': system_doc
                })
                
                # Create individual metric documents for better search
                for metric in metrics:
                    metric_doc = f"""Operational Metric: {metric.get('name', '')}
System: {system_name}
Current Value: {metric.get('value', '')} {metric.get('unit', '')}
Status: {metric.get('status', '')} {self._get_metric_status_emoji(metric.get('status', ''))}
Trend: {metric.get('trend', '')} {self._get_trend_arrow(metric.get('trend', ''))}
Last Updated: {timestamp}

This metric tracks {metric.get('name', '').lower()} for {system_name}.
The current value is {metric.get('value', '')} {metric.get('unit', '')}.
"""
                    
                    documents.append(metric_doc)
                    metadata.append({
                        'source': 'operational_dashboard',
                        'type': 'operational_metric',
                        'system_name': system_name,
                        'metric_name': metric.get('name', ''),
                        'metric_value': f"{metric.get('value', '')} {metric.get('unit', '')}",
                        'metric_status': metric.get('status', ''),
                        'last_updated': timestamp,
                        'content': metric_doc
                    })
            
            # Generate embeddings and add to vector store
            if documents:
                embeddings = self.embedder.encode(documents, show_progress=True)
                self.vector_store.add(embeddings, metadata)
                logger.info(f"✅ Indexed {len(documents)} operational scorecard documents")
            
        except Exception as e:
            logger.error(f"Error indexing operational scorecard: {e}", exc_info=True)
    
    def _create_category_document(self, category: Dict[str, Any], last_updated: str) -> str:
        """
        Create a searchable document for a KPI category.
        
        Args:
            category: Category data from dashboard
            last_updated: Timestamp of last update
            
        Returns:
            Formatted text document
        """
        title = category.get('title', '')
        metrics = category.get('metrics', [])
        
        doc = f"""KPI Category: {title}
Last Updated: {last_updated}

Current Metrics:
"""
        for metric in metrics:
            label = metric.get('label', '')
            value = metric.get('value', '')
            status = metric.get('status', '')
            status_emoji = self._get_status_emoji(status)
            
            doc += f"- {label}: {value} {status_emoji}\n"
        
        return doc.strip()
    
    def _create_metric_document(self, category: str, metric: Dict[str, Any], last_updated: str) -> str:
        """
        Create a searchable document for an individual KPI metric.
        
        Args:
            category: Category name
            metric: Metric data
            last_updated: Timestamp of last update
            
        Returns:
            Formatted text document
        """
        label = metric.get('label', '')
        value = metric.get('value', '')
        status = metric.get('status', '')
        status_text = self._get_status_text(status)
        
        # Create variations for better search matching
        doc = f"""KPI Metric: {label}
Category: {category}
Current Value: {value}
Status: {status_text}
Performance: {status}
Last Updated: {last_updated}

This metric tracks {label.lower()} performance.
The current {label.lower()} is {value}.
Status is {status_text}.
"""
        
        # Add common query variations
        doc += self._add_query_variations(label, value, category)
        
        return doc.strip()
    
    def _create_summary_document(self, kpi_dashboard: Dict[str, Any]) -> str:
        """
        Create a comprehensive summary document with all KPIs.
        
        Args:
            kpi_dashboard: Full dashboard data
            
        Returns:
            Formatted summary document
        """
        last_updated = kpi_dashboard.get('last_updated', '')
        
        doc = f"""Supply Chain KPI Dashboard Summary
Last Updated: {last_updated}

=== COMPLETE KPI OVERVIEW ===

"""
        
        for category in kpi_dashboard.get('categories', []):
            title = category.get('title', '')
            doc += f"\n{title}:\n"
            
            for metric in category.get('metrics', []):
                label = metric.get('label', '')
                value = metric.get('value', '')
                status = metric.get('status', '')
                status_emoji = self._get_status_emoji(status)
                
                doc += f"  • {label}: {value} {status_emoji}\n"
        
        doc += f"\n\nThese are the OFFICIAL KPI values as calculated by the dashboard system."
        doc += f"\nAll percentages, rates, and metrics shown here match the live dashboards."
        doc += f"\nWhen answering KPI questions, use these exact values."
        
        return doc.strip()
    
    def _add_query_variations(self, label: str, value: str, category: str) -> str:
        """
        Add common query variations to improve search matching.
        
        Args:
            label: Metric label
            value: Metric value
            category: Category name
            
        Returns:
            Additional text with query variations
        """
        variations = f"""

Common queries:
- What is the {label.lower()}? Answer: {value}
- Current {label.lower()} = {value}
- {category} metric: {label} = {value}
- How is our {label.lower()}? Answer: {value}
"""
        return variations
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        status_map = {
            'on_target': '✅',
            'attention': '⚠️',
            'critical': '🔴',
            'good': '✅',
            'warning': '⚠️',
            'danger': '🔴'
        }
        return status_map.get(status, '📊')
    
    def _get_status_text(self, status: str) -> str:
        """Get human-readable status text."""
        status_map = {
            'on_target': 'On Target - Performance is meeting goals',
            'attention': 'Needs Attention - Performance requires monitoring',
            'critical': 'Critical - Immediate action needed',
            'good': 'Good - Performance is satisfactory',
            'warning': 'Warning - Performance below target',
            'danger': 'Danger - Severe performance issues',
            'healthy': 'Healthy - System operating normally'
        }
        return status_map.get(status, 'Status: ' + status)
    
    def _get_metric_status_emoji(self, status: str) -> str:
        """Get emoji for operational metric status."""
        status_map = {
            'good': '✅',
            'warning': '⚠️',
            'critical': '🔴',
            'healthy': '✅'
        }
        return status_map.get(status, '📊')
    
    def _get_trend_arrow(self, trend: str) -> str:
        """Get arrow for trend direction."""
        trend_map = {
            'up': '↗️',
            'down': '↘️',
            'stable': '→'
        }
        return trend_map.get(trend, '')
    
    def index_dashboard_summaries(self):
        """
        Index additional dashboard summaries for different views.
        This provides context for non-KPI dashboard questions.
        
        Note: This is a placeholder for future dashboard-specific indexes.
        Currently, KPI Dashboard and Operational Scorecard cover most needs.
        """
        logger.info("Dashboard summaries indexing skipped (already covered by KPI and Operational data)")
        # Future: Add billing-specific, inventory-specific dashboards if needed
    
    def index_exceptions(self, limit: int = 200):
        """
        Index exception data from Exception Management Center.
        This allows chatbot to answer questions about specific exceptions.
        
        Args:
            limit: Maximum number of exceptions to index (default 200 for performance)
        """
        logger.info("Indexing exception data from Exception Management Center...")
        
        try:
            from services.exception_service import ExceptionService
            
            service = ExceptionService()
            
            # Get open and critical exceptions (most relevant for queries)
            exceptions = service.get_all_exceptions(status='open')
            
            # Also get recent resolved exceptions for context
            resolved = service.get_all_exceptions(status='resolved')
            
            # Combine and limit
            all_exceptions = exceptions[:limit] + resolved[:min(50, len(resolved))]
            
            service.session.close()
            
            if not all_exceptions:
                logger.warning("No exceptions found to index")
                return
            
            documents = []
            metadata = []
            
            # Group by severity for summary
            by_severity = {'critical': [], 'warning': [], 'attention': []}
            by_type = {}
            
            for exc in all_exceptions:
                severity = exc.get('severity', 'warning')
                exc_type = exc.get('exception_type', 'unknown')
                
                if severity in by_severity:
                    by_severity[severity].append(exc)
                
                if exc_type not in by_type:
                    by_type[exc_type] = []
                by_type[exc_type].append(exc)
                
                # Create individual exception document
                doc = self._create_exception_document(exc)
                documents.append(doc)
                metadata.append({
                    'source': 'exception_management',
                    'type': 'exception_detail',
                    'exception_id': exc.get('exception_id'),
                    'severity': severity,
                    'exception_type': exc_type,
                    'status': exc.get('status')
                })
            
            # Create summary documents
            summary_doc = self._create_exception_summary_document(all_exceptions, by_severity, by_type)
            documents.append(summary_doc)
            metadata.append({
                'source': 'exception_management',
                'type': 'exception_summary'
            })
            
            # Encode and index all documents
            embeddings = self.embedder.encode(documents)
            self.vector_store.add(embeddings, metadata)
            
            logger.info(f"✅ Indexed {len(documents)} exception documents")
            
        except Exception as e:
            logger.error(f"Error indexing exceptions: {e}")
            raise
    
    def _create_exception_document(self, exc: Dict[str, Any]) -> str:
        """Create a searchable document for a single exception."""
        severity_emoji = {'critical': '🔴', 'warning': '⚠️', 'attention': '⚠️'}.get(exc.get('severity'), '📋')
        
        doc = f"""
=== EXCEPTION DETAIL ===
Exception ID: {exc.get('exception_id')}
Type: {exc.get('exception_type', 'Unknown')}
Severity: {severity_emoji} {exc.get('severity', 'Unknown').upper()}
Status: {exc.get('status', 'Unknown').upper()}
Source System: {exc.get('source_system')}

Title: {exc.get('title')}
Description: {exc.get('description')}

Impact: {exc.get('impact')}
Entity Type: {exc.get('entity_type')}
Entity ID: {exc.get('entity_id')}
"""
        
        # Add optional fields if present
        if exc.get('customer'):
            doc += f"Customer: {exc.get('customer')}\n"
        if exc.get('location'):
            doc += f"Location: {exc.get('location')}\n"
        if exc.get('carrier'):
            doc += f"Carrier: {exc.get('carrier')}\n"
        if exc.get('days_delayed'):
            doc += f"Days Delayed: {exc.get('days_delayed')}\n"
        if exc.get('cost_impact'):
            doc += f"Cost Impact: ${exc.get('cost_impact'):.2f}\n"
        if exc.get('quantity_affected'):
            doc += f"Quantity Affected: {exc.get('quantity_affected')}\n"
        
        if exc.get('detected_at'):
            doc += f"Detected: {exc.get('detected_at')}\n"
        if exc.get('assigned_to'):
            doc += f"Assigned To: {exc.get('assigned_to')}\n"
        
        if exc.get('requires_escalation'):
            doc += "⚠️ REQUIRES ESCALATION\n"
        
        # Add searchable query variations
        doc += f"\nSearchable as: exception {exc.get('exception_id')}, "
        doc += f"{exc.get('exception_type')} exception, "
        doc += f"{exc.get('severity')} severity, "
        doc += f"{exc.get('source_system')} issue"
        
        return doc
    
    def _create_exception_summary_document(self, exceptions: List[Dict], by_severity: Dict, by_type: Dict) -> str:
        """Create a summary document of all exceptions."""
        doc = f"""
=== EXCEPTION MANAGEMENT CENTER SUMMARY ===
Last Updated: {datetime.now().strftime('%b %d, %Y, %I:%M %p')}

Total Active Exceptions: {len(exceptions)}

By Severity:
- 🔴 Critical: {len(by_severity['critical'])} exceptions
- ⚠️ Warning: {len(by_severity['warning'])} exceptions
- ⚠️ Attention: {len(by_severity['attention'])} exceptions

By Type:
"""
        
        for exc_type, excs in sorted(by_type.items(), key=lambda x: len(x[1]), reverse=True):
            doc += f"- {exc_type}: {len(excs)} exceptions\n"
        
        # Add top critical exceptions
        if by_severity['critical']:
            doc += f"\n🔴 Top Critical Exceptions ({min(5, len(by_severity['critical']))}):\n"
            for exc in by_severity['critical'][:5]:
                doc += f"  - {exc.get('exception_id')}: {exc.get('title')} ({exc.get('source_system')})\n"
        
        doc += "\nSearchable as: exception summary, exception count, critical exceptions, exception dashboard, exception management"
        
        return doc