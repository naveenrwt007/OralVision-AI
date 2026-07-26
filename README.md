<div align="center">

# 🦷 OralVision AI
### AI-Powered Oral Cancer Screening & Patient Management System

<p align="center">
An intelligent healthcare platform that combines Deep Learning, Explainable AI, Electronic Medical Records (EMR), and Modern Web Technologies to assist healthcare professionals in the early screening of oral cancer.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?style=for-the-badge)
![MongoDB](https://img.shields.io/badge/MongoDB-Database-4EA94B?style=for-the-badge)
![PyTorch](https://img.shields.io/badge/PyTorch-DeepLearning-EE4C2C?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

</p>

</div>

---

# 📖 Overview

OralVision AI is an intelligent healthcare application designed to assist medical professionals in performing **preliminary oral cancer screening** using Deep Learning and Explainable AI.

Unlike traditional image classification projects, OralVision AI provides an end-to-end digital healthcare workflow including secure authentication, patient management, AI-assisted diagnosis, Grad-CAM visualization, report generation, and screening history management.

The objective of this project is to demonstrate how Artificial Intelligence can be integrated into healthcare systems to improve efficiency, assist clinicians, and support early disease detection.

---

# ✨ Key Features

## 🤖 Artificial Intelligence

- Deep Learning-based Oral Cancer Detection
- EfficientNet-B0 Classification Model
- Confidence Score Prediction
- Explainable AI using Grad-CAM
- Image Quality Assessment

---

## 👨‍⚕️ Patient Management

- Patient Registration
- Multiple Screenings per Patient
- Screening History
- Smart Patient Search
- Medical Record Management

---

## 🔒 Security

- JWT Authentication
- Role-Based Access Control
- Protected APIs
- Secure Password Hashing
- Authorization Middleware

---

## 📊 Dashboard & Analytics

- Live Statistics
- Total Patients
- Total Screenings
- AI Prediction Distribution
- Report Analytics

---

## 📄 Reporting

- Professional PDF Reports
- QR Code Verification
- Downloadable Reports
- Historical Reports

---

# 🏗️ System Architecture

```text
                        +----------------------+
                        |   React Frontend     |
                        +----------+-----------+
                                   |
                                   |
                         REST API (JWT Auth)
                                   |
                                   |
                        +----------v-----------+
                        |   FastAPI Backend    |
                        +----------+-----------+
                                   |
          +------------------------+-----------------------+
          |                        |                       |
          |                        |                       |
   MongoDB Database        AI Prediction Engine      Report Generator
          |                        |                       |
          |                        |                       |
   Patient Records         EfficientNet-B0         PDF + QR Code
                                   |
                                   |
                            Grad-CAM Heatmap
```

---

# 🧠 AI Workflow

```text
Upload Oral Image
        │
        ▼
Image Quality Assessment
        │
        ▼
Deep Learning Prediction
        │
        ▼
Confidence Score
        │
        ▼
Grad-CAM Explanation
        │
        ▼
Store Screening Record
        │
        ▼
Generate PDF Report
```

---

# 💻 Technology Stack

| Category | Technologies |
|-----------|--------------|
| Frontend | React.js, Vite, Tailwind CSS |
| Backend | FastAPI, Python |
| Database | MongoDB |
| Authentication | JWT |
| AI Framework | PyTorch |
| Deep Learning | EfficientNet-B0 |
| Explainability | Grad-CAM |
| Image Processing | OpenCV, Pillow |
| Visualization | Chart.js |
| Deployment Ready | Docker Compatible |

---

# 📈 Model Performance

| Metric | Score |
|---------|------:|
| Accuracy | **87.10%** |
| Precision | **87.18%** |
| Recall | **87.10%** |
| F1 Score | **87.10%** |
| ROC-AUC | **92.92%** |

---

# 📷 Screenshots

> Add screenshots here

- Login
- Dashboard
- Patient Management
- AI Screening
- Grad-CAM Result
- Patient History
- Reports
- Analytics

---

# 🚀 Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/OralVision-AI.git
```

### Backend

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# 📂 Project Structure

```text
OralVision-AI/

backend/
frontend/
screenshots/
outputs/
README.md
LICENSE
```

---

# 🔮 Future Scope

- Multi-Class Oral Disease Detection
- Doctor Portal
- Appointment Management
- Email Notifications
- Cloud Deployment
- Mobile Application
- Electronic Health Record Integration
- Multi-Language Support

---

# ⚠️ Medical Disclaimer

This application is intended for educational and research purposes.

The AI model provides preliminary screening assistance and **must not** be used as a substitute for professional medical diagnosis or treatment.

Final diagnosis should always be performed by qualified healthcare professionals.

---

# 👨‍💻 Author

### Naveen Singh Rawat

B.Tech Computer Science & Engineering

Graphic Era Hill University

GitHub:
https://github.com/naveenrwt007

LinkedIn:
(Add your LinkedIn)

---

<div align="center">

### ⭐ If you found this project helpful, consider giving it a star!

</div>