# app/services/incident_service.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.models import Incident, IncidentHistory, IncidentStatus, AuditLog
from app.schemas import (
    IncidentRequest, IncidentStatusResponse, IncidentListItem, 
    IncidentDetail, IncidentHistoryItem, LocationCoords
)
from app.services.kb_service import NotificationService
from app.config import settings

logger = logging.getLogger(__name__)

class IncidentService:
    def __init__(self):
        self.notification_service = NotificationService(settings)
        
    async def create_incident(self, request: IncidentRequest, db: Session) -> Incident:
        """Create a new incident report"""
        try:
            # Generate unique incident ID
            incident_id = await self._generate_incident_id(db)
            
            # Create incident
            incident = Incident(
                id=incident_id,
                title=request.title,
                description=request.description,
                category=request.category,
                location_text=request.location_text,
                location_coords=request.location_coords.dict() if request.location_coords else None,
                contact_email=request.contact_email,
                contact_phone=request.contact_phone,
                photo_url=request.photo_url,
                status=IncidentStatus.NEW,
                priority=self._determine_priority(request),
                created_at=datetime.utcnow()
            )
            
            db.add(incident)
            db.flush()  # Get the ID
            
            # Create initial history entry
            history_entry = IncidentHistory(
                incident_id=incident.id,
                status=IncidentStatus.NEW,
                notes="Incident report created",
                staff_id="SYSTEM",
                created_at=datetime.utcnow()
            )
            db.add(history_entry)
            
            # Create audit log
            audit_entry = AuditLog(
                action="CREATE_INCIDENT",
                resource_type="incident",
                resource_id=incident.id,
                details={
                    "category": incident.category,
                    "location": incident.location_text,
                    "priority": incident.priority
                },
                created_at=datetime.utcnow()
            )
            db.add(audit_entry)
            
            db.commit()
            
            # Send notifications
            await self._send_creation_notifications(incident)
            
            logger.info(f"Created incident {incident.id}")
            return incident
            
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
            db.rollback()
            raise
    
    async def _generate_incident_id(self, db: Session) -> str:
        """Generate unique incident ID in format INC-YYYY-NNN"""
        current_year = datetime.utcnow().year
        
        # Get the highest number for this year
        latest_incident = db.query(Incident).filter(
            Incident.id.like(f"INC-{current_year}-%")
        ).order_by(desc(Incident.id)).first()
        
        if latest_incident:
            # Extract number from ID like "INC-2025-001"
            try:
                last_num = int(latest_incident.id.split('-')[-1])
                next_num = last_num + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"INC-{current_year}-{next_num:03d}"
    
    def _determine_priority(self, request: IncidentRequest) -> str:
        """Determine incident priority based on category and keywords"""
        high_priority_categories = ['electricity', 'water_supply']
        urgent_keywords = ['emergency', 'urgent', 'dangerous', 'flooding', 'fire', 'explosion']
        
        description_lower = request.description.lower()
        title_lower = request.title.lower()
        
        # Check for urgent keywords
        if any(keyword in description_lower or keyword in title_lower for keyword in urgent_keywords):
            return "URGENT"
        
        # Check category priority
        if request.category in high_priority_categories:
            return "HIGH"
        
        # Default priority
        return "MEDIUM"
    
    async def _send_creation_notifications(self, incident: Incident):
        """Send notifications when incident is created"""
        try:
            # Notify resident
            if incident.contact_email:
                await self.notification_service.send_email(
                    recipient=incident.contact_email,
                    subject=f"Incident Report Submitted - {incident.id}",
                    template="incident_created",
                    variables={
                        "incident_id": incident.id,
                        "title": incident.title,
                        "status": incident.status.value,
                        "category": incident.category.replace('_', ' ').title()
                    }
                )
            
            # Notify staff (internal notification)
            await self.notification_service.notify_staff_new_incident(incident)
            
        except Exception as e:
            logger.error(f"Error sending creation notifications: {e}")
            # Don't raise - notification failure shouldn't fail incident creation
    
    async def get_status(self, incident_id: str, db: Session) -> Optional[IncidentStatusResponse]:
        """Get incident status and history"""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        
        if not incident:
            return None
        
        # Get history
        history_entries = db.query(IncidentHistory).filter(
            IncidentHistory.incident_id == incident_id
        ).order_by(IncidentHistory.created_at).all()
        
        history = [
            IncidentHistoryItem(
                status=entry.status,
                notes=entry.notes,
                staff_id=entry.staff_id if entry.staff_id != "SYSTEM" else None,
                created_at=entry.created_at
            )
            for entry in history_entries
        ]
        
        return IncidentStatusResponse(
            incident_id=incident.id,
            status=incident.status,
            last_update=incident.updated_at,
            history=history,
            title=incident.title,
            description=incident.description,
            category=incident.category
        )
    
    async def list_incidents(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: Session = None
    ) -> List[IncidentListItem]:
        """List incidents with filtering for staff"""
        query = db.query(Incident)
        
        # Apply filters
        if status:
            try:
                status_enum = IncidentStatus(status.upper())
                query = query.filter(Incident.status == status_enum)
            except ValueError:
                logger.warning(f"Invalid status filter: {status}")
        
        if category:
            query = query.filter(Incident.category == category.lower())
        
        # Order by priority and creation date
        incidents = query.order_by(
            Incident.priority.desc(),
            desc(Incident.created_at)
        ).offset(offset).limit(limit).all()
        
        return [
            IncidentListItem(
                incident_id=incident.id,
                title=incident.title,
                category=incident.category,
                status=incident.status,
                created_at=incident.created_at,
                updated_at=incident.updated_at,
                priority=incident.priority
            )
            for incident in incidents
        ]
    
    async def get_detail(self, incident_id: str, db: Session) -> Optional[IncidentDetail]:
        """Get detailed incident information for staff"""
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        
        if not incident:
            return None
        
        # Get history
        history_entries = db.query(IncidentHistory).filter(
            IncidentHistory.incident_id == incident_id
        ).order_by(IncidentHistory.created_at).all()
        
        history = [
            IncidentHistoryItem(
                status=entry.status,
                notes=entry.notes,
                staff_id=entry.staff_id if entry.staff_id != "SYSTEM" else None,
                created_at=entry.created_at
            )
            for entry in history_entries
        ]
        
        return IncidentDetail(
            incident_id=incident.id,
            title=incident.title,
            description=incident.description,
            category=incident.category,
            location_text=incident.location_text,
            location_coords=LocationCoords(**incident.location_coords) if incident.location_coords else None,
            contact_email=incident.contact_email,
            contact_phone=incident.contact_phone,
            photo_url=incident.photo_url,
            status=incident.status,
            priority=incident.priority,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            history=history
        )
    
    async def update_incident(
        self,
        incident_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        priority: Optional[str] = None,
        staff_id: str = None,
        db: Session = None
    ) -> bool:
        """Update incident status and notes"""
        try:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
            
            if not incident:
                return False
            
            old_status = incident.status
            updated = False
            
            # Update status
            if status:
                try:
                    new_status = IncidentStatus(status.upper())
                    incident.status = new_status
                    incident.updated_at = datetime.utcnow()
                    updated = True
                except ValueError:
                    logger.warning(f"Invalid status: {status}")
                    return False
            
            # Update priority
            if priority and priority.upper() in ['LOW', 'MEDIUM', 'HIGH', 'URGENT']:
                incident.priority = priority.upper()
                incident.updated_at = datetime.utcnow()
                updated = True
            
            if not updated and not notes:
                return False  # Nothing to update
            
            # Create history entry
            if updated or notes:
                history_entry = IncidentHistory(
                    incident_id=incident.id,
                    status=incident.status,
                    notes=notes or f"Status updated to {incident.status.value}",
                    staff_id=staff_id or "SYSTEM",
                    created_at=datetime.utcnow()
                )
                db.add(history_entry)
            
            # Create audit log
            audit_details = {}
            if status:
                audit_details["old_status"] = old_status.value
                audit_details["new_status"] = incident.status.value
            if priority:
                audit_details["new_priority"] = incident.priority
            if notes:
                audit_details["notes"] = notes[:100]  # Truncate for storage
            
            audit_entry = AuditLog(
                action="UPDATE_INCIDENT",
                resource_type="incident",
                resource_id=incident.id,
                staff_id=staff_id,
                details=audit_details,
                created_at=datetime.utcnow()
            )
            db.add(audit_entry)
            
            db.commit()
            
            # Send notifications if status changed
            if status and old_status != incident.status:
                await self._send_update_notifications(incident, old_status)
            
            logger.info(f"Updated incident {incident_id} by {staff_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating incident {incident_id}: {e}")
            db.rollback()
            return False
    
    async def _send_update_notifications(self, incident: Incident, old_status: IncidentStatus):
        """Send notifications when incident is updated"""
        try:
            # Notify resident if email provided
            if incident.contact_email:
                await self.notification_service.send_email(
                    recipient=incident.contact_email,
                    subject=f"Incident Update - {incident.id}",
                    template="incident_updated",
                    variables={
                        "incident_id": incident.id,
                        "title": incident.title,
                        "old_status": old_status.value.replace('_', ' ').title(),
                        "new_status": incident.status.value.replace('_', ' ').title(),
                        "category": incident.category.replace('_', ' ').title()
                    }
                )
            
            # Send SMS if phone provided and status is resolved
            if incident.contact_phone and incident.status == IncidentStatus.RESOLVED:
                await self.notification_service.send_sms(
                    recipient=incident.contact_phone,
                    message=f"Good news! Your incident report {incident.id} has been resolved. Thank you for using CivicNavigator."
                )
                
        except Exception as e:
            logger.error(f"Error sending update notifications: {e}")
    
    async def get_incident_statistics(self, db: Session) -> Dict[str, Any]:
        """Get incident statistics for dashboard"""
        try:
            # Status distribution
            status_counts = {}
            for status in IncidentStatus:
                count = db.query(Incident).filter(Incident.status == status).count()
                status_counts[status.value.lower()] = count
            
            # Category distribution
            category_counts = {}
            categories = ['road_maintenance', 'waste_management', 'water_supply', 
                         'electricity', 'street_lighting', 'drainage', 'other']
            for category in categories:
                count = db.query(Incident).filter(Incident.category == category).count()
                category_counts[category] = count
            
            # Priority distribution
            priority_counts = {}
            priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT']
            for priority in priorities:
                count = db.query(Incident).filter(Incident.priority == priority).count()
                priority_counts[priority.lower()] = count
            
            # Recent activity (last 7 days)
            from datetime import timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_incidents = db.query(Incident).filter(
                Incident.created_at >= week_ago
            ).count()
            
            # Resolution rate (resolved vs total)
            total_incidents = db.query(Incident).count()
            resolved_incidents = db.query(Incident).filter(
                Incident.status.in_([IncidentStatus.RESOLVED, IncidentStatus.CLOSED])
            ).count()
            
            resolution_rate = (resolved_incidents / max(total_incidents, 1)) * 100
            
            return {
                "total_incidents": total_incidents,
                "recent_incidents_7d": recent_incidents,
                "resolution_rate_percent": round(resolution_rate, 1),
                "status_distribution": status_counts,
                "category_distribution": category_counts,
                "priority_distribution": priority_counts,
                "average_resolution_time_hours": await self._calculate_avg_resolution_time(db)
            }
            
        except Exception as e:
            logger.error(f"Error getting incident statistics: {e}")
            return {"error": "Failed to calculate statistics"}
    
    async def _calculate_avg_resolution_time(self, db: Session) -> Optional[float]:
        """Calculate average time to resolve incidents"""
        try:
            resolved_incidents = db.query(Incident).filter(
                Incident.status.in_([IncidentStatus.RESOLVED, IncidentStatus.CLOSED])
            ).all()
            
            if not resolved_incidents:
                return None
            
            total_hours = 0
            count = 0
            
            for incident in resolved_incidents:
                resolution_time = incident.updated_at - incident.created_at
                total_hours += resolution_time.total_seconds() / 3600
                count += 1
            
            return round(total_hours / count, 1) if count > 0 else None
            
        except Exception as e:
            logger.error(f"Error calculating resolution time: {e}")
            return None
    
    async def search_incidents(
        self,
        query: str,
        limit: int = 20,
        db: Session = None
    ) -> List[IncidentListItem]:
        """Search incidents by title, description, or ID"""
        try:
            # Search in title, description, and ID
            search_filter = or_(
                Incident.title.ilike(f"%{query}%"),
                Incident.description.ilike(f"%{query}%"),
                Incident.id.ilike(f"%{query}%")
            )
            
            incidents = db.query(Incident).filter(search_filter).order_by(
                desc(Incident.created_at)
            ).limit(limit).all()
            
            return [
                IncidentListItem(
                    incident_id=incident.id,
                    title=incident.title,
                    category=incident.category,
                    status=incident.status,
                    created_at=incident.created_at,
                    updated_at=incident.updated_at,
                    priority=incident.priority
                )
                for incident in incidents
            ]
            
        except Exception as e:
            logger.error(f"Error searching incidents: {e}")
            return []