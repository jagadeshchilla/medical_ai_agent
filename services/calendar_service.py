"""Calendar service for managing medical appointments and availability."""

import os
import uuid
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path


class CalendarService:
    """Service for managing calendar appointments with Calendly-like functionality.
    
    This service handles appointment booking, cancellation, and availability management
    for a medical office system. It maintains data in CSV files and provides
    comprehensive appointment management capabilities.
    """
    
    def __init__(self, availability_file: str = None, appointments_file: str = None):
        """Initialize the calendar service.
        
        Args:
            availability_file: Path to the availability CSV file
            appointments_file: Path to the appointments CSV file
        """
        self.data_dir = os.path.join(os.getcwd(), "data")
        self.availability_file = availability_file or os.path.join(self.data_dir, "availability.csv")
        self.appointments_file = appointments_file or os.path.join(self.data_dir, "doctor_appointments.csv")
        
        os.makedirs(self.data_dir, exist_ok=True)
        self._initialize_data()
    
    def _initialize_data(self):
        """Initialize availability and appointments data."""
        if not os.path.exists(self.availability_file):
            self._create_default_availability()
        
        if not os.path.exists(self.appointments_file):
            self._create_default_appointments()
    
    def _create_default_availability(self):
        """Create default availability data for Monday-Friday, 9 AM to 5 PM, 30-minute slots."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        hours = [f"{h:02d}:00" for h in range(9, 17)] + [f"{h:02d}:30" for h in range(9, 17)]
        
        slots = []
        for day in days:
            for hour in hours:
                slots.append({
                    "day": day,
                    "time": hour,
                    "doctor": "Smith",
                    "available": True
                })
                slots.append({
                    "day": day,
                    "time": hour,
                    "doctor": "Johnson",
                    "available": True
                })
        
        availability_df = pd.DataFrame(slots)
        availability_df.to_csv(self.availability_file, index=False)
        print(f"Created default availability data at {self.availability_file}")
    
    def _create_default_appointments(self):
        """Create default appointments data with required columns."""
        appointments_df = pd.DataFrame(columns=[
            "appointment_id", "patient_id", "patient_name", "doctor", 
            "date", "time", "status", "email", "created_at"
        ])
        appointments_df.to_csv(self.appointments_file, index=False)
        print(f"Created default appointments data at {self.appointments_file}")
    
    def _calculate_end_time(self, start_time: str, duration_minutes: int) -> str:
        """Calculate end time based on start time and duration.
        
        Args:
            start_time: Start time in HH:MM format
            duration_minutes: Duration in minutes
            
        Returns:
            End time in HH:MM format
        """
        try:
            start_hour, start_minute = map(int, start_time.split(":"))
            total_minutes = start_hour * 60 + start_minute + duration_minutes
            end_hour = total_minutes // 60
            end_minute = total_minutes % 60
            return f"{end_hour:02d}:{end_minute:02d}"
        except Exception as e:
            print(f"Error calculating end time: {e}")
            return start_time
    
    def get_available_slots(self, date: str, doctor: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available appointment slots for a specific date.
        
        Args:
            date: Date string in format 'YYYY-MM-DD'
            doctor: Optional doctor name to filter by
            
        Returns:
            List of available time slots
        """
        try:
            availability_df = pd.read_csv(self.availability_file)
            available_slots = availability_df[(availability_df["Date"] == date) & 
                                             (availability_df["Status"] == "Available")]
            
            if doctor and doctor != "Any":
                available_slots = available_slots[available_slots["DoctorName"] == doctor]
            
            appointments_df = pd.read_csv(self.appointments_file)
            
            if "date" in appointments_df.columns:
                date_appointments = appointments_df[appointments_df["date"] == date]
            elif "Date" in appointments_df.columns:
                date_appointments = appointments_df[appointments_df["Date"] == date]
            else:
                date_appointments = pd.DataFrame()
            
            slots = available_slots.to_dict("records")
            available_slots = []
            
            for slot in slots:
                is_booked = False
                for _, appointment in date_appointments.iterrows():
                    appointment_time = appointment.get("time", appointment.get("StartTime", ""))
                    appointment_doctor = appointment.get("doctor", appointment.get("Doctor", ""))
                    
                    if appointment_time == slot["TimeSlot"] and appointment_doctor == slot["DoctorName"]:
                        is_booked = True
                        break
                
                if not is_booked:
                    available_slots.append({
                        "date": date,
                        "start_time": slot["TimeSlot"],
                        "end_time": self._calculate_end_time(slot["TimeSlot"], 30),
                        "doctor": slot["DoctorName"]
                    })
            
            return available_slots
        
        except Exception as e:
            print(f"Error getting available slots: {str(e)}")
            return []
    
    def book_appointment(self, patient_id: str, patient_name: str, doctor: str, 
                        date: str, time: str, email: str) -> Dict[str, Any]:
        """Book an appointment.
        
        Args:
            patient_id: Patient ID
            patient_name: Patient name
            doctor: Doctor name
            date: Appointment date (YYYY-MM-DD)
            time: Appointment time (HH:MM)
            email: Patient email
            
        Returns:
            Dict with appointment details and success status
        """
        try:
            available_slots = self.get_available_slots(date, doctor)
            slot_available = False
            
            for slot in available_slots:
                if slot["start_time"] == time and slot["doctor"] == doctor:
                    slot_available = True
                    break
            
            if not slot_available:
                return {
                    "success": False,
                    "message": f"The selected slot ({date} at {time} with Dr. {doctor}) is not available."
                }
            
            appointments_df = pd.read_csv(self.appointments_file)
            
            from utils.data_loader import DataLoader
            appointment_id = DataLoader.generate_appointment_id()
            
            new_appointment = {
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "doctor": doctor,
                "date": date,
                "time": time,
                "status": "confirmed",
                "email": email,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            new_appointment_df = pd.DataFrame([new_appointment])
            appointments_df = pd.concat([appointments_df, new_appointment_df], ignore_index=True)
            appointments_df.to_csv(self.appointments_file, index=False)
            
            availability_result = self.update_availability_status(doctor, date, time, "Booked")
            if not availability_result["success"]:
                print(f"Warning: Failed to update availability: {availability_result['message']}")
            
            return {
                "success": True,
                "message": "Appointment booked successfully",
                "appointment_id": appointment_id,
                "patient_name": patient_name,
                "doctor": doctor,
                "date": date,
                "time": time
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error booking appointment: {str(e)}"
            }
    
    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Cancel an appointment.
        
        Args:
            appointment_id: Appointment ID
            
        Returns:
            Dict with success status and message
        """
        try:
            appointments_df = pd.read_csv(self.appointments_file)
            appointment = appointments_df[appointments_df["appointment_id"] == appointment_id]
            
            if appointment.empty:
                return {
                    "success": False,
                    "message": f"Appointment with ID {appointment_id} not found."
                }
            
            appointment_details = appointment.iloc[0]
            doctor = appointment_details["doctor"]
            date = appointment_details["date"]
            time = appointment_details["time"]
            
            appointments_df.loc[appointments_df["appointment_id"] == appointment_id, "status"] = "cancelled"
            appointments_df.to_csv(self.appointments_file, index=False)
            
            availability_result = self.update_availability_status(doctor, date, time, "Available")
            if not availability_result["success"]:
                print(f"Warning: Failed to update availability after cancellation: {availability_result['message']}")
            
            return {
                "success": True,
                "message": "Appointment cancelled successfully"
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cancelling appointment: {str(e)}"
            }
    
    def get_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Get appointment details.
        
        Args:
            appointment_id: Appointment ID
            
        Returns:
            Dict with appointment details
        """
        try:
            appointments_df = pd.read_csv(self.appointments_file)
            appointment = appointments_df[appointments_df["appointment_id"] == appointment_id]
            
            if appointment.empty:
                return {
                    "success": False,
                    "message": f"Appointment with ID {appointment_id} not found."
                }
            
            appointment_dict = appointment.iloc[0].to_dict()
            appointment_dict["success"] = True
            return appointment_dict
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error getting appointment: {str(e)}"
            }
    
    def get_patient_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all appointments for a patient.
        
        Args:
            patient_id: Patient ID
            
        Returns:
            List of appointment dictionaries
        """
        try:
            appointments_df = pd.read_csv(self.appointments_file)
            patient_appointments = appointments_df[appointments_df["patient_id"] == patient_id]
            appointments = patient_appointments.to_dict("records")
            return appointments
        
        except Exception as e:
            print(f"Error getting patient appointments: {str(e)}")
            return []
    
    def get_upcoming_appointments(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming appointments within the specified number of days.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of upcoming appointment dictionaries
        """
        try:
            appointments_df = pd.read_csv(self.appointments_file)
            current_date = datetime.now().date()
            future_date = current_date + timedelta(days=days)
            
            upcoming_appointments = []
            
            for _, appointment in appointments_df.iterrows():
                try:
                    appointment_date = datetime.strptime(appointment["date"], "%Y-%m-%d").date()
                    
                    if (current_date <= appointment_date <= future_date and 
                        appointment["status"] == "confirmed"):
                        upcoming_appointments.append(appointment.to_dict())
                except:
                    continue
            
            return upcoming_appointments
        
        except Exception as e:
            print(f"Error getting upcoming appointments: {str(e)}")
            return []
    
    def get_daily_schedule(self, date: str = None) -> List[Dict[str, Any]]:
        """Get the schedule for a specific date.
        
        Args:
            date: Date string in format 'YYYY-MM-DD' (defaults to today)
            
        Returns:
            List of appointment dictionaries for the specified date
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            appointments_df = pd.read_csv(self.appointments_file)
            daily_schedule = appointments_df[(appointments_df["date"] == date) & 
                                           (appointments_df["status"] == "confirmed")]
            schedule = daily_schedule.to_dict("records")
            return schedule
        
        except Exception as e:
            print(f"Error getting daily schedule: {str(e)}")
            return []
    
    def update_availability(self, day: str, time: str, doctor: str, available: bool) -> Dict[str, Any]:
        """Update availability for a specific slot.
        
        Args:
            day: Day of the week
            time: Time slot
            doctor: Doctor name
            available: Availability status
            
        Returns:
            Dict with success status and message
        """
        try:
            availability_df = pd.read_csv(self.availability_file)
            slot_mask = ((availability_df["day"] == day) & 
                        (availability_df["time"] == time) & 
                        (availability_df["doctor"] == doctor))
            
            if not any(slot_mask):
                return {
                    "success": False,
                    "message": f"Slot not found for {day} at {time} with Dr. {doctor}."
                }
            
            availability_df.loc[slot_mask, "available"] = available
            availability_df.to_csv(self.availability_file, index=False)
            
            return {
                "success": True,
                "message": f"Availability updated successfully for {day} at {time} with Dr. {doctor}."
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating availability: {str(e)}"
            }
    
    def update_availability_status(self, doctor: str, date: str, time: str, status: str) -> Dict[str, Any]:
        """Update availability status for a specific date and time slot.
        
        Args:
            doctor: Doctor name
            date: Date in YYYY-MM-DD format
            time: Time slot in HH:MM format
            status: New status ("Available" or "Booked")
            
        Returns:
            Dict with success status and message
        """
        try:
            availability_df = pd.read_csv(self.availability_file)
            print(f"Updating availability: Dr. {doctor}, Date: {date}, Time: {time}, Status: {status}")
            
            slot_mask = ((availability_df["DoctorName"] == doctor) & 
                        (availability_df["Date"] == date) & 
                        (availability_df["TimeSlot"] == time))
            
            print(f"Found {slot_mask.sum()} matching slots")
            
            if not any(slot_mask):
                return {
                    "success": False,
                    "message": f"Slot not found for Dr. {doctor} on {date} at {time}."
                }
            
            availability_df.loc[slot_mask, "Status"] = status
            availability_df.to_csv(self.availability_file, index=False)
            
            print(f"Successfully updated availability for Dr. {doctor} on {date} at {time} to {status}")
            
            return {
                "success": True,
                "message": f"Availability status updated to '{status}' for Dr. {doctor} on {date} at {time}."
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error updating availability status: {str(e)}"
            }