"""
Admin Agent for Medical Appointment System

This module provides the AdminAgent class responsible for generating comprehensive
daily and weekly reports from appointment data. The agent processes appointment
information and creates formatted reports using AI-powered text generation.
"""
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq


class AdminAgent:
    """Agent responsible for generating daily and weekly reports from appointments data.
    
    The AdminAgent processes appointment data and generates comprehensive reports
    containing patient details, doctor information, appointment times, insurance
    information, confirmation status, and reminder tracking.
    
    Attributes:
        appointments_csv_path (str): Path to the appointments CSV file
        patients_csv_path (str): Path to the patients CSV file
        llm: Language model instance for report generation
        report_prompt: Chat prompt template for report generation
        report_chain: Processing chain for report generation
    """
    
    def __init__(self, appointments_csv_path: str = "data/doctor_appointments.csv",
                 patients_csv_path: str = "data/patients.csv",
                 model_name: str = "gpt-3.5-turbo", temperature: float = 0.2):
        """Initialize the AdminAgent with data paths and AI model configuration.
        
        Args:
            appointments_csv_path: Path to the appointments CSV file
            patients_csv_path: Path to the patients CSV file
            model_name: Name of the language model to use
            temperature: Temperature setting for the language model
        """
        self.appointments_csv_path = appointments_csv_path
        self.patients_csv_path = patients_csv_path
        self.llm = ChatGroq(temperature=0, model_name="gemma2-9b-it")
        self.report_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an administrative assistant at a medical office. "
                      "Your job is to generate clear, concise reports based on appointment data. "
                      "Format the information in a professional manner."),
            ("human", "{input}")
        ])
        self.report_chain = self.report_prompt | self.llm | StrOutputParser()
    
    def load_appointments(self) -> pd.DataFrame:
        """Load appointment data from CSV file with column normalization.
        
        Returns:
            DataFrame containing appointment data with normalized column names
        """
        try:
            df = pd.read_csv(self.appointments_csv_path)
            if 'date' in df.columns and 'Date' not in df.columns:
                df['Date'] = df['date']
            if 'appointment_id' in df.columns and 'AppointmentID' not in df.columns:
                df['AppointmentID'] = df['appointment_id']
            return df
        except Exception as e:
            print(f"Error loading appointments data: {e}")
            return pd.DataFrame(columns=[
                "AppointmentID", "PatientID", "PatientName", "Doctor", 
                "Date", "StartTime", "EndTime", "Duration", 
                "InsuranceCarrier", "MemberID", "GroupNumber",
                "ConfirmationStatus", "RemindersSent"
            ])
    
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
    
    def generate_daily_report(self, report_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate a comprehensive daily report for the specified date.
        
        Args:
            report_date: Date for the report (defaults to today)
            
        Returns:
            Dictionary containing report data, success status, and appointment details
        """
        if report_date is None:
            report_date = date.today()
        
        date_str = report_date.strftime("%Y-%m-%d")
        appointments_df = self.load_appointments()
        patients_df = self.load_patients()
        
        if appointments_df.empty:
            return {
                "success": False,
                "report": "No appointment data available.",
                "date": date_str,
                "appointments_count": 0
            }
        
        daily_appointments = appointments_df[appointments_df["Date"] == date_str]
        
        if daily_appointments.empty:
            return {
                "success": False,
                "report": f"No appointments scheduled for {date_str}.",
                "date": date_str,
                "appointments_count": 0
            }
        
        appointments_list = []
        for _, appointment in daily_appointments.iterrows():
            appointment_data = appointment.to_dict()
            
            if not patients_df.empty and "PatientID" in appointment_data:
                patient_id = appointment_data["PatientID"]
                patient_matches = patients_df[patients_df["PatientID"] == patient_id]
                if not patient_matches.empty:
                    patient_data = patient_matches.iloc[0].to_dict()
                    for field in ["Email", "Phone", "PatientType"]:
                        if field in patient_data:
                            appointment_data[field] = patient_data[field]
            
            appointments_list.append(appointment_data)
        
        appointments_text = ""
        for i, appt in enumerate(appointments_list, 1):
            appointments_text += f"Appointment #{i}:\n"
            for key, value in appt.items():
                appointments_text += f"  {key}: {value}\n"
            appointments_text += "\n"
        
        input_text = f"Date: {date_str}\n"
        input_text += f"Total Appointments: {len(appointments_list)}\n\n"
        input_text += f"Appointment Details:\n{appointments_text}\n"
        input_text += "Generate a professional daily appointment report with the above information. "
        input_text += "Include a summary section with key statistics and a detailed section listing each appointment."
        
        report = self.report_chain.invoke({"input": input_text})
        
        return {
            "success": True,
            "report": report,
            "date": date_str,
            "appointments_count": len(appointments_list),
            "appointments": appointments_list
        }
    
    def generate_weekly_report(self, start_date: Optional[date] = None) -> Dict[str, Any]:
        """Generate a comprehensive weekly report starting from the specified date.
        
        Args:
            start_date: Start date for the week (defaults to beginning of current week)
            
        Returns:
            Dictionary containing weekly report data and daily breakdowns
        """
        if start_date is None:
            today = date.today()
            start_date = today - datetime.timedelta(days=today.weekday())
        
        daily_reports = []
        for i in range(7):
            report_date = start_date + datetime.timedelta(days=i)
            daily_report = self.generate_daily_report(report_date)
            daily_reports.append(daily_report)
        
        total_appointments = sum(report["appointments_count"] for report in daily_reports)
        week_str = f"{start_date.strftime('%Y-%m-%d')} to {(start_date + datetime.timedelta(days=6)).strftime('%Y-%m-%d')}"
        
        input_text = f"Weekly Report: {week_str}\n"
        input_text += f"Total Appointments: {total_appointments}\n\n"
        
        for report in daily_reports:
            input_text += f"Date: {report['date']}\n"
            input_text += f"Appointments: {report['appointments_count']}\n\n"
        
        input_text += "Generate a professional weekly appointment report with the above information. "
        input_text += "Include a summary section with key statistics for the week and brief daily breakdowns."
        
        report = self.report_chain.invoke({"input": input_text})
        
        return {
            "success": True,
            "report": report,
            "week": week_str,
            "total_appointments": total_appointments,
            "daily_reports": daily_reports
        }