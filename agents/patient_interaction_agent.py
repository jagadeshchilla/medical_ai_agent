"""
Patient Interaction Agent for Medical Appointment System

This module provides the PatientInteractionAgent class responsible for greeting
patients and collecting basic information. The agent handles initial patient
interaction, information extraction, and conversation management.
"""

from typing import Dict, List, Any, Optional, TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq


class PatientInfo(TypedDict):
    """Type definition for patient information."""
    Name: Optional[str]
    DOB: Optional[str]
    Email: Optional[str]
    Phone: Optional[str]
    DoctorPreference: Optional[str]
    Location: Optional[str]


class PatientInteractionAgent:
    """Agent responsible for greeting patients and collecting basic information.
    
    The PatientInteractionAgent handles the initial interaction with patients,
    greeting them warmly and collecting essential information including name,
    date of birth, email, phone, doctor preference, and location.
    
    Attributes:
        llm: Language model instance for patient interaction
        greeting_prompt: Chat prompt template for patient greeting
        collection_prompt: Chat prompt template for information collection
        greeting_chain: Processing chain for patient greeting
        collection_chain: Processing chain for information collection
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.2):
        """Initialize the PatientInteractionAgent with AI model configuration.
        
        Args:
            model_name: Name of the language model to use
            temperature: Temperature setting for the language model
        """
        self.llm = ChatGroq(temperature=0, model_name="gemma2-9b-it")
        self.greeting_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a friendly medical receptionist at a doctor's office. "
                      "Your job is to greet patients warmly and collect their basic information."),
            ("human", "{input}")
        ])
        
        self.collection_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a friendly medical receptionist at a doctor's office. "
                      "Your job is to collect the following information from the patient: "
                      "Name, Date of Birth (DOB), Email, Phone, Doctor Preference, and Location. "
                      "If any information is missing, politely ask for it. "
                      "Be conversational but efficient."),
            ("human", "{input}")
        ])
        
        self.greeting_chain = self.greeting_prompt | self.llm | StrOutputParser()
        self.collection_chain = self.collection_prompt | self.llm | StrOutputParser()
        
    def greet_patient(self) -> str:
        """Generate a warm greeting for the patient.
        
        Returns:
            Friendly greeting message for the patient
        """
        return "How can I assist you today? I'm here to help you in booking an appointment."
    
    def extract_patient_info(self, conversation_history: List[Dict[str, Any]]) -> PatientInfo:
        """Extract patient information from conversation history.
        
        Args:
            conversation_history: List of conversation messages
            
        Returns:
            PatientInfo dictionary containing extracted information
        """
        patient_info: PatientInfo = {
            "Name": None,
            "DOB": None,
            "Email": None,
            "Phone": None,
            "DoctorPreference": None,
            "Location": None
        }
        
        for message in conversation_history:
            if message.get("role") == "user":
                content = message.get("content", "")
                if "name is" in content.lower():
                    parts = content.split("name is", 1)
                    if len(parts) > 1:
                        patient_info["Name"] = parts[1].strip().split(".")[0]
                
                if "born on" in content.lower() or "dob" in content.lower() or "date of birth" in content.lower():
                    for word in content.split():
                        if "/" in word or "-" in word:
                            patient_info["DOB"] = word.strip(".,;")
                
                if "@" in content:
                    words = content.split()
                    for word in words:
                        if "@" in word:
                            patient_info["Email"] = word.strip(".,;")
                
                if "phone" in content.lower() or "number" in content.lower():
                    words = content.split()
                    for i, word in enumerate(words):
                        if word.lower() in ["phone", "number", "phone:", "number:"]:
                            for j in range(i + 1, len(words)):
                                next_word = words[j].strip(".,;")
                                if next_word.isdigit() or any(char.isdigit() for char in next_word):
                                    patient_info["Phone"] = next_word
                                    break
                            break
                
                if "doctor" in content.lower() or "dr" in content.lower():
                    content_lower = content.lower()
                    
                    if "dr." in content_lower:
                        parts = content_lower.split("dr.", 1)
                        if len(parts) > 1:
                            doctor_name = "Dr. " + parts[1].strip().split(" ")[0].capitalize().strip(".,;")
                            patient_info["DoctorPreference"] = doctor_name
                    
                    elif "dr " in content_lower:
                        parts = content_lower.split("dr ", 1)
                        if len(parts) > 1:
                            doctor_name = "Dr. " + parts[1].strip().split(" ")[0].capitalize().strip(".,;")
                            patient_info["DoctorPreference"] = doctor_name
                    
                    elif content_lower.startswith("dr "):
                        doctor_name = "Dr. " + content_lower[3:].strip().split(" ")[0].capitalize().strip(".,;")
                        patient_info["DoctorPreference"] = doctor_name
                
                if "location" in content.lower() or "city" in content.lower() or "live" in content.lower() or "from" in content.lower():
                    location_keywords = ["location", "city", "live in", "from", "located", "address"]
                    content_lower = content.lower()
                    
                    for keyword in location_keywords:
                        if keyword in content_lower:
                            parts = content_lower.split(keyword, 1)
                            if len(parts) > 1:
                                location_text = parts[1].strip().split(".")[0].split(",")[0].strip()
                                words_to_remove = ["in", "at", "from", "the", "a", "an", "is", "are", "was", "were", "located", "live", "lives", "reside", "resides"]
                                location_words = [word for word in location_text.split() if word.lower() not in words_to_remove]
                                
                                if location_words:
                                    location = location_words[0]
                                    if len(location) > 2:
                                        patient_info["Location"] = location.title()
                                        break
        
        return patient_info
    
    def collect_missing_info(self, patient_info: PatientInfo, conversation_history: List[Dict[str, Any]]) -> str:
        """Generate a response to collect missing information one field at a time.
        
        Args:
            patient_info: Current patient information
            conversation_history: List of conversation messages
            
        Returns:
            Formatted message to collect missing information
        """
        required_for_lookup = ["Name", "DOB", "Email", "Phone"]
        has_lookup_info = all(patient_info.get(field) is not None for field in required_for_lookup[:2])
        
        if has_lookup_info:
            if patient_info.get("DoctorPreference") is None:
                patient_info["DoctorPreference"] = "To be determined"
            
            missing_fields = [field for field, value in patient_info.items() 
                             if value is None and field != "DoctorPreference"]
        else:
            missing_fields = [field for field, value in patient_info.items() if value is None]
        
        if not missing_fields:
            return "Thank you for providing all your information. Let me check if we have you in our system."
        
        first_missing = missing_fields[0]
        prompt = ""
        
        if first_missing == "Name":
            prompt = "Could you please tell me your full name?"
        elif first_missing == "DOB":
            prompt = "What is your date of birth?"
        elif first_missing == "Email":
            prompt = "What email address can we use to contact you?"
        elif first_missing == "Phone":
            prompt = "What's the best phone number to reach you?"
        elif first_missing == "DoctorPreference":
            prompt = "Do you have a preferred doctor you'd like to see?"
        elif first_missing == "Location":
            prompt = "What city or location are you from?"
        
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        return self.collection_chain.invoke({"input": f"Conversation so far:\n{conversation_text}\n\nI need to ask for the patient's {first_missing}. Make it conversational and ask ONLY about {first_missing}. Don't ask for any other information yet."})
    
    def process_message(self, message: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a message from the patient and return a response.
        
        Args:
            message: Patient's message
            conversation_history: List of conversation messages
            
        Returns:
            Dictionary containing response, patient info, and updated conversation history
        """
        conversation_history.append({"role": "user", "content": message})
        
        patient_info = self.extract_patient_info(conversation_history)
        response = self.collect_missing_info(patient_info, conversation_history)
        conversation_history.append({"role": "assistant", "content": response})
        
        return {
            "response": response,
            "patient_info": patient_info,
            "conversation_history": conversation_history
        }