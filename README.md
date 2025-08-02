# Sensor Monitoring System 

This is a full-stack sensor monitoring system built with **FastAPI**, **Streamlit**, and **Docker**. It collects temperature and flow data, stores it in a SQLite database, detects anomalies, and visualizes everything on an interactive dashboard.

---

## Technologies Used

- **Python** (backend + dashboard)
- **FastAPI** (REST API)
- **Streamlit** (dashboard)
- **Docker + Docker Compose**
- **SQLite** (lightweight embedded database)
- **scikit-learn** (for anomaly detection using Isolation Forest)

---

## Features

- Real-time sensor data ingestion via API
- Streamlit dashboard for:
  - Rule-based and ML-based anomaly detection
  - Sensor health check (last seen)
  - Live plots for temp and flow
- Data stored in SQLite
- Fully containerized (backend, dashboard, producer)
- One-command setup with Docker Compose

---

## Quick Start (with Docker)

```bash
git clone https://github.com/justusa11/sensor-monitoring-system.git
cd sensor-monitoring-system
docker-compose up --build
```

---
## Anomaly Detection

### Rule-based Flags
- **Tout > 45°C** → Cooling penalty  
- **Flow = 0 & Tin < 40°C** → Suspected circulation issue

### ML-based Flags
- **Isolation Forest** model detects outliers based on sensor data
---
## Why This Project?

This project demonstrates core software development and system integration skills:

- Backend API development with FastAPI  
- Real-time data handling using a simulated data producer  
- Anomaly detection with machine learning (Isolation Forest)  
- Streamlit dashboard for interactive visualization  
- Docker-based orchestration of multiple components

```
sensor-monitoring-system/
│
├── backend/            # FastAPI application
│   └── main.py         
│
├── dashboard/          # Streamlit dashboard
│   └── app.py          
│
├── producer/           # Simulates real-time sensor data
│   └── producer.py     
│
├── tests/              # Placeholder for future unit tests
│
├── docker-compose.yml  # Multi-container orchestration
├── Dockerfile.*        # Dockerfiles for backend, dashboard, producer
├── README.md           
└── requirements.txt    
```


Aspiring software developer passionate about real-time systems and backend architecture.


