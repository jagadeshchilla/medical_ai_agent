"""Confirmation service for handling appointment confirmations and cancellations."""

import pandas as pd
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging


class ConfirmationService:
    """Service for handling appointment confirmations and cancellations.
    
    This service manages appointment status updates, patient type changes,
    and provides comprehensive confirmation/cancellation functionality
    for the medical office system.
    """
    
    def __init__(self, appointments_csv_path: str = "data/doctor_appointments.csv",
                 patients_csv_path: str = "data/patients.csv"):
        """Initialize confirmation service with data file paths.
        
        Args:
            appointments_csv_path: Path to appointments CSV file
            patients_csv_path: Path to patients CSV file
        """
        self.appointments_csv_path = appointments_csv_path
        self.patients_csv_path = patients_csv_path
        self.logger = logging.getLogger(__name__)
    
    def load_appointments(self) -> pd.DataFrame:
        """Load appointment data from CSV file."""
        try:
            return pd.read_csv(self.appointments_csv_path)
        except Exception as e:
            self.logger.error(f"Error loading appointments data: {e}")
            return pd.DataFrame()
    
    def save_appointments(self, appointments_df: pd.DataFrame) -> bool:
        """Save appointment data to CSV file."""
        try:
            appointments_df.to_csv(self.appointments_csv_path, index=False)
            return True
        except Exception as e:
            self.logger.error(f"Error saving appointments data: {e}")
            return False
    
    def load_patients(self) -> pd.DataFrame:
        """Load patient data from CSV file."""
        try:
            return pd.read_csv(self.patients_csv_path)
        except Exception as e:
            self.logger.error(f"Error loading patients data: {e}")
            return pd.DataFrame()
    
    def save_patients(self, patients_df: pd.DataFrame) -> bool:
        """Save patient data to CSV file."""
        try:
            patients_df.to_csv(self.patients_csv_path, index=False)
            return True
        except Exception as e:
            self.logger.error(f"Error saving patients data: {e}")
            return False
    
    def confirm_appointment(self, appointment_id: str, action: str, 
                          cancel_reason: Optional[str] = None) -> Dict[str, Any]:
        """Confirm or cancel an appointment and update Excel files.
        
        Args:
            appointment_id: The appointment ID
            action: 'confirm' or 'cancel'
            cancel_reason: Reason for cancellation (required if action is 'cancel')
            
        Returns:
            Dict with success status and message
        """
        appointments_df = self.load_appointments()
        
        if appointments_df.empty:
            return {
                "success": False,
                "message": "No appointments data found."
            }
        
        appointment_mask = False
        appointment = None
        
        if "appointment_id" in appointments_df.columns:
            appointment_mask = appointments_df["appointment_id"] == appointment_id
            if any(appointment_mask):
                appointment = appointments_df[appointment_mask].iloc[0]
        
        if appointment is None and "AppointmentID" in appointments_df.columns:
            appointment_mask = appointments_df["AppointmentID"] == appointment_id
            if any(appointment_mask):
                appointment = appointments_df[appointment_mask].iloc[0]
        
        if appointment is None:
            return {
                "success": False,
                "message": f"Appointment with ID {appointment_id} not found."
            }
        
        patient_id = appointment.get("patient_id", appointment.get("PatientID"))
        if patient_id is not None:
            patient_id = str(patient_id)
        
        if action.lower() == "confirm":
            appointments_df.loc[appointment_mask, "ConfirmationStatus"] = "Confirmed"
            appointments_df.loc[appointment_mask, "status"] = "confirmed"
            
            if patient_id:
                self._update_patient_type(patient_id, "Returning")
            
            message = "Appointment confirmed successfully!"
            
        elif action.lower() == "cancel":
            if not cancel_reason or cancel_reason.strip() == "":
                return {
                    "success": False,
                    "message": "Cancel reason is required for cancellation."
                }
            
            appointments_df.loc[appointment_mask, "ConfirmationStatus"] = "Cancelled"
            appointments_df.loc[appointment_mask, "status"] = "cancelled"
            
            if "CancelReason" not in appointments_df.columns:
                appointments_df["CancelReason"] = ""
            appointments_df.loc[appointment_mask, "CancelReason"] = cancel_reason
            
            if patient_id:
                self._update_patient_type(patient_id, "Returning")
            
            message = f"Appointment cancelled successfully. Reason: {cancel_reason}"
            
        else:
            return {
                "success": False,
                "message": f"Invalid action: {action}. Must be 'confirm' or 'cancel'."
            }
        
        save_success = self.save_appointments(appointments_df)
        
        if save_success:
            return {
                "success": True,
                "message": message,
                "appointment_id": appointment_id,
                "action": action,
                "cancel_reason": cancel_reason if action.lower() == "cancel" else None
            }
        else:
            return {
                "success": False,
                "message": "Failed to save appointment updates."
            }
    
    def _update_patient_type(self, patient_id: str, new_type: str) -> bool:
        """Update patient type in patients.csv."""
        try:
            patients_df = self.load_patients()
            
            if patients_df.empty:
                return False
            
            patient_mask = patients_df["PatientID"].astype(str) == str(patient_id)
            
            if any(patient_mask):
                patients_df.loc[patient_mask, "PatientType"] = new_type
                return self.save_patients(patients_df)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating patient type: {e}")
            return False
    
    def get_appointment_status(self, appointment_id: str) -> Dict[str, Any]:
        """Get current status of an appointment."""
        appointments_df = self.load_appointments()
        
        if appointments_df.empty:
            return {
                "success": False,
                "message": "No appointments data found."
            }
        
        appointment_mask = False
        
        if "appointment_id" in appointments_df.columns:
            appointment_mask = appointments_df["appointment_id"] == appointment_id
            if any(appointment_mask):
                appointment = appointments_df[appointment_mask].iloc[0]
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "status": appointment.get("status", appointment.get("ConfirmationStatus", "Unknown")),
                    "patient_name": appointment.get("patient_name", appointment.get("PatientName", "Unknown")),
                    "doctor": appointment.get("doctor", appointment.get("Doctor", "Unknown")),
                    "date": appointment.get("date", appointment.get("Date", "Unknown")),
                    "time": appointment.get("time", appointment.get("StartTime", "Unknown")),
                    "cancel_reason": appointment.get("CancelReason", "")
                }
        
        if "AppointmentID" in appointments_df.columns:
            appointment_mask = appointments_df["AppointmentID"] == appointment_id
            if any(appointment_mask):
                appointment = appointments_df[appointment_mask].iloc[0]
                return {
                    "success": True,
                    "appointment_id": appointment_id,
                    "status": appointment.get("ConfirmationStatus", appointment.get("status", "Unknown")),
                    "patient_name": appointment.get("PatientName", appointment.get("patient_name", "Unknown")),
                    "doctor": appointment.get("Doctor", appointment.get("doctor", "Unknown")),
                    "date": appointment.get("Date", appointment.get("date", "Unknown")),
                    "time": appointment.get("StartTime", appointment.get("time", "Unknown")),
                    "cancel_reason": appointment.get("CancelReason", "")
                }
        
        return {
            "success": False,
            "message": f"Appointment with ID {appointment_id} not found."
        }
