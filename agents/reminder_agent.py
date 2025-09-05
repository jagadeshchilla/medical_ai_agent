"""
Reminder Agent for Medical Appointment System

This module provides the ReminderAgent class responsible for sending appointment reminders.
The agent sends three types of reminders via email and updates appointment records with reminder status.
"""

import pandas as pd
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import string

from services.email_service import EmailService
from services.calendar_service import CalendarService


class ReminderAgent:
    """Agent responsible for sending appointment reminders.
    
    This agent sends three types of reminders via email:
    1. Basic reminder
    2. Form completion reminder + confirmation request
    3. Final check reminder with confirm/cancel option
    
    It also updates the appointment record with reminder status.
    
    Attributes:
        appointments_csv_path (str): Path to the appointments CSV file
        patients_csv_path (str): Path to the patients CSV file
        email_service: Service for sending email reminders
        calendar_service: Service for calendar operations
        logger: Logger instance for debugging
    """
    
    def __init__(self, appointments_csv_path: str = "data/doctor_appointments.csv",
                 patients_csv_path: str = "data/patients.csv"):
        """Initialize the ReminderAgent.
        
        Args:
            appointments_csv_path: Path to the appointments CSV file
            patients_csv_path: Path to the patients CSV file
        """
        self.appointments_csv_path = appointments_csv_path
        self.patients_csv_path = patients_csv_path
        self.email_service = EmailService()
        self.calendar_service = CalendarService()
        self.logger = logging.getLogger(__name__)
    
    def load_appointments(self) -> pd.DataFrame:
        """Load appointment data from CSV file.
        
        Returns:
            DataFrame containing appointment data or empty DataFrame with expected columns if file doesn't exist
        """
        try:
            df = pd.read_csv(self.appointments_csv_path)
            if 'appointment_id' in df.columns and 'AppointmentID' not in df.columns:
                df['AppointmentID'] = df['appointment_id']
            return df
        except Exception as e:
            print(f"Error loading appointments data: {e}")
            return pd.DataFrame(columns=[
                "AppointmentID", "PatientID", "PatientName", "Doctor", 
                "Date", "StartTime", "EndTime", "Duration", 
                "InsuranceCarrier", "MemberID", "GroupNumber",
                "ConfirmationStatus", "RemindersSent", "FormSent"
            ])
    
    def save_appointments(self, appointments_df: pd.DataFrame) -> bool:
        """Save appointment data to CSV file.
        
        Args:
            appointments_df: DataFrame containing appointment data to save
            
        Returns:
            Boolean indicating success of save operation
        """
        try:
            appointments_df.to_csv(self.appointments_csv_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving appointments data: {e}")
            return False
    
    def load_patients(self) -> pd.DataFrame:
        """Load patient data from CSV file.
        
        Returns:
            DataFrame containing patient data or empty DataFrame with expected columns if file doesn't exist
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
    
    def get_upcoming_appointments(self, days_ahead: int = 7) -> pd.DataFrame:
        """Get appointments scheduled within the next X days.
        
        Args:
            days_ahead: Number of days to look ahead for appointments
            
        Returns:
            DataFrame containing upcoming appointments within the specified date range
        """
        appointments_df = self.load_appointments()
        
        if appointments_df.empty:
            return appointments_df
        
        if appointments_df["Date"].dtype != 'datetime64[ns]':
            try:
                appointments_df["Date"] = pd.to_datetime(appointments_df["Date"])
            except Exception as e:
                print(f"Error converting dates: {e}")
                return pd.DataFrame()
        
        today = datetime.now().date()
        future_date = today + timedelta(days=days_ahead)
        
        date_mask = (appointments_df["Date"].dt.date >= today) & \
                    (appointments_df["Date"].dt.date <= future_date)
        
        return appointments_df[date_mask]
    
    def get_patient_contact_info(self, patient_id: str) -> Dict[str, str]:
        """Get patient contact information (email and phone).
        
        Args:
            patient_id: Patient ID to look up
            
        Returns:
            Dictionary containing email and phone information
        """
        patients_df = self.load_patients()
        
        patient_mask = patients_df["PatientID"] == patient_id
        if not any(patient_mask):
            return {"email": "", "phone": ""}
        
        patient = patients_df[patient_mask].iloc[0]
        
        return {
            "email": patient.get("Email", ""),
            "phone": patient.get("Phone", "")
        }
    
    def send_reminder(self, appointment_id: str, reminder_type: int = 1) -> Dict[str, Any]:
        """Send a specific type of reminder for an appointment.
        
        Args:
            appointment_id: ID of the appointment to send reminder for
            reminder_type: Type of reminder (1=Basic, 2=Form+Confirm, 3=Final)
            
        Returns:
            Dictionary containing success status and details about the reminder sent
        """
        appointments_df = self.load_appointments()
        
        appointment_mask = False
        
        print(f"Looking for appointment with ID: {appointment_id}")
        print(f"Available columns: {appointments_df.columns.tolist()}")
        
        appointment_mask = pd.Series([False] * len(appointments_df))
        
        if "AppointmentID" in appointments_df.columns:
            appointment_mask = appointments_df["AppointmentID"].astype(str) == str(appointment_id)
            print(f"Searching by AppointmentID, found: {any(appointment_mask)}")
            if any(appointment_mask):
                print(f"Found appointment with ID: {appointment_id}")
        
        if not any(appointment_mask) and "appointment_id" in appointments_df.columns:
            appointment_mask = appointments_df["appointment_id"].astype(str) == str(appointment_id)
            print(f"Searching by appointment_id, found: {any(appointment_mask)}")
            if any(appointment_mask):
                print(f"Found appointment with ID: {appointment_id}")
            
        if not any(appointment_mask):
            try:
                appointments = self.calendar_service.get_upcoming_appointments()
                if isinstance(appointments, pd.DataFrame) and not appointments.empty:
                    for col in appointments.columns:
                        if col.lower() == "appointmentid" or col.lower() == "appointment_id":
                            appointment_mask = appointments[col] == appointment_id
                            if any(appointment_mask):
                                appointments_df = appointments
                                break
            except Exception as e:
                self.logger.error(f"Error getting appointments from calendar service: {e}")
            
            if not any(appointment_mask):
                return {
                    "success": False,
                    "message": f"Appointment with ID {appointment_id} not found."
                }
        
        appointment = appointments_df[appointment_mask].iloc[0]
        
        patient_email = appointment.get("email", appointment.get("Email", ""))
        
        if not patient_email:
            try:
                patient_id = appointment.get("PatientID", appointment.get("patient_id"))
                if patient_id:
                    contact_info = self.get_patient_contact_info(patient_id)
                    patient_email = contact_info.get("email", "")
            except Exception as e:
                print(f"Error looking up patient contact info: {e}")
        
        if not patient_email:
            return {
                "success": False,
                "message": "No email address found for patient.",
                "appointment_id": appointment_id
            }
        
        patient_name = appointment.get("patient_name", appointment.get("PatientName", "Patient"))
        doctor = appointment.get("doctor", appointment.get("Doctor", "your doctor"))
        date = appointment.get("date", appointment.get("Date", "your scheduled date"))
        start_time = appointment.get("time", appointment.get("StartTime", appointment.get("start_time", "your scheduled time")))
        
        if isinstance(date, datetime):
            date = date.strftime("%A, %B %d, %Y")
        if isinstance(start_time, datetime):
            start_time = start_time.strftime("%I:%M %p")
        
        email_result = {"success": False, "message": "Email not sent"}
        if patient_email:
            email_result = self.email_service.send_reminder(
                patient_email,
                patient_name,
                doctor,
                date,
                start_time,
                reminder_type,
                appointment_id
            )
        
        if email_result["success"]:
            current_reminders = appointment.get("RemindersSent", 0)
            try:
                current_reminders = int(current_reminders) if current_reminders is not None else 0
            except (ValueError, TypeError):
                current_reminders = 0
            
            new_reminder_count = current_reminders + 1
            
            try:
                appointments_df.loc[appointment_mask, "RemindersSent"] = new_reminder_count
                appointments_df.to_csv(self.appointments_csv_path, index=False)
                print(f"Updated RemindersSent from {current_reminders} to {new_reminder_count} for appointment {appointment_id}")
            except Exception as e:
                print(f"Error updating reminder status: {e}")
        
        return {
            "success": email_result["success"],
            "message": f"Reminder type {reminder_type} sent.",
            "appointment_id": appointment_id,
            "reminder_type": reminder_type,
            "email_result": email_result
        }
    
    def process_reminders(self, days_ahead: int = 7) -> Dict[str, Any]:
        """Process smart reminders for upcoming appointments based on timing.
        
        Args:
            days_ahead: Number of days to look ahead for appointments
            
        Returns:
            Dictionary containing processing results and statistics
        """
        upcoming_appointments = self.get_upcoming_appointments(days_ahead)
        
        if upcoming_appointments.empty:
            return {
                "success": True,
                "message": "No upcoming appointments to process.",
                "reminders_sent": 0
            }
        
        if "RemindersSent" not in upcoming_appointments.columns:
            upcoming_appointments["RemindersSent"] = 0
        
        today = datetime.now().date()
        
        date_column = None
        if "Date" in upcoming_appointments.columns:
            date_column = "Date"
        elif "date" in upcoming_appointments.columns:
            date_column = "date"
        else:
            return {
                "success": False,
                "message": "No date column found in appointments data.",
                "reminders_sent": 0
            }
        
        try:
            upcoming_appointments[date_column] = pd.to_datetime(upcoming_appointments[date_column])
            upcoming_appointments["DaysUntil"] = (upcoming_appointments[date_column].dt.date - today).dt.days
        except Exception as e:
            print(f"Error processing dates: {e}")
            return {
                "success": False,
                "message": f"Error processing appointment dates: {str(e)}",
                "reminders_sent": 0
            }
        
        reminders_sent = 0
        results = []
        
        for _, appointment in upcoming_appointments.iterrows():
            appointment_id = None
            for id_col in ["appointment_id", "AppointmentID", "appointmentid"]:
                if id_col in appointment and not pd.isna(appointment[id_col]):
                    appointment_id = appointment[id_col]
                    print(f"Found appointment ID {appointment_id} in column {id_col}")
                    break
            
            if not appointment_id:
                print(f"Warning: Could not find appointment ID in columns: {appointment.index.tolist()}")
                continue
                
            days_until = appointment["DaysUntil"]
            reminders_sent_count = appointment["RemindersSent"]
            
            reminder_type = self._determine_reminder_type(days_until, reminders_sent_count)
            
            if reminder_type:
                result = self.send_reminder(appointment_id, reminder_type)
                results.append(result)
                
                if result["success"]:
                    reminders_sent += 1
        
        return {
            "success": True,
            "message": f"Processed {len(upcoming_appointments)} appointments, sent {reminders_sent} reminders.",
            "reminders_sent": reminders_sent,
            "total_processed": len(upcoming_appointments),
            "results": results
        }
    
    def _determine_reminder_type(self, days_until: int, reminders_sent_count: int) -> Optional[int]:
        """Determine which reminder type to send based on appointment timing and previous reminders.
        
        Args:
            days_until: Days until appointment (0 = today, 1 = tomorrow, etc.)
            reminders_sent_count: Number of reminders already sent
            
        Returns:
            Reminder type (1, 2, 3) or None if no reminder should be sent
        """
        print(f"Determining reminder type for appointment with days_until={days_until}, reminders_sent_count={reminders_sent_count}")
        
        if days_until == 0:
            if reminders_sent_count == 0:
                print("Sending Type 2 reminder for same-day appointment with no previous reminders")
                return 2
            elif reminders_sent_count == 1:
                print("Sending Type 3 reminder for same-day appointment with one previous reminder")
                return 3
            print("No more reminders needed for same-day appointment")
        
        elif days_until == 1:
            if reminders_sent_count == 0:
                print("Sending Type 2 reminder for next-day appointment with no previous reminders")
                return 2
            elif reminders_sent_count == 1:
                print("Sending Type 3 reminder for next-day appointment with one previous reminder")
                return 3
            print("No more reminders needed for next-day appointment")
        
        elif days_until >= 2:
            if days_until == 2 and reminders_sent_count < 1:
                print("Sending Type 1 reminder for appointment 2 days away")
                return 1
            elif days_until == 1 and reminders_sent_count < 2:
                print("Sending Type 2 reminder for appointment 1 day away")
                return 2
            elif days_until == 0 and reminders_sent_count < 3:
                print("Sending Type 3 reminder for appointment today")
                return 3
            print(f"No reminder needed for appointment {days_until} days away with {reminders_sent_count} reminders sent")
        
        print("No reminder type determined")
        return None
    
    def schedule_immediate_reminder(self, appointment_id: str) -> Dict[str, Any]:
        """Schedule immediate reminder for same-day or next-day appointments.
        
        This method should be called right after booking an appointment to handle
        compressed reminder flows for appointments that are today or tomorrow.
        
        Args:
            appointment_id: The appointment ID to schedule reminders for
            
        Returns:
            Dict with success status and message
        """
        appointments_df = self.load_appointments()
        
        appointment = None
        
        if "appointment_id" in appointments_df.columns:
            appointment_mask = appointments_df["appointment_id"] == appointment_id
            if any(appointment_mask):
                appointment = appointments_df[appointment_mask].iloc[0]
                if not pd.isna(appointment.get("date")):
                    pass
                else:
                    appointment = None
        
        if appointment is None and "AppointmentID" in appointments_df.columns:
            appointment_mask = appointments_df["AppointmentID"] == appointment_id
            if any(appointment_mask):
                appointment = appointments_df[appointment_mask].iloc[0]
                if not pd.isna(appointment.get("Date")):
                    pass
                else:
                    appointment = None
        
        if appointment is None:
            for col in appointments_df.columns:
                if 'id' in col.lower() and col.lower() not in ['patientid', 'patient_id']:
                    appointment_mask = appointments_df[col] == appointment_id
                    if any(appointment_mask):
                        potential_appointment = appointments_df[appointment_mask].iloc[0]
                        date_value = potential_appointment.get("Date", potential_appointment.get("date"))
                        if not pd.isna(date_value):
                            appointment = potential_appointment
                            break
            
        if appointment is None:
            return {
                "success": False,
                "message": f"Appointment with ID {appointment_id} not found or has invalid date data."
            }
        
        appointment_date = None
        
        if "date" in appointment and not pd.isna(appointment["date"]):
            appointment_date = appointment["date"]
        elif "Date" in appointment and not pd.isna(appointment["Date"]):
            appointment_date = appointment["Date"]
        else:
            appointment_date = None
        
        if pd.isna(appointment_date) or appointment_date is None:
            return {
                "success": False,
                "message": f"Appointment date is missing or invalid: {appointment_date}"
            }
        
        if isinstance(appointment_date, str):
            appointment_date = pd.to_datetime(appointment_date).date()
        elif isinstance(appointment_date, (int, float)):
            appointment_date = pd.to_datetime(appointment_date, unit='D', origin='1900-01-01').date()
        elif hasattr(appointment_date, 'date'):
            appointment_date = appointment_date.date()
        elif isinstance(appointment_date, datetime):
            appointment_date = appointment_date.date()
        elif pd.isna(appointment_date):
            return {
                "success": False,
                "message": f"Appointment date is NaT (Not a Time): {appointment_date}"
            }
        else:
            try:
                appointment_date = pd.to_datetime(appointment_date).date()
                if pd.isna(appointment_date):
                    return {
                        "success": False,
                        "message": f"Appointment date converted to NaT: {appointment_date}"
                    }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Unable to parse appointment date: {appointment_date}, Error: {str(e)}"
                }
        
        today = datetime.now().date()
        days_until = (appointment_date - today).days
        
        if days_until <= 1:
            print(f"Scheduling immediate Type 2 reminder for appointment {appointment_id}")
            result = self.send_reminder(appointment_id, 2)
            
            if result["success"]:
                print(f"Successfully sent Type 2 reminder for appointment {appointment_id}")
            else:
                print(f"Failed to send Type 2 reminder for appointment {appointment_id}: {result.get('message', 'Unknown error')}")
                print(f"Trying to send a Type 1 reminder instead...")
                result = self.send_reminder(appointment_id, 1)
                print(f"Type 1 reminder result: {result}")
                
                print(f"Trying to send a Type 3 reminder as well...")
                result = self.send_reminder(appointment_id, 3)
                print(f"Type 3 reminder result: {result}")
            
            return {
                "success": result["success"],
                "message": f"Immediate reminder sent for {'same-day' if days_until == 0 else 'next-day'} appointment.",
                "appointment_id": appointment_id,
                "days_until": days_until,
                "reminder_type": 2
            }
        else:
            return {
                "success": True,
                "message": f"Appointment is {days_until} days away. Standard reminder flow will be used.",
                "appointment_id": appointment_id,
                "days_until": days_until
            }
    
    def update_confirmation_status(self, appointment_id: str, confirmed: bool, 
                                  cancel_reason: Optional[str] = None) -> Dict[str, Any]:
        """Update appointment confirmation status based on patient response.
        
        Args:
            appointment_id: ID of the appointment to update
            confirmed: Boolean indicating if appointment is confirmed or cancelled
            cancel_reason: Optional reason for cancellation
            
        Returns:
            Dictionary containing success status and update details
        """
        appointments_df = self.load_appointments()
        
        appointment_mask = appointments_df["AppointmentID"] == appointment_id
        if not any(appointment_mask):
            return {
                "success": False,
                "message": f"Appointment with ID {appointment_id} not found."
            }
        
        if confirmed:
            appointments_df.loc[appointment_mask, "ConfirmationStatus"] = "Confirmed"
            status_message = "Appointment confirmed."
        else:
            appointments_df.loc[appointment_mask, "ConfirmationStatus"] = "Cancelled"
            if cancel_reason:
                if "CancelReason" not in appointments_df.columns:
                    appointments_df["CancelReason"] = ""
                appointments_df.loc[appointment_mask, "CancelReason"] = cancel_reason
            status_message = "Appointment cancelled."
        
        save_success = self.save_appointments(appointments_df)
        
        return {
            "success": save_success,
            "message": status_message,
            "appointment_id": appointment_id,
            "confirmed": confirmed,
            "cancel_reason": cancel_reason if not confirmed else None
        }

