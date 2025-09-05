# 🔧 Environment Setup Guide

<div align="center">

![Setup](https://img.shields.io/badge/Setup-Guide-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![Environment](https://img.shields.io/badge/Environment-Configuration-orange.svg)

*Quick and easy environment setup for the Medical Office Appointment Scheduling Agent*

</div>

---

## 📋 Prerequisites

Before setting up the environment, ensure you have:

- ✅ **Python 3.8 or higher** installed on your system
- ✅ **pip** package manager
- ✅ **Git** (for cloning the repository)
- ✅ **Internet connection** (for downloading dependencies and AI models)

---

## 🚀 Quick Setup

### 1️⃣ **Clone the Repository**
```bash
git clone <repository-url>
cd RagAI
```

### 2️⃣ **Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3️⃣ **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 4️⃣ **Environment Configuration**

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# AI Model Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Application Settings
APP_TITLE=Medical Appointment Scheduling Agent
APP_ICON=🏥
```

### 5️⃣ **Verify Installation**
```bash
# Test the application
streamlit run app.py
```

If successful, you'll see:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

---

## 🔑 API Keys Setup

### **OpenAI API Key**
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and add it to your `.env` file

### **Groq API Key** (Alternative AI Provider)
1. Visit [Groq Console](https://console.groq.com/)
2. Sign up for an account
3. Generate an API key
4. Add it to your `.env` file

---

## 📁 File Structure After Setup

```
RagAI/
├── .env                    # ✅ Your environment configuration
├── venv/                   # ✅ Virtual environment
├── app.py                  # ✅ Main application
├── requirements.txt        # ✅ Dependencies
└── ...                     # ✅ Other project files
```

---

## 🛠️ Troubleshooting

### **Common Issues**

| Issue | Solution |
|-------|----------|
| **Python not found** | Install Python 3.8+ from [python.org](https://python.org) |
| **pip not found** | Reinstall Python with pip included |
| **Virtual environment not activating** | Use full path: `./venv/Scripts/activate` (Windows) |
| **Dependencies not installing** | Update pip: `pip install --upgrade pip` |
| **API key errors** | Verify keys are correctly added to `.env` file |
| **Port 8501 in use** | Use different port: `streamlit run app.py --server.port 8502` |

### **Verification Commands**

```bash
# Check Python version
python --version

# Check pip version
pip --version

# Check installed packages
pip list

# Test Streamlit
streamlit --version
```

---

## ✅ Setup Complete!

Once you see the Streamlit app running in your browser, your environment is ready!

**Next Steps:**
- Open `http://localhost:8501` in your browser
- Start interacting with the Medical Appointment Scheduling Agent
- Check the main [README.md](README.md) for usage instructions

---

<div align="center">

*Happy coding! 🚀*

</div>
