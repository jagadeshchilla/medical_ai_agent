"""
Patient Lookup Agent for Medical Appointment System

This module provides the PatientLookupAgent class responsible for checking if a patient
exists in the system and determining appointment duration based on patient type.
New patients receive 60-minute appointments while returning patients get 30-minute appointments.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq


class PatientLookupAgent:
    """Agent responsible for checking if a patient exists in the system and determining appointment duration.
    
    The PatientLookupAgent performs patient lookups using multiple criteria (name, DOB, email, phone)
    and determines whether a patient is new or returning, which affects appointment duration.
    
    Attributes:
        patients_csv_path (str): Path to the patients CSV file
        llm: Language model for generating responses
        lookup_prompt: Chat prompt template for patient lookup
        lookup_chain: Processing chain for patient lookup
    """
    
    def __init__(self, patients_csv_path: str = "data/patients.csv", model_name: str = "gpt-3.5-turbo", temperature: float = 0.2):
        """Initialize the PatientLookupAgent.
        
        Args:
            patients_csv_path: Path to the patients CSV file
            model_name: Name of the language model to use
            temperature: Temperature setting for the language model
        """
        self.patients_csv_path = patients_csv_path
        self.llm = ChatGroq(temperature=0, model_name="gemma2-9b-it")
        self.lookup_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a medical receptionist assistant. "
                      "Your job is to check if a patient exists in our system and determine "
                      "their appointment duration based on their patient type. "
                      "New patients get 60-minute appointments. "
                      "Returning patients get 30-minute appointments."),
            ("human", "{input}")
        ])
        self.lookup_chain = self.lookup_prompt | self.llm | StrOutputParser()
    
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
                "DoctorPreference", "InsuranceCarrier", 
                "MemberID", "GroupNumber", "Location"
            ])
    
    def lookup_patient(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """Look up a patient in the system and determine appointment duration.
        
        Args:
            patient_info: Dictionary containing patient information (Name, DOB, Email, Phone, etc.)
            
        Returns:
            Dictionary containing:
                - patient_exists: Boolean indicating if patient exists in system
                - patient_id: Patient ID from database or newly generated
                - patient_type: "New" or "Returning"
                - appointment_duration: 30 for returning, 60 for new patients
                - patient_record: Patient data from database or None
                - doctor_preference: Doctor preference from record or provided
                - response: LLM-generated response message
        """
        patients_df = self.load_patients()
        
        name = patient_info.get("Name")
        dob = patient_info.get("DOB")
        email = patient_info.get("Email")
        phone = patient_info.get("Phone")
        doctor_preference = patient_info.get("DoctorPreference")
        
        patient_record = None
        patient_id = None
        
        if name and dob and not patients_df.empty:
            matches = patients_df[(patients_df["Name"].str.lower().str.contains(name.lower().split()[0])) & 
                                 (patients_df["DOB"] == dob)]
            if not matches.empty:
                patient_record = matches.iloc[0].to_dict()
                patient_id = patient_record["PatientID"]
        
        if patient_record is None and email and not patients_df.empty:
            matches = patients_df[patients_df["Email"].str.lower() == email.lower()]
            if not matches.empty:
                patient_record = matches.iloc[0].to_dict()
                patient_id = patient_record["PatientID"]
        
        if patient_record is None and phone and not patients_df.empty:
            phone_digits = ''.join(filter(str.isdigit, phone))
            patients_df["PhoneDigits"] = patients_df["Phone"].apply(
                lambda x: ''.join(filter(str.isdigit, str(x))) if pd.notna(x) else "")
            matches = patients_df[patients_df["PhoneDigits"].str.contains(phone_digits, na=False)]
            if not matches.empty:
                patient_record = matches.iloc[0].to_dict()
                patient_id = patient_record["PatientID"]
        
        if patient_record:
            patient_type = "Returning"
            duration = 30
            exists = True
            
            if patient_record.get("DoctorPreference"):
                doctor_preference = patient_record.get("DoctorPreference")
                patient_info["DoctorPreference"] = doctor_preference
                
            print(f"Found existing patient: {name}, ID: {patient_id}, Type: {patient_type} (30 mins)")
        else:
            patient_type = "New"
            duration = 60
            exists = False
            
            print(f"Patient not found: {name}, {dob}, {email}. Adding as new patient (60 mins).")
            
            from utils.data_loader import DataLoader
            patient_id = DataLoader.add_patient(
                name=name,
                dob=dob,
                email=email,
                phone=phone,
                doctor_preference=doctor_preference,
                location=patient_info.get("Location", "")
            )
        
        exact_name_match = False
        exact_email_match = False
        
        if not patients_df.empty:
            exact_name_match = any(patients_df["Name"].str.lower() == name.lower())
            if email:
                exact_email_match = any(patients_df["Email"].str.lower() == email.lower())
        
        if not (exact_name_match or exact_email_match):
            exists = False
            patient_type = "New"
            duration = 60
            print(f"No exact match found for {name} or {email} - treating as new patient (60 mins)")
            
            if patient_id is None:
                from utils.data_loader import DataLoader
                patient_id = DataLoader.add_patient(
                    name=name,
                    dob=dob,
                    email=email,
                    phone=phone,
                    doctor_preference=doctor_preference,
                    location=patient_info.get("Location", "")
                )
        
        input_text = f"Patient info: Name: {name}, DOB: {dob}, Email: {email}, Phone: {phone}\n"
        input_text += f"Patient exists in system: {exists}\n"
        input_text += f"Patient type: {patient_type}\n"
        input_text += f"Appointment duration: {duration} minutes\n"
        if exists:
            input_text += f"Doctor preference from record: {doctor_preference}\n"
            input_text += "Generate a friendly response explaining that this is a returning patient with a 30-minute appointment and that we'll use their preferred doctor from our records."
        else:
            input_text += "Generate a friendly response explaining that the patient has been added to our system as a new patient and their appointment will be 60 minutes long."
        
        response = self.lookup_chain.invoke({"input": input_text})
        
        return {
            "patient_exists": exists,
            "patient_id": patient_id,
            "patient_type": patient_type,
            "appointment_duration": duration,
            "patient_record": patient_record,
            "doctor_preference": doctor_preference,
            "response": response
        }