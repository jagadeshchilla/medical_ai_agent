"""
Form Distribution Agent for Medical Appointment System

This module provides the FormDistributionAgent class responsible for distributing
intake forms to patients after their appointments have been confirmed. The agent
manages form sending, tracking, and status updates.
"""

import os
import pandas as pd
from typing import Dict, Any, Optional

from services.email_service import EmailService
from services.calendar_service import CalendarService


class FormDistributionAgent:
    """Agent responsible for distributing intake forms to patients.
    
    The FormDistributionAgent handles the distribution of intake forms to patients
    after their appointments have been confirmed. It manages form sending, tracking,
    and status updates to ensure patients receive necessary paperwork.
    
    Attributes:
        appointments_csv_path (str): Path to the appointments CSV file
        patients_csv_path (str): Path to the patients CSV file
        email_service: Email service instance for sending forms
        calendar_service: Calendar service instance for appointment management
    """
    
    def __init__(self, appointments_csv_path: str = "data/doctor_appointments.csv",
                 patients_csv_path: str = "data/patients.csv"):
        """Initialize the FormDistributionAgent with data paths and service instances.
        
        Args:
            appointments_csv_path: Path to the appointments CSV file
            patients_csv_path: Path to the patients CSV file
        """
        self.appointments_csv_path = appointments_csv_path
        self.patients_csv_path = patients_csv_path
        self.email_service = EmailService()
        self.calendar_service = CalendarService()
    
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
                "AppointmentID", "PatientID", "PatientName", "Doctor", 
                "Date", "StartTime", "EndTime", "Duration", 
                "InsuranceCarrier", "MemberID", "GroupNumber",
                "ConfirmationStatus", "RemindersSent", "FormSent"
            ])
        except Exception as e:
            print(f"Error loading appointments data: {e}")
            return pd.DataFrame(columns=[
                "AppointmentID", "PatientID", "PatientName", "Doctor", 
                "Date", "StartTime", "EndTime", "Duration", 
                "InsuranceCarrier", "MemberID", "GroupNumber",
                "ConfirmationStatus", "RemindersSent", "FormSent"
            ])
    
    def save_appointments(self, appointments_df: pd.DataFrame) -> bool:
        """Save appointment data to CSV file for backward compatibility.
        
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
    
    def update_form_sent_status(self, appointment_id: str, status: bool = True) -> bool:
        """Update form sent status for an appointment.
        
        Args:
            appointment_id: ID of the appointment to update
            status: New form sent status (default: True)
            
        Returns:
            True if update was successful, False otherwise
        """
        appointments_df = self.load_appointments()
        
        if "FormSent" not in appointments_df.columns:
            appointments_df["FormSent"] = False
        
        appointment_mask = appointments_df["AppointmentID"] == appointment_id
        if not any(appointment_mask):
            return False
        
        appointments_df.loc[appointment_mask, "FormSent"] = status
        
        return self.save_appointments(appointments_df)
    
    def send_intake_form(self, appointment_id: str) -> Dict[str, Any]:
        """Send intake form for a specific appointment.
        
        Args:
            appointment_id: ID of the appointment to send form for
            
        Returns:
            Dictionary with form sending results and appointment details
        """
        calendar_appointment = self.calendar_service.get_appointment(appointment_id)
        
        if calendar_appointment.get("success", False):
            appointment = calendar_appointment
            
            if "FormSent" in appointment and appointment["FormSent"]:
                return {
                    "success": True,
                    "message": "Intake form has already been sent for this appointment.",
                    "appointment_id": appointment_id
                }
            
            patient_email = appointment.get("email")
            
            if not patient_email and "patient_id" in appointment:
                patients_df = self.load_patients()
                patient_id = appointment["patient_id"]
                patient_mask = patients_df["PatientID"] == patient_id
                if any(patient_mask):
                    patient_record = patients_df[patient_mask].iloc[0]
                    patient_email = patient_record.get("Email")
            
            patient_name = appointment.get("patient_name", "Patient")
            appointment_date = appointment.get("date", "your scheduled date")
            appointment_time = appointment.get("time")
            doctor = appointment.get("doctor")
            
            email_result = self.email_service.send_intake_form(
                patient_email, patient_name, appointment_date, appointment_time, doctor
            )
            
            if email_result["success"]:
                self.update_form_sent_status(appointment_id, True)
            
            return {
                "success": email_result["success"],
                "message": email_result["message"],
                "appointment_id": appointment_id,
                "patient_email": patient_email,
                "patient_name": patient_name,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "doctor": doctor
            }
        
        appointments_df = self.load_appointments()
        
        appointment_mask = appointments_df["AppointmentID"] == appointment_id
        if not any(appointment_mask):
            return {
                "success": False,
                "message": f"Appointment with ID {appointment_id} not found."
            }
        
        appointment = appointments_df[appointment_mask].iloc[0]
        
        if "FormSent" in appointment and appointment["FormSent"]:
            return {
                "success": True,
                "message": "Intake form has already been sent for this appointment.",
                "appointment_id": appointment_id
            }
        
        patients_df = self.load_patients()
        patient_id = appointment.get("PatientID")
        patient_email = None
        
        if patient_id:
            patient_mask = patients_df["PatientID"] == patient_id
            if any(patient_mask):
                patient_record = patients_df[patient_mask].iloc[0]
                patient_email = patient_record.get("Email")
        
        if not patient_email:
            return {
                "success": False,
                "message": "No email address found for patient.",
                "appointment_id": appointment_id
            }
        
        patient_name = appointment.get("PatientName", "Patient")
        appointment_date = appointment.get("Date", "your scheduled date")
        appointment_time = appointment.get("StartTime")
        doctor = appointment.get("Doctor")
        
        email_result = self.email_service.send_intake_form(
            patient_email, patient_name, appointment_date, appointment_time, doctor
        )
        
        if email_result["success"]:
            self.update_form_sent_status(appointment_id, True)
        
        return {
            "success": email_result["success"],
            "message": email_result["message"],
            "appointment_id": appointment_id,
            "patient_email": patient_email,
            "patient_name": patient_name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "doctor": doctor
        }
    
    def process_new_confirmations(self) -> Dict[str, Any]:
        """Process all new confirmations and send intake forms.
        
        Returns:
            Dictionary with processing results and form sending statistics
        """
        calendar_appointments = self.calendar_service.get_upcoming_appointments(days=30)
        
        confirmed_appointments = []
        for appointment in calendar_appointments:
            if appointment.get("status") == "confirmed" and not appointment.get("FormSent", False):
                confirmed_appointments.append(appointment)
        
        if not confirmed_appointments:
            appointments_df = self.load_appointments()
            
            if "FormSent" not in appointments_df.columns:
                appointments_df["FormSent"] = False
            
            if "status" in appointments_df.columns:
                confirmed_mask = (appointments_df["status"] == "confirmed") & (~appointments_df["FormSent"])
            else:
                if "ConfirmationStatus" in appointments_df.columns:
                    if "FormSent" in appointments_df.columns:
                        confirmed_mask = (appointments_df["ConfirmationStatus"] == "Sent") & (~appointments_df["FormSent"])
                    else:
                        confirmed_mask = appointments_df["ConfirmationStatus"] == "Sent"
                else:
                    confirmed_mask = appointments_df["FormSent"] == False
            
            confirmed_appointments_df = appointments_df[confirmed_mask]
            
            if confirmed_appointments_df.empty:
                return {
                    "success": True,
                    "message": "No new confirmations to process.",
                    "forms_sent": 0
                }
            
            confirmed_appointments = confirmed_appointments_df.to_dict("records")
        
        forms_sent = 0
        results = []
        
        for appointment in confirmed_appointments:
            appointment_id = appointment.get("appointment_id", appointment.get("AppointmentID"))
            
            if appointment_id:
                result = self.send_intake_form(appointment_id)
                results.append(result)
                
                if result["success"]:
                    forms_sent += 1
        
        return {
            "success": True,
            "message": f"Processed {len(confirmed_appointments)} confirmations, sent {forms_sent} intake forms.",
            "forms_sent": forms_sent,
            "total_processed": len(confirmed_appointments),
            "results": results
        }
        
    def send_appointment_confirmation(self, appointment_id: str) -> Dict[str, Any]:
        """Send appointment confirmation email with intake form attached.
        
        Args:
            appointment_id: ID of the appointment to send confirmation for
            
        Returns:
            Dictionary with confirmation sending results and appointment details
        """
        appointment = self.calendar_service.get_appointment(appointment_id)
        
        if not appointment.get("success", False):
            return {
                "success": False,
                "message": f"Appointment with ID {appointment_id} not found."
            }
        
        patient_email = appointment.get("email")
        patient_name = appointment.get("patient_name", "Patient")
        appointment_date = appointment.get("date", "your scheduled date")
        appointment_time = appointment.get("time")
        doctor = appointment.get("doctor")
        
        if not patient_email:
            return {
                "success": False,
                "message": "No email address found for patient.",
                "appointment_id": appointment_id
            }
        
        email_result = self.email_service.send_appointment_confirmation(
            patient_email, patient_name, appointment_date, appointment_time, doctor
        )
        
        if email_result["success"]:
            self.update_form_sent_status(appointment_id, True)
        
        return {
            "success": email_result["success"],
            "message": email_result["message"],
            "appointment_id": appointment_id,
            "patient_email": patient_email,
            "patient_name": patient_name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "doctor": doctor
        }