"""Medical Office Appointment Scheduling Chatbot - Main Application."""

import streamlit as st
import pandas as pd
import datetime
import os
import uuid
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

from agents.patient_interaction_agent import PatientInteractionAgent
from agents.patient_lookup_agent import PatientLookupAgent
from agents.scheduling_agent import SchedulingAgent
from agents.insurance_agent import InsuranceAgent
from agents.confirmation_agent import ConfirmationAgent
from agents.form_distribution_agent import FormDistributionAgent
from agents.reminder_agent import ReminderAgent
from agents.admin_agent import AdminAgent

from services.confirmation_service import ConfirmationService

st.set_page_config(
    page_title="Medical Appointment Scheduling Agent",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'current_step' not in st.session_state:
        st.session_state.current_step = "greeting"
    if 'patient_info' not in st.session_state:
        st.session_state.patient_info = {}
    if 'appointment_info' not in st.session_state:
        st.session_state.appointment_info = {}
    if 'insurance_info' not in st.session_state:
        st.session_state.insurance_info = {}
    if 'appointment_id' not in st.session_state:
        st.session_state.appointment_id = None
    if 'available_slots' not in st.session_state:
        st.session_state.available_slots = []
    if 'form_status' not in st.session_state:
        st.session_state.form_status = "not_sent"
    if 'reminder_count' not in st.session_state:
        st.session_state.reminder_count = 0
    if 'edge_case' not in st.session_state:
        st.session_state.edge_case = None
    if 'last_user_input' not in st.session_state:
        st.session_state.last_user_input = None
    if 'confirmation_sent' not in st.session_state:
        st.session_state.confirmation_sent = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "chat"

def initialize_agents():
    if 'agents' not in st.session_state:
        st.session_state.agents = {
            'patient_interaction': PatientInteractionAgent(),
            'patient_lookup': PatientLookupAgent(),
            'scheduling': SchedulingAgent(),
            'insurance': InsuranceAgent(),
            'confirmation': ConfirmationAgent(),
            'form_distribution': FormDistributionAgent(),
            'reminder': ReminderAgent(),
            'admin': AdminAgent()
        }

def add_message(role: str, content: str):
    st.session_state.conversation_history.append({"role": role, "content": content})

def show_agent_info_page():
    """Display agent information page."""
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #1f77b4; margin: 0;">⚕️</h2>
        <h3 style="color: #333; margin: 0.5rem 0;">Medical Appointment</h3>
        <h4 style="color: #666; margin: 0;">Scheduling Agent</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 🤖 About the Agent")
    st.markdown("""
    The Medical Appointment Scheduling Agent is an intelligent AI assistant designed to help patients 
    book medical appointments efficiently. This agent can:
    
    - **Collect patient information** (name, DOB, email, phone, location)
    - **Look up existing patients** in the system
    - **Schedule appointments** with preferred doctors
    - **Handle insurance information** collection
    - **Send confirmations** and reminders
    - **Manage appointment changes** and cancellations
    """)
    
    st.markdown("### 🏥 Available Services")
    st.markdown("""
    - **New Patient Registration**: Add new patients to the system
    - **Appointment Scheduling**: Book appointments with available doctors
    - **Insurance Verification**: Collect and verify insurance information
    - **Appointment Management**: Modify, reschedule, or cancel appointments
    - **Form Distribution**: Send intake forms to patients
    - **Reminder System**: Automated appointment reminders
    """)
    
    st.markdown("### 👨‍⚕️ Available Doctors")
    st.markdown("""
    - **Dr. Kumar** - General Medicine
    - **Dr. Smith** - Cardiology
    - **Dr. Johnson** - Dermatology
    - **Dr. Williams** - Pediatrics
    - **Dr. Brown** - Orthopedics
    """)
    
    st.markdown("### 📍 Locations")
    st.markdown("""
    - **Chicago** - Main Office
    - **New York** - Branch Office
    - **Los Angeles** - West Coast Office
    - **Houston** - Texas Office
    """)
    
    st.markdown("### ⏰ Operating Hours")
    st.markdown("""
    - **Monday - Friday**: 8:00 AM - 6:00 PM
    - **Saturday**: 9:00 AM - 2:00 PM
    - **Sunday**: Closed
    """)

def show_prompts_page():
    """Display example prompts page."""
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #1f77b4; margin: 0;">💬</h2>
        <h3 style="color: #333; margin: 0.5rem 0;">Example Prompts</h3>
        <h4 style="color: #666; margin: 0;">How to interact with the agent</h4>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 📅 Appointment Scheduling Prompts")
    
    st.markdown("#### Complete Information Prompt:")
    st.code("""
I'd like to schedule an appointment. My name is Jagadesh reddy Chilla. 
My date of birth is 2003-02-01. My email is chillajagadesh68@gmail.com. 
My phone number is 6309476048. My city is located in Chicago. 
I want to book appointment with Dr.Kumar.
    """, language="text")
    
    st.markdown("#### Alternative Format:")
    st.code("""
Hi, I need to book a medical appointment. Here are my details:
- Name: Sarah Johnson
- DOB: 1990-05-15
- Email: sarah.johnson@email.com
- Phone: 555-123-4567
- Location: New York
- Preferred Doctor: Dr. Smith
    """, language="text")
    
    st.markdown("#### Simple Request:")
    st.code("""
I want to schedule an appointment with Dr. Johnson in Los Angeles. 
My name is Mike Davis, born on 1985-12-10, email mike.davis@gmail.com, 
phone 555-987-6543.
    """, language="text")
    
    st.markdown("### 🏥 Insurance Information Prompts")
    
    st.markdown("#### Complete Insurance Details:")
    st.code("""
I have Blue Cross Blue Shield, member number XYZ789, group GRP456
    """, language="text")
    
    st.markdown("#### Alternative Insurance Format:")
    st.code("""
My insurance information:
- Carrier: Aetna
- Member ID: AET123456789
- Group Number: GRP789
    """, language="text")
    
    st.markdown("#### Simple Insurance Info:")
    st.code("""
Insurance: UnitedHealth, Member ID: UHC987654, Group: GRP123
    """, language="text")
    
    st.markdown("### 🔄 Other Useful Prompts")
    
    st.markdown("#### Reschedule Appointment:")
    st.code("""
I need to reschedule my appointment. My appointment ID is APT123456. 
Can I change it to next Tuesday?
    """, language="text")
    
    st.markdown("#### Cancel Appointment:")
    st.code("""
I need to cancel my appointment. My appointment ID is APT123456. 
The reason is schedule conflict.
    """, language="text")
    
    st.markdown("#### Check Appointment Status:")
    st.code("""
Can you check the status of my appointment? My appointment ID is APT123456.
    """, language="text")
    
    st.markdown("#### Update Information:")
    st.code("""
I need to update my phone number. My new number is 555-999-8888.
    """, language="text")
    
    st.markdown("### 💡 Tips for Better Interaction")
    st.markdown("""
    - **Be specific**: Provide all required information in one message
    - **Use clear format**: Include name, DOB, email, phone, location, and doctor preference
    - **Check availability**: Ask about specific dates or time preferences
    - **Insurance ready**: Have your insurance card information handy
    - **Ask questions**: Feel free to ask about available slots, doctors, or locations
    """)

def process_message(user_message: str):
    add_message("user", user_message)
    
    current_step = st.session_state.current_step
    
    if current_step == "greeting":
        patient_interaction_agent = st.session_state.agents['patient_interaction']
        result = patient_interaction_agent.process_message(user_message, st.session_state.conversation_history)
        
        response = result["response"]
        extracted_info = result["patient_info"]
        
        st.session_state.patient_info.update(extracted_info)
        
        required_fields = ["Name", "DOB", "Email", "Phone", "DoctorPreference", "Location"]
        missing_fields = [field for field in required_fields if field not in st.session_state.patient_info or not st.session_state.patient_info[field]]
        
        if not missing_fields:
            st.session_state.current_step = "patient_lookup"
            
            patient_lookup_agent = st.session_state.agents['patient_lookup']
            lookup_result = patient_lookup_agent.lookup_patient(st.session_state.patient_info)
            
            st.session_state.patient_info["PatientType"] = lookup_result["patient_type"]
            st.session_state.appointment_info["Duration"] = lookup_result["appointment_duration"]
            
            if "doctor_preference" in lookup_result and lookup_result["doctor_preference"]:
                st.session_state.patient_info["DoctorPreference"] = lookup_result["doctor_preference"]
            
            st.session_state.patient_info["PatientID"] = lookup_result["patient_id"]
            
            if lookup_result["patient_exists"]:
                response = lookup_result['response']
            else:
                response = f"{lookup_result['response']}\n\nI've added you to our system as a new patient. Let's continue with scheduling your appointment."
            
            add_message("assistant", response)
            
            st.session_state.current_step = "scheduling"
            return
        else:
            add_message("assistant", response)
            return
    
    elif current_step == "scheduling":
        scheduling_agent = st.session_state.agents['scheduling']
        
        if "cancel" in user_message.lower():
            st.session_state.edge_case = "patient_cancels"
            response = "I understand you want to cancel. Could you please provide the reason for cancellation? This helps us improve our services."
            add_message("assistant", response)
            return
        
        try:
            selected_date = datetime.datetime.strptime(user_message, "%Y-%m-%d").date()
            st.session_state.appointment_info["Date"] = selected_date
            
            doctor_preference = st.session_state.patient_info.get("DoctorPreference", "Any")
            duration = st.session_state.appointment_info.get("Duration", 30)
            
            available_slots = scheduling_agent.find_available_slots(
                str(selected_date), doctor_preference, duration
            )
            
            if available_slots:
                slot_options = [f"{slot['start_time']} - {slot['end_time']} with Dr. {slot['doctor']}" 
                               for slot in available_slots]
                slot_options_str = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(slot_options)])
                
                response = f"Great! Here are the available slots for {selected_date}:\n{slot_options_str}\n\nPlease select a slot by entering the number."
                st.session_state.available_slots = available_slots
            else:
                st.session_state.edge_case = "doctor_fully_booked"
                
                other_slots = scheduling_agent.find_available_slots(
                    str(selected_date), "Any", duration
                )
                
                if other_slots:
                    slot_options = [f"{slot['start_time']} - {slot['end_time']} with Dr. {slot['doctor']}" 
                                  for slot in other_slots]
                    slot_options_str = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(slot_options)])
                    
                    response = f"I'm sorry, Dr. {doctor_preference} is fully booked on {selected_date}. However, we have the following slots available with other doctors:\n{slot_options_str}\n\nPlease select a slot by entering the number, or enter another date to check Dr. {doctor_preference}'s availability."
                    st.session_state.available_slots = other_slots
                else:
                    response = f"I'm sorry, there are no available slots for {selected_date}. Please try another date."
            
            add_message("assistant", response)
            return
        except ValueError:
            if st.session_state.get("available_slots") and user_message.isdigit():
                slot_index = int(user_message) - 1
                if 0 <= slot_index < len(st.session_state.available_slots):
                    selected_slot = st.session_state.available_slots[slot_index]
                    
                    appointment_date = st.session_state.appointment_info["Date"]
                    doctor = selected_slot["doctor"]
                    start_time = selected_slot["start_time"]
                    end_time = selected_slot["end_time"]
                    duration = st.session_state.appointment_info["Duration"]
                    
                    patient_info = {
                        "PatientID": st.session_state.patient_info.get("PatientID"),
                        "Name": st.session_state.patient_info.get("Name"),
                        "DoctorPreference": doctor,
                        "InsuranceCarrier": st.session_state.insurance_info.get("InsuranceCarrier", ""),
                        "MemberID": st.session_state.insurance_info.get("MemberID", ""),
                        "GroupNumber": st.session_state.insurance_info.get("GroupNumber", "")
                    }
                    
                    scheduling_result = scheduling_agent.schedule_appointment(
                        patient_info, duration, str(appointment_date)
                    )
                    
                    if scheduling_result["success"]:
                        st.session_state.appointment_info.update({
                            "Doctor": doctor,
                            "StartTime": start_time,
                            "EndTime": end_time
                        })
                        
                        response = f"Great! I've scheduled your appointment with {doctor} on {appointment_date} from {start_time} to {end_time}. Now, let's collect your insurance information."
                        st.session_state.current_step = "insurance"
                    else:
                        response = "I'm sorry, there was an error scheduling your appointment. Please try again."
                    
                    add_message("assistant", response)
                    return
                else:
                    response = "Please select a valid slot number from the list."
                    add_message("assistant", response)
                    return
            
            response = "Please enter a date for your appointment in YYYY-MM-DD format."
            add_message("assistant", response)
            return
    
    elif current_step == "insurance":
        insurance_agent = st.session_state.agents['insurance']
        
        patient_id = st.session_state.patient_info.get("PatientID")
        patient_name = st.session_state.patient_info.get("Name")
        
        result = insurance_agent.process_insurance_collection(patient_id, patient_name, user_message)
        
        response = result["message"]
        insurance_info = result.get("insurance_info", {})
        
        st.session_state.insurance_info.update(insurance_info)
        
        if result["success"] and not result.get("needs_response", False):
            confirmation_agent = st.session_state.agents['confirmation']
            
            summary_result = confirmation_agent.show_appointment_summary(
                st.session_state.patient_info,
                st.session_state.appointment_info,
                st.session_state.insurance_info
            )
            
            if summary_result["success"]:
                st.session_state.current_step = "confirmation"
                response = summary_result["confirmation_message"]
            else:
                response = "There was an error preparing your appointment summary. Please try again."
        
        add_message("assistant", response)
        return
    
    elif current_step == "reminders":
        reminder_agent = st.session_state.agents['reminder']
        form_agent = st.session_state.agents['form_distribution']
        
        if st.session_state.form_status == "sent" and st.session_state.reminder_count < 3:
            form_completed = False
            
            if not form_completed:
                st.session_state.edge_case = "form_not_filled"
                st.session_state.reminder_count += 1
                
                reminder_result = reminder_agent.send_reminder(
                    st.session_state.appointment_id,
                    st.session_state.reminder_count
                )
                
                if reminder_result["success"]:
                    response = f"I noticed you haven't completed your intake forms yet. I've sent you reminder #{st.session_state.reminder_count} of 3. Please complete them before your appointment."
                else:
                    response = "Is there anything else I can help you with regarding your upcoming appointment?"
            else:
                response = "Thank you for completing your intake forms. Your appointment is all set!"
                st.session_state.current_step = "completed"
        else:
            response = "Your appointment is all set! If you have any questions or need to make changes, just let me know."
            st.session_state.current_step = "completed"
        
        add_message("assistant", response)
        return
    
    elif current_step == "confirmation":
        confirmation_agent = st.session_state.agents['confirmation']
        
        if "yes" in user_message.lower() or "confirm" in user_message.lower() or "proceed" in user_message.lower():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            progress_bar.progress(25)
            status_text.text("💾 Saving appointment data...")
            
            finalize_result = confirmation_agent.finalize_appointment(
                st.session_state.patient_info,
                st.session_state.appointment_info,
                st.session_state.insurance_info
            )
            
            if finalize_result["success"]:
                progress_bar.progress(50)
                status_text.text("📅 Updating doctor availability...")
                
                st.session_state.appointment_id = finalize_result["appointment_id"]
                
                progress_bar.progress(75)
                status_text.text("📧 Sending confirmation emails...")
                
                progress_bar.progress(100)
                status_text.text("✅ Appointment confirmed successfully!")
                
                progress_bar.empty()
                status_text.empty()
                
                st.session_state.current_step = "reminders"
                
                response = f"✅ **APPOINTMENT CONFIRMED!**\n\nYour appointment with Dr. {st.session_state.appointment_info['Doctor']} on {st.session_state.appointment_info['Date']} at {st.session_state.appointment_info['StartTime']} has been successfully confirmed and saved!\n\n📧 **Confirmation email** sent to {st.session_state.patient_info['Email']}\n📋 **Form completion reminder** sent with intake form attachment\n⏰ **Final reminder** will be sent automatically on the day of your appointment\n\nYour appointment is all set! If you have any questions or need to make changes, just let me know."
            else:
                progress_bar.empty()
                status_text.empty()
                response = f"I'm sorry, there was an error finalizing your appointment: {finalize_result['message']}. Please try again or contact us for assistance."
                
        elif "no" in user_message.lower() or "change" in user_message.lower() or "edit" in user_message.lower():
            response = "I understand you'd like to make changes. What would you like to modify?\n\n• **Patient Information** (name, DOB, email, phone, location)\n• **Appointment Details** (doctor, date, time)\n• **Insurance Information** (carrier, member ID, group number)\n\nPlease let me know what you'd like to change, and I'll help you update it."
            
        else:
            response = "I didn't quite understand your response. Please type 'yes' to confirm and proceed with your appointment, or 'no' to make changes to your information."
        
        add_message("assistant", response)
        return
    
    elif current_step == "completed":
        if "new appointment" in user_message.lower() or "another appointment" in user_message.lower():
            st.session_state.conversation_history = []
            st.session_state.current_step = "greeting"
            st.session_state.patient_info = {}
            st.session_state.appointment_info = {}
            st.session_state.insurance_info = {}
            st.session_state.appointment_id = None
            st.session_state.available_slots = []
            st.session_state.form_status = "not_sent"
            st.session_state.reminder_count = 0
            st.session_state.edge_case = None
            
            patient_interaction_agent = st.session_state.agents['patient_interaction']
            greeting = patient_interaction_agent.greet_patient()
            add_message("assistant", greeting)
        else:
            response = "Your appointment is all set! If you have any questions or need to make changes, just let me know."
        add_message("assistant", response)
        return
    
    add_message("assistant", "I'm not sure how to proceed. Please try again or start over.")

def main():
    initialize_session_state()
    initialize_agents()
    
    st.markdown("""
    <style>
    div[data-testid="stSidebarContent"] {
        background-color: #f8f9fa;
        padding: 1rem;
    }
    button[data-testid="baseButton-secondary"] {
        background-color: #f0f2f6;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #1f77b4; margin: 0;">⚕️</h2>
            <h3 style="color: #333; margin: 0.5rem 0;">Medical Appointment</h3>
            <h4 style="color: #666; margin: 0;">Scheduling Agent</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation buttons
        if st.button("💬 Chat with Agent", key="chat_page", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "chat" else "secondary"):
            st.session_state.current_page = "chat"
            st.rerun()
            
        if st.button("🤖 About Agent", key="agent_page", use_container_width=True,
                    type="primary" if st.session_state.current_page == "agent" else "secondary"):
            st.session_state.current_page = "agent"
            st.rerun()
            
        if st.button("💡 Example Prompts", key="prompts_page", use_container_width=True,
                    type="primary" if st.session_state.current_page == "prompts" else "secondary"):
            st.session_state.current_page = "prompts"
            st.rerun()
        
        st.divider()
        
        if st.button("🔄 Start New Conversation", key="reset_button", use_container_width=True):
            st.session_state.conversation_history = []
            st.session_state.current_step = "greeting"
            st.session_state.patient_info = {}
            st.session_state.appointment_info = {}
            st.session_state.insurance_info = {}
            st.session_state.appointment_id = None
            st.session_state.available_slots = []
            st.session_state.form_status = "not_sent"
            st.session_state.reminder_count = 0
            st.session_state.edge_case = None
            st.session_state.last_user_input = None
            st.session_state.confirmation_sent = False
            st.session_state.current_page = "chat"
            st.rerun()
    
    # Main content area based on current page
    if st.session_state.current_page == "agent":
        show_agent_info_page()
    elif st.session_state.current_page == "prompts":
        show_prompts_page()
    else:  # Default to chat page
        col1, col2 = st.columns([1, 10])
        with col1:
            st.image("https://cdn-icons-png.flaticon.com/512/2785/2785544.png", width=70)
        with col2:
            st.markdown("<h1 style='margin-top: 15px;'>Medical Appointment scheduling agent</h1>", unsafe_allow_html=True)
        
            if not st.session_state.conversation_history:
                patient_interaction_agent = st.session_state.agents['patient_interaction']
                greeting = patient_interaction_agent.greet_patient()
                add_message("assistant", greeting)
            
            displayed_messages = set()
            for message in st.session_state.conversation_history:
                message_id = f"{message['role']}:{message['content']}"
                if message_id not in displayed_messages:
                    if message["role"] == "assistant":
                        with st.chat_message("assistant", avatar="👨‍⚕️"):
                            st.write(message["content"])
                    else:
                        with st.chat_message("user"):
                            st.write(message["content"])
                    displayed_messages.add(message_id)
        
        user_message = st.chat_input("Your message")
        
        if user_message:
            if user_message != st.session_state.last_user_input:
                st.session_state.last_user_input = user_message
                
                with st.spinner("Processing your request..."):
                    process_message(user_message)
            st.rerun()

def handle_confirmation_endpoint():
    """Handle confirmation/cancel endpoint for email links."""
    if "confirm" in st.query_params:
        appointment_id = st.query_params.get("appointment_id")
        action = st.query_params.get("action")
        
        if appointment_id and action:
            confirmation_service = ConfirmationService()
            
            if action == "confirm":
                st.title("✅ Confirm Appointment")
                st.write(f"**Appointment ID:** {appointment_id}")
                
                status = confirmation_service.get_appointment_status(appointment_id)
                if status["success"]:
                    st.write(f"**Patient:** {status['patient_name']}")
                    st.write(f"**Doctor:** {status['doctor']}")
                    st.write(f"**Date:** {status['date']}")
                    st.write(f"**Time:** {status['time']}")
                    
                    if st.button("✅ Confirm Appointment", type="primary", use_container_width=True):
                        result = confirmation_service.confirm_appointment(appointment_id, "confirm")
                        if result["success"]:
                            st.toast("✅ Appointment confirmed successfully!", icon="✅")
                            st.success("✅ Appointment confirmed successfully!")
                            st.balloons()
                        else:
                            st.toast(f"❌ Error: {result['message']}", icon="❌")
                            st.error(f"❌ Error: {result['message']}")
                else:
                    st.error(f"❌ {status['message']}")
            
            elif action == "cancel":
                st.title("❌ Cancel Appointment")
                st.write(f"**Appointment ID:** {appointment_id}")
                
                status = confirmation_service.get_appointment_status(appointment_id)
                if status["success"]:
                    st.write(f"**Patient:** {status['patient_name']}")
                    st.write(f"**Doctor:** {status['doctor']}")
                    st.write(f"**Date:** {status['date']}")
                    st.write(f"**Time:** {status['time']}")
                    
                    cancel_reason = st.text_area(
                        "Please provide a reason for cancellation:",
                        placeholder="e.g., Schedule conflict, illness, etc.",
                        height=100
                    )
                    
                    if st.button("❌ Cancel Appointment", type="primary", use_container_width=True):
                        if cancel_reason.strip():
                            result = confirmation_service.confirm_appointment(
                                appointment_id, "cancel", cancel_reason
                            )
                            if result["success"]:
                                st.toast("❌ Appointment cancelled successfully!", icon="❌")
                                st.success("❌ Appointment cancelled successfully!")
                                st.write(f"**Reason:** {cancel_reason}")
                            else:
                                st.toast(f"❌ Error: {result['message']}", icon="❌")
                                st.error(f"❌ Error: {result['message']}")
                        else:
                            st.toast("Please provide a reason for cancellation.", icon="⚠️")
                            st.error("Please provide a reason for cancellation.")
                else:
                    st.error(f"❌ {status['message']}")
            
            else:
                st.error("Invalid action. Please use 'confirm' or 'cancel'.")
            
            if st.button("🏠 Back to Main App", use_container_width=True):
                st.query_params.clear()
                st.rerun()
            
            return True
    
    return False

if __name__ == "__main__":
    if handle_confirmation_endpoint():
        pass
    else:
        main()


