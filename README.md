# Astro-Vital
ASTRO-VITAL is an astronaut health companion software designed for long-duration space missions. It provides a user-friendly, equipment free daily check-in tool that evaluates key health areas such as immunity, bones and muscles, heart circulation, mind and mood, and sleep while tracking changes against personal baselines


🚀 ASTRO-VITAL — Astronaut Health Companion

**Submitted for the 2026 NASA Space Apps Challenge (Lalitpur)**  
*An educational desktop health monitoring, countermeasure, and behavioral wellness companion for astronauts on space missions.*

> **Disclaimer:** ASTRO-VITAL is an educational prototype designed around NASA Human Research Program (HRP) findings. It does not replace a flight surgeon or certified medical equipment.

---

## 🌟 Overview

**ASTRO-VITAL** is a standalone, zero-dependency Python desktop application that helps crew members monitor their physical and mental readiness across long-duration space missions. Designed with a warm, human-centered interface and an onboard mascot (**Nova**), it combines daily two-minute symptom check-ins, routine physiological tracking, guided exercise animations, an optional computer-vision form coach, and habit-building gamification.

All user profiles, check-in histories, and credentials stay completely local on the user's machine—nothing is transmitted externally.

---

## ✨ Key Features

### 🩺 Daily Health Check-In & Readiness Scoring
* **5 Core Health Domains:** Evaluates **Immunity**, **Bones & Muscles**, **Heart & Circulation**, **Mind & Mood**, and **Sleep & Energy** using weighted scoring.
* **Red-Flag & Critical Triage:** Screens for urgent symptoms (e.g., chest pain, fainting, sudden vision changes, elevated resting pulse) and triggers a high-priority **Mission Control Alert** with actionable checklist steps.
* **Personalized Advice & Onboard Medicine Guide:** Generates tailored recommendations based on domain scores and mission environment, paired with a searchable educational guide to common onboard medical kit options.

### 📋 Mission Routine & Near-Vision (SANS) Tracking
* **Scheduled Physiological Logs:** Tracks resting pulse, body temperature, systolic blood pressure, body mass, height, and near-vision acuity.
* **Custom Diopter Dial:** Features an interactive lens-power picker (`-6.00 D` to `+6.00 D` in `0.25 D` increments) to monitor baseline shifts associated with Spaceflight-Associated Neuro-ocular Syndrome (SANS).
* **Environment Profiles:** Adapts risk ratings and daily tips across four mission settings: **Space Station (LEO)**, **Spacecraft (Deep-Space Transit)**, **Rover**, and **Moon / Mars Base**.

### 🏋️ Guided Exercise & Optional AI Coach Cam
* **Procedural Kinematic Demonstrator:** Built-in forward and inverse kinematics animations demonstrate proper form for ARED squats, deadlifts, overhead presses, heel raises, cycling, treadmill runs, box breathing, and Earth-gazing mindfulness.
* **Computer Vision Coach Cam (Optional):** Uses **OpenCV** and **MediaPipe** (with an automatic motion-tracking fallback if MediaPipe is absent) to count reps and score exercise form in real time via webcam.

### 🎮 Crew Engagement & Gamification
* **XP, Levels & Daily Quests:** Earn XP and **Stardust** for check-ins, hydration logs, routine readings, and reading NASA HRP learning cards.
* **Streaks, Shields & Buddy System:** Maintain daily check-in streaks, purchase **Streak Shields** or **Double XP** boosts in the Stardust Shop, pair up with a **Streak Buddy**, and cheer on crewmates on the weekly leaderboard.
* **Local Accounts & Guest Mode:** Supports salted PBKDF2-HMAC-SHA256 password-protected accounts alongside an in-memory **Guest Mode** that can be promoted to a saved account at any time.

---

## 📊 NASA Resources & Scientific References

The educational modules, symptom weights, and risk models in ASTRO-VITAL are informed by official **NASA Human Research Program (HRP)** documentation:
* [NASA's Five Hazards of Spaceflight](https://www.nasa.gov/hrp/hazards/) (Space Radiation, Isolation & Confinement, Distance from Earth, Gravity Fields, Hostile/Closed Environments)
* [Risk of Spaceflight-Associated Neuro-ocular Syndrome (SANS)](https://www.nasa.gov/reference/risk-of-spaceflight-associated-neuro-ocular-syndrome-sans/)
* [Risk of Altered Sensorimotor and Vestibular Function](https://www.nasa.gov/reference/risk-of-altered-sensorimotor-and-vestibular-function/)
* [Ongoing HRP Crew Health Research (Artemis II & ISS countermeasures)](https://www.nasa.gov/hrp/ongoing-hrp-research/)



## 🛠️ Tech Stack

* **Language:** Python 3.8+
* **GUI & Graphics:** Tkinter (custom vector canvas widgets, procedural animations, interactive charts, and modals—**no external packages required** for core functionality)
* **Optional Computer Vision:** `opencv-python`, `mediapipe`, `numpy` (for the Exercise Coach Cam)
* **Security & Storage:** Local JSON persistence (`astro_vital_data.json`) with salted `PBKDF2-HMAC-SHA256` password hashing
