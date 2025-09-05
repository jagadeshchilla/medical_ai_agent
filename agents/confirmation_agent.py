"""
Confirmation Agent for Medical Appointment System

This module provides the ConfirmationAgent class responsible for managing appointment
confirmations, sending confirmation emails, and handling the finalization process
for scheduled appointments.
"""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
import os

from services.email_service import EmailService
from services.calendar_service import CalendarService
from utils.validators import clean_email, validate_email


class ConfirmationAgent:
    """Agent responsible for confirming appointments and managing the confirmation process.
    
    The ConfirmationAgent handles the final steps of appointment scheduling including
    writing appointment data to the database, sending confirmation emails, and
    coordinating with other services for complete appointment setup.
    
    Attributes:
        appointments_csv_path (str): Path to the appointments CSV file
        patients_csv_path (str): Path to the patients CSV file
        email_service: Email service instance for sending confirmations
        calendar_service: Calendar service instance for appointment management
    """
    
    def __init__(self, appointments_csv_path: str = "data/doctor_appointments.csv",
                 patients_csv_path: str = "data/patients.csv"):
        """Initialize the ConfirmationAgent with data paths and service instances.
        
        Args:
            appointments_csv_path: Path to the appointments CSV file
            patients_csv_path: Path to the patients CSV file
        """
        self.appointments_csv_path = appointments_csv_path
        self.patients_csv_path = patients_csv_path
        self.email_service = EmailService()
        self.calendar_service = CalendarService()
        
        self._initialize_appointments_file()
    
    def _initialize_appointments_file(self):
        """Initialize appointments CSV file if it doesn't exist."""
        if not os.path.exists(self.appointments_csv_path):
            os.makedirs(os.path.dirname(self.appointments_csv_path), exist_ok=True)
            
            appointments_df = pd.DataFrame(columns=[
                "AppointmentID", "PatientID", "PatientName", "Doctor", 
                "Date", "StartTime", "EndTime", "Duration", 
                "InsuranceCarrier", "MemberID", "GroupNumber",
                "ConfirmationStatus", "RemindersSent"
            ])
            
            appointments_df.to_csv(self.appointments_csv_path, index=False)
    
    def load_appointments(self) -> pd.DataFrame:
        """Load appointment data from calendar service or CSV file.
        
        Returns:
            DataFrame containing appointment data with standard columns
        """
        try:
            appointments = self.calendar_service.get_upcoming_appointments(days=30)
            if appointments:
                return pd.DataFrame(appointments)
            
            if os.path.exists(self.appointments_csv_path):
                return pd.read_csv(self.appointments_csv_path)
            
            return pd.DataFrame(columns=[
                "appointment_id", "patient_id", "patient_name", "doctor", 
                "date", "time", "status", "email", "phone", "created_at"
            ])
        except Exception as e:
            print(f"Error loading appointments data: {e}")
            return pd.DataFrame(columns=[
                "appointment_id", "patient_id", "patient_name", "doctor", 
                "date", "time", "status", "email", "phone", "created_at"
            ])
    
    def save_appointments(self, appointments_df: pd.DataFrame) -> bool:
        """Save appointment data to CSV file and calendar service.
        
        Args:
            appointments_df: DataFrame containing appointment data
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            if os.path.exists(self.appointments_csv_path):
                appointments_df.to_csv(self.appointments_csv_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving appointments data: {e}")
            return False
    
    def load_patients(self) -> pd.DataFrame:
        """Load patient data from CSV file.
        
        Returns:
            DataFrame containing patient data with standard columns
        """
        try:
            return pd.read_csv(self.patients_csv_path)
        except Exception as e:
            print(f"Error loading patients data: {e}")
            return pd.DataFrame(columns=[
                "PatientID", "Name", "DOB", "Email", "Phone", 
                "DoctorPreference", "PatientType", "InsuranceCarrier", 
                "MemberID", "GroupNumber"
            ])
    
    def write_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Write appointment information to calendar service and CSV file.
        
        Args:
            appointment_data: Dictionary containing appointment information
            
        Returns:
            Dictionary with success status and appointment ID
        """
        appointment_to_add = {}
        
        field_mapping = {
            "AppointmentID": "appointment_id",
            "PatientID": "patient_id",
            "PatientName": "patient_name",
            "Doctor": "doctor",
            "Date": "date",
            "StartTime": "time",
            "Email": "email",
            "Phone": "phone",
            "ConfirmationStatus": "status"
        }
        
        for old_field, new_field in field_mapping.items():
            if old_field in appointment_data:
                appointment_to_add[new_field] = appointment_data[old_field]
            elif new_field in appointment_data:
                appointment_to_add[new_field] = appointment_data[new_field]
        
        if "email" in appointment_to_add:
            cleaned_email = clean_email(appointment_to_add["email"])
            if cleaned_email:
                appointment_to_add["email"] = cleaned_email
            else:
                return {
                    "success": False,
                    "message": "Invalid email address format."
                }
        
        if "appointment_id" not in appointment_to_add:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            count = len(self.load_appointments()) + 1
            appointment_to_add["appointment_id"] = f"APT-{timestamp}-{count}"
        
        if "status" not in appointment_to_add:
            appointment_to_add["status"] = "pending"
        
        appointment_to_add["created_at"] = datetime.now().isoformat()
        
        calendar_result = {"success": False, "message": "Missing required fields for booking"}
        
        required_fields = ["patient_id", "patient_name", "doctor", "date", "time", "email"]
        if all(field in appointment_to_add for field in required_fields):
            calendar_result = self.calendar_service.book_appointment(
                patient_id=appointment_to_add["patient_id"],
                patient_name=appointment_to_add["patient_name"],
                doctor=appointment_to_add["doctor"],
                date=str(appointment_to_add["date"]),
                time=appointment_to_add["time"],
                email=appointment_to_add["email"]
            )
        
        appointments_df = self.load_appointments()
        appointments_df = pd.concat([appointments_df, pd.DataFrame([appointment_to_add])], ignore_index=True)
        save_success = self.save_appointments(appointments_df)
        
        if calendar_result.get("success", False) or save_success:
            return {
                "success": True,
                "message": "Appointment successfully saved.",
                "appointment_id": appointment_to_add["appointment_id"]
            }
        else:
            return {
                "success": False,
                "message": "Failed to save appointment."
            }
    
    def show_appointment_summary(self, patient_info: Dict[str, Any], 
                                appointment_info: Dict[str, Any], 
                                insurance_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete appointment summary for user confirmation.
        
        Args:
            patient_info: Dictionary containing patient information
            appointment_info: Dictionary containing appointment details
            insurance_info: Dictionary containing insurance information
            
        Returns:
            Dictionary containing formatted summary and confirmation message
        """
        start_time = appointment_info.get("StartTime", "")
        duration = appointment_info.get("Duration", 30)
        
        from datetime import datetime, timedelta
        try:
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = start_dt + timedelta(minutes=duration)
            end_time = end_dt.strftime("%H:%M")
        except:
            end_time = "Unknown"
        
        summary = {
            "patient_name": patient_info.get("Name", ""),
            "patient_dob": patient_info.get("DOB", ""),
            "patient_email": patient_info.get("Email", ""),
            "patient_phone": patient_info.get("Phone", ""),
            "patient_location": patient_info.get("Location", ""),
            "doctor": appointment_info.get("Doctor", ""),
            "appointment_date": appointment_info.get("Date", ""),
            "appointment_time": f"{start_time} - {end_time}",
            "appointment_duration": f"{duration} minutes",
            "patient_type": "New" if not patient_info.get("PatientID") else "Returning",
            "insurance_carrier": insurance_info.get("InsuranceCarrier", ""),
            "member_id": insurance_info.get("MemberID", ""),
            "group_number": insurance_info.get("GroupNumber", "")
        }
        
        confirmation_message = f"""
📋 **APPOINTMENT CONFIRMATION SUMMARY**

**Patient Information:**
• Name: {summary['patient_name']}
• Date of Birth: {summary['patient_dob']}
• Email: {summary['patient_email']}
• Phone: {summary['patient_phone']}
• Location: {summary['patient_location']}

**Appointment Details:**
• Doctor: {summary['doctor']}
• Date: {summary['appointment_date']}
• Time: {summary['appointment_time']}
• Duration: {summary['appointment_duration']}
• Patient Type: {summary['patient_type']}

**Insurance Information:**
• Carrier: {summary['insurance_carrier']}
• Member ID: {summary['member_id']}
• Group Number: {summary['group_number']}

Please review all the information above. Is everything correct?
Type 'yes' to confirm and proceed, or 'no' to make changes.
        """.strip()
        
        return {
            "success": True,
            "summary": summary,
            "confirmation_message": confirmation_message
        }
    
    def finalize_appointment(self, patient_info: Dict[str, Any], 
                           appointment_info: Dict[str, Any], 
                           insurance_info: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize appointment by saving to database and sending confirmation emails.
        
        Args:
            patient_info: Dictionary containing patient information
            appointment_info: Dictionary containing appointment details
            insurance_info: Dictionary containing insurance information
            
        Returns:
            Dictionary with success status and detailed results
        """
        try:
            from utils.data_loader import DataLoader
            patient_id = patient_info.get("PatientID")
            
            DataLoader.add_patient(
                name=patient_info.get("Name", ""),
                dob=patient_info.get("DOB", ""),
                email=patient_info.get("Email", ""),
                phone=patient_info.get("Phone", ""),
                doctor_preference=patient_info.get("DoctorPreference", ""),
                insurance_carrier=insurance_info.get("InsuranceCarrier", ""),
                member_id=insurance_info.get("MemberID", ""),
                group_number=insurance_info.get("GroupNumber", ""),
                location=patient_info.get("Location", "")
            )
            
            from datetime import datetime, date, timedelta
            appointment_date_value = appointment_info.get("Date", "")
            
            if isinstance(appointment_date_value, str):
                appointment_date = datetime.strptime(appointment_date_value, "%Y-%m-%d").date()
            elif isinstance(appointment_date_value, date):
                appointment_date = appointment_date_value
            else:
                appointment_date = date.today()
            
            start_time = appointment_info.get("StartTime", "")
            duration = appointment_info.get("Duration", 30)
            
            try:
                start_dt = datetime.strptime(start_time, "%H:%M")
                end_dt = start_dt + timedelta(minutes=duration)
                end_time = end_dt.strftime("%H:%M")
            except:
                end_time = appointment_info.get("EndTime", "")
            
            appointment_id = DataLoader.add_appointment(
                patient_id=patient_id,
                patient_name=patient_info.get("Name", ""),
                doctor=appointment_info.get("Doctor", ""),
                date=appointment_date,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                insurance_carrier=insurance_info.get("InsuranceCarrier", ""),
                member_id=insurance_info.get("MemberID", ""),
                group_number=insurance_info.get("GroupNumber", "")
            )
            
            from services.calendar_service import CalendarService
            calendar_service = CalendarService()
            
            availability_date = appointment_info.get("Date", "")
            if isinstance(availability_date, date):
                availability_date = availability_date.strftime("%Y-%m-%d")
            
            availability_result = calendar_service.update_availability_status(
                appointment_info.get("Doctor", ""),
                availability_date,
                appointment_info.get("StartTime", ""),
                "Booked"
            )
            
            print(f"Availability update result: {availability_result}")
            
            confirmation_email_result = self.email_service.send_appointment_confirmation(
                to_email=patient_info.get("Email", ""),
                patient_name=patient_info.get("Name", ""),
                appointment_date=appointment_info.get("Date", ""),
                appointment_time=appointment_info.get("StartTime", ""),
                doctor=appointment_info.get("Doctor", "")
            )
            
            form_reminder_result = self.email_service.send_reminder(
                to_email=patient_info.get("Email", ""),
                patient_name=patient_info.get("Name", ""),
                doctor=appointment_info.get("Doctor", ""),
                appointment_date=appointment_info.get("Date", ""),
                appointment_time=appointment_info.get("StartTime", ""),
                reminder_type=2,
                appointment_id=appointment_id
            )
            
            return {
                "success": True,
                "message": "Appointment has been successfully confirmed and saved!",
                "appointment_id": appointment_id,
                "availability_updated": availability_result.get("success", False),
                "availability_message": availability_result.get("message", ""),
                "confirmation_email_sent": confirmation_email_result.get("success", False),
                "form_reminder_sent": form_reminder_result.get("success", False),
                "confirmation_email_message": confirmation_email_result.get("message", ""),
                "form_reminder_message": form_reminder_result.get("message", "")
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error finalizing appointment: {str(e)}"
            }
    
    def send_confirmation_email(self, patient_email: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send confirmation email to patient with intake form attached.
        
        Args:
            patient_email: Patient's email address
            appointment_data: Dictionary containing appointment details
            
        Returns:
            Dictionary with email sending results and reminder status
        """
        doctor = appointment_data.get("doctor", appointment_data.get("Doctor", "your doctor"))
        date = appointment_data.get("date", appointment_data.get("Date", "the scheduled date"))
        time = appointment_data.get("time", appointment_data.get("StartTime", "the scheduled time"))
        patient_name = appointment_data.get("patient_name", appointment_data.get("PatientName", "Patient"))
        appointment_id = appointment_data.get("appointment_id", appointment_data.get("AppointmentID"))
        
        email_result = self.email_service.send_appointment_confirmation(
            patient_email, patient_name, date, time, doctor
        )
        
        if email_result.get("success", False) and appointment_id:
            from agents.reminder_agent import ReminderAgent
            reminder_agent = ReminderAgent()
            reminder_result = reminder_agent.schedule_immediate_reminder(appointment_id)
            email_result["immediate_reminder"] = reminder_result
        
        return email_result
    
    
    def update_confirmation_status(self, appointment_id: str, status: str) -> Dict[str, Any]:
        """Update confirmation status for an appointment.
        
        Args:
            appointment_id: ID of the appointment to update
            status: New confirmation status
            
        Returns:
            Dictionary with success status and message
        """
        appointments_df = self.load_appointments()
        
        if "AppointmentID" in appointments_df.columns:
            appointment_mask = appointments_df["AppointmentID"] == appointment_id
        elif "appointment_id" in appointments_df.columns:
            appointment_mask = appointments_df["appointment_id"] == appointment_id
        else:
            return {
                "success": False,
                "message": "Appointment ID column not found in dataframe."
            }
            
        if not any(appointment_mask):
            return {
                "success": False,
                "message": f"Appointment with ID {appointment_id} not found."
            }
        
        if "ConfirmationStatus" in appointments_df.columns:
            appointments_df.loc[appointment_mask, "ConfirmationStatus"] = status
        elif "status" in appointments_df.columns:
            appointments_df.loc[appointment_mask, "status"] = status
        else:
            appointments_df["ConfirmationStatus"] = None
            appointments_df.loc[appointment_mask, "ConfirmationStatus"] = status
        
        save_success = self.save_appointments(appointments_df)
        
        if save_success:
            return {
                "success": True,
                "message": f"Confirmation status updated to '{status}'.",
                "appointment_id": appointment_id
            }
        else:
            return {
                "success": False,
                "message": "Failed to update confirmation status."
            }
    
    def process_confirmation(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process appointment confirmation by sending email and updating status.
        
        Args:
            appointment_data: Dictionary containing appointment information
            
        Returns:
            Dictionary with confirmation processing results
        """
        patient_email = appointment_data.get("email", appointment_data.get("Email", None))
        appointment_id = appointment_data.get("appointment_id", appointment_data.get("AppointmentID", None))
        
        email_result = {"success": False, "message": "Email not sent"}
        
        if patient_email:
            email_result = self.send_confirmation_email(patient_email, appointment_data)
        
        if appointment_id and email_result.get("success", False):
            self.update_confirmation_status(appointment_id, "Sent")
        
        return {
            "success": email_result.get("success", False),
            "message": email_result.get("message", "No confirmation sent"),
            "appointment_id": appointment_id
        }