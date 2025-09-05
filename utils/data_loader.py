"""Data loader utility for managing medical office data files."""

import os
import pandas as pd
import datetime
import uuid
from typing import Dict, List, Any, Optional


class DataLoader:
    """Utility class for loading and saving data from/to CSV files.
    
    This class provides comprehensive data management functionality for the medical office system,
    including patient records, appointment scheduling, and availability management.
    """
    
    @staticmethod
    def ensure_data_directory():
        """Ensure the data directory exists."""
        if not os.path.exists('data'):
            os.makedirs('data')
    
    @staticmethod
    def load_patients() -> pd.DataFrame:
        """Load patients data from CSV file.
        
        If the file doesn't exist or is empty, create it with the required columns.
        """
        DataLoader.ensure_data_directory()
        
        patients_file = 'data/patients.csv'
        
        if not os.path.exists(patients_file) or os.path.getsize(patients_file) == 0:
            patients_df = pd.DataFrame(columns=[
                "PatientID", "Name", "DOB", "Email", "Phone", 
                "DoctorPreference", "InsuranceCarrier", 
                "MemberID", "GroupNumber", "Location"
            ])
            patients_df.to_csv(patients_file, index=False)
            return patients_df
        
        try:
            return pd.read_csv(patients_file)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            patients_df = pd.DataFrame(columns=[
                "PatientID", "Name", "DOB", "Email", "Phone", 
                "DoctorPreference", "InsuranceCarrier", 
                "MemberID", "GroupNumber", "Location"
            ])
            patients_df.to_csv(patients_file, index=False)
            return patients_df
    
    @staticmethod
    def save_patients(patients_df: pd.DataFrame) -> None:
        """Save patients data to CSV file."""
        DataLoader.ensure_data_directory()
        patients_df.to_csv('data/patients.csv', index=False)
    
    @staticmethod
    def load_availability() -> pd.DataFrame:
        """
        Load availability data from CSV file.
        If the file doesn't exist or is empty, create it with sample data.
        """
        DataLoader.ensure_data_directory()
        
        availability_file = 'data/availability.csv'
        
        if not os.path.exists(availability_file) or os.path.getsize(availability_file) == 0:
            today = datetime.datetime.now().date()
            tomorrow = today + datetime.timedelta(days=1)
            next_week = today + datetime.timedelta(days=7)
            
            from datetime import date
            dates = [today, tomorrow, next_week, date(2025, 9, 5), date(2025, 9, 6), date(2025, 9, 7)]
            doctors = ["Dr. Kumar", "Dr. Mehta", "Dr. Sharma", "Dr. Singh", "Dr. Patel"]
            
            availability_data = []
            
            for date in dates:
                for doctor in doctors:
                    for hour in range(9, 12):
                        availability_data.append({
                            "Date": date,
                            "DoctorName": doctor,
                            "TimeSlot": f"{hour:02d}:00",
                            "Status": "Available"
                        })
                        availability_data.append({
                            "Date": date,
                            "DoctorName": doctor,
                            "TimeSlot": f"{hour:02d}:30",
                            "Status": "Available"
                        })
                    
                    for hour in range(13, 17):
                        availability_data.append({
                            "Date": date,
                            "DoctorName": doctor,
                            "TimeSlot": f"{hour:02d}:00",
                            "Status": "Available"
                        })
                        availability_data.append({
                            "Date": date,
                            "DoctorName": doctor,
                            "TimeSlot": f"{hour:02d}:30",
                            "Status": "Available"
                        })
            
            availability_df = pd.DataFrame(availability_data)
            availability_df.to_csv(availability_file, index=False)
            return availability_df
        
        try:
            return pd.read_csv(availability_file)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            today = datetime.datetime.now().date()
            tomorrow = today + datetime.timedelta(days=1)
            next_week = today + datetime.timedelta(days=7)
            
            from datetime import date
            dates = [today, tomorrow, next_week, date(2025, 9, 5), date(2025, 9, 6), date(2025, 9, 7)]
            doctors = ["Dr. Kumar", "Dr. Mehta", "Dr. Sharma", "Dr. Singh", "Dr. Patel"]
            
            availability_data = []
            
            for date in dates:
                for doctor in doctors:
                    for hour in range(9, 12):
                        availability_data.append({
                            "Date": date,
                            "DoctorName": doctor,
                            "TimeSlot": f"{hour:02d}:00",
                            "Status": "Available"
                        })
                        availability_data.append({
                            "Date": date,
                            "DoctorName": doctor,
                            "TimeSlot": f"{hour:02d}:30",
                            "Status": "Available"
                        })
                    
                    for hour in range(13, 17):
                        availability_data.append({
                            "Date": date,
                            "DoctorName": doctor,
                            "TimeSlot": f"{hour:02d}:00",
                            "Status": "Available"
                        })
                        availability_data.append({
                            "Date": date,
                            "DoctorName": doctor,
                            "TimeSlot": f"{hour:02d}:30",
                            "Status": "Available"
                        })
            
            availability_df = pd.DataFrame(availability_data)
            availability_df.to_csv(availability_file, index=False)
            return availability_df
    
    @staticmethod
    def save_availability(availability_df: pd.DataFrame) -> None:
        """Save availability data to CSV file."""
        DataLoader.ensure_data_directory()
        availability_df.to_csv('data/availability.csv', index=False)
    
    @staticmethod
    def load_appointments() -> pd.DataFrame:
        """
        Load appointments data from CSV file.
        If the file doesn't exist or is empty, create it with the required columns.
        """
        DataLoader.ensure_data_directory()
        
        appointments_file = 'data/doctor_appointments.csv'
        
        if not os.path.exists(appointments_file) or os.path.getsize(appointments_file) == 0:
            appointments_df = pd.DataFrame(columns=[
                "AppointmentID", "PatientID", "PatientName", "Doctor", 
                "Date", "StartTime", "EndTime", "Duration", 
                "InsuranceCarrier", "MemberID", "GroupNumber",
                "ConfirmationStatus", "RemindersSent", "FormSent"
            ])
            appointments_df.to_csv(appointments_file, index=False)
            return appointments_df
        
        try:
            return pd.read_csv(appointments_file)
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            appointments_df = pd.DataFrame(columns=[
                "AppointmentID", "PatientID", "PatientName", "Doctor", 
                "Date", "StartTime", "EndTime", "Duration", 
                "InsuranceCarrier", "MemberID", "GroupNumber",
                "ConfirmationStatus", "RemindersSent", "FormSent"
            ])
            appointments_df.to_csv(appointments_file, index=False)
            return appointments_df
    
    @staticmethod
    def save_appointments(appointments_df: pd.DataFrame) -> None:
        """Save appointments data to CSV file."""
        DataLoader.ensure_data_directory()
        appointments_df.to_csv('data/doctor_appointments.csv', index=False)
    
    @staticmethod
    def generate_id() -> str:
        """
        Generate a unique sequential ID for patients.
        """
        patients_df = DataLoader.load_patients()
        
        if patients_df.empty:
            return "1"
        
        numeric_ids = []
        for patient_id in patients_df['PatientID']:
            try:
                numeric_ids.append(int(patient_id))
            except (ValueError, TypeError):
                continue
        
        if not numeric_ids:
            return "1"
        
        return str(max(numeric_ids) + 1)
    
    @staticmethod
    def generate_appointment_id() -> str:
        """
        Generate a unique sequential ID for appointments.
        """
        appointments_df = DataLoader.load_appointments()
        
        if appointments_df.empty:
            return "1"
        
        numeric_ids = []
        for appointment_id in appointments_df['AppointmentID']:
            try:
                numeric_ids.append(int(appointment_id))
            except (ValueError, TypeError):
                continue
        
        if not numeric_ids:
            return "1"
        
        return str(max(numeric_ids) + 1)
    
    @staticmethod
    def add_patient(name: str, dob: str, email: str, phone: str, 
                   doctor_preference: str = "",
                   insurance_carrier: str = "", member_id: str = "", 
                   group_number: str = "", location: str = "") -> str:
        """
        Add a new patient to the patients.csv file.
        Returns the PatientID.
        """
        patients_df = DataLoader.load_patients()
        
        existing_patient = patients_df[
            (patients_df['Name'] == name) & 
            (patients_df['DOB'] == dob)
        ]
        
        if not existing_patient.empty:
            patient_id = existing_patient.iloc[0]['PatientID']
            idx = existing_patient.index[0]
            
            patients_df.at[idx, 'Email'] = email if email else existing_patient.iloc[0]['Email']
            patients_df.at[idx, 'Phone'] = phone if phone else existing_patient.iloc[0]['Phone']
            patients_df.at[idx, 'DoctorPreference'] = doctor_preference if doctor_preference else existing_patient.iloc[0]['DoctorPreference']
            patients_df.at[idx, 'InsuranceCarrier'] = insurance_carrier if insurance_carrier else existing_patient.iloc[0]['InsuranceCarrier']
            patients_df.at[idx, 'MemberID'] = member_id if member_id else existing_patient.iloc[0]['MemberID']
            patients_df.at[idx, 'GroupNumber'] = group_number if group_number else existing_patient.iloc[0]['GroupNumber']
            patients_df.at[idx, 'Location'] = location if location else existing_patient.iloc[0].get('Location', '')
        else:
            patient_id = DataLoader.generate_id()
            new_patient = {
                'PatientID': patient_id,
                'Name': name,
                'DOB': dob,
                'Email': email,
                'Phone': phone,
                'DoctorPreference': doctor_preference,
                'InsuranceCarrier': insurance_carrier,
                'MemberID': member_id,
                'GroupNumber': group_number,
                'Location': location
            }
            patients_df = pd.concat([patients_df, pd.DataFrame([new_patient])], ignore_index=True)
        
        DataLoader.save_patients(patients_df)
        return patient_id
    
    @staticmethod
    def add_appointment(patient_id: str, patient_name: str, doctor: str,
                       date: datetime.date, start_time: str, end_time: str,
                       duration: int, insurance_carrier: str = "",
                       member_id: str = "", group_number: str = "") -> str:
        """
        Add a new appointment to the doctor_appointments.csv file.
        Returns the AppointmentID.
        """
        appointments_df = DataLoader.load_appointments()
        
        appointment_id = DataLoader.generate_appointment_id()
        new_appointment = {
            'AppointmentID': appointment_id,
            'PatientID': patient_id,
            'PatientName': patient_name,
            'Doctor': doctor,
            'Date': date,
            'StartTime': start_time,
            'EndTime': end_time,
            'Duration': duration,
            'InsuranceCarrier': insurance_carrier,
            'MemberID': member_id,
            'GroupNumber': group_number,
            'ConfirmationStatus': 'Pending',
            'RemindersSent': 0,
            'FormSent': False
        }
        
        appointments_df = pd.concat([appointments_df, pd.DataFrame([new_appointment])], ignore_index=True)
        DataLoader.save_appointments(appointments_df)
        
        return appointment_id
    
    @staticmethod
    def update_appointment_status(appointment_id: str, confirmation_status: str = None,
                                reminders_sent: int = None, form_sent: bool = None) -> bool:
        """
        Update the status of an appointment.
        Returns True if successful, False otherwise.
        """
        appointments_df = DataLoader.load_appointments()
        
        appointment = appointments_df[appointments_df['AppointmentID'] == appointment_id]
        
        if appointment.empty:
            return False
        
        idx = appointment.index[0]
        
        if confirmation_status is not None:
            appointments_df.at[idx, 'ConfirmationStatus'] = confirmation_status
        
        if reminders_sent is not None:
            appointments_df.at[idx, 'RemindersSent'] = reminders_sent
        
        if form_sent is not None:
            appointments_df.at[idx, 'FormSent'] = form_sent
        
        DataLoader.save_appointments(appointments_df)
        return True
    
    @staticmethod
    def get_upcoming_appointments(days: int = 7) -> pd.DataFrame:
        """
        Get appointments in the next specified number of days.
        """
        appointments_df = DataLoader.load_appointments()
        
        if appointments_df.empty:
            return appointments_df
        
        if not pd.api.types.is_datetime64_any_dtype(appointments_df['Date']):
            appointments_df['Date'] = pd.to_datetime(appointments_df['Date'])
        
        today = datetime.datetime.now().date()
        cutoff_date = today + datetime.timedelta(days=days)
        
        upcoming = appointments_df[
            (appointments_df['Date'] >= today) & 
            (appointments_df['Date'] <= cutoff_date)
        ]
        
        return upcoming
    
    @staticmethod
    def get_daily_appointments(date: Optional[datetime.date] = None) -> pd.DataFrame:
        """
        Get appointments for a specific date.
        If date is None, use today's date.
        """
        if date is None:
            date = datetime.datetime.now().date()
        
        appointments_df = DataLoader.load_appointments()
        
        if appointments_df.empty:
            return appointments_df
        
        if not pd.api.types.is_datetime64_any_dtype(appointments_df['Date']):
            appointments_df['Date'] = pd.to_datetime(appointments_df['Date'])
        
        daily = appointments_df[appointments_df['Date'].dt.date == date]
        
        return daily