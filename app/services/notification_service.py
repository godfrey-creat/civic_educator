"""
Notification Service for Civic Educator Project

Handles email, SMS, and push notifications for civic education platform,
including course reminders, assignment notifications, and system updates.
"""

import asyncio
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional, Union
import json
import requests
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Enumeration of available notification channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class NotificationTemplate:
    """Template for notifications with civic education context."""
    name: str
    subject: str
    body: str
    channel: NotificationChannel
    category: str
    variables: List[str]

class NotificationService:
    """
    Comprehensive notification service for civic education platform.
    Supports multiple channels and civic-specific notification types.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the notification service.
        
        Args:
            config (dict): Configuration dictionary containing service settings
        """
        self.config = config
        self.email_config = config.get('email', {})
        self.sms_config = config.get('sms', {})
        self.push_config = config.get('push', {})
        
        # Initialize templates
        self.templates = self._load_civic_templates()
        
        # Queue for batch processing
        self.notification_queue = []
        self.batch_size = config.get('batch_size', 100)
        
        # Statistics tracking
        self.stats = {
            'sent': 0,
            'failed': 0,
            'pending': 0,
            'by_channel': {channel.value: 0 for channel in NotificationChannel}
        }
    
    def _load_civic_templates(self) -> Dict[str, NotificationTemplate]:
        """Load civic education specific notification templates."""
        templates = {
            'course_reminder': NotificationTemplate(
                name='course_reminder',
                subject='Civic Education Reminder: {course_name}',
                body='''Hello {user_name},
                
This is a friendly reminder about your civic education course: {course_name}.

Next lesson: {next_lesson}
Due date: {due_date}
Progress: {completion_percentage}%

Your civic engagement journey matters! Continue learning about {topic} to become a more informed citizen.

Best regards,
Civic Educator Team''',
                channel=NotificationChannel.EMAIL,
                category='education',
                variables=['user_name', 'course_name', 'next_lesson', 'due_date', 'completion_percentage', 'topic']
            ),
            
            'voting_reminder': NotificationTemplate(
                name='voting_reminder',
                subject='Important: Upcoming Election Information',
                body='''Dear {user_name},
                
There's an important election coming up in {location}!

Election Date: {election_date}
Registration Deadline: {registration_deadline}
Polling Location: {polling_location}

Make sure you're registered and ready to participate in democracy.
Visit our voting guide for more information: {voting_guide_url}

Your vote matters!
Civic Educator Team''',
                channel=NotificationChannel.EMAIL,
                category='voting',
                variables=['user_name', 'location', 'election_date', 'registration_deadline', 'polling_location', 'voting_guide_url']
            ),
            
            'achievement_unlocked': NotificationTemplate(
                name='achievement_unlocked',
                subject='🏆 Civic Achievement Unlocked!',
                body='''Congratulations {user_name}!

You've unlocked a new civic achievement: {achievement_name}

Description: {achievement_description}
Points Earned: {points}
Total Civic Score: {total_score}

Keep up the great work in building your civic knowledge!

Civic Educator Team''',
                channel=NotificationChannel.PUSH,
                category='achievement',
                variables=['user_name', 'achievement_name', 'achievement_description', 'points', 'total_score']
            ),
            
            'community_event': NotificationTemplate(
                name='community_event',
                subject='Community Engagement Opportunity: {event_name}',
                body='''Hello {user_name},
                
There's a community engagement opportunity in your area:

Event: {event_name}
Date: {event_date}
Location: {event_location}
Description: {event_description}

This is a great opportunity to apply your civic knowledge in real-world action!

Register here: {registration_url}

Civic Educator Team''',
                channel=NotificationChannel.EMAIL,
                category='community',
                variables=['user_name', 'event_name', 'event_date', 'event_location', 'event_description', 'registration_url']
            )
        }
        
        return templates
    
    async def send_notification(self, 
                              recipient: str,
                              template_name: str,
                              variables: Dict[str, str],
                              channel: Optional[NotificationChannel] = None,
                              priority: NotificationPriority = NotificationPriority.MEDIUM) -> bool:
        """
        Send a single notification using specified template.
        
        Args:
            recipient: Recipient contact (email, phone, user_id)
            template_name: Name of the template to use
            variables: Variables to substitute in template
            channel: Specific channel to use (overrides template default)
            priority: Notification priority level
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            template = self.templates.get(template_name)
            if not template:
                logger.error(f"Template '{template_name}' not found")
                return False
            
            # Use specified channel or template default
            notification_channel = channel or template.channel
            
            # Prepare notification content
            subject = self._substitute_variables(template.subject, variables)
            body = self._substitute_variables(template.body, variables)
            
            # Send based on channel
            success = False
            if notification_channel == NotificationChannel.EMAIL:
                success = await self._send_email(recipient, subject, body)
            elif notification_channel == NotificationChannel.SMS:
                success = await self._send_sms(recipient, body)
            elif notification_channel == NotificationChannel.PUSH:
                success = await self._send_push(recipient, subject, body)
            elif notification_channel == NotificationChannel.IN_APP:
                success = await self._send_in_app(recipient, subject, body)
            
            # Update statistics
            if success:
                self.stats['sent'] += 1
                self.stats['by_channel'][notification_channel.value] += 1
                logger.info(f"Notification sent successfully to {recipient} via {notification_channel.value}")
            else:
                self.stats['failed'] += 1
                logger.error(f"Failed to send notification to {recipient}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            self.stats['failed'] += 1
            return False
    
    async def send_bulk_notifications(self, 
                                    notifications: List[Dict[str, Any]],
                                    batch_size: Optional[int] = None) -> Dict[str, int]:
        """
        Send multiple notifications in batches.
        
        Args:
            notifications: List of notification dictionaries
            batch_size: Override default batch size
            
        Returns:
            dict: Statistics of sent/failed notifications
        """
        batch_size = batch_size or self.batch_size
        results = {'sent': 0, 'failed': 0}
        
        for i in range(0, len(notifications), batch_size):
            batch = notifications[i:i + batch_size]
            batch_tasks = []
            
            for notification in batch:
                task = self.send_notification(
                    recipient=notification['recipient'],
                    template_name=notification['template_name'],
                    variables=notification.get('variables', {}),
                    channel=notification.get('channel'),
                    priority=notification.get('priority', NotificationPriority.MEDIUM)
                )
                batch_tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results['failed'] += 1
                elif result:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
            
            # Brief pause between batches
            await asyncio.sleep(0.1)
        
        logger.info(f"Bulk notification complete: {results['sent']} sent, {results['failed']} failed")
        return results
    
    async def send_civic_course_reminder(self, user_email: str, course_data: Dict[str, Any]) -> bool:
        """Send a civic education course reminder."""
        return await self.send_notification(
            recipient=user_email,
            template_name='course_reminder',
            variables=course_data,
            priority=NotificationPriority.MEDIUM
        )
    
    async def send_voting_reminder(self, user_email: str, election_data: Dict[str, Any]) -> bool:
        """Send voting reminder with election information."""
        return await self.send_notification(
            recipient=user_email,
            template_name='voting_reminder',
            variables=election_data,
            priority=NotificationPriority.HIGH
        )
    
    async def send_achievement_notification(self, user_id: str, achievement_data: Dict[str, Any]) -> bool:
        """Send achievement unlock notification."""
        return await self.send_notification(
            recipient=user_id,
            template_name='achievement_unlocked',
            variables=achievement_data,
            channel=NotificationChannel.PUSH,
            priority=NotificationPriority.HIGH
        )
    
    def _substitute_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Substitute variables in template text."""
        for key, value in variables.items():
            text = text.replace(f'{{{key}}}', str(value))
        return text
    
    async def _send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send email notification."""
        try:
            smtp_server = self.email_config.get('smtp_server', 'localhost')
            smtp_port = self.email_config.get('smtp_port', 587)
            username = self.email_config.get('username')
            password = self.email_config.get('password')
            sender_email = self.email_config.get('sender_email')
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return False
    
    async def _send_sms(self, recipient: str, message: str) -> bool:
        """Send SMS notification."""
        try:
            # Implementation would depend on SMS service provider (Twilio, etc.)
            sms_api_url = self.sms_config.get('api_url')
            api_key = self.sms_config.get('api_key')
            
            if not sms_api_url or not api_key:
                logger.warning("SMS configuration incomplete")
                return False
            
            # Mock SMS sending (replace with actual SMS service)
            logger.info(f"SMS sent to {recipient}: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return False
    
    async def _send_push(self, recipient: str, title: str, body: str) -> bool:
        """Send push notification."""
        try:
            push_service_url = self.push_config.get('service_url')
            api_key = self.push_config.get('api_key')
            
            if not push_service_url or not api_key:
                logger.warning("Push notification configuration incomplete")
                return False
            
            # Mock push notification (replace with actual push service)
            logger.info(f"Push notification sent to {recipient}: {title}")
            return True
        except Exception as e:
            logger.error(f"Push notification failed: {str(e)}")
            return False
    
    async def _send_in_app(self, recipient: str, title: str, body: str) -> bool:
        """Send in-app notification."""
        try:
            # Store in-app notification in database or cache
            notification_data = {
                'recipient': recipient,
                'title': title,
                'body': body,
                'timestamp': datetime.now().isoformat(),
                'read': False
            }
            
            # Mock in-app notification storage
            logger.info(f"In-app notification stored for {recipient}")
            return True
        except Exception as e:
            logger.error(f"In-app notification failed: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification service statistics."""
        return {
            'total_sent': self.stats['sent'],
            'total_failed': self.stats['failed'],
            'pending_in_queue': len(self.notification_queue),
            'by_channel': self.stats['by_channel'],
            'templates_available': len(self.templates),
            'success_rate': (self.stats['sent'] / max(1, self.stats['sent'] + self.stats['failed'])) * 100
        }
    
    def add_custom_template(self, template: NotificationTemplate) -> bool:
        """Add a custom notification template."""
        try:
            self.templates[template.name] = template
            logger.info(f"Custom template '{template.name}' added successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to add custom template: {str(e)}")
            return False