"""
Insurance Agent for Medical Appointment System

This module provides the InsuranceAgent class responsible for collecting and
processing insurance information from patients. The agent handles insurance
data collection, validation, and storage in patient records.
"""

import pandas as pd
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser


class InsuranceAgent:
    """Agent responsible for collecting and processing insurance information from patients.
    
    The InsuranceAgent handles the collection of insurance details including carrier,
    member ID, and group number. It processes patient responses and updates patient
    records with insurance information.
    
    Attributes:
        patients_csv_path (str): Path to the patients CSV file
        llm: Language model instance for insurance processing
        insurance_prompt: Chat prompt template for insurance collection
        extraction_prompt: Chat prompt template for information extraction
        insurance_chain: Processing chain for insurance collection
        extraction_chain: Processing chain for information extraction
    """
    
    def __init__(self, patients_csv_path: str = "data/patients.csv",
                 model_name: str = "gpt-3.5-turbo", temperature: float = 0.2):
        """Initialize the InsuranceAgent with data paths and AI model configuration.
        
        Args:
            patients_csv_path: Path to the patients CSV file
            model_name: Name of the language model to use
            temperature: Temperature setting for the language model
        """
        self.patients_csv_path = patients_csv_path
        self.llm = ChatGroq(temperature=0, model_name="gemma2-9b-it")
        
        self.insurance_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful medical office assistant collecting insurance information. "
                      "Ask for the required insurance information in a friendly, professional manner. "
                      "Be clear about what information is needed."),
            ("human", "I need to collect insurance information from a patient named {patient_name}. "
                     "I need their insurance carrier, member ID, and group number. "
                     "What's a good way to ask for this information?")
        ])
        
        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful medical office assistant. "
                      "Extract the insurance information from the patient's response. "
                      "Return a JSON object with the following fields: "
                      "InsuranceCarrier, MemberID, GroupNumber. "
                      "If any field is missing, set its value to null."),
            ("human", "Patient response: {patient_response}")
        ])
        
        self.insurance_chain = self.insurance_prompt | self.llm | StrOutputParser()
        self.extraction_chain = self.extraction_prompt | self.llm | StrOutputParser()
    
    def load_patients(self) -> pd.DataFrame:
        """Load patient data from CSV file using the main DataLoader.
        
        Returns:
            DataFrame containing patient data with standard columns
        """
        try:
            from utils.data_loader import DataLoader
            return DataLoader.load_patients()
        except Exception as e:
            print(f"Error loading patients data: {e}")
            return pd.DataFrame(columns=[
                "PatientID", "Name", "DOB", "Email", "Phone", 
                "DoctorPreference", "InsuranceCarrier", 
                "MemberID", "GroupNumber", "Location", "PatientType"
            ])
    
    def save_patients(self, patients_df: pd.DataFrame) -> bool:
        """Save patient data to CSV file using the main DataLoader.
        
        Args:
            patients_df: DataFrame containing patient data
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            from utils.data_loader import DataLoader
            DataLoader.save_patients(patients_df)
            return True
        except Exception as e:
            print(f"Error saving patients data: {e}")
            return False
    
    def get_insurance_collection_message(self, patient_name: str) -> str:
        """Generate a message to collect insurance information from a patient.
        
        Args:
            patient_name: Name of the patient
            
        Returns:
            Formatted message for insurance information collection
        """
        return self.insurance_chain.invoke({"patient_name": patient_name})
    
    def extract_insurance_info(self, patient_response: str) -> Dict[str, Any]:
        """Extract insurance information from patient response.
        
        Args:
            patient_response: Patient's response containing insurance information
            
        Returns:
            Dictionary containing extracted insurance information
        """
        insurance_info = self._simple_insurance_extraction(patient_response)
        
        if any(insurance_info.values()):
            return insurance_info
        
        try:
            extraction_result = self.extraction_chain.invoke({"patient_response": patient_response})
            
            if "InsuranceCarrier" in extraction_result:
                carrier_start = extraction_result.find("InsuranceCarrier") + len("InsuranceCarrier") + 2
                carrier_end = extraction_result.find(",", carrier_start)
                if carrier_end == -1:
                    carrier_end = extraction_result.find("}", carrier_start)
                if carrier_end != -1:
                    carrier = extraction_result[carrier_start:carrier_end].strip()
                    carrier = carrier.strip('"').strip("'")
                    insurance_info["InsuranceCarrier"] = carrier
            
            if "MemberID" in extraction_result:
                member_id_start = extraction_result.find("MemberID") + len("MemberID") + 2
                member_id_end = extraction_result.find(",", member_id_start)
                if member_id_end == -1:
                    member_id_end = extraction_result.find("}", member_id_start)
                if member_id_end != -1:
                    member_id = extraction_result[member_id_start:member_id_end].strip()
                    member_id = member_id.strip('"').strip("'")
                    insurance_info["MemberID"] = member_id
            
            if "GroupNumber" in extraction_result:
                group_number_start = extraction_result.find("GroupNumber") + len("GroupNumber") + 2
                group_number_end = extraction_result.find(",", group_number_start)
                if group_number_end == -1:
                    group_number_end = extraction_result.find("}", group_number_start)
                if group_number_end != -1:
                    group_number = extraction_result[group_number_start:group_number_end].strip()
                    group_number = group_number.strip('"').strip("'")
                    insurance_info["GroupNumber"] = group_number
                    
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
        
        return insurance_info
    
    def _simple_insurance_extraction(self, patient_response: str) -> Dict[str, Any]:
        """Simple keyword-based insurance information extraction.
        
        Args:
            patient_response: Patient's response containing insurance information
            
        Returns:
            Dictionary containing extracted insurance information
        """
        insurance_info = {}
        content_lower = patient_response.lower()
        
        insurance_carriers = [
            "aetna", "blue cross", "bluecross", "cigna", "humana", "unitedhealth", 
            "kaiser", "medicare", "medicaid", "anthem", "bcbs", "bc/bs"
        ]
        
        for carrier in insurance_carriers:
            if carrier in content_lower:
                insurance_info["InsuranceCarrier"] = carrier.title()
                break
        
        import re
        member_id_patterns = [
            r"member\s*id[:\s]+is\s+([a-zA-Z0-9]+)",
            r"member\s*id[:\s]+([a-zA-Z0-9]+)",
            r"member\s*number[:\s]+is\s+([a-zA-Z0-9]+)",
            r"member\s*number[:\s]+([a-zA-Z0-9]+)",
            r"id[:\s]+([a-zA-Z0-9]{6,})",
        ]
        
        for pattern in member_id_patterns:
            match = re.search(pattern, content_lower)
            if match:
                insurance_info["MemberID"] = match.group(1).upper()
                break
        
        group_patterns = [
            r"group\s*number[:\s]+is\s+([a-zA-Z0-9]+)",
            r"group\s*number[:\s]+([a-zA-Z0-9]+)",
            r"group[:\s]+([a-zA-Z0-9]+)",
        ]
        
        for pattern in group_patterns:
            match = re.search(pattern, content_lower)
            if match:
                insurance_info["GroupNumber"] = match.group(1).upper()
                break
        
        return insurance_info
    
    def update_patient_insurance(self, patient_id: str, insurance_info: Dict[str, Any]) -> bool:
        """Update patient record with insurance information.
        
        Args:
            patient_id: ID of the patient to update
            insurance_info: Dictionary containing insurance information
            
        Returns:
            True if update was successful, False otherwise
        """
        patients_df = self.load_patients()
        
        if patients_df.empty:
            print(f"Insurance Agent: No patients data found")
            return False
        
        patients_df["PatientID"] = patients_df["PatientID"].astype(str)
        
        patient_mask = patients_df["PatientID"] == str(patient_id)
        if not any(patient_mask):
            print(f"Insurance Agent: Patient ID {patient_id} not found in database")
            print(f"Available PatientIDs: {patients_df['PatientID'].tolist()}")
            return False
        
        for field, value in insurance_info.items():
            if field in patients_df.columns and value is not None:
                patients_df.loc[patient_mask, field] = value
                print(f"Insurance Agent: Updated {field} = {value} for patient {patient_id}")
        
        success = self.save_patients(patients_df)
        if success:
            print(f"Insurance Agent: Successfully saved insurance info for patient {patient_id}")
        else:
            print(f"Insurance Agent: Failed to save insurance info for patient {patient_id}")
        return success
    
    def process_insurance_collection(self, patient_id: str, patient_name: str, 
                                     patient_response: Optional[str] = None) -> Dict[str, Any]:
        """Process insurance collection for a patient.
        
        Args:
            patient_id: ID of the patient
            patient_name: Name of the patient
            patient_response: Patient's response containing insurance information
            
        Returns:
            Dictionary with collection results and next steps
        """
        if patient_response is None:
            collection_message = self.get_insurance_collection_message(patient_name)
            return {
                "success": True,
                "message": collection_message,
                "needs_response": True,
                "patient_id": patient_id,
                "patient_name": patient_name
            }
        
        insurance_info = self.extract_insurance_info(patient_response)
        
        required_fields = ["InsuranceCarrier", "MemberID", "GroupNumber"]
        missing_fields = [field for field in required_fields if field not in insurance_info]
        
        if missing_fields:
            missing_fields_str = ", ".join(missing_fields)
            collection_message = f"Thank you for providing your insurance information. "
            collection_message += f"However, we still need your {missing_fields_str}. "
            collection_message += f"Could you please provide this information?"
            
            return {
                "success": False,
                "message": collection_message,
                "needs_response": True,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "missing_fields": missing_fields
            }
        
        update_success = self.update_patient_insurance(patient_id, insurance_info)
        
        if update_success:
            return {
                "success": True,
                "message": "Thank you for providing your insurance information. It has been saved to your record.",
                "needs_response": False,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "insurance_info": insurance_info
            }
        else:
            return {
                "success": False,
                "message": "We encountered an issue saving your insurance information. Please try again later.",
                "needs_response": False,
                "patient_id": patient_id,
                "patient_name": patient_name
            }