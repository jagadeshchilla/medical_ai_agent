"""Email service for sending medical appointment notifications and forms."""

import os
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv
from utils.validators import clean_email, validate_email

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

load_dotenv()


class EmailService:
    """Service for sending emails using SMTP or SendGrid.
    
    This service provides comprehensive email functionality for the medical office system,
    including appointment confirmations, reminders, and intake form distribution.
    It supports both SMTP and SendGrid providers with automatic fallback.
    """
    
    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None,
                 smtp_server: Optional[str] = None, smtp_port: Optional[int] = None,
                 smtp_username: Optional[str] = None, smtp_password: Optional[str] = None):
        """Initialize email service with SMTP and SendGrid configuration.
        
        Args:
            api_key: SendGrid API key
            from_email: Sender email address
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@medicaloffice.com")
        
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME", self.from_email)
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        
        self.sendgrid_available = SENDGRID_AVAILABLE and self.api_key is not None
        self.smtp_available = self.smtp_server and self.smtp_port and self.smtp_username and self.smtp_password
        self.is_available = self.sendgrid_available or self.smtp_available
        
        if not self.is_available:
            if not SENDGRID_AVAILABLE and not self.smtp_available:
                print("Warning: Neither SendGrid nor SMTP is configured. Email service will be simulated.")
            elif not self.sendgrid_available and not self.smtp_available:
                print("Warning: Email service credentials are not set. Email service will be simulated.")
    
    def send_email(self, to_email: str, subject: str, content: str, 
                  attachments: Optional[List[str]] = None, is_html: bool = False) -> Dict[str, Any]:
        """Send an email using SMTP or SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email body content (plain text or HTML)
            attachments: List of file paths to attach
            is_html: Whether content is HTML format
            
        Returns:
            Dict with success status and message
        """
        # Clean and validate email address
        cleaned_email = clean_email(to_email)
        if not cleaned_email:
            return {
                "success": False,
                "message": f"Invalid email address: {to_email}"
            }
        
        # Use the cleaned email
        to_email = cleaned_email
        
        # If no email service is available, simulate sending
        if not self.is_available:
            attachment_info = ""
            if attachments:
                attachment_info = f"\nAttachments: {', '.join(attachments)}"
            
            print(f"\nSIMULATED EMAIL:\nTo: {to_email}\nSubject: {subject}\nContent: {content}{attachment_info}\n")
            return {
                "success": True,
                "message": "Email simulated (no email service available)",
                "to": to_email,
                "subject": subject
            }
        
        # Try SMTP first if available
        if self.smtp_available:
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = self.from_email
                msg['To'] = to_email
                msg['Subject'] = subject
                
                # Attach content (HTML or plain text)
                content_type = 'html' if is_html else 'plain'
                msg.attach(MIMEText(content, content_type))
                
                # Attach files if provided
                if attachments:
                    for file_path in attachments:
                        if os.path.exists(file_path):
                            with open(file_path, 'rb') as file:
                                file_name = os.path.basename(file_path)
                                attachment = MIMEApplication(file.read(), Name=file_name)
                                attachment['Content-Disposition'] = f'attachment; filename="{file_name}"'
                                msg.attach(attachment)
                
                # Connect to SMTP server and send
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                
                return {
                    "success": True,
                    "message": "Email sent successfully via SMTP",
                    "to": to_email,
                    "subject": subject
                }
            except Exception as e:
                print(f"SMTP email failed: {str(e)}. Trying SendGrid if available.")
                # If SMTP fails and SendGrid is not available, simulate email
                if not self.sendgrid_available:
                    print(f"\nSIMULATED EMAIL (SMTP failed):\nTo: {to_email}\nSubject: {subject}\nContent: {content}\n")
                    return {
                        "success": True,
                        "message": f"Email simulated (SMTP failed: {str(e)})",
                        "to": to_email,
                        "subject": subject
                    }
        
        # Try SendGrid if available
        if self.sendgrid_available:
            try:
                # Create SendGrid mail object
                if is_html:
                    message = Mail(
                        from_email=self.from_email,
                        to_emails=to_email,
                        subject=subject,
                        html_content=content
                    )
                else:
                    message = Mail(
                        from_email=self.from_email,
                        to_emails=to_email,
                        subject=subject,
                        plain_text_content=content
                    )
                
                # TODO: Add attachment handling for SendGrid
                # This would require additional code for SendGrid attachments
                
                # Send email using SendGrid
                sg = SendGridAPIClient(self.api_key)
                response = sg.send(message)
                
                return {
                    "success": True,
                    "message": "Email sent successfully via SendGrid",
                    "status_code": response.status_code,
                    "to": to_email,
                    "subject": subject
                }
            except Exception as e:
                print(f"SendGrid email failed: {str(e)}. Simulating email.")
                print(f"\nSIMULATED EMAIL (SendGrid failed):\nTo: {to_email}\nSubject: {subject}\nContent: {content}\n")
                return {
                    "success": True,
                    "message": f"Email simulated (SendGrid failed: {str(e)})",
                    "to": to_email,
                    "subject": subject
                }
        
        # This should not happen, but just in case
        return {
            "success": False,
            "message": "No email service available",
            "to": to_email,
            "subject": subject
        }
    
    def send_intake_form(self, to_email: str, patient_name: str, appointment_date: str, 
                         appointment_time: str = None, doctor: str = None) -> Dict[str, Any]:
        """Send intake form email to patient with PDF attachment.
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            appointment_date: Appointment date
            appointment_time: Appointment time (optional)
            doctor: Doctor name (optional)
            
        Returns:
            Dict with success status and message
        """
        # Format appointment details
        appointment_details = f"on {appointment_date}"
        if appointment_time:
            appointment_details += f" at {appointment_time}"
        if doctor:
            appointment_details += f" with Dr. {doctor}"
        
        subject = f"Intake Form for Your Appointment {appointment_details}"
        
        content = f"Dear {patient_name},\n\n"
        content += f"Thank you for scheduling your appointment {appointment_details}. "
        content += "Please complete the attached intake form before your upcoming appointment. "
        content += "This will help us provide you with the best possible care.\n\n"
        content += "Your appointment has been added to our calendar system. "
        content += "You will receive a reminder 24 hours before your appointment.\n\n"
        content += "If you have any questions or need to reschedule, please don't hesitate to contact our office.\n\n"
        content += "Thank you,\nMedical Office Staff"
        
        # Path to the intake form PDF
        intake_form_path = os.path.join(os.getcwd(), "data", "New Patient Intake Form.pdf")
        
        # Check if the file exists
        if not os.path.exists(intake_form_path):
            print(f"Warning: Intake form PDF not found at {intake_form_path}")
            return self.send_email(to_email, subject, content)
        
        # Send email with attachment
        return self.send_email(to_email, subject, content, attachments=[intake_form_path])
        
    def send_appointment_confirmation(self, to_email: str, patient_name: str, 
                                     appointment_date: str, appointment_time: str,
                                     doctor: str) -> Dict[str, Any]:
        """Send appointment confirmation email to patient.
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            appointment_date: Appointment date
            appointment_time: Appointment time
            doctor: Doctor name
            
        Returns:
            Dict with success status and message
        """
        subject = f"Appointment Confirmation: {appointment_date} at {appointment_time}"
        
        content = f"Dear {patient_name},\n\n"
        content += f"This email confirms your appointment with Dr. {doctor} on {appointment_date} at {appointment_time}.\n\n"
        content += "Please complete the attached New Patient Intake Form and bring it with you to your appointment. "
        content += "This form contains important information about your medical history and current health status that will help us provide you with the best possible care.\n\n"
        content += "Please arrive 15 minutes before your scheduled time to complete any additional paperwork.\n\n"
        content += "If you need to reschedule or cancel, please contact us at least 24 hours in advance.\n\n"
        content += "Thank you,\nMedical Office Staff"
        
        # Path to the intake form PDF
        intake_form_path = os.path.join(os.getcwd(), "data", "New Patient Intake Form.pdf")
        
        # Send email with attachment if the file exists
        if os.path.exists(intake_form_path):
            return self.send_email(to_email, subject, content, attachments=[intake_form_path])
        else:
            return self.send_email(to_email, subject, content)
    
    def send_reminder(self, to_email: str, patient_name: str, doctor: str, 
                     appointment_date: str, appointment_time: str, 
                     reminder_type: int, appointment_id: str = None) -> Dict[str, Any]:
        """Send appointment reminder email based on type.
        
        Args:
            to_email: Patient email address
            patient_name: Patient name
            doctor: Doctor name
            appointment_date: Appointment date
            appointment_time: Appointment time
            reminder_type: 1=Basic, 2=Form+Confirm, 3=Final
            
        Returns:
            Dict with success status and message
        """
        if reminder_type == 1:
            # Basic reminder
            subject = f"Reminder: Upcoming Appointment with Dr. {doctor}"
            content = f"Dear {patient_name},\n\n"
            content += f"This is a friendly reminder about your upcoming appointment with Dr. {doctor} on {appointment_date} at {appointment_time}.\n\n"
            content += "Please make sure to arrive 15 minutes early for your appointment.\n\n"
            content += "If you need to reschedule or cancel, please contact us at least 24 hours in advance.\n\n"
            content += "Thank you,\nMedical Office Staff"
            
        elif reminder_type == 2:
            # Form completion + confirmation reminder
            subject = f"Action Required: Complete Forms & Confirm Appointment with Dr. {doctor}"
            
            # Create HTML content with buttons
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>Dear {patient_name},</p>
                
                <p>Your appointment with Dr. {doctor} on {appointment_date} at {appointment_time} is approaching.</p>
                
                <p><strong>IMPORTANT:</strong> Please complete the attached New Patient Intake Form if you haven't already done so. 
                This form contains important information about your medical history and current health status.</p>
                
                <p>Please confirm your appointment by clicking one of the buttons below:</p>
                
                <div style="margin: 20px 0; text-align: center;">
                    <a href="https://medicalschedulingagent.streamlit.app/confirm?appointment_id={appointment_id}&action=confirm" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; margin: 10px; display: inline-block; font-weight: bold;">
                        ✅ CONFIRM APPOINTMENT
                    </a>
                    <a href="https://medicalschedulingagent.streamlit.app/confirm?appointment_id={appointment_id}&action=cancel" 
                       style="background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; margin: 10px; display: inline-block; font-weight: bold;">
                        ❌ CANCEL APPOINTMENT
                    </a>
                </div>
                
                <p>If you need to reschedule, please contact us at least 24 hours in advance.</p>
                
                <p>Thank you,<br>Medical Office Staff</p>
            </body>
            </html>
            """
            
            # Create plain text fallback
            content = f"Dear {patient_name},\n\n"
            content += f"Your appointment with Dr. {doctor} on {appointment_date} at {appointment_time} is approaching.\n\n"
            content += "IMPORTANT: Please complete the attached New Patient Intake Form if you haven't already done so. "
            content += "This form contains important information about your medical history and current health status.\n\n"
            content += "Please confirm your appointment by clicking one of the links below:\n\n"
            content += f"✅ CONFIRM APPOINTMENT: https://medicalschedulingagent.streamlit.app/confirm?appointment_id={appointment_id}&action=confirm\n\n"
            content += f"❌ CANCEL APPOINTMENT: https://medicalschedulingagent.streamlit.app/confirm?appointment_id={appointment_id}&action=cancel\n\n"
            content += "If you need to reschedule, please contact us at least 24 hours in advance.\n\n"
            content += "Thank you,\nMedical Office Staff"
            
        elif reminder_type == 3:
            # Final check reminder with confirm/cancel option
            subject = f"Final Reminder: Appointment with Dr. {doctor} - Please Confirm"
            
            # Create HTML content with buttons
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>Dear {patient_name},</p>
                
                <p>This is your final reminder about your appointment with Dr. {doctor} on {appointment_date} at {appointment_time}.</p>
                
                <p><strong>URGENT:</strong> Please confirm your attendance by clicking one of the buttons below:</p>
                
                <div style="margin: 20px 0; text-align: center;">
                    <a href="https://medicalschedulingagent.streamlit.app/confirm?appointment_id={appointment_id}&action=confirm" 
                       style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; margin: 10px; display: inline-block; font-weight: bold;">
                        ✅ CONFIRM APPOINTMENT
                    </a>
                    <a href="https://medicalschedulingagent.streamlit.app/confirm?appointment_id={appointment_id}&action=cancel" 
                       style="background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; 
                              border-radius: 5px; margin: 10px; display: inline-block; font-weight: bold;">
                        ❌ CANCEL APPOINTMENT
                    </a>
                </div>
                
                <p>If you haven't completed your intake forms yet, please do so immediately and bring them to your appointment.</p>
                
                <p>Please arrive 15 minutes early for your appointment.</p>
                
                <p>Thank you,<br>Medical Office Staff</p>
            </body>
            </html>
            """
            
            # Create plain text fallback
            content = f"Dear {patient_name},\n\n"
            content += f"This is your final reminder about your appointment with Dr. {doctor} on {appointment_date} at {appointment_time}.\n\n"
            content += "URGENT: Please confirm your attendance by clicking one of the links below:\n\n"
            content += f"✅ CONFIRM APPOINTMENT: https://medicalschedulingagent.streamlit.app/confirm?appointment_id={appointment_id}&action=confirm\n\n"
            content += f"❌ CANCEL APPOINTMENT: https://medicalschedulingagent.streamlit.app/confirm?appointment_id={appointment_id}&action=cancel\n\n"
            content += "If you haven't completed your intake forms yet, please do so immediately and bring them to your appointment.\n\n"
            content += "Please arrive 15 minutes early for your appointment.\n\n"
            content += "Thank you,\nMedical Office Staff"
            
        else:
            return {
                "success": False,
                "message": f"Invalid reminder type: {reminder_type}"
            }
        
        # Path to the intake form PDF
        intake_form_path = os.path.join(os.getcwd(), "data", "New Patient Intake Form.pdf")
        
        # For debugging
        print(f"\nSending reminder type {reminder_type} to {to_email} for appointment {appointment_id}")
        
        # Send email with attachment if the file exists and it's a form reminder
        if reminder_type == 2:
            # For type 2 reminder (form completion + confirmation)
            print(f"Sending Type 2 reminder with HTML content: {html_content[:100]}...")
            if os.path.exists(intake_form_path):
                return self.send_email(to_email, subject, html_content, attachments=[intake_form_path], is_html=True)
            else:
                return self.send_email(to_email, subject, html_content, is_html=True)
        elif reminder_type == 3:
            # For type 3 reminder (final check)
            print(f"Sending Type 3 reminder with HTML content: {html_content[:100]}...")
            return self.send_email(to_email, subject, html_content, is_html=True)
        else:
            # For type 1 reminder (basic)
            print(f"Sending Type 1 reminder with plain text content: {content[:100]}...")
            return self.send_email(to_email, subject, content)