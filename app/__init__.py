"""
Civic Educator Project - Package Initialization

A comprehensive civic education platform for promoting civic engagement,
government transparency, and democratic participation.
"""

__version__ = "1.0.0"
__author__ = "Civic Educator Team"
__description__ = "A platform for civic education and democratic engagement"

# Core module imports
from .services.notification_service import NotificationService
from .models import User, Course, Lesson, Quiz, Progress
from .database import DatabaseManager
from .auth import AuthManager
from .content import ContentManager

# Configuration
DEFAULT_CONFIG = {
    'database_url': 'sqlite:///civic_educator.db',
    'secret_key': 'your-secret-key-here',
    'debug': False,
    'notification_settings': {
        'email_enabled': True,
        'sms_enabled': False,
        'push_enabled': True,
        'batch_size': 100,
        'retry_attempts': 3
    },
    'content_settings': {
        'max_upload_size': 10485760,  # 10MB
        'allowed_file_types': ['.pdf', '.mp4', '.mp3', '.jpg', '.png'],
        'content_cache_ttl': 3600  # 1 hour
    }
}

# Application factory
def create_app(config=None):
    """
    Application factory for creating the civic educator app instance.
    
    Args:
        config (dict): Configuration dictionary to override defaults
        
    Returns:
        CivicEducatorApp: Configured application instance
    """
    from main import CivicEducatorApp
    
    app_config = DEFAULT_CONFIG.copy()
    if config:
        app_config.update(config)
    
    app = CivicEducatorApp(app_config)
    return app

# Utility functions
def get_version():
    """Return the current version of the civic educator package."""
    return __version__

def get_supported_languages():
    """Return list of supported languages for civic content."""
    return ['en', 'es', 'fr', 'sw', 'ar']

def get_civic_topics():
    """Return available civic education topics."""
    return [
        'voting_rights',
        'government_structure',
        'civil_rights',
        'public_policy',
        'community_engagement',
        'legal_literacy',
        'budget_transparency',
        'democratic_processes'
    ]

# Exception classes
class CivicEducatorError(Exception):
    """Base exception for civic educator application."""
    pass

class NotificationError(CivicEducatorError):
    """Exception raised for notification service errors."""
    pass

class ContentError(CivicEducatorError):
    """Exception raised for content management errors."""
    pass

class AuthenticationError(CivicEducatorError):
    """Exception raised for authentication errors."""
    pass

# Module level constants
CIVIC_EDUCATION_LEVELS = {
    'BEGINNER': 1,
    'INTERMEDIATE': 2,
    'ADVANCED': 3,
    'EXPERT': 4
}

USER_ROLES = {
    'STUDENT': 'student',
    'EDUCATOR': 'educator',
    'ADMIN': 'admin',
    'MODERATOR': 'moderator'
}

NOTIFICATION_TYPES = {
    'COURSE_REMINDER': 'course_reminder',
    'ASSIGNMENT_DUE': 'assignment_due',
    'NEW_CONTENT': 'new_content',
    'ACHIEVEMENT': 'achievement',
    'SYSTEM_UPDATE': 'system_update'
}

# Initialize logging
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())