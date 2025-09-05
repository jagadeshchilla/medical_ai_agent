import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

# -------------------------
# 1. Generate Patients Data
# -------------------------
def generate_patients(n=50, filename="data/patients.csv"):
    patients = []
    insurance_carriers = ["Aetna", "BlueCross", "Cigna", "UnitedHealth", "Humana"]
    doctors = ["Dr. Kumar", "Dr. Mehta", "Dr. Sharma", "Dr. Singh", "Dr. Patel"]
    locations = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]

    for i in range(1, n + 1):
        name = fake.name()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
        email = fake.email()
        phone = fake.phone_number()
        doctor_pref = random.choice(doctors)
        insurance = random.choice(insurance_carriers)
        member_id = fake.bothify(text="??#####")
        group_number = fake.bothify(text="GRP###")
        location = random.choice(locations)

        patients.append([
            i, name, dob.strftime("%Y-%m-%d"), email, phone,
            doctor_pref, insurance, member_id, group_number, location
        ])

    df = pd.DataFrame(patients, columns=[
        "PatientID", "Name", "DOB", "Email", "Phone",
        "DoctorPreference", "InsuranceCarrier",
        "MemberID", "GroupNumber", "Location"
    ])
    df.to_csv(filename, index=False)
    print(f"✅ Generated {n} patient records → {filename}")


# -------------------------
# 2. Generate Doctor Availability
# -------------------------
def generate_availability(days=7, filename="data/availability.csv"):
    doctors = ["Dr. Kumar", "Dr. Mehta", "Dr. Sharma", "Dr. Singh", "Dr. Patel"]
    timeslots = [f"{hour}:00" for hour in range(9, 17)]  # 9 AM – 5 PM
    start_date = datetime.today()

    schedule = []
    for doctor in doctors:
        for d in range(days):
            date = (start_date + timedelta(days=d)).strftime("%Y-%m-%d")
            for slot in timeslots:
                status = random.choice(["Available", "Booked", "Available"])
                schedule.append([doctor, date, slot, status])

    df = pd.DataFrame(schedule, columns=["DoctorName", "Date", "TimeSlot", "Status"])
    df.to_csv(filename, index=False)
    print(f"✅ Generated doctor availability for {days} days → {filename}")


if __name__ == "__main__":
    # Ensure data/ folder exists
    import os
    os.makedirs("data", exist_ok=True)

    generate_patients(50, "data/patients.csv")
    generate_availability(7, "data/availability.csv")
