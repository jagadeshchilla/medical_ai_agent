import os

# Define the project structure
structure = {
    "data": ["patients.csv", "availability.xlsx", "appointments.xlsx"],
    "agents": [
        "patient_interaction_agent.py",
        "patient_lookup_agent.py",
        "scheduling_agent.py",
        "insurance_agent.py",
        "confirmation_agent.py",
        "form_distribution_agent.py",
        "reminder_agent.py",
        "admin_agent.py"
    ],
    "services": [
        "email_service.py",
        "sms_service.py",
        "calendar_service.py"
    ],
    "utils": [
        "data_loader.py",
        "logger.py",
        "validators.py"
    ],
    
    "tests": [
        "test_agents.py",
        "test_services.py",
        "test_end_to_end.py"
    ]
}

# Ensure root files exist
root_files = ["main.py", "README.md"]
for f in root_files:
    if not os.path.exists(f):
        open(f, "w").close()

# Create folders & files
for folder, files in structure.items():
    os.makedirs(folder, exist_ok=True)
    # Add __init__.py to make it a package
    init_path = os.path.join(folder, "__init__.py")
    if not os.path.exists(init_path):
        open(init_path, "w").close()
    # Add placeholder files
    for file in files:
        file_path = os.path.join(folder, file)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write(f"# {file}\n")

print("✅ Project structure created successfully!")
