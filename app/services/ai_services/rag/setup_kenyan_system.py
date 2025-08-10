# setup_kenyan_system.py
"""
Setup script for CivicNavigator Kenyan document retrieval system.
Run this script to initialize the system with real Kenyan government documents.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KenyanSystemSetup:
    """Setup and initialization for the Kenyan CivicNavigator system."""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.kb_path = self.project_root / "knowledge_base" / "sourced_pdfs"
        self.index_path = self.project_root / "indexes" / "kenyan_kb"
        
    def check_dependencies(self):
        """Check if all required dependencies are installed."""
        logger.info("Checking dependencies...")
        
        required_packages = [
            'sentence-transformers',
            'faiss-cpu',
            'PyMuPDF',  # fitz
            'PyPDF2',
            'aiohttp',
            'aiofiles',
            'beautifulsoup4',
            'nltk',
            'numpy',
            'pandas',
            'scikit-learn'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Install with: pip install " + " ".join(missing_packages))
            return False
        
        logger.info("All dependencies found!")
        return True
    
    def create_directory_structure(self):
        """Create the required directory structure."""
        logger.info("Creating directory structure...")
        
        directories = [
            self.project_root / "knowledge_base" / "sourced_pdfs",
            self.project_root / "indexes",
            self.project_root / "ai_services" / "retrieval",
            self.project_root / "ai_services" / "utils",
            self.project_root / "backend" / "app" / "api" / "v1",
            self.project_root / "backend" / "app" / "services",
            self.project_root / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def download_nltk_data(self):
        """Download required NLTK data."""
        logger.info("Downloading NLTK data...")
        
        try:
            import nltk
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            logger.info("NLTK data downloaded successfully")
        except Exception as e:
            logger.error(f"Error downloading NLTK data: {e}")
    
    def create_environment_file(self):
        """Create .env file with Kenyan-specific configuration."""
        logger.info("Creating environment configuration...")
        
        env_content = """# CivicNavigator Kenyan Configuration
# Database
DATABASE_URL=postgresql://civicnav:password@localhost/civicnav_db
REDIS_URL=redis://localhost:6379/0

# AI Service Configuration
KNOWLEDGE_BASE_PATH=./knowledge_base/sourced_pdfs
INDEX_PATH=./indexes/kenyan_kb
REBUILD_INDEX=false
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Kenyan Government URLs (automatically fetched)
FETCH_REMOTE_DOCS=true

# API Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=true

# Performance Settings
MAX_WORKERS=4
BATCH_SIZE=16
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Contact Form Integration
NAIROBI_CONTACT_URL=https://nairobi.go.ke/contacts
AUTO_FILL_CONTACTS=true

# Kenyan Localization
DEFAULT_COUNTY=nairobi
SUPPORT_SWAHILI=true
PHONE_FORMAT=kenyan
"""
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write(env_content)
            logger.info("Created .env file")
        else:
            logger.info(".env file already exists")
    
    def check_pdf_directory(self):
        """Check if PDF directory exists and has files."""
        logger.info(f"Checking PDF directory: {self.kb_path}")
        
        if not self.kb_path.exists():
            logger.warning(f"PDF directory does not exist: {self.kb_path}")
            logger.info("Creating directory and adding sample message...")
            self.kb_path.mkdir(parents=True, exist_ok=True)
            
            # Create a placeholder file
            placeholder = self.kb_path / "README.txt"
            with open(placeholder, 'w') as f:
                f.write("""CivicNavigator Knowledge Base
================================

This directory should contain PDF documents from Kenyan government sources.

To use the system:
1. Add PDF files to this directory
2. Run: python setup_kenyan_system.py --rebuild-index
3. Start the backend server

The system will also automatically fetch documents from:
- nairobi.go.ke
- nairobiassembly.go.ke  
- nema.go.ke
- parliament.go.ke

For more information, see the documentation.
""")
            
            return False
        
        pdf_files = list(self.kb_path.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in directory")
        
        if pdf_files:
            logger.info("PDF files found:")
            for pdf in pdf_files[:5]:  # Show first 5
                logger.info(f"  - {pdf.name}")
            if len(pdf_files) > 5:
                logger.info(f"  ... and {len(pdf_files) - 5} more")
        
        return len(pdf_files) > 0
    
    async def initialize_retrieval_system(self, rebuild_index=False):
        """Initialize the document retrieval system."""
        logger.info("Initializing Kenyan document retrieval system...")
        
        try:
            # Import our enhanced retriever
            sys.path.append(str(self.project_root))
            from ai_services.retrieval.kenyan_document_retriever import KenyanDocumentRetriever
            
            # Initialize retriever
            retriever = KenyanDocumentRetriever(
                kb_path=str(self.kb_path),
                index_path=str(self.index_path)
            )
            
            # Build/load index
            await retriever.initialize_full_system(rebuild_index=rebuild_index)
            
            # Test with a simple query
            test_results = retriever.search("waste collection nairobi", top_k=3)
            
            if test_results:
                logger.info(f"✅ System initialized successfully! Found {len(test_results)} results for test query")
                for result in test_results[:2]:
                    logger.info(f"  - {result['title']} (score: {result['score']:.3f})")
            else:
                logger.warning("⚠️ System initialized but no test results found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error initializing retrieval system: {e}")
            return False
    
    def create_test_script(self):
        """Create a test script for the system."""
        logger.info("Creating test script...")
        
        test_script = self.project_root / "test_kenyan_system.py"
        
        test_content = '''#!/usr/bin/env python3
"""
Test script for CivicNavigator Kenyan system.
Run this to verify everything is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

from ai_services.retrieval.kenyan_document_retriever import KenyanDocumentRetriever, ContactFormFiller

async def main():
    """Run system tests."""
    print("🇰🇪 Testing CivicNavigator Kenyan System")
    print("="*50)
    
    # Initialize retriever
    retriever = KenyanDocumentRetriever()
    
    print("Loading existing index...")
    await retriever.initialize_full_system(rebuild_index=False)
    
    # Test queries
    test_queries = [
        "When is garbage collected in South C?",
        "How to apply for business permit Nairobi County?",
        "Water connection requirements and fees",
        "Report broken streetlight contact information",
        "County assembly meeting schedule",
        "Environmental waste management best practices"
    ]
    
    contact_filler = ContactFormFiller()
    
    print("\\nRunning test queries...")
    print("-" * 30)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\\n{i}. Query: {query}")
        
        results = retriever.search(query, top_k=2)
        
        if results:
            print(f"   ✅ Found {len(results)} results")
            best_result = results[0]
            print(f"   📄 Best match: {best_result['title']}")
            print(f"   📊 Score: {best_result['score']:.3f}")
            print(f"   📍 Category: {best_result['category']}")
            
            # Test contact form filling
            contact_info = contact_filler.extract_contact_info(results)
            if any(contact_info.values()):
                print(f"   📞 Contact info extracted: {len(contact_info['phones'])} phones, {len(contact_info['emails'])} emails")
        else:
            print("   ❌ No results found")
    
    print("\\n" + "="*50)
    print("✅ Test completed! System is ready for use.")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with open(test_script, 'w') as f:
            f.write(test_content)
        
        # Make executable on Unix systems
        try:
            os.chmod(test_script, 0o755)
        except:
            pass
        
        logger.info(f"Created test script: {test_script}")
    
    def create_requirements_file(self):
        """Create requirements.txt file."""
        logger.info("Creating requirements.txt...")
        
        requirements = """# CivicNavigator Kenyan System Requirements

# Core ML and AI
sentence-transformers>=2.2.2
faiss-cpu>=1.7.4
torch>=2.0.0
transformers>=4.30.0

# Document Processing
PyMuPDF>=1.23.0
PyPDF2>=3.0.0
python-docx>=0.8.11
beautifulsoup4>=4.12.0
markdown>=3.4.0

# Web and Async
aiohttp>=3.8.0
aiofiles>=23.1.0
requests>=2.31.0

# Data Processing
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
nltk>=3.8.0

# FastAPI and Backend
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
python-multipart>=0.0.6
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Database
sqlalchemy>=2.0.0
alembic>=1.11.0
psycopg2-binary>=2.9.6
redis>=4.6.0

# Development and Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0

# Monitoring and Logging
structlog>=23.1.0
python-dotenv>=1.0.0

# Kenyan Specific
phonenumbers>=8.13.0  # For Kenyan phone number parsing
"""
        
        requirements_file = self.project_root / "requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write(requirements)
        
        logger.info("Created requirements.txt")

async def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup CivicNavigator Kenyan System")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild the document index")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloading remote documents")
    args = parser.parse_args()
    
    setup = KenyanSystemSetup()
    
    print("🇰🇪 CivicNavigator Kenyan System Setup")
    print("="*50)
    
    # Step 1: Check dependencies
    if not setup.check_dependencies():
        print("\n❌ Please install missing dependencies first:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Step 2: Create directory structure
    setup.create_directory_structure()
    
    # Step 3: Download NLTK data
    setup.download_nltk_data()
    
    # Step 4: Create configuration files
    setup.create_environment_file()
    setup.create_requirements_file()
    setup.create_test_script()
    
    # Step 5: Check PDF directory
    has_pdfs = setup.check_pdf_directory()
    
    if not has_pdfs:
        print("\n⚠️  No PDF files found in knowledge_base/sourced_pdfs/")
        print("   Add your Kenyan government PDF documents there, then run:")
        print("   python setup_kenyan_system.py --rebuild-index")
        print("\n   The system will also fetch documents from official URLs automatically.")
    
    # Step 6: Initialize retrieval system
    print(f"\n📚 Initializing document retrieval system...")
    success = await setup.initialize_retrieval_system(rebuild_index=args.rebuild_index)
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Test the system: python test_kenyan_system.py")
        print("2. Start the backend: cd backend && python -m uvicorn app.main:app --reload")
        print("3. Check the API at: http://localhost:8000/docs")
        
        if not has_pdfs:
            print("\n💡 To improve results, add more PDF documents to knowledge_base/sourced_pdfs/")
            print("   Then rebuild the index with: python setup_kenyan_system.py --rebuild-index")
    else:
        print("\n❌ Setup encountered errors. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())


# backend/app/services/kenyan_ai_service.py
"""
Enhanced AI service specifically for Kenyan government documents and services.
Integrates with the Kenyan document retrieval system.
"""

import asyncio
import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime

from fastapi import HTTPException
from pydantic import BaseModel

# Import our Kenyan-specific components
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from ai_services.retrieval.kenyan_document_retriever import KenyanDocumentRetriever, ContactFormFiller
from ai_services.utils.citations import CitationExtractor, Citation
from ai_services.utils.confidence import ConfidenceScorer, ConfidenceAssessment

logger = logging.getLogger(__name__)

class KenyanChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_context: Optional[Dict] = None
    county: str = "nairobi"  # Default to Nairobi
    language: str = "en"     # English or Swahili

class KenyanChatResponse(BaseModel):
    reply: str
    citations: List[Dict]
    confidence: float
    should_clarify: bool = False
    clarifying_questions: List[str] = []
    conversation_id: str
    contact_form_data: Optional[Dict] = None  # For auto-filling contact forms
    suggested_actions: List[str] = []

class KenyanCivicAIService:
    """Enhanced AI service for Kenyan civic services."""
    
    def __init__(self):
        self.retriever: Optional[KenyanDocumentRetriever] = None
        self.citation_extractor = CitationExtractor()
        self.confidence_scorer = ConfidenceScorer()
        self.contact_filler = ContactFormFiller()
        self.is_initialized = False
        
        # Kenyan-specific response templates
        self.kenyan_responses = {
            "greeting_en": "Jambo! Welcome to CivicNavigator. I can help you with Nairobi County services. What would you like to know?",
            "greeting_sw": "Jambo! Karibu CivicNavigator. Naweza kukusaidia na huduma za Kaunti ya Nairobi. Unataka kujua nini?",
            "no_results": "Samahani, I couldn't find specific information about that in our knowledge base. You can contact Nairobi County directly at 0709 704 704 or visit nairobi.go.ke for more help.",
            "clarification_needed": "Ili nikupe majibu sahihi (to give you accurate answers), please provide more details about your location or specific service needed.",
            "contact_suggestion": "Based on your question, I can help you fill out a contact form to reach the right department. Would you like me to prepare that for you?"
        }
        
        # Common Kenyan service categories with keywords
        self.kenyan_service_keywords = {
            'waste_management': [
                'waste', 'garbage', 'collection', 'takataka', 'uchafu', 'mazingira',
                'recycling', 'disposal', 'dumping', 'bins', 'truck'
            ],
            'business_permits': [
                'business', 'permit', 'license', 'biashara', 'kibali', 'application',
                'sbp', 'single business permit', 'trade', 'shop', 'kiosk'
            ],
            'water_services': [
                'water', 'maji', 'connection', 'bill', 'sewer', 'drainage',
                'plumbing', 'leak', 'shortage', 'rationing', 'borehole'
            ],
            'transport': [
                'matatu', 'boda', 'road', 'barabara', 'traffic', 'parking',
                'driving', 'vehicle', 'inspection', 'route', 'stage'
            ],
            'health_services': [
                'hospital', 'clinic', 'health', 'afya', 'doctor', 'medicine',
                'dispensary', 'vaccination', 'treatment', 'ambulance'
            ],
            'education': [
                'school', 'shule', 'education', 'elimu', 'bursary', 'scholarship',
                'kcpe', 'kcse', 'teacher', 'student', 'fees'
            ]
        }
    
    async def initialize(self):
        """Initialize the Kenyan AI service."""
        if self.is_initialized:
            return
            
        try:
            logger.info("Initializing Kenyan CivicAI Service...")
            
            # Initialize Kenyan document retriever
            kb_path = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base/sourced_pdfs")
            index_path = os.getenv("INDEX_PATH", "./indexes/kenyan_kb")
            
            self.retriever = KenyanDocumentRetriever(
                kb_path=kb_path,
                index_path=index_path
            )
            
            # Load existing index or build new one
            rebuild_index = os.getenv("REBUILD_INDEX", "false").lower() == "true"
            await self.retriever.initialize_full_system(rebuild_index=rebuild_index)
            
            self.is_initialized = True
            logger.info("Kenyan CivicAI Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kenyan AI service: {e}")
            raise HTTPException(status_code=500, detail="AI service initialization failed")
    
    async def process_message(self, message: KenyanChatMessage) -> KenyanChatResponse:
        """Process a message with Kenyan context and government services."""
        
        if not self.is_initialized:
            await self.initialize()
        
        try:
            query = message.message.strip()
            
            # Handle Swahili greetings and basic responses
            if self._is_greeting(query):
                greeting_response = (
                    self.kenyan_responses["greeting_sw"] if message.language == "sw" 
                    else self.kenyan_responses["greeting_en"]
                )
                return KenyanChatResponse(
                    reply=greeting_response,
                    citations=[],
                    confidence=1.0,
                    conversation_id=message.conversation_id or "new",
                    suggested_actions=["Ask about waste collection", "Business permit info", "Water services", "Report an issue"]
                )
            
            # Retrieve relevant documents
            retrieved_docs = self.retriever.search(query, top_k=5)
            
            # Check if we found relevant information
            if not retrieved_docs or retrieved_docs[0]["score"] < 0.3:
                return await self._handle_no_results(message, query)
            
            # Extract citations
            citations = self.citation_extractor.extract_citations_from_retrieval(
                query, retrieved_docs, top_k=3
            )
            
            # Generate contextual response
            response_text = await self._generate_kenyan_response(
                query, retrieved_docs, message.user_context, message.county
            )
            
            # Calculate confidence
            confidence_assessment = self.confidence_scorer.calculate_confidence(
                query=query,
                retrieved_docs=retrieved_docs,
                response_text=response_text,
                citations=citations,
                context=message.user_context
            )
            
            # Extract contact information for form filling
            contact_form_data = None
            if self._should_offer_contact_form(query, confidence_assessment.overall_score):
                contact_info = self.contact_filler.extract_contact_info(retrieved_docs)
                contact_form_data = self.contact_filler.format_for_nairobi_contact_form(
                    contact_info, query
                )
            
            # Generate suggested actions
            suggested_actions = self._generate_suggested_actions(query, retrieved_docs)
            
            # Format citations
            formatted_citations = self.citation_extractor.format_citations_for_display(citations)
            
            return KenyanChatResponse(
                reply=response_text,
                citations=formatted_citations,
                confidence=confidence_assessment.overall_score,
                should_clarify=confidence_assessment.should_clarify,
                clarifying_questions=confidence_assessment.clarifying_questions,
                conversation_id=message.conversation_id or "new",
                contact_form_data=contact_form_data,
                suggested_actions=suggested_actions
            )
            
        except Exception as e:
            logger.error(f"Error processing Kenyan message: {e}")
            return KenyanChatResponse(
                reply="Pole, I'm having trouble processing your request. Please try again or contact Nairobi County at 0709 704 704.",
                citations=[],
                confidence=0.0,
                conversation_id=message.conversation_id or "new"
            )
    
    async def _handle_no_results(self, message: KenyanChatMessage, query: str) -> KenyanChatResponse:
        """Handle cases where no relevant documents are found."""
        
        # Try to categorize the query and provide helpful guidance
        category = self._categorize_query(query)
        
        if category == 'waste_management':
            response = "For waste collection information, you can contact the Environment department at 0709 704 704 or check the collection schedule for your specific ward."
            suggested_actions = ["Contact Environment Department", "Check Ward Collection Schedule", "Visit County Office"]
        
        elif category == 'business_permits':
            response = "For business permits, visit any Huduma Centre or contact Nairobi County Trade department at 0709 704 704. You'll need your ID, KRA PIN, and business location details."
            suggested_actions = ["Visit Huduma Centre", "Contact Trade Department", "Prepare Required Documents"]
        
        elif category == 'water_services':
            response = "For water services, contact Nairobi Water at 0800 720 720 or visit their offices. For new connections, you'll need site plans and location maps."
            suggested_actions = ["Contact Nairobi Water", "Visit Water Offices", "Prepare Connection Documents"]
        
        else:
            response = self.kenyan_responses["no_results"]
            suggested_actions = ["Contact County Call Center", "Visit County Website", "Visit Nearest County Office"]
        
        return KenyanChatResponse(
            reply=response,
            citations=[],
            confidence=0.3,
            should_clarify=True,
            clarifying_questions=[
                "Which specific service are you looking for?",
                "Which area or ward are you located in?",
                "Are you looking to apply for something or get information?"
            ],
            conversation_id=message.conversation_id or "new",
            suggested_actions=suggested_actions
        )
    
    async def _generate_kenyan_response(self, query: str, docs: List[Dict], user_context: Optional[Dict], county: str) -> str:
        """Generate a contextual response for Kenyan users."""
        
        if not docs:
            return self.kenyan_responses["no_results"]
        
        primary_doc = docs[0]
        snippet = primary_doc["snippet"]
        category = primary_doc.get("category", "general")
        
        # Create contextual response based on category and document type
        response_parts = []
        
        # Add main answer
        if category == "waste_management":
            response_parts.append(f"According to the county waste management information: {snippet}")
            
            if "schedule" in query.lower() or "when" in query.lower():
                response_parts.append("For your specific area, collection times may vary. Please confirm with your local ward office or call 0709 704 704.")
        
        elif category == "service_charter":
            response_parts.append(f"Based on the Nairobi County Service Charter: {snippet}")
            response_parts.append("This is the official county commitment to service delivery standards.")
        
        elif category == "business_permits" or "permit" in query.lower():
            response_parts.append(f"For business permits: {snippet}")
            response_parts.append("You can apply at any Huduma Centre or visit the county offices at City Hall.")
        
        elif category == "development_plan":
            response_parts.append(f"According to the County Integrated Development Plan: {snippet}")
            
        else:
            response_parts.append(f"Based on available information: {snippet}")
        
        # Add county-specific context if available
        if county == "nairobi":
            response_parts.append("For additional assistance, contact Nairobi County at 0709 704 704.")
        
        # Add multilingual touch for common terms
        response = " ".join(response_parts)
        
        # Replace some English terms with Kenyan context
        replacements = {
            "garbage": "garbage (takataka)",
            "business": "business (biashara)",
            "water": "water (maji)",
            "office hours": "office hours (masaa ya ofisi)"
        }
        
        for eng, bilingual in replacements.items():
            if eng in response.lower():
                response = response.replace(eng, bilingual, 1)  # Replace first occurrence only
        
        return response
    
    def _categorize_query(self, query: str) -> str:
        """Categorize query using Kenyan service keywords."""
        query_lower = query.lower()
        
        for category, keywords in self.kenyan_service_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def _should_offer_contact_form(self, query: str, confidence: float) -> bool:
        """Determine if we should offer to fill contact form."""
        
        # Offer contact form for specific scenarios
        contact_indicators = [
            'report', 'complaint', 'broken', 'not working', 'problem',
            'apply', 'application', 'how to', 'process', 'requirements'
        ]
        
        query_lower = query.lower()
        has_contact_need = any(indicator in query_lower for indicator in contact_indicators)
        
        # Offer if confidence is medium and user seems to need direct help
        return has_contact_need and 0.4 < confidence < 0.8
    
    def _generate_suggested_actions(self, query: str, docs: List[Dict]) -> List[str]:
        """Generate suggested follow-up actions."""
        
        category = self._categorize_query(query)
        actions = []
        
        if category == 'waste_management':
            actions = [
                "Check your ward collection schedule",
                "Report missed collection",
                "Find nearest waste drop-off point",
                "Learn about recycling programs"
            ]
        
        elif category == 'business_permits':
            actions = [
                "Visit nearest Huduma Centre",
                "Download application forms",
                "Check permit fees",
                "Track application status"
            ]
        
        elif category == 'water_services':
            actions = [
                "Apply for new water connection",
                "Report water issues",
                "Check your water bill",
                "Find water kiosks nearby"
            ]
        
        elif category == 'transport':
            actions = [
                "Check matatu routes",
                "Report transport issues",
                "Find parking information",
                "Get vehicle inspection details"
            ]
        
        else:
            actions = [
                "Contact county offices",
                "Visit county website",
                "Find service locations",
                "Get more information"
            ]
        
        return actions[:4]  # Limit to 4 suggestions
    
    def _is_greeting(self, message: str) -> bool:
        """Check if message is a greeting in English or Swahili."""
        greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "jambo", "habari", "mambo", "hujambo", "shikamoo", "salamu"
        ]
        return any(greeting in message.lower() for greeting in greetings)
    
    async def health_check(self) -> Dict:
        """Health check with Kenyan system status."""
        
        status = {
            "status": "healthy" if self.is_initialized else "initializing",
            "kenyan_retriever_loaded": self.retriever is not None,
            "documents_indexed": len(self.retriever.documents) if self.retriever else 0,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0-kenya",
            "supported_counties": ["nairobi"],  # Can be extended
            "supported_languages": ["en", "sw-basic"]
        }
        
        if self.retriever:
            # Add more detailed stats
            doc_categories = {}
            for doc in self.retriever.documents:
                category = doc.metadata.get('category', 'unknown')
                doc_categories[category] = doc_categories.get(category, 0) + 1
            
            status["document_categories"] = doc_categories
            status["index_file_exists"] = os.path.exists(f"{self.retriever.index_path}.faiss")
        
        return status

# Integration with FastAPI
# backend/app/api/v1/kenyan_chat.py
"""
FastAPI endpoints specifically for Kenyan chat functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict
import json
import logging
from datetime import datetime

from app.services.kenyan_ai_service import KenyanCivicAIService, KenyanChatMessage, KenyanChatResponse
from app.core.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Global Kenyan AI service instance
kenyan_ai_service = KenyanCivicAIService()

@router.on_event("startup")
async def startup_kenyan_service():
    """Initialize Kenyan AI service on startup."""
    try:
        await kenyan_ai_service.initialize()
        logger.info("Kenyan AI service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Kenyan AI service: {e}")

@router.post("/chat/kenyan", response_model=KenyanChatResponse)
async def kenyan_chat_message(
    message: KenyanChatMessage,
    current_user = Depends(get_current_user)
):
    """Process a chat message with Kenyan context."""
    try:
        # Add user context
        message.user_context = {
            "user_id": current_user.id if current_user else None,
            "timestamp": datetime.utcnow().isoformat(),
            "client_ip": "unknown"  # Could be extracted from request
        }
        
        # Process with Kenyan AI service
        response = await kenyan_ai_service.process_message(message)
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing Kenyan chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.post("/contact/auto-fill")
async def auto_fill_contact_form(
    query: str,
    current_user = Depends(get_current_user)
):
    """Auto-fill contact form based on query and available information."""
    try:
        # Search for relevant documents
        docs = kenyan_ai_service.retriever.search(query, top_k=3)
        
        # Extract contact information
        contact_info = kenyan_ai_service.contact_filler.extract_contact_info(docs)
        form_data = kenyan_ai_service.contact_filler.format_for_nairobi_contact_form(
            contact_info, query
        )
        
        return {
            "form_data": form_data,
            "source_documents": [doc["title"] for doc in docs[:2]],
            "confidence": "high" if docs and docs[0]["score"] > 0.7 else "medium"
        }
        
    except Exception as e:
        logger.error(f"Error auto-filling contact form: {e}")
        raise HTTPException(status_code=500, detail="Failed to auto-fill contact form")

@router.get("/kenyan/health")
async def kenyan_health_check():
    """Health check for Kenyan AI service."""
    try:
        health_status = await kenyan_ai_service.health_check()
        return JSONResponse(content=health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)},
            status_code=503
        )

@router.get("/kenyan/stats")
async def kenyan_system_stats():
    """Get statistics about the Kenyan document system."""
    try:
        if not kenyan_ai_service.retriever:
            return {"status": "not_initialized"}
        
        stats = {
            "total_documents": len(kenyan_ai_service.retriever.documents),
            "total_chunks": len(kenyan_ai_service.retriever.chunk_to_doc_mapping),
            "document_sources": {},
            "categories": {},
            "counties": {},
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Analyze documents
        for doc in kenyan_ai_service.retriever.documents:
            # Count by source type
            source_type = doc.metadata.get('source_type', 'unknown')
            stats["document_sources"][source_type] = stats["document_sources"].get(source_type, 0) + 1
            
            # Count by category  
            category = doc.metadata.get('category', 'unknown')
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Count by county
            county = doc.metadata.get('county', 'unknown')
            stats["counties"][county] = stats["counties"].get(county, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting Kenyan system stats: {e}")
        return {"status": "error", "message": str(e)}