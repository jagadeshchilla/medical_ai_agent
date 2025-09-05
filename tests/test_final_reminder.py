#!/usr/bin/env python3
"""
Test script to verify that final reminder (Type 3) functionality works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.email_service import EmailService
import pandas as pd
from datetime import datetime, date, timedelta

def test_final_reminder():
    """Test that final reminder (Type 3) can be sent successfully"""
    print("Testing final reminder (Type 3) functionality...")
    
    # Create email service
    email_service = EmailService()
    
    # Test data
    test_email = "test@example.com"
    test_patient_name = "Test Patient"
    test_doctor = "Dr. Test"
    test_appointment_date = "2024-01-15"
    test_appointment_time = "10:00 AM"
    test_appointment_id = "TEST123"
    
    print(f"Test parameters:")
    print(f"  Email: {test_email}")
    print(f"  Patient: {test_patient_name}")
    print(f"  Doctor: {test_doctor}")
    print(f"  Date: {test_appointment_date}")
    print(f"  Time: {test_appointment_time}")
    print(f"  Appointment ID: {test_appointment_id}")
    
    # Test Type 3 reminder (Final reminder)
    print(f"\nTesting Type 3 reminder (Final reminder)...")
    result = email_service.send_reminder(
        to_email=test_email,
        patient_name=test_patient_name,
        doctor=test_doctor,
        appointment_date=test_appointment_date,
        appointment_time=test_appointment_time,
        reminder_type=3,  # Final reminder
        appointment_id=test_appointment_id
    )
    
    print(f"Type 3 reminder result: {result}")
    
    if result["success"]:
        print("✅ Type 3 reminder sent successfully!")
    else:
        print("❌ Type 3 reminder failed!")
        print(f"Error: {result.get('message', 'Unknown error')}")
    
    # Test Type 2 reminder for comparison
    print(f"\nTesting Type 2 reminder (Form completion + confirmation)...")
    result2 = email_service.send_reminder(
        to_email=test_email,
        patient_name=test_patient_name,
        doctor=test_doctor,
        appointment_date=test_appointment_date,
        appointment_time=test_appointment_time,
        reminder_type=2,  # Form completion + confirmation
        appointment_id=test_appointment_id
    )
    
    print(f"Type 2 reminder result: {result2}")
    
    if result2["success"]:
        print("✅ Type 2 reminder sent successfully!")
    else:
        print("❌ Type 2 reminder failed!")
        print(f"Error: {result2.get('message', 'Unknown error')}")

def test_reminder_agent():
    """Test the reminder agent's send_reminder method"""
    print("\n" + "="*50)
    print("Testing ReminderAgent send_reminder method...")
    
    try:
        from agents.reminder_agent import ReminderAgent
        
        # Create reminder agent
        reminder_agent = ReminderAgent()
        
        # Load current appointments to see what we have
        appointments_df = reminder_agent.load_appointments()
        print(f"Current appointments count: {len(appointments_df)}")
        
        if not appointments_df.empty:
            print("Sample appointments:")
            for idx, row in appointments_df.head(3).iterrows():
                appointment_id = row.get('AppointmentID', row.get('appointment_id', 'Unknown'))
                patient_name = row.get('PatientName', row.get('patient_name', 'Unknown'))
                doctor = row.get('Doctor', row.get('doctor', 'Unknown'))
                print(f"  ID: {appointment_id}, Patient: {patient_name}, Doctor: {doctor}")
            
            # Test with the first appointment
            first_appointment_id = appointments_df.iloc[0].get('AppointmentID', appointments_df.iloc[0].get('appointment_id'))
            if first_appointment_id:
                print(f"\nTesting send_reminder with appointment ID: {first_appointment_id}")
                
                # Test Type 3 reminder
                result = reminder_agent.send_reminder(first_appointment_id, reminder_type=3)
                print(f"ReminderAgent Type 3 result: {result}")
                
                if result["success"]:
                    print("✅ ReminderAgent Type 3 reminder sent successfully!")
                else:
                    print("❌ ReminderAgent Type 3 reminder failed!")
                    print(f"Error: {result.get('message', 'Unknown error')}")
        else:
            print("No appointments found to test with")
            
    except Exception as e:
        print(f"Error testing ReminderAgent: {e}")

if __name__ == "__main__":
    test_final_reminder()
    test_reminder_agent()
    print("\n✅ All final reminder tests completed!")
