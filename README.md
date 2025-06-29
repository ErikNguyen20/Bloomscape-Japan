# 🌸 **Bloomscape Japan** 🌸  
_A Cherry Blossom AI Forecasting Web Application_

---

## **About**

**Bloomscape Japan** is a 🌸 cherry blossom forecasting web app that predicts upcoming bloom dates **and displays historic cherry blossom bloom records** using **historic weather and bloom data** powered by machine learning.  
Track historic trends and forecast the next blooms! 🇯🇵

✨ **Live updates:** A **cron job runs daily at midnight from December to June**, and **weekly (Sundays) at midnight from July to November**, to refresh weather data and forecast predictions automatically, so you’ll always see the most up-to-date bloom forecast!  
**Note:** The update job takes about **20–30 minutes**, so new data appears early each morning.  
_(The initial data from Google Drive is current as of **June 28, 2025**.)_

[![React](https://img.shields.io/badge/Frontend-ReactJS-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite)](https://www.sqlite.org/)
[![LightGBM](https://img.shields.io/badge/ML-LightGBM-FFD700?style=for-the-badge)](https://lightgbm.readthedocs.io/)

![Docker](https://img.shields.io/badge/docker-ready-blue?style=for-the-badge)  
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)  

---

## 📽️ Preview

> **Watch it in action:**

https://github.com/user-attachments/assets/b213bbd4-a43d-4d65-815c-f13a7f5374a4

---

## 🚀 **Installation**

1. **Clone the repository:**  
   ```bash
   git clone https://github.com/ErikNguyen20/Bloomscape-Japan.git
   cd Bloomscape-Japan

2. **Add the data:**  
   - Download the `data.zip` file from [Google Drive](https://drive.google.com/file/d/1fr1wJ3CLZpbIjP4b3hHH9ymnir4ZaseR/view?usp=sharing)  
   - Extract it **inside** the `backend` directory, so it looks like:  
     ```
     backend/data/*
     ```

   ✅ **Do not place the files directly in `backend`!** The folder structure must remain `backend/data/*`.

3. **Run with Docker Compose:**  
   ```bash
   docker-compose up --build
   ```

4. **Visit the app:**  
   Open your browser and go to [http://localhost:5173/](http://localhost:5173/) 🌸

---

## 🗺️ **Credits**

- Historic weather data: [Open-Meteo](https://open-meteo.com/)  
- Cherry blossom data: [Japan Meteorological Agency (JMA)](https://www.jma.go.jp/jma/index.html)  
- Map tiles: [Geospatial Information Authority of Japan (GSI)](https://www.gsi.go.jp/)

---
