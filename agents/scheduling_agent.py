"""
Scheduling Agent for Medical Appointment System

This module provides the SchedulingAgent class responsible for finding available appointment slots
based on doctor preference and appointment duration.
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq


class SchedulingAgent:
    """Agent responsible for finding available appointment slots based on doctor preference and appointment duration.
    
    The SchedulingAgent manages doctor availability, finds suitable appointment slots,
    and handles the scheduling process for medical appointments.
    
    Attributes:
        availability_csv_path (str): Path to the availability CSV file
        llm: Language model for generating responses
        scheduling_prompt: Chat prompt template for scheduling
        scheduling_chain: Processing chain for scheduling
    """
    
    def __init__(self, availability_csv_path: str = "data/availability.csv", 
                 model_name: str = "gpt-3.5-turbo", temperature: float = 0.2):
        """Initialize the SchedulingAgent.
        
        Args:
            availability_csv_path: Path to the availability CSV file
            model_name: Name of the language model to use
            temperature: Temperature setting for the language model
        """
        self.availability_csv_path = availability_csv_path
        self.llm = ChatGroq(temperature=0, model_name="gemma2-9b-it")
        self.scheduling_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a medical receptionist assistant. "
                      "Your job is to help schedule appointments based on doctor availability "
                      "and appointment duration. Be friendly and professional."),
            ("human", "{input}")
        ])
        self.scheduling_chain = self.scheduling_prompt | self.llm | StrOutputParser()
    
    def load_availability(self) -> pd.DataFrame:
        """Load doctor availability data from CSV file.
        
        Returns:
            DataFrame containing availability data or empty DataFrame with expected columns if file doesn't exist
        """
        try:
            return pd.read_csv(self.availability_csv_path)
        except Exception as e:
            print(f"Error loading availability data: {e}")
            return pd.DataFrame(columns=["DoctorName", "Date", "TimeSlot", "Status"])
    
    def find_available_slots(self, selected_date: str, doctor_preference: Optional[str], 
                             appointment_duration: int) -> List[Dict[str, Any]]:
        """Find available appointment slots for the specified doctor and duration.
        
        Args:
            selected_date: Date to search for availability
            doctor_preference: Preferred doctor name or None for any doctor
            appointment_duration: Duration of appointment in minutes
            
        Returns:
            List of available appointment slots with doctor, date, and time information
        """
        availability_df = self.load_availability()
        
        if availability_df.empty:
            return []
        
        date_df = availability_df[availability_df["Date"] == selected_date]
        
        if doctor_preference and doctor_preference != "Any":
            doctor_df = date_df[date_df["DoctorName"] == doctor_preference]
            if doctor_df.empty:
                doctor_df = date_df
        else:
            doctor_df = date_df
        
        available_slots = doctor_df[doctor_df["Status"] == "Available"]
        
        if available_slots.empty:
            return []
        
        available_slots = available_slots.sort_values(by=["DoctorName", "TimeSlot"])
        
        available_appointments = []
        
        for _, row in available_slots.iterrows():
            doctor = row["DoctorName"]
            date = row["Date"]
            start_time = row["TimeSlot"]
            
            slots_needed = max(1, appointment_duration // 30)
            
            start_hour = int(start_time.split(":")[0])
            start_minute = int(start_time.split(":")[1])
            
            total_minutes = start_hour * 60 + start_minute + appointment_duration
            end_hour = total_minutes // 60
            end_minute = total_minutes % 60
            end_time = f"{end_hour:02d}:{end_minute:02d}"
            
            available_appointments.append({
                "doctor": doctor,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "duration": appointment_duration
            })
        
        return available_appointments
    
    def schedule_appointment(self, patient_info: Dict[str, Any], 
                           appointment_duration: int, selected_date: str = None) -> Dict[str, Any]:
        """Schedule an appointment based on patient info and duration.
        
        Args:
            patient_info: Dictionary containing patient information
            appointment_duration: Duration of appointment in minutes
            selected_date: Specific date to schedule (optional)
            
        Returns:
            Dictionary containing scheduling results and appointment details
        """
        doctor_preference = patient_info.get("DoctorPreference")
        
        if selected_date:
            available_slots = self.find_available_slots(selected_date, doctor_preference, appointment_duration)
        else:
            from datetime import datetime, timedelta
            today = datetime.now().date()
            for i in range(7):
                check_date = today + timedelta(days=i)
                available_slots = self.find_available_slots(str(check_date), doctor_preference, appointment_duration)
                if available_slots:
                    break
        
        if not available_slots:
            input_text = f"Patient: {patient_info.get('Name')}\n"
            input_text += f"Doctor preference: {doctor_preference}\n"
            input_text += f"Appointment duration: {appointment_duration} minutes\n"
            input_text += "No available slots found. Generate a friendly response explaining that there are no available appointments and suggesting to call the office."
            
            response = self.scheduling_chain.invoke({"input": input_text})
            
            return {
                "success": False,
                "available_slots": [],
                "selected_slot": None,
                "response": response
            }
        
        selected_slot = available_slots[0]
        
        input_text = f"Patient: {patient_info.get('Name')}\n"
        input_text += f"Doctor: {selected_slot['doctor']}\n"
        input_text += f"Date: {selected_slot['date']}\n"
        input_text += f"Time: {selected_slot['start_time']} - {selected_slot['end_time']}\n"
        input_text += f"Duration: {appointment_duration} minutes\n"
        
        patient_type = patient_info.get("PatientType", "New")
        input_text += f"Patient type: {patient_type}\n"
        
        from utils.data_loader import DataLoader
        appointment_id = DataLoader.generate_appointment_id()
        
        input_text += "Generate a friendly response confirming the appointment details. Mention that we'll collect insurance information next and then confirm everything before finalizing the appointment."
        
        response = self.scheduling_chain.invoke({"input": input_text})
        
        return {
            "success": True,
            "available_slots": available_slots,
            "selected_slot": selected_slot,
            "appointment_id": appointment_id,
            "response": response
        }
    
    def update_availability(self, selected_slot: Dict[str, Any]) -> bool:
        """Update availability after scheduling an appointment.
        
        Args:
            selected_slot: Dictionary containing appointment slot details
            
        Returns:
            Boolean indicating success of availability update
        """
        try:
            availability_df = self.load_availability()
            
            if availability_df.empty:
                return False
            
            doctor = selected_slot["doctor"]
            date = selected_slot["date"]
            start_time = selected_slot["start_time"]
            end_time = selected_slot["end_time"]
            
            start_hour = int(start_time.split(":")[0])
            end_hour = int(end_time.split(":")[0])
            hours_to_book = end_hour - start_hour
            
            for hour in range(start_hour, end_hour):
                time_slot = f"{hour}:00"
                mask = ((availability_df["DoctorName"] == doctor) & 
                        (availability_df["Date"] == date) & 
                        (availability_df["TimeSlot"] == time_slot))
                availability_df.loc[mask, "Status"] = "Booked"
            
            availability_df.to_csv(self.availability_csv_path, index=False)
            return True
        
        except Exception as e:
            print(f"Error updating availability: {e}")
            return False