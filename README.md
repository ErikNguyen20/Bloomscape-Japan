# 🌸 **Bloomscape Japan** 🌸  
_A Cherry Blossom Forecasting Web Application_

---

## **About**

**Bloomscape Japan** is a 🌸 cherry blossom forecasting web app that predicts upcoming bloom dates **and displays historic cherry blossom bloom records** using **historic weather and bloom data** powered by machine learning.  
Track historic trends and forecast the next blooms! 🇯🇵

[![React](https://img.shields.io/badge/Frontend-ReactJS-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite)](https://www.sqlite.org/)
[![LightGBM](https://img.shields.io/badge/ML-LightGBM-FFD700?style=for-the-badge)](https://lightgbm.readthedocs.io/)

![Docker](https://img.shields.io/badge/docker-ready-blue?style=for-the-badge)  
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)  

---

## 📽️ Preview

> **Watch it in action:**  
> [![Bloomscape Japan Preview](https://your-preview-image-url.com)](https://www.youtube.com/watch?v=513x2Wop94k&ab_channel=eriknguyen)  
> *(Click the image to watch the video)*

---

## 🚀 **Installation**

1. **Clone the repository:**  
   ```bash
   git clone https://github.com/ErikNguyen20/Bloomscape-Japan.git
   cd Bloomscape-Japan

2. **Add the data:**  
   - Download the `data.zip` file from [Google Drive](YOUR-GOOGLE-DRIVE-URL)  
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
