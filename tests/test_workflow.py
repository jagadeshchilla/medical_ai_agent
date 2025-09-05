# test_workflow.py

import os
import pandas as pd
import datetime
from typing import Dict, Any

# Import agents
from agents.patient_interaction_agent import PatientInteractionAgent
from agents.patient_lookup_agent import PatientLookupAgent
from agents.scheduling_agent import SchedulingAgent
from agents.insurance_agent import InsuranceAgent
from agents.confirmation_agent import ConfirmationAgent
from agents.form_distribution_agent import FormDistributionAgent
from agents.reminder_agent import ReminderAgent
from agents.admin_agent import AdminAgent

# Ensure data files exist
def ensure_data_files():
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Create patients.csv if it doesn't exist
    if not os.path.exists('data/patients.csv'):
        patients_df = pd.DataFrame(columns=[
            "PatientID", "Name", "DOB", "Email", "Phone", 
            "DoctorPreference", "PatientType", "InsuranceCarrier", 
            "MemberID", "GroupNumber"
        ])
        patients_df.to_csv('data/patients.csv', index=False)
    
    # Create availability.csv if it doesn't exist
    if not os.path.exists('data/availability.csv'):
        # Create sample availability data for calendar service
        today = datetime.datetime.now().date()
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)
        
        # Create sample data for multiple days
        dates = [today, tomorrow, next_week]
        doctors = ["Smith", "Johnson", "Williams"]
        
        # Create availability DataFrame
        availability_data = []
        
        for date in dates:
            for doctor in doctors:
                # Morning slots
                for hour in range(9, 12):
                    availability_data.append({
                        "Date": date,
                        "Doctor": doctor,
                        "StartTime": f"{hour:02d}:00",
                        "EndTime": f"{hour:02d}:30",
                        "Available": True
                    })
                    availability_data.append({
                        "Date": date,
                        "Doctor": doctor,
                        "StartTime": f"{hour:02d}:30",
                        "EndTime": f"{hour+1:02d}:00",
                        "Available": True
                    })
                
                # Afternoon slots
                for hour in range(13, 17):
                    availability_data.append({
                        "Date": date,
                        "Doctor": doctor,
                        "StartTime": f"{hour:02d}:00",
                        "EndTime": f"{hour:02d}:30",
                        "Available": True
                    })
                    availability_data.append({
                        "Date": date,
                        "Doctor": doctor,
                        "StartTime": f"{hour:02d}:30",
                        "EndTime": f"{hour+1:02d}:00",
                        "Available": True
                    })
        
        availability_df = pd.DataFrame(availability_data)
        availability_df.to_csv('data/availability.csv', index=False)
    
    # Create doctor_appointments.csv if it doesn't exist
    if not os.path.exists('data/doctor_appointments.csv'):
        appointments_df = pd.DataFrame(columns=[
            "AppointmentID", "PatientID", "PatientName", "Doctor", 
            "Date", "StartTime", "EndTime", "Duration", "Email", 
            "InsuranceCarrier", "MemberID", "GroupNumber",
            "ConfirmationStatus", "RemindersSent", "FormSent"
        ])
        appointments_df.to_csv('data/doctor_appointments.csv', index=False)

# Test the complete workflow
def test_workflow():
    print("Starting workflow test...")
    
    # Ensure data files exist
    ensure_data_files()
    
    # Initialize agents
    patient_interaction_agent = PatientInteractionAgent()
    patient_lookup_agent = PatientLookupAgent()
    scheduling_agent = SchedulingAgent()
    insurance_agent = InsuranceAgent()
    confirmation_agent = ConfirmationAgent()
    form_distribution_agent = FormDistributionAgent()
    reminder_agent = ReminderAgent()
    admin_agent = AdminAgent()
    
    print("All agents initialized successfully.")
    
    # Test patient interaction
    print("\nTesting Patient Interaction Agent...")
    greeting = patient_interaction_agent.greet_patient()
    print(f"Greeting: {greeting}")
    
    # Simulate conversation with patient
    conversation_history = []
    
    # First message
    result = patient_interaction_agent.process_message(
        "My name is John Doe, I'd like to schedule an appointment with Dr. Smith.",
        conversation_history
    )
    response = result["response"]
    extracted_info = result["patient_info"]
    conversation_history = result["conversation_history"]
    
    print(f"Response: {response}")
    print(f"Extracted info: {extracted_info}")
    
    # Second message
    result = patient_interaction_agent.process_message(
        "My date of birth is 1980-01-01, email is john.doe@example.com, and phone is 555-123-4567.",
        conversation_history
    )
    response = result["response"]
    more_info = result["patient_info"]
    conversation_history = result["conversation_history"]
    
    print(f"Response: {response}")
    print(f"More extracted info: {more_info}")
    
    # Combine all patient info
    patient_info = {**extracted_info, **more_info}
    print(f"Complete patient info: {patient_info}")
    
    # Test patient lookup
    print("\nTesting Patient Lookup Agent...")
    lookup_result = patient_lookup_agent.lookup_patient({
        "Name": patient_info.get("Name", ""),
        "DOB": patient_info.get("DOB", ""),
        "Email": patient_info.get("Email", ""),
        "Phone": patient_info.get("Phone", "")
    })
    patient_status = lookup_result["patient_exists"]
    duration = lookup_result["appointment_duration"]
    lookup_response = lookup_result["response"]
    print(f"Patient status: {patient_status}")
    print(f"Appointment duration: {duration} minutes")
    print(f"Lookup response: {lookup_response}")
    
    # Test scheduling
    print("\nTesting Scheduling Agent...")
    today = datetime.datetime.now().date()
    available_slots = scheduling_agent.find_available_slots(
        patient_info.get("DoctorPreference", "Any"), duration
    )
    print(f"Available slots: {available_slots[:2]}...")
    
    scheduling_result = scheduling_agent.schedule_appointment(
        patient_info, duration
    )
    print(f"Scheduling result: {scheduling_result}")

    if not scheduling_result["success"]:
        print("No available slots found.")
        return

    slot = scheduling_result["selected_slot"]

    # Test insurance collection
    print("\nTesting Insurance Agent...")
    insurance_message = "My insurance is Aetna, member ID ABC123, group number G-12345."
    insurance_info = insurance_agent.extract_insurance_info(insurance_message)
    print(f"Insurance info: {insurance_info}")
    
    # Update patient with insurance info
    patient_id = insurance_agent.update_patient_insurance(
        "12345",  # Using a dummy patient ID since we don't have a real one
        insurance_info
    )
    print(f"Patient ID: {patient_id}")
    
    # Test confirmation
    print("\nTesting Confirmation Agent...")
    appointment_data = {
        "PatientID": patient_id,
        "PatientName": patient_info["Name"],
        "Doctor": slot["doctor"],
        "Date": today,
        "StartTime": slot["start_time"],
        "EndTime": slot["end_time"],
        "Duration": duration,
        "InsuranceCarrier": insurance_info["InsuranceCarrier"],
        "MemberID": insurance_info["MemberID"],
        "GroupNumber": insurance_info["GroupNumber"],
        "email": patient_info["Email"]  # Add lowercase email for form_distribution_agent
    }
    appointment_result = confirmation_agent.write_appointment(appointment_data)
    appointment_id = appointment_result["appointment_id"]
    print(f"Appointment ID: {appointment_id}")
    
    # Send confirmation
    confirmation_result = confirmation_agent.process_confirmation(appointment_data)
    print(f"Confirmation result: {confirmation_result}")
    
    # No need to update confirmation status separately as process_confirmation does this
    # confirmation_agent.update_confirmation_status(appointment_id, "Sent")
    
    # Test form distribution
    print("\nTesting Form Distribution Agent...")
    form_result = form_distribution_agent.send_intake_form(appointment_id)
    print(f"Form distribution result: {form_result}")
    
    # Test reminder agent
    print("\nTesting Reminder Agent...")
    # First try to get an existing appointment ID from the doctor_appointments.csv file
    try:
        appointments_df = pd.read_csv('data/doctor_appointments.csv')
        if not appointments_df.empty and 'AppointmentID' in appointments_df.columns:
            existing_appointment_id = appointments_df['AppointmentID'].iloc[0]
            reminder_result = reminder_agent.send_reminder(existing_appointment_id, 1)  # Send first reminder
        else:
            # Fall back to the appointment ID from the current test
            reminder_result = reminder_agent.send_reminder(appointment_id, 1)  # Send first reminder
    except Exception as e:
        print(f"Error getting existing appointment ID: {e}")
        # Fall back to the appointment ID from the current test
        reminder_result = reminder_agent.send_reminder(appointment_id, 1)  # Send first reminder
    
    print(f"Reminder result: {reminder_result}")
    
    # Test admin agent
    print("\nTesting Admin Agent...")
    report_result = admin_agent.generate_daily_report(today)
    if isinstance(report_result, dict) and 'report' in report_result:
        daily_report = report_result['report']
        print(f"Daily report preview: {daily_report[:100] if isinstance(daily_report, str) else 'No appointments found'}...")
    else:
        print(f"Daily report result: {report_result}")
    
    print("\nWorkflow test completed successfully!")

# Run the test
if __name__ == "__main__":
    test_workflow()