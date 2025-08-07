#!/usr/bin/env python3
"""Load sample data into the database"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import *
from app.services.ai_service import AIService
from app.services.kb_service import KnowledgeBaseService

# Sample knowledge base content
SAMPLE_KB_DOCS = [
    {
        "title": "Waste Collection Schedule - Nairobi Areas",
        "content": """
Waste collection schedules for different areas in Nairobi:

**Westlands Ward:**
- Domestic waste: Monday, Wednesday, Friday (6:00 AM - 10:00 AM)
- Commercial waste: Tuesday, Thursday, Saturday (5:00 AM - 9:00 AM)
- Recyclable materials: Every Saturday (8:00 AM - 12:00 PM)

**Karen Ward:**
- Domestic waste: Tuesday, Thursday, Saturday (7:00 AM - 11:00 AM)
- Garden waste: Every Monday (8:00 AM - 4:00 PM)
- Bulk waste collection: First Saturday of each month

**South C Ward:**
- Domestic waste: Monday, Wednesday, Friday (5:30 AM - 9:30 AM)
- Commercial waste: Daily except Sunday (6:00 AM - 10:00 AM)
- Special collections on public holidays: Check with local office

**Kilimani Ward:**
- Domestic waste: Daily except Sunday (6:00 AM - 10:00 AM)
- Commercial waste: Daily (5:00 AM - 9:00 AM)
- Recycling: Wednesday and Saturday

Note: During public holidays, collection may be delayed by one day. Contact your local collection point for updates.
        """,
        "tags": ["waste", "collection", "schedule", "nairobi"],
        "source_url": "https://nairobi.go.ke/waste-management"
    },
    {
        "title": "Water Supply Issues and Reporting",
        "content": """
How to report water supply issues in Nairobi:

**Types of Issues to Report:**
- No water supply for more than 6 hours
- Low water pressure
- Water quality issues (color, taste, smell)
- Burst pipes
- Illegal connections
- Water meter problems

**How to Report:**
1. Online portal: www.nairobiwater.co.ke
2. SMS: Send details to 20050
3. Phone: 0800 720 720 (toll-free)
4. Mobile app: Nairobi Water App
5. Visit nearest customer service center

**Information to Provide:**
- Your account number
- Exact location/address
- Description of the problem
- Your contact details
- Any photos if applicable

**Response Times:**
- Emergency issues (burst pipes): 2-4 hours
- No water supply: 24-48 hours
- Low pressure: 48-72 hours
- Billing issues: 5 working days

**Emergency Contacts:**
- 24/7 Emergency line: 0800 720 720
- WhatsApp: +254 711 673 673
        """,
        "tags": ["water", "supply", "reporting", "emergency"],
        "source_url": "https://nairobiwater.co.ke/services"
    },
    {
        "title": "Street Lighting Maintenance and Reporting",
        "content": """
Street lighting issues - how to report and what to expect:

**Common Street Lighting Issues:**
- Faulty street lights
- Complete darkness in an area
- Flickering lights
- Damaged light poles
- Missing bulbs or fixtures

**How to Report Street Light Issues:**
1. County website: www.nairobi.go.ke
2. Customer care: 0709 590 000
3. Email: info@nairobi.go.ke
4. Social media: @NairobiCounty
5. Visit ward office during working hours

**Required Information:**
- Exact location (road name, landmarks)
- Nature of the problem
- Pole number (if visible)
- Your contact information
- Time when issue was first noticed

**Response and Resolution Times:**
- Assessment: 48-72 hours
- Repair of individual lights: 3-7 working days
- Major electrical repairs: 2-3 weeks
- New installations: 4-6 weeks

**Priority Areas:**
- Schools and hospitals vicinity
- Major roads and highways
- Markets and commercial areas
- Residential areas with security concerns

**Preventive Maintenance:**
Regular inspections are conducted quarterly in all wards. Report any hazardous conditions immediately.
        """,
        "tags": ["street", "lighting", "maintenance", "reporting", "safety"],
        "source_url": "https://nairobi.go.ke/street-lighting"
    },
    {
        "title": "Road Maintenance and Pothole Reporting",
        "content": """
Road maintenance issues and how to report them:

**Types of Road Issues:**
- Potholes
- Damaged road surfaces
- Missing or damaged road signs
- Blocked drainage systems
- Damaged road markings
- Traffic light malfunctions

**Reporting Process:**
1. Nairobi County app (available on Google Play/App Store)
2. Website: nairobi.go.ke/road-maintenance
3. Phone: 0709 590 000
4. Email: roads@nairobi.go.ke
5. Walk-in: County Hall, City Square

**Information Needed:**
- GPS coordinates or detailed location
- Photos of the damage
- Description of the problem
- Traffic impact level
- Your contact details

**Response Times:**
- Emergency repairs (major roads): 24-48 hours
- Pothole repairs: 1-2 weeks
- Road resurfacing: 1-3 months (depending on budget)
- Sign replacement: 2-4 weeks

**Priority Classification:**
- Critical: Major roads, emergency access routes
- High: Arterial roads, public transport routes  
- Medium: Collector roads in residential areas
- Low: Minor access roads

**Temporary Measures:**
For dangerous conditions, temporary barriers or warning signs may be installed within 24 hours while permanent repairs are scheduled.
        """,
        "tags": ["road", "maintenance", "potholes", "traffic", "repair"],
        "source_url": "https://nairobi.go.ke/road-maintenance"
    },
    {
        "title": "Electricity Connection and Fault Reporting - Kenya Power",
        "content": """
Electricity services and fault reporting through Kenya Power:

**Power Outage Reporting:**
1. SMS: Send your account number to 95551
2. Call: 0711 070 000 or 0732 170 000
3. WhatsApp: 0711 070 070
4. Website: www.kplc.co.ke
5. Social media: @KenyaPower

**Types of Electrical Faults:**
- Complete power outage
- Partial power outage
- Low voltage/power fluctuations
- Transformer faults
- Fallen power lines (EMERGENCY)
- Faulty meters

**Emergency Response:**
- Fallen power lines: Call 999 immediately
- Electrical fires: Call fire department (999) and Kenya Power
- Never approach fallen power lines

**New Connection Process:**
1. Visit nearest Kenya Power office
2. Fill application form
3. Pay connection fees
4. Site inspection within 5 working days
5. Connection within 15 working days

**Required Documents:**
- National ID/Passport copy
- Land ownership documents
- Location map/GPS coordinates
- Architectural drawings (for commercial)

**Response Times:**
- Emergency faults: 2-4 hours
- Area outages: 4-8 hours
- Individual connection issues: 24-48 hours
- New connections: 15 working days

**Customer Care Centers:**
Available in all major towns, open Monday-Friday 8AM-5PM, Saturday 8AM-1PM.
        """,
        "tags": ["electricity", "power", "kenya power", "outage", "connection"],
        "source_url": "https://kplc.co.ke/customer-services"
    }
]

# Sample incidents for testing
SAMPLE_INCIDENTS = [
    {
        "title": "Broken street light on Ngong Road",
        "description": "The street light near the Shell petrol station has been out for 3 days. It's very dark and unsafe for pedestrians at night.",
        "category": "street_lighting",
        "location_text": "Ngong Road, near Shell Petrol Station",
        "contact_email": "resident1@example.com",
        "priority": "HIGH"
    },
    {
        "title": "Overflowing garbage collection point",
        "description": "The waste collection point at South C shopping center has been overflowing for over a week. It's attracting flies and rodents.",
        "category": "waste_management",
        "location_text": "South C Shopping Center",
        "contact_email": "concerned.citizen@example.com",
        "priority": "MEDIUM"
    },
    {
        "title": "Large pothole on Uhuru Highway",
        "description": "There's a very large pothole on Uhuru Highway that's causing damage to vehicles. Multiple cars have gotten flat tires.",
        "category": "road_maintenance",
        "location_text": "Uhuru Highway, near National Museum",
        "contact_phone": "+254712345678",
        "priority": "URGENT"
    }
]

async def main():
    print("🔄 Loading sample data...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize AI service
    ai_service = AIService()
    await ai_service.initialize()
    
    db = SessionLocal()
    try:
        # Load knowledge base documents
        kb_service = KnowledgeBaseService(ai_service)
        
        print("📚 Loading knowledge base documents...")
        for doc_data in SAMPLE_KB_DOCS:
            try:
                await kb_service.create_or_update_document(
                    title=doc_data["title"],
                    content=doc_data["content"],
                    tags=doc_data["tags"],
                    source_url=doc_data.get("source_url"),
                    db=db
                )
                print(f"✅ Loaded: {doc_data['title']}")
            except Exception as e:
                print(f"❌ Failed to load {doc_data['title']}: {e}")
        
        # Load sample incidents
        print("\n🚨 Loading sample incidents...")
        incident_service = None
        
        for i, incident_data in enumerate(SAMPLE_INCIDENTS, 1):
            try:
                # Generate incident ID
                incident_id = f"INC-2025-{i:03d}"
                
                # Create incident
                incident = Incident(
                    id=incident_id,
                    title=incident_data["title"],
                    description=incident_data["description"],
                    category=incident_data["category"],
                    location_text=incident_data["location_text"],
                    contact_email=incident_data.get("contact_email"),
                    contact_phone=incident_data.get("contact_phone"),
                    status=IncidentStatus.NEW,
                    priority=incident_data["priority"],
                    created_at=datetime.utcnow() - timedelta(days=i)  # Stagger creation dates
                )
                
                db.add(incident)
                db.flush()
                
                # Add history entry
                history = IncidentHistory(
                    incident_id=incident.id,
                    status=IncidentStatus.NEW,
                    notes="Incident report created",
                    staff_id="SYSTEM",
                    created_at=incident.created_at
                )
                db.add(history)
                
                print(f"✅ Created incident: {incident_id}")
                
            except Exception as e:
                print(f"❌ Failed to create incident: {e}")
        
        # Update one incident to show progression
        try:
            first_incident = db.query(Incident).first()
            if first_incident:
                first_incident.status = IncidentStatus.IN_PROGRESS
                first_incident.updated_at = datetime.utcnow() - timedelta(hours=12)
                
                # Add progress history
                progress_history = IncidentHistory(
                    incident_id=first_incident.id,
                    status=IncidentStatus.IN_PROGRESS,
                    notes="Assigned to maintenance team for inspection",
                    staff_id="STAFF001",
                    created_at=first_incident.updated_at
                )
                db.add(progress_history)
                
                print(f"✅ Updated {first_incident.id} to IN_PROGRESS")
        except Exception as e:
            print(f"❌ Failed to update incident status: {e}")
        
        db.commit()
        print("\n🎉 Sample data loaded successfully!")
        print(f"📊 Loaded {len(SAMPLE_KB_DOCS)} knowledge base documents")
        print(f"📊 Created {len(SAMPLE_INCIDENTS)} sample incidents")
        
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        await ai_service.cleanup()

if __name__ == "__main__":
    asyncio.run(main())