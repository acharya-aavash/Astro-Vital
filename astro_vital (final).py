#!/usr/bin/env python3
"""
ASTRO-VITAL  |  Astronaut Health Companion
NASA Open App Challenge 2026 - Lalitpur

Single-file version. Run it:   python astro_vital.py
Needs:     Python 3.8+ with Tkinter (no pip packages required)
Optional:  pip install opencv-python mediapipe     (for the Exercise coach cam)

New in this version: guest mode, stardust + streak shields + buddy streaks + shop,
a mascot, accounts (username + password), warm "human" theme, lens-power (diopter)
near-vision check, a redesigned critical alert, and celebration pop-ups.

Sections inside this file (in order):
  1. content     questions, advice, plans, environments, learning cards
  2. logic       scoring, saving, XP, quests, badges, leaderboard
  3. widgets     rounded buttons, chips, lists, icons, progress bar
  4. animations  the "show me how" exercise animations
  5. coach       optional camera coach (rep counting and form score)
  6. app         the main window and all its screens

This is an educational prototype. It does not replace the flight surgeon.
"""
import datetime as dt
import math
import random
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import deque
import json
import os
import re
import sys
import hashlib
import hmac
import secrets
import zlib


##############################################################################
# SECTION: content
# content.py - all the text and static data for ASTRO-VITAL.
# No GUI code in here, so it is easy to read, edit and translate.
##############################################################################

# ---------------------------------------------------------------- palette
BG = "#17110d"
SIDE = "#110c09"
CARD = "#231b15"
CARD2 = "#2f251d"
LINE = "#453628"
TEXT = "#f8efe3"
MUTED = "#b8a690"
ACCENT = "#4fc1a6"
ACCENT2 = "#f2b84b"
GOOD = "#8fd45a"
WATCH = "#f4cf5e"
CAUTION = "#f5a14a"
CRIT = "#ef5b6b"
INK = "#1a130e"          # dark text that sits on bright fills
FONT = "Segoe UI"
SEV_COLORS = [GOOD, WATCH, CAUTION, CRIT]

# ---------------------------------------------------------------- health areas
IMMUNE, BONE, HEART, MIND, SLEEP = ("Immunity", "Bones & Muscles", "Heart & Circulation",
                                    "Mind & Mood", "Sleep & Energy")
DOMAINS = [IMMUNE, BONE, HEART, MIND, SLEEP]
DOMAIN_COLORS = {IMMUNE: "#6bb8e8", BONE: "#c89bd9", HEART: "#f27b8f", MIND: "#6fd0b0", SLEEP: "#f4cf5e"}
WEIGHTS = {IMMUNE: 0.22, BONE: 0.18, HEART: 0.22, MIND: 0.22, SLEEP: 0.16}

SCALE = ["Not at all", "A little", "Quite a bit", "Very much"]

QUESTIONS = [
    dict(id="i1", d=IMMUNE, q="Do you feel feverish, chilly or unusually tired?",
         h="Think about the last 24 hours.", o=SCALE),
    dict(id="i2", d=IMMUNE, q="Is your skin itchy, rashy, or are cuts healing slowly?",
         h="Dry or irritated skin is common in a closed cabin.", o=SCALE),
    dict(id="i3", d=IMMUNE, q="Do you have a sore throat, stuffy nose, cough or irritated eyes?",
         h="Any of these counts.", o=SCALE),
    dict(id="i4", d=IMMUNE, q="Have you seen flashes of light, or felt sick or headachy after a radiation alert?",
         h="Cosmic rays can cause brief flashes in your vision.", o=SCALE),
    dict(id="b1", d=BONE, q="Do you have back, hip or joint pain?",
         h="Bones and the spine are affected by low gravity.", o=SCALE),
    dict(id="b2", d=BONE, q="Do your muscles feel weak or sore?",
         h="Compared with how you normally feel.", o=SCALE),
    dict(id="b3", d=BONE, q="How much of your exercise did you do today?",
         h="Strength and cardio sessions both count.", o=["All of it", "Most of it", "A little", "None"]),
    dict(id="h1", d=HEART, q="Do you feel dizzy, light-headed or notice a racing heartbeat?",
         h="Even for a few moments.", o=SCALE),
    dict(id="h2", d=HEART, q="Does your head feel full or pressured, or is your face puffy or reading blurry?",
         h="Body fluids shift toward the head in microgravity.", o=SCALE),
    dict(id="h3", d=HEART, q="Do simple tasks leave you out of breath?",
         h="For example moving between modules or doing chores.", o=SCALE),
    dict(id="h4", d=HEART, q="Do you have a lingering headache or feel drowsy?",
         h="In a closed cabin this can sometimes mean stale air.", o=SCALE),
    dict(id="m1", d=MIND, q="How is your mood today?",
         h="Be honest. There are no wrong answers.", o=["Great", "Okay", "Low", "Very low"]),
    dict(id="m2", d=MIND, q="Do you feel lonely, cut off or tense with others?",
         h="Isolation and confinement affect everyone.", o=SCALE),
    dict(id="m3", d=MIND, q="Is it hard to concentrate or make decisions?",
         h="Compared with a normal day.", o=SCALE),
    dict(id="s1", d=SLEEP, q="How many hours did you sleep last night?",
         h="Your best estimate is fine.", o=["7 or more", "6 to 7", "4 to 6", "Under 4"]),
    dict(id="s2", d=SLEEP, q="How well did you sleep?",
         h="", o=["Very well", "Okay", "Poorly", "Barely slept"]),
    dict(id="s3", d=SLEEP, q="How is your energy right now?",
         h="", o=["High", "Normal", "Low", "Exhausted"]),
    dict(id="s4", d=SLEEP, q="How is your appetite and thirst?",
         h="Eating and drinking less is an early warning sign.", o=["Normal", "A bit low", "Low", "Almost none"]),
]

RED_FLAGS = [
    "Chest pain or pressure",
    "Fainting or nearly fainting",
    "Trouble breathing while resting",
    "Sudden loss of vision or a major vision change",
    "Severe headache with confusion or vomiting",
    "Thoughts of hurting myself or others",
]

CRITICAL = {"i1": "a high fever and weakness", "h1": "severe dizziness or a racing heart",
            "h3": "severe shortness of breath", "m1": "feeling very low or hopeless"}

# rough numbers used to turn check-in answers into chartable values
SLEEP_HOURS = [7.5, 6.5, 5.0, 3.5]
MOOD_SCORE = [95, 70, 40, 10]

# ---------------------------------------------------------------- advice
ADVICE = {
    IMMUNE: {
        "good": ["Your immune picture looks stable. Keep up hand hygiene and the cabin cleaning schedule.",
                 "Eat balanced meals with protein and vitamin D from the food system.",
                 "Log radiation alerts when they happen so patterns are easy to see."],
        "watch": ["Wipe high-touch surfaces and wear a mask if a crewmate is unwell.",
                  "Rest more: stress and broken sleep both weaken immunity in space.",
                  "Check your temperature twice a day and report a rising trend.",
                  "During a solar storm alert, move to the best-shielded module."],
        "high": ["Limit close contact with crewmates and tell the flight surgeon today.",
                 "Drink extra fluids and rest.",
                 "Do not start antibiotics unless the flight surgeon directs you to.",
                 "Photograph any rash or sore for telemedicine review."],
    },
    BONE: {
        "good": ["Your routine is working. Keep daily resistive exercise (about 2 hours of exercise per day).",
                 "Keep calcium and vitamin D on plan."],
        "watch": ["Add one more resistive session this week (squats, deadlifts, heel raises).",
                  "Never skip the warm-up: muscles and tendons are more injury-prone after weeks in orbit.",
                  "Track back and hip discomfort; it can be an early sign of bone and disc changes."],
        "high": ["Report lasting bone or joint pain to the flight surgeon.",
                 "Switch to a lighter, supervised plan until the pain is checked.",
                 "Prioritise protein and calcium, and avoid heavy loading on a painful area."],
    },
    HEART: {
        "good": ["Heart and circulation indicators look good. Keep up cycling or treadmill sessions.",
                 "Stay hydrated; fluids shifting toward the head is normal in microgravity."],
        "watch": ["Rest for 10 minutes, then check how you feel again.",
                  "Drink more fluids; use thigh cuffs or lower-body negative pressure if prescribed.",
                  "If headaches or drowsiness continue, ask the crew to check cabin CO2 levels.",
                  "Move slowly when you stand up quickly after exercise."],
        "high": ["Stop strenuous exercise and rest.",
                 "Contact the flight surgeon and describe your symptoms.",
                 "Ask for an immediate cabin CO2 and ventilation check.",
                 "Report any new vision change straight away; it can signal eye and brain pressure changes."],
    },
    MIND: {
        "good": ["Your mood and sense of connection look healthy. Keep a routine with free time.",
                 "Schedule regular calls with family and friends."],
        "watch": ["Try 5 minutes of slow breathing, then chat with a crewmate you trust.",
                  "Look out of a window at Earth and spend time on a hobby for perspective.",
                  "Keep your daily routine and light cycle steady."],
        "high": ["Ask for a private session with the behavioral health team today.",
                 "Reaching out early is a sign of strength, and you are not alone.",
                 "Share a meal or workout with a crewmate instead of being alone.",
                 "If you have thoughts of harming yourself, tell a crewmate and Mission Control immediately."],
    },
    SLEEP: {
        "good": ["Sleep and energy are solid. Keep regular sleep times and dim lights in the evening."],
        "watch": ["Aim for 7 to 8 hours in your sleep station and avoid bright screens 1 hour before bed.",
                  "Check noise and temperature in your crew quarters.",
                  "Avoid caffeine in the second half of your day."],
        "high": ["Fatigue can seriously affect critical tasks. Ask for schedule relief.",
                 "Avoid high-risk work such as spacewalks or robotics while exhausted.",
                 "Talk to the flight surgeon about sleep support."],
    },
}

# ---------------------------------------------------------------- medicine guide
MEDKIT = {
    "Headache": dict(
        options=["Acetaminophen (paracetamol)", "Ibuprofen, taken with food"],
        notes="Check cabin CO2 first. In a closed environment a lasting headache is often stale air. "
              "Drink water and rest your eyes.",
        call="Sudden severe headache, vision change, confusion or repeated vomiting."),
    "Nausea / space motion sickness": dict(
        options=["Promethazine (as prescribed)", "Scopolamine patch", "Meclizine"],
        notes="Move your head slowly, keep your eyes on a fixed point, and sip fluids. "
              "These medicines can cause drowsiness, so avoid critical tasks.",
        call="Vomiting that will not stop, or signs of dehydration."),
    "Stuffy nose / sinus pressure": dict(
        options=["Saline nasal spray", "Pseudoephedrine decongestant (short term)", "Cetirizine (antihistamine)"],
        notes="Fluid shift causes a stuffy feeling in the head. Try saline spray first.",
        call="Fever with thick discharge or facial pain."),
    "Back pain": dict(
        options=["Acetaminophen", "Ibuprofen", "Topical lidocaine or warming pads"],
        notes="Do gentle spine-lengthening stretches and core work. Back pain is common as the spine lengthens.",
        call="Numbness, leg weakness or pain that does not ease."),
    "Sore muscles": dict(
        options=["Topical anti-inflammatory gel", "Ibuprofen (short term)"],
        notes="Warm up, cool down and stretch. Lower the load for a session, then build up again slowly.",
        call="Sudden sharp pain, swelling or being unable to move a limb."),
    "Trouble sleeping": dict(
        options=["Melatonin", "A short-term sleep aid only if prescribed by the flight surgeon"],
        notes="Habits first: dim lights, a fixed schedule, a cool and quiet sleep station, no late caffeine.",
        call="More than 3 poor nights in a row, or any impairment during critical work."),
    "Skin rash or itching": dict(
        options=["Hydrocortisone cream", "Moisturiser", "Antihistamine for itching"],
        notes="Keep the area clean and dry, and change clothes often. Photograph it for telemedicine.",
        call="A spreading rash, blisters, fever or pus."),
    "Irritated eyes": dict(
        options=["Lubricating eye drops"],
        notes="Do not rub your eyes: floating particles (or dust on a surface mission) can scratch the cornea. Rinse gently.",
        call="Pain, vision change or something stuck in your eye."),
    "Constipation": dict(
        options=["Stool softener", "Fibre and extra fluids"],
        notes="Common in microgravity. Keep exercising and drinking.",
        call="Severe belly pain or no bowel movement for several days."),
    "Upset stomach / diarrhea": dict(
        options=["Loperamide", "Oral rehydration solution"],
        notes="Rehydrate first. Report it, because infections spread easily in a closed cabin.",
        call="Blood in stool, fever or signs of dehydration."),
    "Fever or feeling unwell": dict(
        options=["Acetaminophen for fever and aches", "Fluids and rest"],
        notes="Do not start antibiotics on your own. Keep distance from crewmates and monitor how you feel.",
        call="A high fever, confusion or breathing problems: call right away."),
    "Anxiety or low mood": dict(
        options=["Non-medicine first: slow breathing, exercise, talking to family or a counselor",
                 "Medicine only on the flight surgeon's decision"],
        notes="Isolation and confinement are normal stressors. Talking early prevents bigger problems.",
        call="Lasting low mood, panic, or any thoughts of harming yourself."),
    "Allergic reaction": dict(
        options=["Antihistamine (mild)", "Epinephrine auto-injector (severe emergency only)"],
        notes="Remove the trigger and watch your breathing.",
        call="Throat tightness, facial swelling or trouble breathing: EMERGENCY."),
}

# ---------------------------------------------------------------- exercise plans
# (step name, seconds, description). The animation is chosen from the step name.
PLANS = {
    "Bone & Muscle Protection": [
        ("Warm-up: dynamic stretch", 300, "Arm circles, leg swings and hip openings using foot restraints. Gently raise your heart rate."),
        ("ARED squats", 420, "Resistive device. 3 to 4 sets of 8 to 12 reps. Loads hips, spine and thigh bones, which lose density fastest."),
        ("ARED deadlifts", 420, "3 sets of 8 to 10 reps. Keep a neutral spine and brace your core."),
        ("ARED heel raises", 240, "3 sets of 12 to 15 reps to protect calves and lower-leg bones."),
        ("Upper body: band press and rows", 300, "Resistance bands: press and pull to keep shoulders and back strong."),
        ("Cool-down and stretch", 300, "Slow stretches for hamstrings, hips, shoulders and spine."),
    ],
    "Heart & Cardio": [
        ("Warm-up: easy cycling", 300, "Cycle ergometer at low resistance."),
        ("Treadmill with harness: steady run", 1200, "Steady pace with a comfortable harness load. Builds stamina and loads the legs."),
        ("Cycle intervals", 600, "1 minute hard, 2 minutes easy, repeated. Stay hydrated."),
        ("Cool-down walk", 300, "Slow walk on the treadmill so your heart rate settles gradually."),
    ],
    "Mind Reset": [
        ("Box breathing", 300, "Breathe in for 4 s, hold 4 s, out 4 s, hold 4 s. Keep shoulders relaxed."),
        ("Muscle relaxation", 420, "Tense and release each muscle group from your feet up to your face."),
        ("Gentle stretch / yoga", 420, "Slow, controlled stretches with feet anchored in restraints."),
        ("Earth-gazing mindfulness", 300, "Look out of a window; name 5 things you see, 4 you feel, 3 you hear."),
    ],
    "Easy Recovery Day": [
        ("Light cycling", 600, "Easy pace. You should be able to hold a conversation."),
        ("Neck, shoulders and gaze steadying", 300, "Slow head turns while keeping your eyes on a fixed point."),
        ("Gentle stretching", 420, "Full body, no strain."),
        ("Calm breathing", 300, "Slow breathing, about 6 breaths per minute."),
    ],
    "Partial-Gravity Strength": [
        ("Warm-up: dynamic stretch", 300, "Moon and Mars gravity is gentler than Earth's, so don't skip loading. Joints first."),
        ("Loaded squats", 420, "Wear a weighted pack if you have one. 3 sets of 10."),
        ("Hip-hinge deadlifts", 420, "Pack or bar. Hinge at the hips, flat back."),
        ("Overhead press with bands", 300, "3 sets of 10. Brace your core."),
        ("Heel raises", 240, "3 sets of 15 for calves and ankles."),
        ("Cool-down and stretch", 300, "Slow stretches, especially hips and back."),
    ],
    "Balanced Daily Mix": [
        ("Warm-up: dynamic stretch", 300, "Get joints and muscles ready for loading."),
        ("ARED squats and deadlifts", 600, "Alternate sets: 3 x 8 to 10 of each."),
        ("Cycle ergometer", 900, "Moderate, steady effort."),
        ("Core and posture", 300, "Core bracing and spine-lengthening holds."),
        ("Cool-down and breathing", 300, "Stretch and slow breaths."),
    ],
}
PLAN_GROUP = {"Bone & Muscle Protection": "plan_bone", "Partial-Gravity Strength": "plan_bone",
              "Heart & Cardio": "plan_cardio", "Mind Reset": "plan_mind"}

# ---------------------------------------------------------------- environments
# risk level 1 (low) to 5 (high). Simplified and for orientation only.
ENVS = {
    "Space Station": dict(
        sub="Low Earth orbit, microgravity", color="#6bb8e8",
        risks=[("Radiation", 2), ("Gravity change", 5), ("Confinement", 3), ("Dust & air", 2), ("Day/night rhythm", 4)],
        tips=["You get about 16 sunrises a day up here. Keep strict lights-out times and a dark sleep station.",
              "Microgravity is hardest on bones, muscles and body fluids. Do your 2 hours of exercise every day.",
              "Fluids shift to your head. Tell someone early if close-up reading goes blurry."]),
    "Spacecraft": dict(
        sub="Deep-space transit", color="#c89bd9",
        risks=[("Radiation", 4), ("Gravity change", 4), ("Confinement", 5), ("Dust & air", 2), ("Day/night rhythm", 3)],
        tips=["Know where your storm shelter is before any solar event happens.",
              "Small space, same people, for months. Plan some alone time and some shared meals.",
              "Messages from home arrive with a delay. Keep your own daily routine going."]),
    "Rover": dict(
        sub="Surface expedition vehicle", color="#f4cf5e",
        risks=[("Radiation", 3), ("Gravity change", 2), ("Confinement", 4), ("Dust & air", 4), ("Day/night rhythm", 2)],
        tips=["Vibration and cramped seats are hard on your back. Stretch at least every 2 hours.",
              "Dust gets into everything. Wipe your hands and eyes, and keep suit gear out of the sleeping area.",
              "Cabins heat up fast and thirst fades. Sip water on a schedule, not when you feel like it."]),
    "Moon / Mars Base": dict(
        sub="Surface habitat, partial gravity", color="#f5a14a",
        risks=[("Radiation", 4), ("Gravity change", 3), ("Confinement", 3), ("Dust & air", 5), ("Day/night rhythm", 4)],
        tips=["Partial gravity is kinder to your bones than orbit but it isn't enough. Keep doing loaded exercises.",
              "Surface dust is sharp and irritating. Leave suit gear in the airlock and rinse itchy eyes.",
              "A Mars day is about 40 minutes longer than 24 hours. Bright light in the morning helps your body clock."]),
}

# ---------------------------------------------------------------- routine measurements
# ranges: (low, high, colour, label). axis = (min, max) of the bar.
ROUTINE = [
    dict(id="pulse", title="Resting pulse", glyph="♥", every=1, xp=15, unit="beats per minute", axis=(30, 160),
         decimals=0, color="#f27b8f",
         prompt="Time for a quick pulse check. It takes one minute.",
         steps=["Sit down and relax for about 5 minutes.",
                "Place two fingers on the inside of your wrist, below the thumb. Or on the side of your neck.",
                "Look at a clock and count the beats for 30 seconds.",
                "Multiply by 2. That is your pulse in beats per minute."],
         why="Your heart works differently in space. A pulse that creeps up over days can mean dehydration, "
             "stress, infection or tiredness.",
         ranges=[(30, 40, CRIT, "Very low"), (40, 50, WATCH, "Low"), (50, 100, GOOD, "Normal"),
                 (100, 120, WATCH, "High"), (120, 160, CRIT, "Very high")]),
    dict(id="temp", title="Body temperature", glyph="°", every=3, xp=15, unit="°C", axis=(34, 41),
         decimals=1, color="#f5a14a",
         prompt="Quick temperature check, if you have a thermometer handy.",
         steps=["Wait 15 minutes after exercise or a hot drink.",
                "Use the kit thermometer as the label says.",
                "Write down the number it shows."],
         why="A fever is one of the first signs that your immune system is fighting something.",
         ranges=[(34, 35.5, WATCH, "Low"), (35.5, 37.8, GOOD, "Normal"), (37.8, 38.5, WATCH, "Raised"),
                 (38.5, 41, CRIT, "Fever")]),
    dict(id="bp", title="Blood pressure", glyph="◎", every=7, xp=20, unit="mmHg (top number)", axis=(70, 190),
         decimals=0, color="#6bb8e8",
         prompt="Weekly blood pressure check, if you have a cuff.",
         steps=["Sit quietly for 5 minutes with your back supported and feet restrained or flat.",
                "Put the cuff on your bare upper arm at heart level.",
                "Start the cuff and keep still and silent.",
                "Enter the TOP (systolic) number."],
         why="Fluid shifts change how your blood vessels behave. A steady rise or a very low number is worth reporting.",
         ranges=[(70, 90, WATCH, "Low"), (90, 130, GOOD, "Normal"), (130, 140, WATCH, "Raised"),
                 (140, 190, CRIT, "High")]),
    dict(id="weight", title="Body mass", glyph="⚖", every=7, xp=15, unit="kg", axis=(30, 140),
         decimals=1, color="#8fd45a", baseline=True,
         prompt="Weekly mass check with the mass measurement device.",
         steps=["Use the mass measurement device the same way every time.",
                "Do it at the same time of day, before eating.",
                "Enter the number it shows."],
         why="Losing mass quickly can mean you aren't eating or drinking enough. We compare against your first reading.",
         ranges=None),
    dict(id="nearpower", title="Near-vision check", glyph="\u25c9", every=7, xp=20, unit="D (diopters)",
         axis=(-6.0, 6.0), decimals=2, color="#c89bd9", diopter=True, step=0.25,
         prompt="Weekly near-vision check. Find the lens power that makes small print sharp.",
         steps=["Hold your reading card at about 40 cm (arm's length) in good light.",
                "Cover one eye and put on the adjustable-focus glasses (or the kit's trial lenses) set to 0.00.",
                "Turn the power until the smallest line you can read looks sharp. Minus (-) lenses help near-sighted "
                "blur, plus (+) lenses help far-sighted blur.",
                "Repeat with the other eye and enter the power for your weaker eye (the one that needed more help)."],
         why="Fluid shifting toward your head can slightly reshape your eye, and close-up focus often drifts toward "
             "far-sighted (plus). We compare each reading with your own first one: a shift of 1.00 D or more is "
             "something flight surgeons want to hear about.",
         ranges=None),
    dict(id="height", title="Height", glyph="↕", every=14, xp=10, unit="cm", axis=(140, 210), decimals=1,
         color="#b8a690", info_only=True,
         prompt="Fortnightly height check.",
         steps=["Stretch out against a flat surface with your feet restrained.",
                "Have a crewmate mark or measure the top of your head.",
                "Enter the number in centimetres."],
         why="Without gravity your spine lengthens, and many astronauts gain 2 to 3 cm. That is normal, "
             "but it is also why back pain is common.",
         ranges=None),
]
ROUTINE_BY_ID = {t["id"]: t for t in ROUTINE}

# ---------------------------------------------------------------- indicators for charts
# id -> label, unit, colour, axis, bands (lo, hi, colour)
INDICATORS = [
    ("overall", "Overall readiness", "score", ACCENT, (0, 100),
     [(0, 40, CRIT), (40, 60, CAUTION), (60, 80, WATCH), (80, 100, GOOD)]),
    ("sleep", "Sleep per night", "hours", DOMAIN_COLORS[SLEEP], (2, 10),
     [(2, 4, CRIT), (4, 6, WATCH), (6, 10, GOOD)]),
    ("mood", "Mood", "score", DOMAIN_COLORS[MIND], (0, 100),
     [(0, 30, CRIT), (30, 60, WATCH), (60, 100, GOOD)]),
    ("pulse", "Resting pulse", "bpm", "#f27b8f", (30, 160),
     [(30, 40, CRIT), (40, 50, WATCH), (50, 100, GOOD), (100, 120, WATCH), (120, 160, CRIT)]),
    ("temp", "Temperature", "°C", "#f5a14a", (34, 41),
     [(34, 35.5, WATCH), (35.5, 37.8, GOOD), (37.8, 38.5, WATCH), (38.5, 41, CRIT)]),
    ("bp", "Blood pressure (top)", "mmHg", "#6bb8e8", (70, 190),
     [(70, 90, WATCH), (90, 130, GOOD), (130, 140, WATCH), (140, 190, CRIT)]),
    ("weight", "Body mass", "kg", "#8fd45a", (30, 140), []),
    ("nearpower", "Near vision (lens power)", "D", "#c89bd9", (-6, 6), []),
] + [(d, d, "score", DOMAIN_COLORS[d], (0, 100),
      [(0, 40, CRIT), (40, 60, CAUTION), (60, 80, WATCH), (80, 100, GOOD)]) for d in DOMAINS]

# ---------------------------------------------------------------- learning cards
LEARN = [
    dict(id="colors", title="How to read the colors", color=ACCENT,
         tldr="Green is fine, yellow is a heads-up, orange is take care, red is call someone.",
         body=["Everything in this app uses the same four colors, so you can read your status at a glance.",
               "GREEN means all good. YELLOW means keep an eye on it. ORANGE means take care and follow the advice. "
               "RED means ask the flight surgeon for help now.",
               "The colors are a guide, not a diagnosis. If something feels wrong, trust your instincts and speak up."],
         do=["Check the colors on your home screen each day", "Tap any health area to see why it has its color"]),
    dict(id="bones", title="Why bones and muscles weaken", color=DOMAIN_COLORS[BONE],
         tldr="No weight on your legs means your body stops rebuilding them.",
         body=["On Earth gravity makes your bones and muscles work all day. In orbit that load disappears, so the body "
               "slowly lets go of what it doesn't need. Without countermeasures astronauts can lose around 1% of bone "
               "density a month, mostly in the hips and spine.",
               "Weight-bearing exercise is the best defense, which is why crews train about two hours a day."],
         do=["Do your resistive session every day", "Eat enough protein, calcium and vitamin D",
             "Report bone or back pain that doesn't go away"]),
    dict(id="radiation", title="Space radiation in plain words", color=DOMAIN_COLORS[IMMUNE],
         tldr="Particles from the Sun and deep space pass right through the walls.",
         body=["Outside Earth's magnetic shield, high-energy particles pass through spacecraft and through you. "
               "Short bursts from solar storms and slow exposure over months both matter.",
               "Effects can include a weaker immune system, eye problems and a higher long-term cancer risk. "
               "Some astronauts also see brief flashes of light, which is normal and caused by single particles hitting the eye."],
         do=["Know your storm shelter location", "Follow every radiation alert",
             "Tell the team about nausea or headaches after an alert"]),
    dict(id="fluid", title="Fluid shift, your heart and your eyes", color=DOMAIN_COLORS[HEART],
         tldr="Without gravity, body fluids drift up toward your head.",
         body=["On Earth gravity pulls blood and fluid toward your feet. In space it spreads evenly, so your face may "
               "look puffy, your nose feels stuffy and your legs get thinner.",
               "Over months your heart does less work and can get weaker. Pressure around the eyes can also change "
               "your vision, which is why we ask you to check near-vision every week."],
         do=["Drink fluids regularly", "Do your cardio sessions", "Report blurry reading or pressure in your head"]),
    dict(id="sleep", title="Sleep and your body clock", color=DOMAIN_COLORS[SLEEP],
         tldr="Your brain needs dark and routine, even when the sun keeps rising.",
         body=["On the space station the sun rises about 16 times a day. Your body clock loses its normal cue, and "
               "many astronauts sleep less than 6 hours.",
               "Poor sleep lowers mood, memory, reaction time and immunity. Treat sleep like a mission task."],
         do=["Keep lights out at the same time", "Dim screens in the evening", "Cut caffeine in the afternoon"]),
    dict(id="mind", title="Isolation, confinement and crew life", color=DOMAIN_COLORS[MIND],
         tldr="Small space, same people, far from home. It's tough for everyone.",
         body=["Feeling low, irritable or lonely is normal on long missions. It is not weakness.",
               "Small habits help a lot: keep your routine, get some privacy, call home, share meals, and talk early "
               "if something is bothering you."],
         do=["Schedule calls with family", "Share at least one meal with the crew",
             "Ask for a conversation with the behavioral health team if you feel low for several days"]),
    dict(id="immune", title="Immune changes", color=DOMAIN_COLORS[IMMUNE],
         tldr="Stress, radiation and poor sleep all quietly weaken your defenses.",
         body=["In space the immune system behaves differently. Some dormant viruses can wake up, and skin rashes "
               "are more common. Germs also spread easily in a closed cabin.",
               "Hygiene, sleep and good food are your best tools."],
         do=["Wipe shared surfaces", "Tell the doctor early if you feel unwell", "Take your temperature when something feels off"]),
    dict(id="hydration", title="Drinking enough", color="#6bb8e8",
         tldr="Your thirst signal gets weaker, so drink on a schedule.",
         body=["Fluid shifts can make you feel less thirsty even when you need water. Being dry makes headaches, "
               "tiredness and a fast pulse worse.",
               "A good habit is a few sips every hour. Pale yellow urine is a good sign."],
         do=["Log your drinks in the app", "Drink before and after exercise"]),
    dict(id="dust", title="Dust and air quality", color=CAUTION,
         tldr="Dust on the Moon and Mars is sharp and irritating. Cabin air matters everywhere.",
         body=["Surface dust can scratch eyes and irritate lungs and skin. Inside any closed cabin, carbon dioxide can "
               "build up if ventilation is poor, causing headaches and drowsiness.",
               "If several people have headaches at once, tell the team and check the air."],
         do=["Leave suit gear in the airlock", "Rinse itchy eyes with clean water",
             "Report headaches or drowsiness that come together with a stuffy room"]),
]

# ---------------------------------------------------------------- gamification text
QUESTS = [
    ("checkin", "Do your daily check-in", 50),
    ("exercise", "Finish an exercise session", 60),
    ("water", "Log 6 drinks of water", 25),
    ("routine", "Complete a routine measurement", 20),
]
WATER_GOAL = 6
BONUS_XP = 40
TITLES = ["Cadet", "Pilot", "Specialist", "Flight Engineer", "Mission Specialist", "Commander", "Legend"]

# name, xp, weekly points, streak, cheers, environment
DEMO_CREW = [
    ("Asha", 880, 215, 12, 4, "Space Station"),
    ("Ravi", 540, 160, 5, 2, "Space Station"),
    ("Lina", 310, 95, 3, 6, "Space Station"),
]

CREW_NOTES = [
    "Small habits, every day. That is how crews stay strong up here.",
    "Drink some water. Seriously, now.",
    "Look out of a window for one full minute today.",
    "A short stretch counts. You do not need a perfect workout.",
    "Check on a crewmate. Ask how they really are.",
    "Sleep is part of the mission plan. Protect it.",
    "Lights low an hour before bed. Your brain will thank you.",
    "Eat a proper meal together if you can.",
    "Notice how you feel before you try to fix it.",
    "Nobody is fine every day. Saying so early helps.",
    "Stand tall, shoulders back. Your spine is longer up here.",
    "One more rep than yesterday is plenty.",
]


##############################################################################
# SECTION: logic
# logic.py - scoring, saving, XP, quests, badges, measurements and the leaderboard.
# Nothing in here draws anything, which keeps it easy to test.
##############################################################################

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "astro_vital_data.json")


# ------------------------------------------------------------------ dates
def today():
    return dt.date.today().isoformat()


def week_key(d=None):
    d = d or dt.date.today()
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


# ------------------------------------------------------------------ status helpers
def status_of(score):
    if score >= 80:
        return "NOMINAL", GOOD, "You are doing great"
    if score >= 60:
        return "WATCH", WATCH, "A few things to keep an eye on"
    if score >= 40:
        return "CAUTION", CAUTION, "Take care today and follow the advice"
    return "CRITICAL", CRIT, "Please seek medical advice now"


def level_of(score):
    return "good" if score >= 80 else "watch" if score >= 60 else "high"


# ------------------------------------------------------------------ profiles
def new_profile(name, env="Space Station", demo=False):
    return dict(
        name=name, env=env, demo=demo, history=[], measures=[], xp=0, lvl_seen=1,
        weekly=dict(week=week_key(), pts=0), badges=[], learned=[],
        quests=dict(date=today(), done={}, water=0, bonus=False),
        stats=dict(sessions=0, reps=0, plan_bone=0, plan_cardio=0, plan_mind=0,
                   water_days=0, best_streak=0, minutes=0),
        cheers=0, demo_streak=0,
        gems=0, gems_total=0, shields=0, frozen=[], owned=[], buddy="", boost_until=0,
        streak_ms=[], buddy_ms=[],
    )


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,20}$")
PBKDF2_ROUNDS = 200_000


def hash_password(password, salt=None):
    """Salted PBKDF2-HMAC-SHA256. Only this hash is ever stored, never the password."""
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return dict(salt=salt.hex(), hash=dk.hex(), rounds=PBKDF2_ROUNDS)


def check_password(auth, password):
    if not auth:
        return False
    try:
        salt = bytes.fromhex(auth["salt"])
        rounds = int(auth.get("rounds", PBKDF2_ROUNDS))
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(dk.hex(), auth["hash"])
    except (KeyError, ValueError, TypeError):
        return False


def password_problem(password, username=""):
    """Returns a short message if the password is not acceptable, else ''."""
    if len(password) < 8:
        return "Use at least 8 characters."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Include at least one letter and one number."
    if username and password.lower() == username.lower():
        return "Your password can't be the same as your username."
    return ""


def password_strength(password):
    """0 (weak) to 4 (strong), just for the little meter."""
    s = 0
    s += len(password) >= 8
    s += len(password) >= 12
    s += bool(re.search(r"[a-z]", password) and re.search(r"[A-Z]", password))
    s += bool(re.search(r"\d", password))
    s += bool(re.search(r"[^A-Za-z0-9]", password))
    return min(s, 4)


class Store:
    """All crew profiles live in one JSON file next to the program.
    Every real profile is an account: a username plus a salted, hashed password.
    Nobody is signed in when the program starts."""

    MAX_FAILS, LOCK_SECONDS = 5, 30

    def __init__(self, path=DATA_FILE):
        self.path = path
        self.data = self._load()
        self._fails = {}
        self._dummy_auth = None
        self.guest = None          # a guest lives in memory only and is never written to disk

    def _load(self):
        data = {"active": None, "crew": {}, "hide_demo": False, "last_user": ""}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict) and isinstance(loaded.get("crew"), dict):
                data.update(loaded)
        except (OSError, ValueError):
            pass
        if not data["crew"]:
            for name, xp, wk, st, ch, env in DEMO_CREW:
                p = new_profile(name, env, demo=True)
                p.update(xp=xp, demo_streak=st, cheers=ch)
                p["weekly"]["pts"] = wk
                p["lvl_seen"] = level_info(xp)[0]
                data["crew"][name] = p
        data["active"] = None
        return data

    def save(self):
        try:
            out = dict(self.data)
            if out.get("active") == GUEST_KEY:        # a guest session leaves no trace on disk
                out["active"] = None
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)
            return True
        except OSError:
            return False

    @property
    def profile(self):
        if self.data["active"] == GUEST_KEY:
            return self.guest
        return self.data["crew"].get(self.data["active"])

    @property
    def is_guest(self):
        return self.data["active"] == GUEST_KEY and self.guest is not None

    def get_profile(self, name):
        if self.guest is not None and name == self.guest["name"] and self.data["active"] == GUEST_KEY:
            return self.guest
        return self.data["crew"].get(name)

    def start_guest(self, env="Space Station"):
        self.guest = new_profile("Guest", env)
        self.data["active"] = GUEST_KEY

    def promote_guest(self, username, password):
        """Turn the current guest into a real account, keeping all progress. -> ("ok", name) | ("error", msg)"""
        if not self.is_guest:
            return "error", "There is no guest session to save."
        username = username.strip()
        if not USERNAME_RE.match(username):
            return "error", "Username: 3 to 20 letters, numbers, dots, dashes or underscores."
        if username.lower() == "guest" or self.find_user(username):
            return "error", "That username is taken. Try another one."
        bad = password_problem(password, username)
        if bad:
            return "error", bad
        p = self.guest
        p["name"], p["auth"] = username, hash_password(password)
        self.data["crew"][username] = p
        self.guest = None
        self.data["active"] = username
        self.data["last_user"] = username
        self.save()
        return "ok", username

    def real_names(self):
        return [n for n, p in self.data["crew"].items() if not p.get("demo")]

    # ------------------------------------------------------------ accounts
    def find_user(self, username):
        u = username.strip().lower()
        for n in self.data["crew"]:
            if n.lower() == u:
                return n
        return None

    def sign_up(self, username, password, env):
        """-> ("ok", name) or ("error", message)"""
        username = username.strip()
        if not USERNAME_RE.match(username):
            return "error", "Username: 3 to 20 letters, numbers, dots, dashes or underscores."
        if username.lower() == "guest" or self.find_user(username):
            return "error", "That username is taken. Try another one."
        bad = password_problem(password, username)
        if bad:
            return "error", bad
        if env not in ENVS:
            env = "Space Station"
        p = new_profile(username, env)
        p["auth"] = hash_password(password)
        self.data["crew"][username] = p
        self.data["active"] = username
        self.data["last_user"] = username
        self.save()
        return "ok", username

    def _locked_for(self, key):
        _, until = self._fails.get(key, (0, 0.0))
        left = until - time.time()
        return int(left) + 1 if left > 0 else 0

    def _fail(self, key):
        n, until = self._fails.get(key, (0, 0.0))
        n += 1
        if n >= self.MAX_FAILS:
            self._fails[key] = (0, time.time() + self.LOCK_SECONDS)
        else:
            self._fails[key] = (n, until)

    def log_in(self, username, password):
        """-> ("ok", name) | ("bad", None) | ("locked", seconds) | ("claim", name)"""
        key = username.strip().lower()
        wait = self._locked_for(key)
        if wait:
            return "locked", wait
        name = self.find_user(username)
        p = self.data["crew"].get(name) if name else None
        if p is None or p.get("demo"):
            if self._dummy_auth is None:
                self._dummy_auth = hash_password("not-a-real-password")
            check_password(self._dummy_auth, password)   # same time cost either way
            self._fail(key)
            return "bad", None
        if not p.get("auth"):
            return "claim", name        # profile made before accounts existed
        if not check_password(p["auth"], password):
            self._fail(key)
            return "bad", None
        self._fails.pop(key, None)
        self.data["active"] = name
        self.data["last_user"] = name
        self.save()
        return "ok", name

    def claim(self, name, password):
        """Set the first password on an older profile and sign in. -> ("ok", name) | ("error", msg)"""
        p = self.data["crew"].get(name)
        if not p or p.get("demo") or p.get("auth"):
            return "error", "This profile can't be claimed."
        bad = password_problem(password, name)
        if bad:
            return "error", bad
        p["auth"] = hash_password(password)
        self.data["active"] = name
        self.data["last_user"] = name
        self.save()
        return "ok", name

    def change_password(self, name, old, new):
        p = self.data["crew"].get(name)
        if not p or not check_password(p.get("auth"), old):
            return "Your current password isn't right."
        bad = password_problem(new, name)
        if bad:
            return bad
        p["auth"] = hash_password(new)
        self.save()
        return ""

    def log_out(self):
        self.data["active"] = None
        self.guest = None
        self.save()

    def delete_account(self, name, password):
        """Permanently remove one account after checking its password. Returns '' or an error message."""
        p = self.data["crew"].get(name)
        if not p or p.get("demo"):
            return "That account can't be deleted."
        if not check_password(p.get("auth"), password):
            return "That password isn't right."
        del self.data["crew"][name]
        if self.data.get("last_user") == name:
            self.data["last_user"] = ""
        self.data["active"] = None
        self.save()
        return ""

    def reset_all(self):
        """Wipe every account and all progress on this computer, back to a fresh install."""
        try:
            os.remove(self.path)
        except OSError:
            pass
        self.data = self._load()
        self._fails = {}
        self.guest = None
        self.save()


# ------------------------------------------------------------------ XP and levels
def need_for(level):
    return 150 + (level - 1) * 40


def level_info(xp):
    """-> (level, xp into this level, xp needed for the next level)"""
    lvl = 1
    while xp >= need_for(lvl):
        xp -= need_for(lvl)
        lvl += 1
    return lvl, xp, need_for(lvl)


def title_for(level):
    return TITLES[min(level - 1, len(TITLES) - 1)]


def ensure_today(p):
    if p["quests"].get("date") != today():
        p["quests"] = dict(date=today(), done={}, water=0, bonus=False)
    if p["weekly"].get("week") != week_key():
        p["weekly"] = dict(week=week_key(), pts=0)


def add_xp(p, pts):
    ensure_today(p)
    if pts > 0 and time.time() < p.get("boost_until", 0):
        pts *= 2                                   # Double XP boost from the shop
    p["xp"] += pts
    p["weekly"]["pts"] += pts
    if not p.get("demo"):
        give_gems(p, pts // 5)                     # every 5 XP earns 1 stardust


def complete_quest(p, qid):
    """Mark a daily quest done. Returns a list of (text, xp) events."""
    ensure_today(p)
    q = p["quests"]
    events = []
    if q["done"].get(qid):
        return events
    q["done"][qid] = True
    for key, title, pts in QUESTS:
        if key == qid:
            add_xp(p, pts)
            events.append((f"Quest: {title}", pts))
    if all(q["done"].get(k) for k, _, _ in QUESTS) and not q.get("bonus"):
        q["bonus"] = True
        add_xp(p, BONUS_XP)
        events.append(("Full orbit: all daily quests done", BONUS_XP))
    return events


def log_water(p):
    ensure_today(p)
    q = p["quests"]
    if q["water"] >= WATER_GOAL:
        return []
    q["water"] += 1
    events = [("Hydration logged", 2)]
    add_xp(p, 2)
    if q["water"] >= WATER_GOAL:
        p["stats"]["water_days"] += 1
        events += complete_quest(p, "water")
    return events


# ------------------------------------------------------------------ streaks
def streak(history):
    days = sorted({e["time"][:10] for e in history})
    if not days:
        return 0
    last = dt.date.fromisoformat(days[-1])
    if (dt.date.today() - last).days > 1:
        return 0
    count = 1
    for prev in reversed(days[:-1]):
        pd = dt.date.fromisoformat(prev)
        if (last - pd).days == 1:
            count += 1
            last = pd
        else:
            break
    return count


def best_streak_of(history):
    days = sorted({dt.date.fromisoformat(e["time"][:10]) for e in history})
    best = run = 0
    prev = None
    for d in days:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        best = max(best, run)
        prev = d
    return best


def profile_streak(p):
    return p.get("demo_streak", 0) if p.get("demo") else streak_days(p)


# ------------------------------------------------------------------ analysis
def analyze(answers, pulse, flags, prior):
    scores = {}
    for d in DOMAINS:
        qs = [q for q in QUESTIONS if q["d"] == d]
        sev = sum(answers.get(q["id"], 0) for q in qs)
        scores[d] = 100.0 - 100.0 * sev / (3 * len(qs))

    alerts, notes = [], []
    if pulse is not None:
        if pulse > 120 or pulse < 40:
            scores[HEART] -= 30
            alerts.append(f"Your resting pulse ({pulse:.0f} bpm) is far outside the safe range.")
        elif pulse > 100 or pulse < 50:
            scores[HEART] -= 15
            notes.append(f"Your pulse ({pulse:.0f} bpm) is outside the usual resting range of 50 to 100.")
    for qid, what in CRITICAL.items():
        if answers.get(qid, 0) == 3:
            alerts.append(f"You reported {what}.")
    if answers.get("s1", 0) == 3:
        notes.append("You slept under 4 hours. Avoid risky tasks until you have rested.")

    for d in DOMAINS:
        scores[d] = max(0, min(100, round(scores[d])))
    overall = round(sum(scores[d] * WEIGHTS[d] for d in DOMAINS))
    for f in flags:
        alerts.append(f"Urgent symptom: {f}")
    if flags:
        overall = min(overall, 35)
    elif alerts:
        overall = min(overall, 45)

    recent = prior[-7:]
    if len(recent) >= 2:
        avg = sum(e["overall"] for e in recent) / len(recent)
        if overall - avg <= -10:
            notes.append(f"Your overall score is {abs(overall - avg):.0f} points below your recent average.")
        drops = []
        for d in DOMAINS:
            vals = [e["scores"][d] for e in recent if d in e.get("scores", {})]
            if len(vals) >= 2 and scores[d] <= sum(vals) / len(vals) - 15:
                drops.append((scores[d] - sum(vals) / len(vals), d))
        for _, d in sorted(drops)[:2]:
            notes.append(f"{d} has dropped noticeably compared with your usual.")
    return dict(scores=scores, overall=int(overall), alerts=alerts, notes=notes)


# ------------------------------------------------------------------ routine measurements
def last_measure(p, tid):
    for m in reversed(p["measures"]):
        if m["task"] == tid:
            return m
    return None


def days_since(iso_time):
    return (dt.date.today() - dt.date.fromisoformat(iso_time[:10])).days


def due_tasks(p):
    """Routine tasks that are due. Returns list of (task, days_overdue)."""
    out = []
    for t in ROUTINE:
        m = last_measure(p, t["id"])
        if m is None:
            out.append((t, 0))
        else:
            gap = days_since(m["time"]) - t["every"]
            if gap >= 0:
                out.append((t, gap))
    return out


def measure_status(task, value, p):
    """-> (colour, label) for a reading."""
    if task.get("diopter"):
        vals = [m["value"] for m in p["measures"] if m["task"] == task["id"]]
        if not vals:
            return ACCENT, "Logged"
        if len(vals) == 1 and abs(value - vals[0]) < 1e-9:
            return ACCENT, "Baseline set"
        shift = abs(value - vals[0])
        if shift < 0.5:
            return GOOD, "Steady"
        return (WATCH if shift < 1.0 else CRIT), f"Shift of {shift:.2f} D"
    if task.get("ranges"):
        rng = task["ranges"]
        if value < rng[0][0]:
            return rng[0][2], rng[0][3]
        for lo, hi, col, label in rng:
            if lo <= value < hi:
                return col, label
        return rng[-1][2], rng[-1][3]
    if task.get("baseline"):
        first = next((m["value"] for m in p["measures"] if m["task"] == task["id"]), None)
        if first:
            change = abs(value - first) / first * 100
            if change < 3:
                return GOOD, "Steady"
            if change < 5:
                return WATCH, f"{change:.0f}% from your start"
            return CRIT, f"{change:.0f}% from your start"
    return ACCENT, "Logged"


def record_measure(p, tid, value):
    task = ROUTINE_BY_ID[tid]
    p["measures"].append(dict(time=dt.datetime.now().strftime("%Y-%m-%d %H:%M"), task=tid, value=value))
    events = []
    add_xp(p, task["xp"])
    events.append((f"{task['title']} logged", task["xp"]))
    events += complete_quest(p, "routine")
    return events


# ------------------------------------------------------------------ chart series
def series(p, key):
    """List of (time string, value) for an indicator id."""
    if key == "overall":
        return [(e["time"], e["overall"]) for e in p["history"]]
    if key == "sleep":
        return [(e["time"], SLEEP_HOURS[e["answers"]["s1"]]) for e in p["history"] if "s1" in e.get("answers", {})]
    if key == "mood":
        return [(e["time"], MOOD_SCORE[e["answers"]["m1"]]) for e in p["history"] if "m1" in e.get("answers", {})]
    if key in ROUTINE_BY_ID:
        return [(m["time"], m["value"]) for m in p["measures"] if m["task"] == key]
    return [(e["time"], e["scores"][key]) for e in p["history"] if key in e.get("scores", {})]


# ------------------------------------------------------------------ badges
BADGES = [
    ("first", "First Orbit", "Complete your first check-in", ACCENT, lambda p: len(p["history"]) >= 1),
    ("checkins10", "Regular", "Complete 10 check-ins", ACCENT, lambda p: len(p["history"]) >= 10),
    ("streak3", "Warming Up", "3-day check-in streak", CAUTION, lambda p: p["stats"]["best_streak"] >= 3),
    ("streak7", "Week Strong", "7-day check-in streak", CAUTION, lambda p: p["stats"]["best_streak"] >= 7),
    ("streak30", "Iron Habit", "30-day check-in streak", CRIT, lambda p: p["stats"]["best_streak"] >= 30),
    ("bone", "Iron Bones", "Finish 5 strength sessions", DOMAIN_COLORS[BONE], lambda p: p["stats"]["plan_bone"] >= 5),
    ("heart", "Heart Hero", "Finish 3 cardio sessions", DOMAIN_COLORS[HEART], lambda p: p["stats"]["plan_cardio"] >= 3),
    ("mind", "Calm Mind", "Finish 3 mind reset sessions", DOMAIN_COLORS[MIND], lambda p: p["stats"]["plan_mind"] >= 3),
    ("water", "Hydration Hero", "Hit the water goal on 3 days", "#6bb8e8", lambda p: p["stats"]["water_days"] >= 3),
    ("reps", "Rep Machine", "Count 50 reps with the coach cam", WATCH, lambda p: p["stats"]["reps"] >= 50),
    ("data", "Data Pilot", "Log 5 routine measurements", "#6bb8e8", lambda p: len(p["measures"]) >= 5),
    ("scholar", "Curious Mind", "Read 5 learning cards", ACCENT2, lambda p: len(p["learned"]) >= 5),
    ("peak", "Peak Form", "Reach an overall score of 90+", GOOD, lambda p: any(e["overall"] >= 90 for e in p["history"])),
    ("rising", "Rising Star", "Reach level 5", WATCH, lambda p: level_info(p["xp"])[0] >= 5),
]
BADGES += [
    ("buddy3", "Better Together", "3-day streak with a streak buddy", WATCH, lambda p: p["stats"].get("best_buddy", 0) >= 3),
    ("shield", "Safety First", "Buy your first Streak Shield", "#6bb8e8", lambda p: p["stats"].get("shields_bought", 0) >= 1),
    ("dust", "Stardust Collector", "Earn 300 stardust in total", ACCENT2, lambda p: p.get("gems_total", 0) >= 300),
]
BADGE_XP = 25


def check_badges(p):
    """Unlock any newly earned badges. Returns list of (id, name)."""
    p["stats"]["best_streak"] = max(p["stats"]["best_streak"], best_streak_of(p["history"]))
    new = []
    for bid, name, _, _, fn in BADGES:
        if bid not in p["badges"]:
            try:
                ok = fn(p)
            except (KeyError, ValueError):
                ok = False
            if ok:
                p["badges"].append(bid)
                add_xp(p, BADGE_XP)
                new.append((bid, name))
    return new


# ------------------------------------------------------------------ stardust, shields, boosts, buddy streaks
GUEST_KEY = "__guest__"
SHIELD_MAX = 2
STREAK_MILESTONES = {3: 15, 7: 30, 14: 50, 30: 100, 60: 150, 100: 250}      # days -> stardust
BUDDY_MILESTONES = {3: 20, 7: 40, 14: 80, 30: 150}

SHOP = [
    dict(id="shield", name="Streak Shield", price=60, glyph="\u2744", color="#6bb8e8",
         desc="Protects your streak if you miss a day. Used automatically. Hold up to 2."),
    dict(id="boost", name="Double XP", price=50, glyph="\u26a1", color="#f2b84b",
         desc="Every XP you earn counts twice for the next 30 minutes."),
    dict(id="ring", name="Gold Ring", price=120, glyph="\u25ce", color="#f4cf5e",
         desc="A golden ring around your avatar everywhere in the app."),
    dict(id="scarf", name="Nova's Scarf", price=80, glyph="\u2740", color="#f27b8f",
         desc="A cosy scarf for your mascot, Nova. Looks great on the Home screen."),
]
SHOP_BY_ID = {i["id"]: i for i in SHOP}


def gems_of(p):
    return p.get("gems", 0)


def give_gems(p, n):
    p["gems"] = p.get("gems", 0) + n
    p["gems_total"] = p.get("gems_total", 0) + n


def streak_days(p):
    """Check-in streak. Days covered by a Streak Shield keep it alive but do not add to it."""
    real = {e["time"][:10] for e in p["history"]}
    allow = real | set(p.get("frozen", []))
    d = dt.date.today()
    if d.isoformat() not in allow:
        d -= dt.timedelta(days=1)
    count = 0
    while d.isoformat() in allow:
        if d.isoformat() in real:
            count += 1
        d -= dt.timedelta(days=1)
    return count


def apply_shields(p):
    """If whole days were missed and enough shields are held, spend them. Returns shields used."""
    if p.get("demo"):
        return 0
    real = {e["time"][:10] for e in p["history"]}
    seen = real | set(p.get("frozen", []))
    if not seen or p.get("shields", 0) <= 0:
        return 0
    last = dt.date.fromisoformat(max(seen))
    yesterday = dt.date.today() - dt.timedelta(days=1)
    missed = [(last + dt.timedelta(days=i)).isoformat() for i in range(1, (yesterday - last).days + 1)]
    if not missed or len(missed) > p["shields"]:
        return 0
    p.setdefault("frozen", []).extend(missed)
    p["shields"] -= len(missed)
    return len(missed)


def week_activity(p):
    """Seven (letter, done, is_today, shielded) tuples for the last 7 days, oldest first."""
    days = {e["time"][:10] for e in p["history"]}
    froz = set(p.get("frozen", []))
    out = []
    for i in range(6, -1, -1):
        d = dt.date.today() - dt.timedelta(days=i)
        iso = d.isoformat()
        out.append((d.strftime("%a")[0], iso in days, i == 0, iso in froz and iso not in days))
    return out


def day_active(store, name, iso):
    """Did this crewmate check in on that day? Demo crewmates follow a fixed, repeatable pattern."""
    p = store.get_profile(name)
    if p is None:
        return False
    if p.get("demo"):
        return zlib.crc32(f"{name}{iso}".encode()) % 10 != 0
    return iso in {e["time"][:10] for e in p["history"]} or iso in set(p.get("frozen", []))


def buddy_info(store, p):
    """-> None if no buddy, else dict(name, streak, me_today, buddy_today)."""
    name = p.get("buddy")
    if not name or store.get_profile(name) is None or name == p["name"]:
        return None
    mine = {e["time"][:10] for e in p["history"]} | set(p.get("frozen", []))
    d = dt.date.today()
    me_today = d.isoformat() in mine
    buddy_today = day_active(store, name, d.isoformat())
    if not (me_today and buddy_today):
        d -= dt.timedelta(days=1)
    n = 0
    while d.isoformat() in mine and day_active(store, name, d.isoformat()):
        n += 1
        d -= dt.timedelta(days=1)
    return dict(name=name, streak=n, me_today=me_today, buddy_today=buddy_today)


def buy_item(p, item_id):
    """-> (ok, message)"""
    item = SHOP_BY_ID[item_id]
    if gems_of(p) < item["price"]:
        return False, f"You need {item['price'] - gems_of(p)} more stardust."
    owned = p.setdefault("owned", [])
    if item_id == "shield":
        if p.get("shields", 0) >= SHIELD_MAX:
            return False, f"You already hold {SHIELD_MAX} shields."
        p["shields"] = p.get("shields", 0) + 1
        p["stats"]["shields_bought"] = p["stats"].get("shields_bought", 0) + 1
    elif item_id == "boost":
        base = max(p.get("boost_until", 0), time.time())
        p["boost_until"] = base + 30 * 60
    else:
        if item_id in owned:
            return False, "You already own this."
        owned.append(item_id)
    p["gems"] -= item["price"]
    return True, f"{item['name']} is yours."


def boost_left(p):
    """Seconds of Double XP left."""
    return max(int(p.get("boost_until", 0) - time.time()), 0)


# ------------------------------------------------------------------ leaderboard
def leaderboard(store):
    rows = []
    for name, p in store.data["crew"].items():
        if p.get("demo") and store.data.get("hide_demo"):
            continue
        ensure_today(p)
        lvl = level_info(p["xp"])[0]
        rows.append(dict(name=name, xp=p["xp"], level=lvl, title=title_for(lvl), weekly=p["weekly"]["pts"],
                         streak=profile_streak(p), cheers=p.get("cheers", 0), demo=p.get("demo", False),
                         badges=len(p["badges"]), ring="ring" in p.get("owned", [])))
    if store.is_guest:
        p = store.guest
        ensure_today(p)
        lvl = level_info(p["xp"])[0]
        rows.append(dict(name=p["name"], xp=p["xp"], level=lvl, title=title_for(lvl), weekly=p["weekly"]["pts"],
                         streak=profile_streak(p), cheers=p.get("cheers", 0), demo=False, badges=len(p["badges"]),
                         ring="ring" in p.get("owned", [])))
    rows.sort(key=lambda r: (-r["weekly"], -r["xp"], r["name"]))
    return rows


##############################################################################
# SECTION: widgets
# widgets.py - small custom Tkinter widgets and drawing helpers.
# Tkinter has no rounded buttons or gradients, so we draw them on canvases.
##############################################################################

def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Blend colour a toward colour b by fraction t (0..1)."""
    ra, rb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(int(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))


def rrect(c, x1, y1, x2, y2, r=16, **kw):
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


# ------------------------------------------------------------------ buttons and inputs
class Pill(tk.Canvas):
    """Rounded button."""

    def __init__(self, parent, text, command, w=180, h=44, fill=ACCENT, fg=INK,
                 surface=BG, size=11, ghost=False):
        super().__init__(parent, width=w, height=h, bg=surface, highlightthickness=0, bd=0, cursor="hand2")
        self.cmd, self.fill, self.ghost, self.surface = command, fill, ghost, surface
        self.shape = rrect(self, 1, 1, w - 1, h - 1, r=h // 2,
                           fill=surface if ghost else fill, outline=LINE if ghost else fill)
        self.txt = self.create_text(w / 2, h / 2, text=text, fill=TEXT if ghost else fg,
                                    font=(FONT, size, "bold"))
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", lambda e: self.cmd())

    def _enter(self, e=None):
        self.itemconfigure(self.shape, fill=CARD2 if self.ghost else mix(self.fill, "#ffffff", 0.18))

    def _leave(self, e=None):
        self.itemconfigure(self.shape, fill=self.surface if self.ghost else self.fill)

    def set_text(self, t):
        self.itemconfigure(self.txt, text=t)

    def set_fill(self, color):
        self.fill = color
        self.itemconfigure(self.shape, fill=color, outline=color)


# ------------------------------------------------------------------ lens power picker
def fmt_reading(tid, v):
    """Readable text for a saved reading. Lens power shows its sign, like a real prescription."""
    if tid == "nearpower":
        return "0.00 D" if abs(v) < 0.005 else f"{v:+.2f} D"
    return f"{v:g}"


class DiopterDial(tk.Canvas):
    """Lens-power picker like a real prescription: minus (near-sighted side) to plus (far-sighted side),
    in 0.25 D steps. Click or drag the track, use the - / + buttons, or press the arrow keys."""
    LO, HI, STEP = -6.0, 6.0, 0.25
    COOL, WARM = "#6bb8e8", "#f2b84b"

    def __init__(self, parent, value=0.0, surface=CARD, on_change=None, height=160):
        super().__init__(parent, height=height, bg=surface, highlightthickness=0, cursor="hand2", takefocus=1)
        self.surface, self.on_change, self._drag_ok = surface, on_change, False
        self.value = self._snap(value)
        self.bind("<Configure>", lambda e: self.draw())
        self.bind("<Button-1>", self._click)
        self.bind("<B1-Motion>", self._drag)
        for key, d in (("<Left>", -1), ("<Down>", -1), ("<Right>", 1), ("<Up>", 1)):
            self.bind(key, lambda e, d=d: self.nudge(d * self.STEP))

    def _snap(self, v):
        v = round(float(v) / self.STEP) * self.STEP
        return round(max(self.LO, min(self.HI, v)), 2)

    def set_value(self, v):
        v = self._snap(v)
        if v != self.value:
            self.value = v
            self.draw()
            if self.on_change:
                self.on_change(v)

    def nudge(self, d):
        self.set_value(self.value + d)

    def _geom(self):
        W = max(self.winfo_width(), 420)
        return W, 64, W - 64, 100            # width, track left, track right, track y

    def _px(self, v):
        W, x1, x2, _ = self._geom()
        return x1 + (x2 - x1) * (v - self.LO) / (self.HI - self.LO)

    def _click(self, e):
        self.focus_set()
        W, x1, x2, ty = self._geom()
        if (e.x - 30) ** 2 + (e.y - ty) ** 2 <= 20 ** 2:
            self.nudge(-self.STEP)
        elif (e.x - (W - 30)) ** 2 + (e.y - ty) ** 2 <= 20 ** 2:
            self.nudge(self.STEP)
        elif x1 - 14 <= e.x <= x2 + 14 and 66 <= e.y <= 134:
            self._drag_ok = True
            self._drag(e)

    def _drag(self, e):
        if not self._drag_ok:
            return
        W, x1, x2, _ = self._geom()
        self.set_value(self.LO + (self.HI - self.LO) * (e.x - x1) / (x2 - x1))

    def _label(self, v):
        return "0.00" if abs(v) < 0.005 else f"{v:+.2f}".replace("-", "\u2212")

    def draw(self):
        self.delete("all")
        W, x1, x2, ty = self._geom()
        v = self.value
        col = self.COOL if v < -0.001 else self.WARM if v > 0.001 else TEXT
        self.create_text(W / 2 - 14, 30, text=self._label(v), fill=col, font=(FONT, 32, "bold"), anchor="e")
        self.create_text(W / 2 - 6, 38, text="D", fill=MUTED, font=(FONT, 14, "bold"), anchor="w")
        meaning = ("no correction needed" if abs(v) < 0.001 else
                   "minus lens: helps near-sighted blur" if v < 0 else "plus lens: helps far-sighted blur")
        self.create_text(W / 2, 64, text=meaning, fill=MUTED, font=(FONT, 10))
        # - and + buttons
        for cx, sym in ((30, "\u2212"), (W - 30, "+")):
            self.create_oval(cx - 18, ty - 18, cx + 18, ty + 18, fill=CARD2, outline=LINE, width=2)
            self.create_text(cx, ty - 1, text=sym, fill=TEXT, font=(FONT, 18, "bold"))
        # track: cool on the minus side, warm on the plus side
        steps = int((x2 - x1) / 4)
        for i in range(steps):
            xa = x1 + i * 4
            f = i / max(steps - 1, 1)
            base = mix(self.COOL, CARD2, min(f * 2, 1)) if f < .5 else mix(CARD2, self.WARM, (f - .5) * 2)
            self.create_rectangle(xa, ty - 5, xa + 4, ty + 5, fill=mix(self.surface, base, .6), outline="")
        x0, xv = self._px(0), self._px(v)
        if abs(xv - x0) > 1:
            self.create_rectangle(min(x0, xv), ty - 5, max(x0, xv), ty + 5, fill=col, outline="")
        # ticks and labels
        for k in range(int(self.LO), int(self.HI) + 1):
            x = self._px(k)
            big = k % 2 == 0
            self.create_line(x, ty + 9, x, ty + (17 if big else 13), fill=MUTED if big else LINE, width=2 if k == 0 else 1)
            if big:
                self.create_text(x, ty + 28, text="0" if k == 0 else (f"+{k}" if k > 0 else f"\u2212{abs(k)}"),
                                 fill=TEXT if k == 0 else MUTED, font=(FONT, 9, "bold" if k == 0 else "normal"))
        # handle
        self.create_oval(xv - 15, ty - 13, xv + 15, ty + 17, fill=mix(self.surface, "#000000", .35), outline="")
        self.create_oval(xv - 14, ty - 15, xv + 14, ty + 13, fill=TEXT, outline=col, width=4)
        self.create_text(W - 70, 146, text="far-sighted (plus)  \u25b6", fill=MUTED, font=(FONT, 9), anchor="e")
        self.create_text(70, 146, text="\u25c0  near-sighted (minus)", fill=MUTED, font=(FONT, 9), anchor="w")


# ------------------------------------------------------------------ segmented control
class Segmented(tk.Canvas):
    """Two or three tabs in a rounded track (used for Log in / Sign up)."""

    def __init__(self, parent, options, value, command, w=400, h=44, surface=BG):
        super().__init__(parent, width=w, height=h, bg=surface, highlightthickness=0, cursor="hand2")
        self.options, self.value, self.cmd, self.w, self.h = options, value, command, w, h
        self.bind("<Button-1>", self._click)
        self.draw()

    def draw(self):
        self.delete("all")
        rrect(self, 1, 1, self.w - 1, self.h - 1, r=self.h // 2, fill=CARD2, outline=LINE)
        seg = (self.w - 8) / len(self.options)
        for i, (key, text) in enumerate(self.options):
            x1, on = 4 + i * seg, key == self.value
            if on:
                rrect(self, x1, 4, x1 + seg, self.h - 4, r=(self.h - 8) // 2, fill=ACCENT, outline="")
            self.create_text(x1 + seg / 2, self.h / 2, text=text, fill=INK if on else MUTED, font=(FONT, 11, "bold"))

    def _click(self, e):
        seg = (self.w - 8) / len(self.options)
        key = self.options[int(max(0, min(len(self.options) - 1, (e.x - 4) // seg)))][0]
        if key != self.value:
            self.value = key
            self.draw()
            self.cmd(key)


# ------------------------------------------------------------------ pop-up windows
class Modal(tk.Toplevel):
    """A borderless pop-up with a dimmed backdrop. Closing it (button, Esc, or code) calls on_close."""

    def __init__(self, app, w, h, border=LINE, on_close=None):
        app.update_idletasks()
        scrim = None
        if sys.platform in ("win32", "darwin"):          # real see-through backdrops only work here
            try:                                         # made BEFORE the pop-up so the pop-up sits above it
                scrim = tk.Toplevel(app)
                scrim.overrideredirect(True)
                scrim.geometry(f"{app.winfo_width()}x{app.winfo_height()}+{app.winfo_rootx()}+{app.winfo_rooty()}")
                scrim.configure(bg="#000000")
                scrim.attributes("-alpha", 0.6)
            except tk.TclError:
                scrim = None
        super().__init__(app)
        self.app, self.on_close_cb, self.alive, self.scrim = app, on_close, True, scrim
        self.overrideredirect(True)
        x = app.winfo_rootx() + max((app.winfo_width() - w) // 2, 0)
        y = app.winfo_rooty() + max((app.winfo_height() - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(bg=border)
        self.body = tk.Frame(self, bg=CARD)
        self.body.pack(fill="both", expand=True, padx=2, pady=2)
        self.bind("<Escape>", lambda e: self.close())
        self.lift()
        if self.scrim is not None:
            try:
                self.lift(self.scrim)                    # make sure the pop-up is above the backdrop
            except tk.TclError:
                pass
        self.focus_force()
        try:
            self.update_idletasks()
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass

    def close(self):
        if not self.alive:
            return
        self.alive = False
        for w in (self.scrim,):
            if w is not None:
                try:
                    w.destroy()
                except tk.TclError:
                    pass
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()
        if self.on_close_cb:
            self.on_close_cb()


# ------------------------------------------------------------------ sign in / sign up screen
class LoginScreen(tk.Frame):
    """Full-window screen shown at launch and after logging out. Covers the whole app."""

    def __init__(self, app, store, on_success, on_guest):
        super().__init__(app, bg=BG)
        self.app, self.store, self.on_success, self.on_guest = app, store, on_success, on_guest
        self.mode, self.claim_name, self.env_choice = "login", "", "Space Station"
        self.user_var, self.t, self.stars = tk.StringVar(), 0.0, []
        self.pw_var = self.pw2_var = self.show_var = None
        self.secret_entries, self.err = [], None
        self.art = tk.Canvas(self, bg=BG, highlightthickness=0, width=540)
        self.art.pack(side="left", fill="y")
        self.art.bind("<Configure>", self._draw_art)
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self.form = tk.Frame(right, bg=BG)
        self.form.place(relx=.5, rely=.5, anchor="center")
        self.build_form()
        self._twinkle()

    # ---------------------------------------------------------- artwork
    def _draw_art(self, e=None):
        c = self.art
        c.delete("all")
        w, h = max(c.winfo_width(), 400), max(c.winfo_height(), 600)
        top, bot = "#130d0a", "#5e3020"
        n = 56
        for i in range(n):
            c.create_rectangle(0, h * i / n, w, h * (i + 1) / n + 1, outline="",
                               fill=mix(top, bot, (i / (n - 1)) ** 1.6))
        rnd = random.Random(11)
        self.stars = []
        for _ in range(80):
            x, y, r = rnd.random() * w, rnd.random() * h * .75, rnd.choice((1, 1, 1.5, 2))
            self.stars.append((c.create_oval(x - r, y - r, x + r, y + r, fill="#ffffff", outline=""),
                               rnd.random() * 6.28))
        # moon
        mx, my = w * .8, h * .17
        c.create_oval(mx - 30, my - 30, mx + 30, my + 30, fill="#f6e7cf", outline="")
        c.create_oval(mx - 9, my - 12, mx + 3, my, fill="#e5d2b4", outline="")
        c.create_oval(mx + 8, my + 8, mx + 20, my + 20, fill="#e5d2b4", outline="")
        # planet rising from the bottom
        cx, cy, R = w * .6, h * 1.05, w * .52
        for k in range(7, 0, -1):
            c.create_oval(cx - R - k * 11, cy - R - k * 11, cx + R + k * 11, cy + R + k * 11, outline="",
                          fill=mix("#4a2518", "#f08a5d", .05 * (8 - k)))
        c.create_oval(cx - R, cy - R, cx + R, cy + R, fill="#d9704a", outline="")
        for d, th, shade in ((-.62, 12, .35), (-.38, 18, .5), (-.12, 10, .3), (.14, 20, .45)):
            dy, hw = R * d, math.sqrt(max(R * R - (R * d) ** 2, 1)) * .97
            c.create_oval(cx - hw, cy + dy - th, cx + hw, cy + dy + th, outline="",
                          fill=mix("#d9704a", "#8e3f28", shade))
        c.create_arc(cx - R, cy - R, cx + R, cy + R, start=95, extent=70, style="arc", outline="#ffb98f", width=6)
        draw_mascot(c, cx - R * .22, cy - R - 58, 1.3, "nova", "cheer")
        # words
        c.create_oval(44, 40, 76, 72, fill="#e07a52", outline=ACCENT2, width=2)
        c.create_oval(34, 50, 86, 62, outline=ACCENT, width=2)
        c.create_text(98, 50, anchor="w", text="ASTRO-VITAL", fill=TEXT, font=(FONT, 16, "bold"))
        c.create_text(98, 70, anchor="w", text="Astronaut Health Companion", fill=MUTED, font=(FONT, 9))
        c.create_text(44, 140, anchor="nw", text="Your health,\nyour mission.", fill=TEXT, font=(HEAD, 34, "bold"))
        c.create_text(44, 236, anchor="nw", width=w - 100, fill=mix(TEXT, MUTED, .35), font=(FONT, 12),
                      text="Two-minute check-ins, quick routines, and a crew that cheers you on.")
        rows = [("xp", "Earn XP for every healthy habit"), ("fire", "Keep your daily streak burning"),
                ("star", "Climb the crew leaderboard")]
        for i, (ic, text) in enumerate(rows):
            y = 316 + i * 46
            c.create_oval(44, y - 17, 78, y + 17, fill=mix("#2a1a12", ACCENT2, .25), outline=ACCENT2, width=1)
            if ic == "fire":
                draw_flame(c, 61, y - 1, 10, "ic")
            else:
                c.create_text(61, y, text="\u2726" if ic == "xp" else "\u2605", fill=ACCENT2, font=(FONT, 14, "bold"))
            c.create_text(92, y, anchor="w", text=text, fill=TEXT, font=(FONT, 12, "bold"))

    def _twinkle(self):
        if self.winfo_ismapped():
            self.t += .12
            for item, ph in self.stars:
                v = (math.sin(self.t + ph * 3) + 1) / 2
                try:
                    self.art.itemconfigure(item, fill=mix("#6d5848", "#fff6e6", v))
                except tk.TclError:
                    return
        self.after(110, self._twinkle)

    # ---------------------------------------------------------- form
    def show(self):
        self.mode = "login" if self.store.real_names() else "signup"
        self.user_var.set(self.store.data.get("last_user", "") if self.mode == "login" else "")
        self.build_form()
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.lift()

    def hide(self):
        self.place_forget()

    def set_mode(self, mode):
        self.mode = mode
        self.build_form()

    def _field(self, label, var, secret=False):
        tk.Label(self.form, text=label, bg=BG, fg=MUTED, font=(FONT, 10, "bold")).pack(anchor="w")
        e = tk.Entry(self.form, textvariable=var, width=36, bg=CARD2, fg=TEXT, insertbackground=TEXT,
                     relief="flat", font=(FONT, 13), highlightthickness=2, highlightbackground=LINE,
                     highlightcolor=ACCENT, show="\u2022" if secret else "")
        e.pack(fill="x", pady=(4, 12), ipady=7)
        e.bind("<Return>", lambda ev: self.submit())
        if secret:
            self.secret_entries.append(e)
        return e

    def build_form(self):
        for w in self.form.winfo_children():
            w.destroy()
        f, mode = self.form, self.mode
        tk.Frame(f, bg=BG, width=400, height=1).pack(anchor="w")      # keeps the form 400 px wide
        self.pw_var, self.pw2_var, self.show_var = tk.StringVar(), tk.StringVar(), tk.BooleanVar(value=False)
        self.secret_entries = []
        head = {"login": ("Welcome back", "Log in to continue your mission."),
                "signup": ("Join the crew", "Create your account. Your data stays on this computer."),
                "claim": ("Secure your profile",
                          f"\u201c{self.claim_name}\u201d was made before accounts existed. "
                          "Choose a password so nobody else can open it.")}[mode]
        tk.Label(f, text=head[0], bg=BG, fg=TEXT, font=(HEAD, 28, "bold")).pack(anchor="w")
        tk.Label(f, text=head[1], bg=BG, fg=MUTED, font=(FONT, 12), wraplength=400, justify="left").pack(
            anchor="w", pady=(4, 18))
        if mode != "claim":
            Segmented(f, [("login", "Log in"), ("signup", "Sign up")], mode, self.set_mode, w=400).pack(
                anchor="w", pady=(0, 20))
            first = self._field("USERNAME", self.user_var)
        else:
            first = None
        pw = self._field("PASSWORD" if mode == "login" else "CHOOSE A PASSWORD", self.pw_var, secret=True)
        if mode != "login":
            self.meter = tk.Canvas(f, width=400, height=22, bg=BG, highlightthickness=0)
            self.meter.pack(anchor="w", pady=(0, 10))
            self.pw_var.trace_add("write", lambda *a: self._draw_meter())
            self._draw_meter()
            self._field("CONFIRM PASSWORD", self.pw2_var, secret=True)
        if mode == "signup":
            tk.Label(f, text="WHERE ARE YOU BASED?", bg=BG, fg=MUTED, font=(FONT, 10, "bold")).pack(anchor="w")
            grid = tk.Frame(f, bg=BG)
            grid.pack(anchor="w", pady=(4, 10))
            self.env_labels = {}
            for i, name in enumerate(ENVS):
                l = tk.Label(grid, text=f"\u25cf  {name}", bg=CARD2, fg=MUTED, font=(FONT, 10, "bold"), width=19,
                             anchor="w", padx=10, pady=7, cursor="hand2", highlightthickness=2,
                             highlightbackground=LINE)
                l.grid(row=i // 2, column=i % 2, padx=(0, 8), pady=(0, 8))
                l.bind("<Button-1>", lambda e, n=name: self._pick_env(n))
                self.env_labels[name] = l
            self._pick_env(self.env_choice)
        tk.Checkbutton(f, text="Show password", variable=self.show_var, command=self._toggle_show, bg=BG, fg=MUTED,
                       selectcolor=CARD2, activebackground=BG, activeforeground=TEXT, bd=0, highlightthickness=0,
                       font=(FONT, 10), cursor="hand2").pack(anchor="w")
        self.err = tk.Label(f, text="", bg=BG, fg=CRIT, font=(FONT, 10, "bold"), wraplength=400, justify="left",
                            anchor="w")
        self.err.pack(anchor="w", pady=(8, 8), fill="x")
        label = {"login": "Log in  \u203a", "signup": "Create account  \u203a", "claim": "Set password  \u203a"}[mode]
        Pill(f, label, self.submit, w=400, h=50, surface=BG, size=12).pack(anchor="w")
        if mode != "claim":
            Pill(f, "Continue as guest", self.on_guest, w=400, h=44, ghost=True, surface=BG, size=11).pack(
                anchor="w", pady=(10, 0))
            tk.Label(f, text="Try everything first. We'll only ask you to sign up if you want to keep your progress.",
                     bg=BG, fg=MUTED, font=(FONT, 9), wraplength=400, justify="left").pack(anchor="w", pady=(6, 0))
        if mode == "claim":
            back = tk.Label(f, text="\u2039 Back to log in", bg=BG, fg=MUTED, font=(FONT, 10, "bold"), cursor="hand2")
            back.pack(anchor="w", pady=(14, 0))
            back.bind("<Button-1>", lambda e: self.set_mode("login"))
        tk.Label(f, text="Passwords are salted and hashed on this computer. Nothing is sent anywhere.", bg=BG,
                 fg=mix(MUTED, BG, .35), font=(FONT, 9), wraplength=400, justify="left").pack(anchor="w", pady=(16, 0))
        if mode != "claim":
            wipe = tk.Label(f, text="Forgot a password, or want a clean start?  Erase all data", bg=BG, fg=MUTED,
                            font=(FONT, 9, "underline"), cursor="hand2")
            wipe.pack(anchor="w", pady=(6, 0))
            wipe.bind("<Button-1>", lambda e: self.app.reset_all_dialog())
            wipe.bind("<Enter>", lambda e: wipe.config(fg=CRIT))
            wipe.bind("<Leave>", lambda e: wipe.config(fg=MUTED))
        target = first if first is not None else pw
        if mode == "login" and self.user_var.get().strip():
            target = pw
        self.after(60, target.focus_set)

    def _pick_env(self, name):
        self.env_choice = name
        for n, l in self.env_labels.items():
            on = n == name
            col = ENVS[n]["color"]
            l.config(bg=mix(CARD2, col, .25) if on else CARD2, fg=TEXT if on else MUTED,
                     highlightbackground=col if on else LINE)

    def _toggle_show(self):
        for e in self.secret_entries:
            e.config(show="" if self.show_var.get() else "\u2022")

    def _draw_meter(self):
        c, pw = self.meter, self.pw_var.get()
        c.delete("all")
        s = max(password_strength(pw), 1) if pw else 0
        col = [CARD2, CRIT, WATCH, ACCENT, GOOD][s]
        for i in range(4):
            rrect(c, i * 62, 4, i * 62 + 56, 12, r=4, fill=col if i < s else CARD2, outline="")
        c.create_text(256, 8, anchor="w", fill=MUTED, font=(FONT, 9, "bold"),
                      text=["8+ characters, a letter and a number", "Weak", "Okay", "Good", "Strong"][s])

    def say(self, text, color=CRIT):
        if self.err is not None:
            self.err.config(text=text, fg=color)
            self.err.update_idletasks()

    def submit(self):
        u, pw, mode = self.user_var.get().strip(), self.pw_var.get(), self.mode
        if mode == "login":
            if not u or not pw:
                return self.say("Enter your username and password.")
            self.say("Checking\u2026", MUTED)
            st, val = self.store.log_in(u, pw)
            if st == "ok":
                return self._done(val)
            if st == "locked":
                return self.say(f"Too many tries. Please wait {val} seconds and try again.")
            if st == "claim":
                self.claim_name = val
                self.mode = "claim"
                self.build_form()
                return self.say("Set a password to protect this profile.", ACCENT)
            return self.say("That username and password don't match.")
        if pw != self.pw2_var.get():
            return self.say("The two passwords don't match.")
        self.say("Creating your account\u2026", MUTED)
        if mode == "signup":
            st, val = self.store.sign_up(u, pw, self.env_choice)
        else:
            st, val = self.store.claim(self.claim_name, pw)
        if st == "ok":
            return self._done(val)
        self.say(val)

    def _done(self, name):
        self.pw_var.set("")
        self.pw2_var.set("")
        self.on_success(name)


class OptionCard(tk.Canvas):
    """Big tappable answer card with a severity meter."""

    def __init__(self, parent, idx, text, command, selected=False, surface=CARD):
        super().__init__(parent, width=196, height=126, bg=surface, highlightthickness=0, cursor="hand2")
        self.idx, self.text, self.cmd, self.sel = idx, text, command, selected
        self.color = SEV_COLORS[idx]
        self.draw(False)
        self.bind("<Enter>", lambda e: self.draw(True))
        self.bind("<Leave>", lambda e: self.draw(False))
        self.bind("<Button-1>", lambda e: self.cmd(self.idx))

    def set_selected(self, v):
        self.sel = v
        self.draw(False)

    def draw(self, hover):
        self.delete("all")
        fill = mix(CARD2, "#ffffff", 0.07) if hover else CARD2
        outline = self.color if self.sel else (ACCENT if hover else LINE)
        rrect(self, 3, 3, 193, 123, r=18, fill=fill, outline=outline, width=3 if self.sel else 1)
        for i in range(3):
            x = 70 + i * 28
            filled = i < self.idx
            self.create_oval(x - 8, 20, x + 8, 36, fill=self.color if filled else CARD2,
                             outline=self.color if filled else LINE, width=2)
        self.create_text(98, 80, text=self.text, fill=TEXT, font=(FONT, 12, "bold"), width=164, justify="center")
        if self.sel:
            self.create_oval(168, 10, 186, 28, fill=self.color, outline="")
            self.create_text(177, 19, text="✓", fill=INK, font=(FONT, 9, "bold"))


class Chip(tk.Canvas):
    """Toggle chip."""

    def __init__(self, parent, text, color, on_toggle=None, selected=False, surface=BG):
        w = int(len(text) * 7.8) + 58
        super().__init__(parent, width=w, height=38, bg=surface, highlightthickness=0, cursor="hand2")
        self.text, self.color, self.on_toggle = text, color, on_toggle
        self.sel, self.surface, self.w = selected, surface, w
        self.draw()
        self.bind("<Button-1>", self._click)

    def _click(self, e=None):
        self.sel = not self.sel
        self.draw()
        if self.on_toggle:
            self.on_toggle(self.sel)

    def draw(self):
        self.delete("all")
        fill = mix(self.surface, self.color, 0.28) if self.sel else CARD2
        rrect(self, 1, 1, self.w - 1, 37, r=18, fill=fill, outline=self.color if self.sel else LINE, width=2)
        self.create_oval(14, 13, 26, 25, fill=self.color if self.sel else CARD2, outline=self.color, width=2)
        self.create_text(36, 19, anchor="w", text=self.text, fill=TEXT if self.sel else MUTED,
                         font=(FONT, 11, "bold" if self.sel else "normal"))


class ListMenu(tk.Frame):
    """Simple modern vertical list with optional colored dots."""

    def __init__(self, parent, on_select, surface=CARD, pady=9):
        super().__init__(parent, bg=surface)
        self.on_select, self.surface, self.pady = on_select, surface, pady
        self.items, self.labels, self.sel = [], [], None

    def set_items(self, items, selected=0):
        for l in self.labels:
            l.destroy()
        self.labels, self.items, self.sel = [], list(items), None
        for i, t in enumerate(self.items):
            l = tk.Label(self, text=t, bg=self.surface, fg=MUTED, font=(FONT, 11), anchor="w",
                         padx=14, pady=self.pady, cursor="hand2")
            l.pack(fill="x", pady=1)
            l.bind("<Button-1>", lambda e, i=i: self.select(i, True))
            l.bind("<Enter>", lambda e, i=i: self._hover(i, True))
            l.bind("<Leave>", lambda e, i=i: self._hover(i, False))
            self.labels.append(l)
        if self.items and selected is not None:
            self.select(selected, False)

    def _hover(self, i, on):
        if i != self.sel and i < len(self.labels):
            self.labels[i].config(bg=mix(self.surface, CARD2, 0.6) if on else self.surface)

    def select(self, i, fire=True):
        self.sel = i
        for j, l in enumerate(self.labels):
            l.config(bg=CARD2 if j == i else self.surface, fg=TEXT if j == i else MUTED,
                     font=(FONT, 11, "bold" if j == i else "normal"))
        if fire:
            self.on_select(i)

    def rename(self, i, text):
        if 0 <= i < len(self.labels):
            self.labels[i].config(text=text)


class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")


# ------------------------------------------------------------------ drawing helpers
def draw_icon(c, domain, x, y, s, color, cut, tag):
    """Tiny vector icon for each health area."""
    if domain == IMMUNE:
        c.create_polygon(x - s, y - s * .8, x + s, y - s * .8, x + s, y, x, y + s, x - s, y,
                         fill=color, outline="", tags=tag)
        c.create_line(x - s * .4, y - s * .05, x - s * .05, y + s * .3, x + s * .5, y - s * .4,
                      fill=cut, width=3, tags=tag)
    elif domain == BONE:
        c.create_line(x - s * .7, y + s * .7, x + s * .7, y - s * .7, fill=color, width=s * .5,
                      capstyle="round", tags=tag)
        for dx, dy in ((-.95, .45), (-.45, .95), (.95, -.45), (.45, -.95)):
            r = s * .32
            c.create_oval(x + dx * s - r, y + dy * s - r, x + dx * s + r, y + dy * s + r,
                          fill=color, outline="", tags=tag)
    elif domain == HEART:
        r = s * .55
        c.create_oval(x - s * .95, y - s * .85, x - s * .95 + 2 * r + s * .3, y - s * .85 + 2 * r + s * .3,
                      fill=color, outline="", tags=tag)
        c.create_oval(x + s * .95 - 2 * r - s * .3, y - s * .85, x + s * .95, y - s * .85 + 2 * r + s * .3,
                      fill=color, outline="", tags=tag)
        c.create_polygon(x - s * .98, y - s * .05, x + s * .98, y - s * .05, x, y + s * 1.0,
                         fill=color, outline="", tags=tag)
    elif domain == MIND:
        c.create_oval(x - s, y - s, x + s, y + s, fill=color, outline="", tags=tag)
        c.create_oval(x - s * .45, y - s * .35, x - s * .2, y - s * .1, fill=cut, outline="", tags=tag)
        c.create_oval(x + s * .2, y - s * .35, x + s * .45, y - s * .1, fill=cut, outline="", tags=tag)
        c.create_arc(x - s * .55, y - s * .3, x + s * .55, y + s * .6, start=200, extent=140,
                     style="arc", outline=cut, width=3, tags=tag)
    else:
        c.create_oval(x - s, y - s, x + s, y + s, fill=color, outline="", tags=tag)
        c.create_oval(x - s * .3, y - s * 1.15, x + s * 1.5, y + s * .75, fill=cut, outline="", tags=tag)


def draw_flame(c, x, y, s, tag, hot=True):
    """Streak flame. 'hot' False draws a cold grey one."""
    c1, c2 = ("#ff6a1a", "#ffb52e") if hot else ("#4a3d33", "#6a5a4b")
    pts = [x, y - s, x + s * .55, y - s * .15, x + s * .62, y + s * .35, x + s * .3, y + s * .85,
           x - s * .3, y + s * .85, x - s * .62, y + s * .35, x - s * .5, y - s * .1,
           x - s * .15, y + s * .05, x - s * .1, y - s * .5]
    c.create_polygon(pts, smooth=True, fill=c1, outline="", tags=tag)
    k = .55
    pts2 = [x, y - s * .2 * k + s * .1, x + s * .5 * k, y + s * .25, x + s * .45 * k, y + s * .62,
            x, y + s * .78, x - s * .45 * k, y + s * .62, x - s * .5 * k, y + s * .25]
    c.create_polygon(pts2, smooth=True, fill=c2, outline="", tags=tag)


def draw_xp_bar(c, x1, y1, x2, y2, frac, c1, c2, tag):
    """Segmented gradient progress bar with quarter ticks and round caps."""
    frac = max(0.0, min(1.0, frac))
    rrect(c, x1, y1, x2, y2, r=(y2 - y1) / 2, fill=CARD2, outline=LINE, tags=tag)
    inset = 3
    fx = x1 + (x2 - x1) * frac
    r = (y2 - y1) / 2 - inset
    if frac > 0.01:
        n = max(1, int((fx - x1 - 2 * inset) / 4))
        for i in range(n):
            xa = x1 + inset + i * 4
            xb = min(xa + 4, fx - inset)
            col = mix(c1, c2, i / max(n - 1, 1))
            c.create_rectangle(xa, y1 + inset, xb, y2 - inset, fill=col, outline=col, tags=tag)
        c.create_oval(x1 + inset, y1 + inset, x1 + inset + 2 * r, y2 - inset, fill=c1, outline="", tags=tag)
        c.create_oval(fx - inset - 2 * r, y1 + inset, fx - inset, y2 - inset, fill=c2, outline="", tags=tag)
    for q in (.25, .5, .75):
        x = x1 + (x2 - x1) * q
        c.create_line(x, y1 + 5, x, y2 - 5, fill=mix(CARD2, BG, 0.55), tags=tag)
    return fx


def draw_medal(c, x, y, r, rank, tag):
    cols = {1: "#f4cf5e", 2: "#d9d3ca", 3: "#d99a6c"}
    col = cols.get(rank, CARD2)
    c.create_oval(x - r, y - r, x + r, y + r, fill=col, outline="", tags=tag)
    c.create_text(x, y, text=str(rank), fill=INK if rank in cols else MUTED,
                  font=(FONT, int(r * .9), "bold"), tags=tag)


def draw_avatar(c, x, y, r, name, color, tag, ring=False):
    if ring:
        c.create_oval(x - r - 5, y - r - 5, x + r + 5, y + r + 5, outline="#f4cf5e", width=3, tags=tag)
    c.create_oval(x - r, y - r, x + r, y + r, fill=mix(CARD, color, 0.35), outline=color, width=2, tags=tag)
    c.create_text(x, y, text=(name[:1] or "?").upper(), fill=TEXT, font=(FONT, int(r * .85), "bold"), tags=tag)


HEAD = "Georgia"          # warm serif for headlines, so it feels written by a person, not a template


def draw_shield(c, x, y, s, color, tag="", fill=None):
    """Small shield (Streak Shield). s is roughly the half-width."""
    pts = [x - s, y - s * .9, x, y - s * 1.15, x + s, y - s * .9, x + s, y + s * .1, x, y + s * 1.2, x - s, y + s * .1]
    c.create_polygon(pts, fill=fill or mix(CARD, color, .4), outline=color, width=2, smooth=False, tags=tag)
    c.create_line(x, y - s * .55, x, y + s * .6, fill=color, width=2, tags=tag)
    c.create_line(x - s * .45, y - s * .05, x + s * .45, y - s * .05, fill=color, width=2, tags=tag)


def draw_mascot(c, x, y, s=1.0, tag="mascot", mood="happy", scarf=False):
    """Nova, the crew's little astronaut. Moods: happy, cheer, worried, sleepy."""
    R = 26 * s
    cream, shade = "#f8efe3", "#d9c9b3"
    # body and arms
    c.create_oval(x - 30 * s, y + R - 2 * s, x - 18 * s, y + R + 16 * s, fill=ACCENT, outline="", tags=tag)
    c.create_oval(x + 18 * s, y + R - 2 * s, x + 30 * s, y + R + 16 * s, fill=ACCENT, outline="", tags=tag)
    rrect(c, x - 19 * s, y + R - 8 * s, x + 19 * s, y + R + 28 * s, r=int(12 * s), fill=ACCENT, outline="", tags=tag)
    c.create_oval(x - 5 * s, y + R + 6 * s, x + 5 * s, y + R + 16 * s, fill=ACCENT2, outline="", tags=tag)
    if scarf:
        rrect(c, x - 21 * s, y + R - 9 * s, x + 21 * s, y + R + 2 * s, r=int(5 * s), fill="#f27b8f", outline="", tags=tag)
        rrect(c, x + 8 * s, y + R, x + 17 * s, y + R + 22 * s, r=int(4 * s), fill="#e0617a", outline="", tags=tag)
    # antenna
    c.create_line(x, y - R, x + 5 * s, y - R - 13 * s, fill=shade, width=max(int(2 * s), 1), tags=tag)
    c.create_oval(x + 1 * s, y - R - 19 * s, x + 11 * s, y - R - 9 * s, fill=ACCENT2, outline="", tags=tag)
    # helmet and visor
    c.create_oval(x - R, y - R, x + R, y + R, fill=cream, outline=shade, width=max(int(2 * s), 1), tags=tag)
    c.create_oval(x - 18 * s, y - 14 * s, x + 18 * s, y + 15 * s, fill="#2a1f18", outline="", tags=tag)
    c.create_arc(x - 15 * s, y - 12 * s, x + 3 * s, y + 2 * s, start=95, extent=70, style="arc",
                 outline="#6a5a4b", width=max(int(2 * s), 1), tags=tag)
    ex, ey, er = 7 * s, -2 * s, 3 * s
    if mood == "cheer":
        for sx in (-1, 1):
            c.create_arc(x + sx * ex - 4 * s, y + ey - 3 * s, x + sx * ex + 4 * s, y + ey + 5 * s, start=0, extent=180,
                         style="arc", outline=cream, width=max(int(2 * s), 1), tags=tag)
        c.create_oval(x - 5 * s, y + 4 * s, x + 5 * s, y + 12 * s, fill="#f27b8f", outline="", tags=tag)
    elif mood == "sleepy":
        for sx in (-1, 1):
            c.create_line(x + sx * ex - 4 * s, y + ey + s, x + sx * ex + 4 * s, y + ey + s, fill=cream,
                          width=max(int(2 * s), 1), tags=tag)
        c.create_oval(x - 3 * s, y + 6 * s, x + 3 * s, y + 11 * s, fill=cream, outline="", tags=tag)
    else:
        for sx in (-1, 1):
            c.create_oval(x + sx * ex - er, y + ey - er, x + sx * ex + er, y + ey + er, fill=cream, outline="", tags=tag)
        if mood == "worried":
            c.create_line(x - ex - 5 * s, y - 9 * s, x - ex + 4 * s, y - 6 * s, fill=cream, width=max(int(2 * s), 1), tags=tag)
            c.create_line(x + ex + 5 * s, y - 9 * s, x + ex - 4 * s, y - 6 * s, fill=cream, width=max(int(2 * s), 1), tags=tag)
            c.create_arc(x - 5 * s, y + 7 * s, x + 5 * s, y + 15 * s, start=20, extent=140, style="arc", outline=cream,
                         width=max(int(2 * s), 1), tags=tag)
        else:
            c.create_arc(x - 6 * s, y + 1 * s, x + 6 * s, y + 12 * s, start=200, extent=140, style="arc", outline=cream,
                         width=max(int(2 * s), 1), tags=tag)


##############################################################################
# SECTION: animations
# animations.py - the "show me how" panel on the Exercise page.
#
# A small side-view figure is built from joint angles (forward kinematics) and
# animated between two poses. Cycling and running use inverse kinematics.
# Breathing, relaxation, Earth-gazing and neck exercises have their own scenes.
##############################################################################

# kind -> (title, seconds per cycle, (first half label, second half label), cues)
KINDS = {
    "squat": ("Squat", 4.0, ("Lower down", "Stand up"),
              ["Chest up, knees over your toes", "Push through your heels", "Breathe out as you stand"]),
    "deadlift": ("Hip hinge / deadlift", 4.0, ("Hinge back", "Stand tall"),
                 ["Push your hips back", "Keep your back flat", "Squeeze your glutes at the top"]),
    "press": ("Overhead press", 3.5, ("Press up", "Lower slowly"),
              ["Brace your core", "Press straight up", "Control the way down"]),
    "heel": ("Heel raise", 3.0, ("Rise up", "Lower slowly"),
             ["Rise as high as you can", "Pause for one second", "Lower with control"]),
    "reach": ("Reach and stretch", 6.0, ("Reach", "Return"),
              ["Breathe in as you reach", "Lengthen your spine", "Relax your shoulders"]),
    "run": ("Treadmill run", 1.0, ("", ""),
            ["Light, quick steps", "Keep your torso tall", "Swing your arms, relax your hands"]),
    "bike": ("Cycle ergometer", 2.0, ("", ""),
             ["Smooth circles", "Relax your shoulders", "Keep breathing steadily"]),
    "box": ("Box breathing", 16.0, ("", ""), ["In for 4, hold for 4", "Out for 4, hold for 4"]),
    "calm": ("Calm breathing", 10.0, ("", ""), ["In for 5 seconds", "Out for 5 seconds"]),
    "relax": ("Muscle relaxation", 10.0, ("", ""), ["Tense one muscle group", "Then let it go completely"]),
    "earth": ("Earth gazing", 30.0, ("", ""), ["Name 5 things you can see", "Name 4 things you can feel"]),
    "neck": ("Neck and gaze steadying", 8.0, ("", ""), ["Turn your head slowly", "Keep your eyes on the dot"]),
}


def kind_for(name):
    n = name.lower()
    if "box" in n:
        return "box"
    if "relax" in n:
        return "relax"
    if "earth" in n:
        return "earth"
    if "neck" in n or "gaze" in n:
        return "neck"
    if "breath" in n:
        return "calm"
    if "cycl" in n or "ergometer" in n or "interval" in n:
        return "bike"
    if "treadmill" in n or "run" in n or "walk" in n:
        return "run"
    if "squat" in n:
        return "squat"
    if "deadlift" in n:
        return "deadlift"
    if "heel" in n:
        return "heel"
    if "press" in n or "row" in n:
        return "press"
    return "reach"


# pose = angles in degrees. t: torso lean from vertical (forward +).
# tn/sn: near thigh / shin, tf/sf: far thigh / shin, un/fn: near upper arm / forearm, uf/ff: far arm.
# Limb angles are measured from straight down, toward the front.
POSES = {
    "squat": (dict(t=0, tn=0, sn=0, tf=0, sf=0, un=75, fn=80, uf=75, ff=80, lift=0),
              dict(t=28, tn=82, sn=-22, tf=82, sf=-22, un=80, fn=85, uf=80, ff=85, lift=0)),
    "deadlift": (dict(t=0, tn=0, sn=0, tf=0, sf=0, un=4, fn=4, uf=4, ff=4, lift=0),
                 dict(t=75, tn=25, sn=-8, tf=25, sf=-8, un=0, fn=0, uf=0, ff=0, lift=0)),
    "press": (dict(t=0, tn=0, sn=0, tf=0, sf=0, un=25, fn=165, uf=25, ff=165, lift=0),
              dict(t=0, tn=0, sn=0, tf=0, sf=0, un=172, fn=178, uf=172, ff=178, lift=0)),
    "heel": (dict(t=0, tn=0, sn=0, tf=0, sf=0, un=3, fn=6, uf=3, ff=6, lift=0),
             dict(t=0, tn=0, sn=0, tf=0, sf=0, un=3, fn=6, uf=3, ff=6, lift=14)),
    "reach": (dict(t=-12, tn=0, sn=0, tf=0, sf=0, un=172, fn=178, uf=172, ff=178, lift=0),
              dict(t=14, tn=0, sn=0, tf=0, sf=0, un=172, fn=178, uf=172, ff=178, lift=0)),
}

NEAR = ACCENT
FAR = mix(ACCENT, CARD2, 0.55)


def smooth(t):
    return t * t * (3 - 2 * t)


def ik(a, b, l1, l2, forward=True):
    """Two-bone inverse kinematics. Returns the middle joint (knee or elbow)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = max(1e-6, min(math.hypot(dx, dy), l1 + l2 - 0.5))
    ang = math.atan2(dy, dx)
    cosv = max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))
    a1 = math.acos(cosv)
    c1 = (a[0] + l1 * math.cos(ang + a1), a[1] + l1 * math.sin(ang + a1))
    c2 = (a[0] + l1 * math.cos(ang - a1), a[1] + l1 * math.sin(ang - a1))
    if forward:
        return c1 if c1[0] > c2[0] else c2
    return c1 if c1[1] > c2[1] else c2


class Demonstrator(tk.Canvas):
    LEG, TORSO, HEAD, ARM = 40, 54, 11, 27

    def __init__(self, parent, w=310, h=270):
        super().__init__(parent, width=w, height=h, bg=CARD, highlightthickness=0)
        self.w, self.h = w, h
        self.kind, self.t0, self.job, self.running = "reach", time.time(), None, False
        self.ground = h - 52

    def set_kind(self, kind):
        self.kind = kind if kind in KINDS else "reach"
        self.t0 = time.time()

    def start(self):
        if not self.running:
            self.running = True
            self._loop()

    def stop(self):
        self.running = False
        if self.job:
            self.after_cancel(self.job)
            self.job = None

    def _loop(self):
        if not self.running:
            return
        try:
            self.draw(time.time() - self.t0)
        except tk.TclError:
            return
        self.job = self.after(40, self._loop)

    # ------------------------------------------------------------ figure helpers
    def _pt(self, o, L, ang):
        r = math.radians(ang)
        return (o[0] + L * math.sin(r), o[1] + L * math.cos(r))

    def _limbs(self, hip, p, dx_far=0):
        L, T, H, A = self.LEG, self.TORSO, self.HEAD, self.ARM
        tr = math.radians(p["t"])
        neck = (hip[0] + T * math.sin(tr), hip[1] - T * math.cos(tr))
        head = (neck[0] + (H + 6) * math.sin(tr), neck[1] - (H + 6) * math.cos(tr))
        kn = self._pt(hip, L, p["tn"])
        an = self._pt(kn, L, p["sn"])
        kf = self._pt(hip, L, p["tf"])
        af = self._pt(kf, L, p["sf"])
        en = self._pt(neck, A, p["un"])
        wn = self._pt(en, A, p["fn"])
        ef = self._pt(neck, A, p["uf"])
        wf = self._pt(ef, A, p["ff"])
        g = self.ground
        return dict(hip=hip, neck=neck, head=head, kn=kn, an=an, tn=(an[0] + 16, g),
                    kf=kf, af=af, tf=(af[0] + 16, g), en=en, wn=wn, ef=ef, wf=wf)

    def _draw_figure(self, j, dx_far=-7, props=None):
        def far(pt):
            return (pt[0] + dx_far, pt[1])
        w = 7
        kw = dict(width=w, capstyle="round", joinstyle="round")
        self.create_line(j["hip"], far(j["kf"]), far(j["af"]), far(j["tf"]), fill=FAR, **kw)
        self.create_line(j["neck"], far(j["ef"]), far(j["wf"]), fill=FAR, **kw)
        self.create_line(j["hip"], j["neck"], fill=NEAR, **kw)
        self.create_line(j["hip"], j["kn"], j["an"], j["tn"], fill=NEAR, **kw)
        self.create_line(j["neck"], j["en"], j["wn"], fill=NEAR, **kw)
        x, y = j["head"]
        self.create_oval(x - 12, y - 12, x + 12, y + 12, fill=NEAR, outline="")
        for k in ("kn", "en"):
            px, py = j[k]
            self.create_oval(px - 4, py - 4, px + 4, py + 4, fill=CARD, outline="")
        if props == "plate":
            px, py = j["wn"]
            self.create_oval(px - 12, py - 12, px + 12, py + 12, outline=CAUTION, width=4)
            self.create_oval(px - 3, py - 3, px + 3, py + 3, fill=CAUTION, outline="")

    # ------------------------------------------------------------ scenes
    def draw(self, t):
        self.delete("all")
        rrect(self, 2, 2, self.w - 2, self.h - 2, r=20, fill=CARD, outline=LINE)
        title, period, labels, cues = KINDS[self.kind]
        self.create_text(18, 22, anchor="w", text=title.upper(), fill=MUTED, font=(FONT, 10, "bold"))
        scene = getattr(self, "_scene_" + self.kind, None)
        phase_label = ""
        if self.kind in POSES:
            u = (t % period) / period
            s = 0.5 - 0.5 * math.cos(2 * math.pi * u)
            phase_label = labels[0] if u < 0.5 else labels[1]
            self._scene_pose(s)
        elif scene:
            phase_label = scene(t) or ""
        if phase_label:
            self.create_text(self.w - 18, 22, anchor="e", text=phase_label, fill=ACCENT, font=(FONT, 12, "bold"))
        cue = cues[int(t // 4) % len(cues)]
        self.create_text(self.w / 2, self.h - 22, text=cue, fill=TEXT, font=(FONT, 11), width=self.w - 40)

    def _scene_pose(self, s):
        a, b = POSES[self.kind]
        s = smooth(s)
        p = {k: a[k] + (b[k] - a[k]) * s for k in a}
        g, L = self.ground, self.LEG
        ANK = 6
        ax = self.w / 2 - 6
        ox = L * math.sin(math.radians(p["tn"])) + L * math.sin(math.radians(p["sn"]))
        oy = L * math.cos(math.radians(p["tn"])) + L * math.cos(math.radians(p["sn"]))
        hip = (ax - ox, g - ANK - p["lift"] - oy)
        self.create_line(30, g, self.w - 30, g, fill=LINE, width=3, capstyle="round")
        j = self._limbs(hip, p)
        self._draw_figure(j, props="plate" if self.kind in ("deadlift", "press") else None)

    def _scene_run(self, t):
        g = self.ground
        hip = (self.w / 2 - 6, g - 76)
        self.create_line(30, g, self.w - 30, g, fill=LINE, width=3)
        for i in range(-1, 10):
            x = 30 + ((i * 36 - (t * 140) % 36) % (self.w - 60))
            self.create_line(x, g + 8, x + 16, g + 8, fill=mix(CARD, LINE, .8), width=3)
        th = t * 2 * math.pi / KINDS["run"][1]
        pts = []
        for k in (0, math.pi):
            a = th + k
            lift = 26 * max(0, -math.sin(a))
            pts.append((hip[0] + 34 * math.cos(a), g - 4 - lift))
        tr = math.radians(8)
        neck = (hip[0] + self.TORSO * math.sin(tr), hip[1] - self.TORSO * math.cos(tr))
        head = (neck[0] + 18 * math.sin(tr), neck[1] - 18 * math.cos(tr))
        kw = dict(width=7, capstyle="round", joinstyle="round")
        far_k, near_k = ik(hip, pts[1], self.LEG, self.LEG), ik(hip, pts[0], self.LEG, self.LEG)
        self.create_line(hip, far_k, pts[1], (pts[1][0] + 14, g), fill=FAR, **kw)
        sw = 40 * math.sin(th)
        ef, wf = self._pt(neck, self.ARM, 30 + sw), None
        wf = self._pt(ef, self.ARM, 100 + sw)
        en = self._pt(neck, self.ARM, 30 - sw)
        wn = self._pt(en, self.ARM, 100 - sw)
        self.create_line(neck, ef, wf, fill=FAR, **kw)
        self.create_line(hip, neck, fill=NEAR, **kw)
        self.create_line(hip, near_k, pts[0], (pts[0][0] + 14, g), fill=NEAR, **kw)
        self.create_line(neck, en, wn, fill=NEAR, **kw)
        self.create_oval(head[0] - 12, head[1] - 12, head[0] + 12, head[1] + 12, fill=NEAR, outline="")
        return ""

    def _scene_bike(self, t):
        g = self.ground
        hip = (self.w / 2 - 40, g - 76)
        th = t * 2 * math.pi / KINDS["bike"][1]
        crank = (hip[0] + 36, hip[1] + 56)
        kw = dict(width=7, capstyle="round", joinstyle="round")
        self.create_oval(crank[0] - 40, crank[1] - 40, crank[0] + 40, crank[1] + 40, outline=mix(CARD, LINE, .8), width=3)
        self.create_line(hip[0] - 8, hip[1] + 8, crank, fill=LINE, width=4)
        bar = (hip[0] + 76, hip[1] - 22)
        self.create_line(crank, bar, fill=LINE, width=4)
        self.create_line(hip[0] - 22, hip[1] + 6, hip[0] + 6, hip[1] + 6, fill=LINE, width=5, capstyle="round")
        feet = [(crank[0] + 18 * math.cos(th + k), crank[1] + 18 * math.sin(th + k)) for k in (0, math.pi)]
        tr = math.radians(32)
        neck = (hip[0] + self.TORSO * math.sin(tr), hip[1] - self.TORSO * math.cos(tr))
        head = (neck[0] + 18 * math.sin(tr), neck[1] - 18 * math.cos(tr))
        elbow = ik(neck, bar, self.ARM, self.ARM, forward=False)
        kf = ik(hip, feet[1], self.LEG, self.LEG)
        kn = ik(hip, feet[0], self.LEG, self.LEG)
        self.create_line(hip, kf, feet[1], fill=FAR, **kw)
        self.create_line(hip, neck, fill=NEAR, **kw)
        self.create_line(hip, kn, feet[0], fill=NEAR, **kw)
        self.create_line(neck, elbow, bar, fill=NEAR, **kw)
        self.create_oval(head[0] - 12, head[1] - 12, head[0] + 12, head[1] + 12, fill=NEAR, outline="")
        return ""

    def _breath(self, t, period, phases, colors, base=34, grow=44):
        """Generic breathing circle. phases = list of (seconds, label, start_r, end_r)."""
        tt = t % period
        acc = 0
        for sec, label, r0, r1 in phases:
            if tt < acc + sec:
                f = smooth((tt - acc) / sec)
                r = base + grow * (r0 + (r1 - r0) * f)
                left = int(math.ceil(acc + sec - tt))
                break
            acc += sec
        cx, cy = self.w / 2, self.h / 2 - 8
        col = colors.get(label, ACCENT)
        for k, a in ((18, .08), (10, .16)):
            self.create_oval(cx - r - k, cy - r - k, cx + r + k, cy + r + k, fill=mix(CARD, col, a), outline="")
        self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=mix(CARD, col, .45), outline=col, width=3)
        self.create_text(cx, cy - 8, text=label, fill=TEXT, font=(FONT, 17, "bold"))
        self.create_text(cx, cy + 18, text=str(left), fill=TEXT, font=(FONT, 15))
        return ""

    def _scene_box(self, t):
        ph = [(4, "Breathe in", 0, 1), (4, "Hold", 1, 1), (4, "Breathe out", 1, 0), (4, "Hold", 0, 0)]
        return self._breath(t, 16, ph, {"Breathe in": ACCENT, "Hold": WATCH, "Breathe out": GOOD})

    def _scene_calm(self, t):
        ph = [(5, "Breathe in", 0, 1), (5, "Breathe out", 1, 0)]
        return self._breath(t, 10, ph, {"Breathe in": ACCENT, "Breathe out": GOOD})

    def _scene_relax(self, t):
        ph = [(5, "Tense", 0.35, 0.1), (5, "Let go", 0.1, 1)]
        return self._breath(t, 10, ph, {"Tense": CRIT, "Let go": GOOD})

    def _scene_earth(self, t):
        w, h = self.w, self.h
        x1, y1, x2, y2 = 24, 40, w - 24, h - 48
        self.create_rectangle(x1, y1, x2, y2, fill="#0d0907", outline=LINE, width=3)
        for i in range(36):
            sx = x1 + 6 + (i * 53) % (x2 - x1 - 12)
            sy = y1 + 6 + (i * 29) % ((y2 - y1) // 2)
            tw = 0.5 + 0.5 * math.sin(t * 2 + i)
            self.create_oval(sx, sy, sx + 2, sy + 2, fill=mix("#0d0907", "#ffffff", 0.3 + 0.6 * tw), outline="")
        cx, cy, R = (x1 + x2) / 2, y2 + 150, 230
        self.create_oval(cx - R - 8, cy - R - 8, cx + R + 8, cy + R + 8, fill="#16356b", outline="")
        self.create_oval(cx - R, cy - R, cx + R, cy + R, fill="#1c4fa8", outline="")
        for i in range(5):
            px = x1 + ((i * 97 + t * 14) % (x2 - x1 + 60)) - 30
            py = y2 - 36 - (i % 3) * 14
            self.create_oval(px - 30, py - 6, px + 30, py + 6, fill=mix("#1c4fa8", "#ffffff", .75), outline="")
        self.create_rectangle(x1 - 3, y2, x2 + 3, y2 + 40, fill=CARD, outline="")
        self.create_rectangle(x1, y1, x2, y2, outline=LINE, width=3)
        return ""

    def _scene_neck(self, t):
        cx, cy = self.w / 2, self.h / 2 + 4
        turn = math.sin(t * 2 * math.pi / KINDS["neck"][1])
        self.create_line(cx - 62, cy + 62, cx - 40, cy + 40, cx + 40, cy + 40, cx + 62, cy + 62,
                         fill=FAR, width=9, capstyle="round", joinstyle="round", smooth=True)
        self.create_line(cx, cy + 40, cx, cy + 18, fill=FAR, width=9, capstyle="round")
        hx = cx + 12 * turn
        self.create_oval(hx - 30, cy - 46, hx + 30, cy + 18, fill=NEAR, outline="")
        for ex in (-11, 11):
            ey = cy - 18
            self.create_oval(hx + ex + 22 * turn * .5 - 6, ey - 6, hx + ex + 22 * turn * .5 + 6, ey + 6,
                             fill=TEXT, outline="")
            px = hx + ex + 22 * turn * .5 - 3 * turn
            self.create_oval(px - 3, ey - 3, px + 3, ey + 3, fill=INK, outline="")
        self.create_oval(hx + 24 * turn - 3, cy - 12, hx + 24 * turn + 3, cy - 6, fill=mix(NEAR, "#ffffff", .5), outline="")
        self.create_oval(cx - 6, 52, cx + 6, 64, fill=WATCH, outline="")
        self.create_text(cx + 18, 58, anchor="w", text="focus", fill=MUTED, font=(FONT, 9))
        return "Left" if turn < -0.2 else "Right" if turn > 0.2 else "Centre"


##############################################################################
# SECTION: coach
# coach.py - optional camera coach for the Exercise page.
#
# Modes (picked automatically, nothing is required to run the rest of the app):
#   pose    OpenCV + MediaPipe installed: tracks your joints, counts reps and
#           scores your form for squats, hip hinges, overhead presses and reaches.
#   motion  Only OpenCV installed: tracks how much and how rhythmically you move.
#   off     Neither installed: the app tells you how to enable it.
#
# Install (optional):   pip install opencv-python mediapipe
# Everything is processed on this computer. No video is saved or sent anywhere.
##############################################################################

POSE_KINDS = ("squat", "deadlift", "press", "reach")
W, H = 256, 192

# MediaPipe landmark ids
NOSE, LSH, RSH, LEL, REL, LWR, RWR, LHIP, RHIP, LKN, RKN, LAN, RAN = 0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28
BONES = [(LSH, RSH), (LSH, LEL), (LEL, LWR), (RSH, REL), (REL, RWR), (LSH, LHIP), (RSH, RHIP),
         (LHIP, RHIP), (LHIP, LKN), (LKN, LAN), (RHIP, RKN), (RKN, RAN)]


def angle(a, b, c):
    """Angle at b (degrees) formed by points a-b-c."""
    v1, v2 = (a[0] - b[0], a[1] - b[1]), (c[0] - b[0], c[1] - b[1])
    n = math.hypot(*v1) * math.hypot(*v2) + 1e-9
    return math.degrees(math.acos(max(-1, min(1, (v1[0] * v2[0] + v1[1] * v2[1]) / n))))


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


class Coach:
    def __init__(self):
        self.cv2 = self.np = self.pose_mod = None
        self.probed = False
        self.mode = "off"
        self.reason = ""
        self.cap = self.pose = None
        self.running = False
        self.kind = "reach"
        self.unclaimed = 0
        self._reset()

    # ------------------------------------------------------------ setup
    def probe(self):
        """Look for OpenCV / MediaPipe (done lazily, importing them is slow)."""
        if self.probed:
            return self.mode
        self.probed = True
        try:
            import cv2
            import numpy as np
            self.cv2, self.np = cv2, np
        except Exception:
            self.mode = "off"
            self.reason = "The coach cam needs OpenCV. Install it with:  pip install opencv-python mediapipe"
            return self.mode
        try:
            import mediapipe as mp
            self.pose_mod = mp.solutions.pose
            self.mode = "pose"
        except Exception:
            self.mode = "motion"
            self.reason = "MediaPipe not found, using basic movement tracking. For form scoring: pip install mediapipe"
        return self.mode

    def _reset(self):
        self.reps, self.scores, self.state = 0, [], "up"
        self.last_score, self.last_rep_t, self.tip = None, 0.0, "Get ready"
        self.min_ang, self.max_lean, self.best = 180.0, 0.0, 0.0
        self.bg, self.hist, self.mstate = None, deque(maxlen=90), "low"

    def set_kind(self, kind):
        if kind != self.kind:
            self.kind = kind
            self._reset()

    def claim_reps(self):
        n, self.unclaimed = self.unclaimed, 0
        return n

    def start(self):
        if self.probe() == "off":
            return False, self.reason
        cv2 = self.cv2
        cap = None
        for args in ((0, getattr(cv2, "CAP_DSHOW", 0)), (0,)):
            try:
                cap = cv2.VideoCapture(*args)
                if cap is not None and cap.isOpened():
                    break
            except Exception:
                cap = None
        if cap is None or not cap.isOpened():
            return False, "I couldn't open the camera. Close other apps that use it and try again."
        self.cap = cap
        if self.mode == "pose":
            try:
                self.pose = self.pose_mod.Pose(model_complexity=0, smooth_landmarks=True,
                                               min_detection_confidence=0.5, min_tracking_confidence=0.5)
            except Exception:
                self.mode, self.pose = "motion", None
        self._reset()
        self.running = True
        return True, "Camera on. " + self.reason

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.pose is not None:
            try:
                self.pose.close()
            except Exception:
                pass
            self.pose = None

    # ------------------------------------------------------------ main step
    def step(self):
        """Read one frame. Returns (ppm_bytes, stats_dict) or None."""
        if not self.running or self.cap is None:
            return None
        ok, frame = self.cap.read()
        if not ok:
            return None
        cv2 = self.cv2
        frame = cv2.flip(cv2.resize(frame, (W, H)), 1)
        if self.mode == "pose" and self.kind in POSE_KINDS and self.pose is not None:
            stats = self._pose_step(frame)
        else:
            stats = self._motion_step(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return b"P6 %d %d 255\n" % (W, H) + rgb.tobytes(), stats

    def _stats(self, tracking, form, mode):
        avg = round(sum(self.scores) / len(self.scores)) if self.scores else None
        return dict(mode=mode, tracking=tracking, reps=self.reps, form=form, last=self.last_score,
                    avg=avg, tip=self.tip)

    def _count(self, score):
        self.reps += 1
        self.unclaimed += 1
        self.scores.append(score)
        self.last_score = score
        self.last_rep_t = time.time()

    # ------------------------------------------------------------ pose mode
    def _pose_step(self, frame):
        cv2 = self.cv2
        res = self.pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if not res.pose_landmarks:
            self.tip = "Step back so your whole body is in view"
            return self._stats(False, 0, "pose")
        lm = res.pose_landmarks.landmark
        P = {i: (lm[i].x * W, lm[i].y * H) for i in range(33)}
        V = {i: lm[i].visibility for i in range(33)}
        side = "L" if sum(V[i] for i in (LHIP, LKN, LAN)) >= sum(V[i] for i in (RHIP, RKN, RAN)) else "R"
        sh, hp, kn, an = ((LSH, LHIP, LKN, LAN) if side == "L" else (RSH, RHIP, RKN, RAN))
        form = getattr(self, "_" + self.kind)(P, V, sh, hp, kn, an)
        col = (97, 220, 61) if form >= 75 else (60, 200, 255) if form >= 50 else (93, 93, 255)
        for a, b in BONES:
            if V[a] > 0.4 and V[b] > 0.4:
                cv2.line(frame, (int(P[a][0]), int(P[a][1])), (int(P[b][0]), int(P[b][1])), col, 3)
        for i in (LSH, RSH, LEL, REL, LWR, RWR, LHIP, RHIP, LKN, RKN, LAN, RAN):
            if V[i] > 0.4:
                cv2.circle(frame, (int(P[i][0]), int(P[i][1])), 4, (255, 255, 255), -1)
        return self._stats(True, int(form), "pose")

    def _squat(self, P, V, sh, hp, kn, an):
        ang = angle(P[hp], P[kn], P[an])
        lean = math.degrees(math.atan2(abs(P[sh][0] - P[hp][0]), max(P[hp][1] - P[sh][1], 1)))
        if self.state == "up" and ang < 115:
            self.state, self.min_ang, self.max_lean = "down", ang, lean
        elif self.state == "down":
            self.min_ang, self.max_lean = min(self.min_ang, ang), max(self.max_lean, lean)
            if ang > 158:
                depth = clamp((150 - self.min_ang) / 55 * 100)
                posture = clamp(100 - (self.max_lean - 25) * 3)
                score = round(0.65 * depth + 0.35 * posture)
                self.tip = ("Go a little deeper next time" if depth < 60 else
                            "Keep your chest up" if posture < 60 else "Nice rep")
                self._count(score)
                self.state = "up"
        if self.state == "down":
            return clamp((150 - self.min_ang) / 55 * 100)
        return self.last_score or 60

    def _deadlift(self, P, V, sh, hp, kn, an):
        hipang = angle(P[sh], P[hp], P[kn])
        kneeang = angle(P[hp], P[kn], P[an])
        if self.state == "up" and hipang < 120:
            self.state, self.min_ang, self.best = "down", hipang, kneeang
        elif self.state == "down":
            self.min_ang, self.best = min(self.min_ang, hipang), min(self.best, kneeang)
            if hipang > 160:
                hinge = clamp((150 - self.min_ang) / 55 * 100)
                legs = 100 if self.best > 125 else 60
                self.tip = ("Hinge further back" if hinge < 60 else
                            "Keep your knees straighter, hinge at the hips" if legs < 100 else "Solid hinge")
                self._count(round(0.7 * hinge + 0.3 * legs))
                self.state = "up"
        return clamp((150 - hipang) / 55 * 100) if self.state == "down" else (self.last_score or 60)

    def _press(self, P, V, sh, hp, kn, an):
        torso = max(abs(P[LHIP][1] - P[LSH][1]), 30)
        lw, rw = P[LWR][1], P[RWR][1]
        sy = (P[LSH][1] + P[RSH][1]) / 2
        up_amt = (sy - (lw + rw) / 2) / torso
        el = (angle(P[LSH], P[LEL], P[LWR]) + angle(P[RSH], P[REL], P[RWR])) / 2
        if self.state == "up" and up_amt < 0.1:
            self.state, self.best = "down", 0
        elif self.state == "down":
            self.best = max(self.best, el)
            if up_amt > 0.35 and el > 140:
                sym = clamp(100 - abs(lw - rw) / torso * 250)
                lock = clamp((self.best - 120) / 55 * 100)
                self.tip = ("Press both arms evenly" if sym < 60 else
                            "Lock your arms out at the top" if lock < 70 else "Strong press")
                self._count(round(0.6 * lock + 0.4 * sym))
                self.state = "up"
        return clamp(up_amt * 160)

    def _reach(self, P, V, sh, hp, kn, an):
        torso = max(abs(P[LHIP][1] - P[LSH][1]), 30)
        h = (P[NOSE][1] - (P[LWR][1] + P[RWR][1]) / 2) / torso
        if self.state == "up" and h > 0.25:
            self.state = "down"
            self.tip = "Lengthen up, nice"
            self._count(round(clamp(h * 180)))
        elif self.state == "down" and h < 0.05:
            self.state = "up"
        return clamp(h * 180)

    # ------------------------------------------------------------ motion mode
    def _motion_step(self, frame):
        cv2, np = self.cv2, self.np
        gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (21, 21), 0)
        if self.bg is None:
            self.bg = gray.astype(np.float32)
        cv2.accumulateWeighted(gray, self.bg, 0.05)
        diff = cv2.absdiff(gray, cv2.convertScaleAbs(self.bg))
        mask = cv2.dilate(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1], None, iterations=2)
        motion = float(mask.mean()) / 255.0
        m = mask > 0
        if m.any():
            frame[m] = (frame[m] * 0.5 + np.array([97, 220, 61]) * 0.5).astype(np.uint8)
        form = clamp(motion * 450)
        ys = np.nonzero(mask)[0]
        now = time.time()
        if len(ys) > 200:
            self.hist.append((now, float(ys.mean()) / H))
        if len(self.hist) > 10:
            vals = [v for t, v in self.hist if now - t < 2.5]
            if vals:
                lo, hi = min(vals), max(vals)
                rng, mid, cy = hi - lo, (hi + lo) / 2, vals[-1]
                if rng > 0.07:
                    if self.mstate == "low" and cy < mid - 0.25 * rng:
                        self.mstate = "high"
                    elif self.mstate == "high" and cy > mid + 0.25 * rng and now - self.last_rep_t > 0.6:
                        self.mstate = "low"
                        self._count(round(clamp(40 + rng * 500)))
        self.tip = ("Step in front of the camera and move" if motion < 0.015 else
                    "Good energy, keep a steady rhythm" if form > 40 else "Try to move a bit bigger")
        return self._stats(motion >= 0.015, int(form), "motion")


##############################################################################
# SECTION: astro_vital
# ASTRO-VITAL  |  Astronaut Health Companion
# NASA Open App Challenge 2026 - Lalitpur
#
# Run this file:   python astro_vital.py
# Needs:           Python 3.8+ with Tkinter (no pip packages required)
# Optional:        pip install opencv-python mediapipe     (for the Exercise coach cam)
#
# Files in this folder:
#   astro_vital.py   the app and all its screens (this file)
#   content.py       questions, advice, plans, environments, learning cards
#   logic.py         scoring, saving, XP, quests, badges, leaderboard
#   widgets.py       rounded buttons, chips, lists, icons, progress bar
#   animations.py    the "show me how" exercise animations
#   coach.py         optional camera coach (rep counting and form score)
#
# This is an educational prototype. It does not replace the flight surgeon.
##############################################################################

#!/usr/bin/env python3


CAM_W, CAM_H = W, H
IND = {i[0]: i for i in INDICATORS}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASTRO-VITAL  |  Astronaut Health Companion")
        self.geometry("1320x820")
        self.minsize(1180, 720)
        self.configure(bg=BG)
        self.store = Store()
        self.coach = Coach()
        self.ui_built = False

        self.pages, self.navs, self.current = {}, {}, None
        self.gauge_now, self.gauge_target, self._gjob = 0.0, 0.0, None
        self.gcx, self.gcy, self.gr = 190, 270, 100
        self.shimmer, self.xp_geom, self.hw = 0.0, None, []
        self.day_var = tk.StringVar(value="1")
        self.pulse_var = tk.StringVar()
        self.answers, self.flag_state, self.step = {}, {}, 0
        self.steps = [("welcome",)] + [("q", q) for q in QUESTIONS] + [("pulse",), ("flags",)]
        self.toasts, self._toast_busy, self._reminded = [], False, set()
        self._modal_q, self._modal_open, self._nudges = [], False, 0
        self.ind_key, self.chart_prog, self._chart_job = "overall", 1.0, None
        self.cur_kind, self.cam_img, self._cam_job = "reach", None, None
        self.tip_seed = dt.date.today().toordinal()

        self._style()
        self.bind_all("<MouseWheel>", lambda e: self._wheel(-1 if e.delta > 0 else 1))
        self.bind_all("<Button-4>", lambda e: self._wheel(-1))
        self.bind_all("<Button-5>", lambda e: self._wheel(1))
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.login = LoginScreen(self, self.store, self.start_session, self.start_guest)
        self.login.show()

    # ------------------------------------------------------------------ basics
    @property
    def p(self):
        return self.store.profile

    @property
    def latest(self):
        h = self.p["history"]
        return h[-1] if h else None

    def next_day(self):
        h = self.p["history"]
        if not h:
            return 1
        try:
            d0 = int(h[-1]["day"])
            gap = (dt.date.today() - dt.date.fromisoformat(h[-1]["time"][:10])).days
            return d0 + max(gap, 0)
        except (ValueError, KeyError):
            return 1

    def _style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=28, borderwidth=0, font=(FONT, 10))
        s.configure("Treeview.Heading", background=CARD2, foreground=ACCENT, borderwidth=0,
                    font=(FONT, 10, "bold"))
        s.map("Treeview", background=[("selected", CARD2)])
        s.configure("Vertical.TScrollbar", background=CARD2, troughcolor=BG, bordercolor=BG,
                    arrowcolor=MUTED, lightcolor=CARD2, darkcolor=CARD2)

    def _entry(self, parent, var, width=22, size=14):
        return tk.Entry(parent, textvariable=var, width=width, bg=CARD2, fg=TEXT, insertbackground=TEXT,
                        relief="flat", font=(FONT, size), highlightthickness=2,
                        highlightbackground=LINE, highlightcolor=ACCENT)

    def _wheel(self, d):
        page = self.pages.get(self.current)
        sc = getattr(page, "scroll_canvas", None)
        if sc is not None:
            sc.yview_scroll(d * 2, "units")

    # ------------------------------------------------------------------ toasts and rewards
    def toast(self, text, color=ACCENT):
        self.toasts.append((text, color))
        if not self._toast_busy:
            self._next_toast()

    def _next_toast(self):
        if not self.toasts:
            self._toast_busy = False
            return
        self._toast_busy = True
        text, color = self.toasts.pop(0)
        bg = mix(CARD, color, 0.25)
        f = tk.Frame(self, bg=bg, highlightthickness=2, highlightbackground=color)
        tk.Label(f, text=text, bg=bg, fg=TEXT, font=(FONT, 12, "bold"), padx=18, pady=12).pack()
        f.place(relx=1.0, x=-24, y=24, anchor="ne")
        f.lift()

        def done():
            f.destroy()
            self._next_toast()
        self.after(2200, done)

    def reward(self, events):
        """Show XP toasts, unlock badges, handle level-ups, save."""
        p = self.p
        for text, pts in events:
            self.toast(f"+{pts} XP   {text}", ACCENT)
        for bid, name in check_badges(p):
            info = next((b for b in BADGES if b[0] == bid), None)
            col, desc = (info[3], info[2]) if info else (WATCH, "")
            self.queue_modal(lambda done, n=name, d=desc, c=col: self.show_celebration(
                done, "BADGE UNLOCKED", n, f"{d}\n+{BADGE_XP} XP", c, "\u2605"))
        lvl = level_info(p["xp"])[0]
        if lvl > p.get("lvl_seen", 1):
            p["lvl_seen"] = lvl
            give_gems(p, 20)
            self.queue_modal(lambda done, l=lvl: self.show_celebration(
                done, "LEVEL UP", f"Level {l}", f"You are now a {title_for(l)}. Keep it going!\n+20 stardust", ACCENT2, str(l)))
        st = profile_streak(p)
        reached = p.setdefault("streak_ms", [])
        for days, bonus in STREAK_MILESTONES.items():
            if st >= days and days not in reached:
                reached.append(days)
                give_gems(p, bonus)
                self.queue_modal(lambda done, d=days, b=bonus: self.show_celebration(
                    done, "STREAK MILESTONE", f"{d}-day streak", f"You're on fire.\n+{b} stardust", "#ff9f3a", str(d)))
        bd = buddy_info(self.store, p)
        if bd:
            p["stats"]["best_buddy"] = max(p["stats"].get("best_buddy", 0), bd["streak"])
            reached_b = p.setdefault("buddy_ms", [])
            for days, bonus in BUDDY_MILESTONES.items():
                if bd["streak"] >= days and days not in reached_b:
                    reached_b.append(days)
                    give_gems(p, bonus)
                    self.queue_modal(lambda done, d=days, b=bonus, n=bd["name"]: self.show_celebration(
                        done, "BUDDY STREAK", f"{d} days with {n}", f"Better together.\n+{b} stardust", WATCH, str(d)))
        if self.store.is_guest:
            n = self._nudges
            if (n == 0 and p["xp"] >= 40) or (n == 1 and (lvl >= 2 or len(p["badges"]) >= 2)):
                self._nudges += 1
                self.queue_modal(self.show_save_nudge)
        self.store.save()
        self.update_sidebar()
        self.redraw_current()

    def drink(self):
        ev = log_water(self.p)
        if ev:
            self.reward(ev)
        else:
            self.toast("Water goal done for today. Nice.", "#6bb8e8")

    def reminder_check(self):
        p = self.p
        if p is None:
            self.after(60 * 1000, self.reminder_check)
            return
        due = [t for t, _ in due_tasks(p) if (today(), t["id"]) not in self._reminded]
        if due and self.current != "routine":
            for t in due:
                self._reminded.add((today(), t["id"]))
            names = ", ".join(t["title"].lower() for t in due[:3])
            self.toast(f"Routine reminder: {names} due. Open Mission Routine.", CAUTION)
        self.after(20 * 60 * 1000, self.reminder_check)

    # ------------------------------------------------------------------ sign in / out
    def start_session(self, name):
        """Called by the sign-in screen once a username and password check out."""
        self.store.data["active"] = name
        if not self.ui_built:
            self.day_var.set(str(self.next_day()))
            self._build_sidebar()
            self.content = tk.Frame(self, bg=BG)
            self.content.pack(side="left", fill="both", expand=True)
            for build in (self._build_home, self._build_checkin, self._build_routine, self._build_advice,
                          self._build_meds, self._build_exercise, self._build_learn, self._build_progress,
                          self._build_rewards, self._build_crew):
                build()
            self.ui_built = True
            self.refresh_all()
            self.show("home")
            self._tick_clock()
            self._shimmer_loop()
            self.after(4000, self.reminder_check)
        else:
            self.on_profile_change()
        self.login.hide()
        p = self.p
        used = apply_shields(p)
        if used:
            self.toast(f"A Streak Shield kept your streak alive ({used} used).", "#6bb8e8")
        self.toast("Welcome aboard, astronaut!" if self.store.is_guest else f"Welcome back, {p['name']}!", ACCENT)
        self._daily_chest()

    def logout(self):
        self.confirm_leave(self._do_logout)

    def _do_logout(self):
        self._stop_activity()
        self.store.log_out()
        self.login.show()

    def _stop_activity(self):
        for fn in (self.stop_cam, self.demo.stop, self._cancel):
            try:
                fn()
            except Exception:
                pass
        self.running = False
        self._modal_q.clear()

    def delete_account_dialog(self):
        m = Modal(self, 460, 420, border=CRIT)
        b = m.body
        tk.Label(b, text="Delete my account", bg=CARD, fg=TEXT, font=(HEAD, 22, "bold")).pack(anchor="w", padx=30, pady=(26, 4))
        tk.Label(b, text=f"This permanently removes {self.p['name']} and all of its check-ins, readings, XP and badges "
                         "from this computer. It cannot be undone.", bg=CARD, fg=MUTED, font=(FONT, 11),
                 wraplength=400, justify="left").pack(anchor="w", padx=30, pady=(0, 16))
        tk.Label(b, text="TYPE YOUR PASSWORD TO CONFIRM", bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=30)
        v = tk.StringVar()
        e = tk.Entry(b, textvariable=v, show="\u2022", width=34, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat",
                     font=(FONT, 12), highlightthickness=2, highlightbackground=LINE, highlightcolor=CRIT)
        e.pack(anchor="w", padx=30, pady=(4, 8), ipady=6)
        err = tk.Label(b, text="", bg=CARD, fg=CRIT, font=(FONT, 10, "bold"))
        err.pack(anchor="w", padx=30)

        def go(ev=None):
            name = self.p["name"]
            self._stop_activity()
            msg = self.store.delete_account(name, v.get())
            if msg:
                return err.config(text=msg)
            m.close()
            self.login.show()
            self.login.say("Your account and data were deleted.", GOOD)
        e.bind("<Return>", go)
        row = tk.Frame(b, bg=CARD)
        row.pack(anchor="w", padx=30, pady=16)
        Pill(row, "Delete forever", go, w=170, h=44, fill=CRIT, surface=CARD).pack(side="left")
        Pill(row, "Cancel", m.close, w=110, h=44, ghost=True, surface=CARD).pack(side="left", padx=10)
        m.after(80, e.focus_set)

    def reset_all_dialog(self):
        m = Modal(self, 480, 440, border=CRIT)
        b = m.body
        tk.Label(b, text="Erase all data", bg=CARD, fg=TEXT, font=(HEAD, 22, "bold")).pack(anchor="w", padx=30, pady=(26, 4))
        tk.Label(b, text="This deletes EVERY account and all progress saved on this computer, including test profiles, "
                         "and starts fresh. It cannot be undone.", bg=CARD, fg=MUTED, font=(FONT, 11),
                 wraplength=420, justify="left").pack(anchor="w", padx=30, pady=(0, 16))
        tk.Label(b, text="TYPE  DELETE  TO CONFIRM", bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=30)
        v = tk.StringVar()
        e = tk.Entry(b, textvariable=v, width=34, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat",
                     font=(FONT, 12), highlightthickness=2, highlightbackground=LINE, highlightcolor=CRIT)
        e.pack(anchor="w", padx=30, pady=(4, 8), ipady=6)
        err = tk.Label(b, text="", bg=CARD, fg=CRIT, font=(FONT, 10, "bold"))
        err.pack(anchor="w", padx=30)

        def go(ev=None):
            if v.get().strip() != "DELETE":
                return err.config(text="Type DELETE in capital letters to confirm.")
            self._stop_activity()
            self.store.reset_all()
            m.close()
            self.login.show()
            self.login.say("All data erased. Create a new account to start fresh.", GOOD)
        e.bind("<Return>", go)
        row = tk.Frame(b, bg=CARD)
        row.pack(anchor="w", padx=30, pady=16)
        Pill(row, "Erase everything", go, w=190, h=44, fill=CRIT, surface=CARD).pack(side="left")
        Pill(row, "Cancel", m.close, w=110, h=44, ghost=True, surface=CARD).pack(side="left", padx=10)
        tk.Label(b, text=f"Saved in: {self.store.path}", bg=CARD, fg=mix(MUTED, CARD, .3), font=(FONT, 8),
                 wraplength=420, justify="left").pack(anchor="w", padx=30)
        m.after(80, e.focus_set)

    def change_password_dialog(self):
        m = Modal(self, 440, 440, border=ACCENT)
        b = m.body
        tk.Label(b, text="Change password", bg=CARD, fg=TEXT, font=(HEAD, 22, "bold")).pack(anchor="w", padx=30, pady=(26, 2))
        tk.Label(b, text="Pick something only you would know.", bg=CARD, fg=MUTED, font=(FONT, 11)).pack(
            anchor="w", padx=30, pady=(0, 16))
        vs, first = [tk.StringVar() for _ in range(3)], None
        for label, v in zip(("CURRENT PASSWORD", "NEW PASSWORD", "CONFIRM NEW PASSWORD"), vs):
            tk.Label(b, text=label, bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=30)
            e = tk.Entry(b, textvariable=v, show="\u2022", width=34, bg=CARD2, fg=TEXT, insertbackground=TEXT,
                         relief="flat", font=(FONT, 12), highlightthickness=2, highlightbackground=LINE,
                         highlightcolor=ACCENT)
            e.pack(anchor="w", padx=30, pady=(4, 10), ipady=6)
            first = first or e
        err = tk.Label(b, text="8+ characters with a letter and a number.", bg=CARD, fg=MUTED, font=(FONT, 10, "bold"))
        err.pack(anchor="w", padx=30)

        def save():
            old, new, conf = (v.get() for v in vs)
            if new != conf:
                return err.config(text="The new passwords don't match.", fg=CRIT)
            msg = self.store.change_password(self.p["name"], old, new)
            if msg:
                return err.config(text=msg, fg=CRIT)
            m.close()
            self.toast("Password updated.", GOOD)
        row = tk.Frame(b, bg=CARD)
        row.pack(anchor="w", padx=30, pady=16)
        Pill(row, "Save password", save, w=180, h=44, surface=CARD).pack(side="left")
        Pill(row, "Cancel", m.close, w=110, h=44, ghost=True, surface=CARD).pack(side="left", padx=10)
        m.after(80, first.focus_set)

    # ------------------------------------------------------------------ pop-ups (queued so they never stack)
    def queue_modal(self, builder, urgent=False):
        if urgent:
            self._modal_q.insert(0, builder)
        else:
            self._modal_q.append(builder)
        if not self._modal_open:
            self.after(300, self._next_modal)

    def _next_modal(self):
        if self._modal_open or not self._modal_q or self.p is None:
            return
        builder = self._modal_q.pop(0)
        self._modal_open = True

        def done():
            self._modal_open = False
            self.after(250, self._next_modal)
        try:
            builder(done)
        except Exception:                      # a broken pop-up must never lock the app
            done()

    def show_critical(self, alerts, done):
        shown, extra = alerts[:3], max(len(alerts) - 3, 0)
        h = min(480 + 62 * len(shown) + (26 if extra else 0), max(self.winfo_height() - 30, 600))
        m = Modal(self, 640, h, border=CRIT, on_close=done)
        b, W = m.body, 636
        hdr = tk.Canvas(b, width=W, height=152, bg=CARD, highlightthickness=0)
        hdr.pack()
        base = mix(CARD, CRIT, .30)
        for i in range(31):
            hdr.create_rectangle(0, i * 5, W, i * 5 + 5, fill=mix(base, CARD, i / 30), outline="")
        hdr.create_oval(56, 46, 116, 106, fill=CRIT, outline="")
        hdr.create_text(86, 76, text="!", fill="#ffffff", font=(FONT, 30, "bold"))
        hdr.create_text(148, 56, anchor="w", text="Mission Control alert", fill=TEXT, font=(FONT, 25, "bold"))
        hdr.create_text(148, 90, anchor="w", text="Your check-in flagged something that needs a human.",
                        fill=mix(TEXT, MUTED, .4), font=(FONT, 12))
        rrect(hdr, 148, 112, 262, 136, r=12, fill=mix(CARD, CRIT, .45), outline=CRIT)
        hdr.create_text(205, 124, text="HIGH PRIORITY", fill=TEXT, font=(FONT, 8, "bold"))
        x = hdr.create_text(W - 22, 20, text="\u2715", fill=MUTED, font=(FONT, 12, "bold"))
        hdr.tag_bind(x, "<Button-1>", lambda e: m.close())
        t = {"v": 0.0}

        def pulse():
            if not m.alive:
                return
            t["v"] += .028
            hdr.delete("ring")
            for k in range(3):
                ph = (t["v"] + k / 3) % 1
                r = 30 + ph * 38
                hdr.create_oval(86 - r, 76 - r, 86 + r, 76 + r, outline=mix(base, CRIT, .95 * (1 - ph)), width=2,
                                tags="ring")
            m.after(40, pulse)
        pulse()
        pad = tk.Frame(b, bg=CARD)
        pad.pack(fill="both", expand=True, padx=34)
        tk.Label(pad, text="WHAT WE NOTICED", bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", pady=(16, 6))
        for a in shown:
            card = tk.Frame(pad, bg=CARD2)
            card.pack(fill="x", pady=3)
            tk.Frame(card, bg=CRIT, width=5).pack(side="left", fill="y")
            tk.Label(card, text=a, bg=CARD2, fg=TEXT, font=(FONT, 11, "bold"), wraplength=520, justify="left",
                     anchor="w", padx=14, pady=10).pack(side="left", fill="x", expand=True)
        if extra:
            tk.Label(pad, text=f"+ {extra} more in My Advice", bg=CARD, fg=MUTED, font=(FONT, 10)).pack(anchor="w")
        tk.Label(pad, text="DO THIS NOW", bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", pady=(16, 6))
        for text in ("Stay calm. Secure yourself and breathe slowly.",
                     "Contact the flight surgeon or Mission Control.",
                     "Check in again in about 30 minutes."):
            row = tk.Frame(pad, bg=CARD, cursor="hand2")
            row.pack(fill="x", pady=3)
            box = tk.Canvas(row, width=26, height=26, bg=CARD, highlightthickness=0, cursor="hand2")
            box.pack(side="left")
            lbl = tk.Label(row, text=text, bg=CARD, fg=TEXT, font=(FONT, 11), anchor="w", cursor="hand2")
            lbl.pack(side="left", padx=10)
            st = {"on": False}

            def paint(box=box, st=st):
                box.delete("all")
                box.create_oval(3, 3, 23, 23, outline=GOOD if st["on"] else LINE, width=2, fill=GOOD if st["on"] else CARD)
                if st["on"]:
                    box.create_text(13, 13, text="\u2713", fill=INK, font=(FONT, 11, "bold"))

            def toggle(e=None, st=st, paint=paint, lbl=lbl):
                st["on"] = not st["on"]
                paint()
                lbl.config(fg=MUTED if st["on"] else TEXT)
            paint()
            for w in (box, lbl, row):
                w.bind("<Button-1>", toggle)
        btns = tk.Frame(b, bg=CARD)
        btns.pack(fill="x", padx=34, pady=(16, 6))
        Pill(btns, "I've contacted Mission Control",
             lambda: (m.close(), self.toast("Good. Stay safe and check in again soon.", GOOD)),
             w=290, h=50, fill=CRIT, surface=CARD, size=11).pack(side="left")
        Pill(btns, "See my advice", lambda: (m.close(), self.show("advice")), w=170, h=50, ghost=True,
             surface=CARD, size=11).pack(side="left", padx=12)
        tk.Label(b, text="Educational prototype. In an emergency, follow your mission emergency procedures.",
                 bg=CARD, fg=mix(MUTED, CARD, .3), font=(FONT, 9)).pack(pady=(4, 12))

    def show_celebration(self, done, kicker, title, sub, color, glyph):
        m = Modal(self, 480, 420, border=color, on_close=done)
        c = tk.Canvas(m.body, width=476, height=416, bg=CARD, highlightthickness=0)
        c.pack()
        for i in range(30):
            c.create_rectangle(0, i * 14, 476, i * 14 + 14, fill=mix(mix(CARD, color, .22), CARD, i / 29), outline="")
        c.create_text(238, 40, text=kicker, fill=color, font=(FONT, 11, "bold"))
        c.create_text(238, 246, text=title, fill=TEXT, font=(HEAD, 28, "bold"), width=420, justify="center")
        c.create_text(238, 300, text=sub, fill=mix(TEXT, MUTED, .35), font=(FONT, 12), width=380, justify="center")
        c.create_window(238, 366, window=Pill(c, "Awesome!", m.close, w=200, h=48, fill=color, surface=CARD, size=12))
        rnd = random.Random()
        pal = [ACCENT, ACCENT2, GOOD, "#f27b8f", "#6bb8e8", "#fff6e6", color]
        parts = [[rnd.random() * 476, -rnd.random() * 420, rnd.uniform(-.7, .7), rnd.uniform(2.2, 5), rnd.randint(6, 11),
                  rnd.choice(pal), rnd.random() * 6] for _ in range(72)]
        fr = {"n": 0}

        def frame():
            if not m.alive:
                return
            fr["n"] += 1
            n = fr["n"]
            c.delete("dyn")
            pop = min(n / 16, 1)
            s = 1 + 2.7 * (pop - 1) ** 3 + 1.7 * (pop - 1) ** 2
            R = 58 * max(s, .05)
            for k, a in ((26, .10), (16, .18), (8, .3)):
                c.create_oval(238 - R - k, 140 - R - k, 238 + R + k, 140 + R + k, fill=mix(CARD, color, a),
                              outline="", tags="dyn")
            c.create_oval(238 - R, 140 - R, 238 + R, 140 + R, fill=color, outline=TEXT, width=3, tags="dyn")
            c.create_text(238, 140, text=glyph, fill=INK, font=(FONT, max(int(46 * s), 8), "bold"), tags="dyn")
            for p in parts:
                p[1] += p[3]
                p[0] += p[2] + math.sin(n * .1 + p[6]) * .8
                if p[1] > 420:
                    if n < 140:
                        p[0], p[1] = rnd.random() * 476, -10
                    else:
                        continue
                wdt = max(p[4] * abs(math.cos(n * .17 + p[6])), 1.5)
                c.create_rectangle(p[0], p[1], p[0] + wdt, p[1] + p[4] * .6, fill=p[5], outline="", tags="dyn")
            m.after(33, frame)
        frame()

    # ------------------------------------------------------------------ lens-power range bar
    def _diopter_bar(self, c, t, last):
        c.delete("all")
        W = max(c.winfo_width(), 300)
        x1, x2, y1, y2 = 8, W - 8, 30, 52
        vals = [m["value"] for m in self.p["measures"] if m["task"] == t["id"]]
        base = vals[0] if vals else None
        lo, hi = (base - 3.0, base + 3.0) if base is not None else t["axis"]

        def px(v):
            return x1 + (x2 - x1) * (max(lo, min(hi, v)) - lo) / (hi - lo)

        def sgn(k):
            return "0" if k == 0 else (f"+{k}" if k > 0 else f"\u2212{abs(k)}")
        c.create_text(x1, 12, anchor="w", text="CHANGE FROM YOUR BASELINE" if base is not None else "LENS POWER SCALE (D)",
                      fill=MUTED, font=(FONT, 9, "bold"))
        if base is not None:
            rrect(c, x1, y1, x2, y2, r=6, fill=CRIT, outline="")
            c.create_rectangle(px(base - 1), y1, px(base + 1), y2, fill=WATCH, outline="")
            c.create_rectangle(px(base - .5), y1, px(base + .5), y2, fill=GOOD, outline="")
            c.create_line(px(base), y1 - 2, px(base), y2 + 2, fill=INK, width=2, dash=(3, 2))
            for k in range(math.ceil(lo), math.floor(hi) + 1):
                c.create_text(px(k), y2 + 12, text=sgn(k), fill=MUTED, font=(FONT, 8))
            lx = x1
            for col, text, step in ((GOOD, "Steady (within 0.50 D)", 190), (WATCH, "Small shift", 120),
                                    (CRIT, "Notable shift (1.00 D or more)", 0)):
                c.create_oval(lx, y2 + 30, lx + 9, y2 + 39, fill=col, outline="")
                c.create_text(lx + 14, y2 + 35, anchor="w", text=text, fill=MUTED, font=(FONT, 8))
                lx += step
        else:
            rrect(c, x1, y1, x2, y2, r=6, fill=CARD2, outline=LINE)
            for k in range(-6, 7, 2):
                c.create_text(px(k), y2 + 12, text=sgn(k), fill=MUTED, font=(FONT, 8))
            c.create_text(x1, y2 + 35, anchor="w", fill=MUTED, font=(FONT, 9),
                          text="Your first reading becomes your baseline. After that we show how far you drift from it.")
        if last:
            x = px(last["value"])
            col, label = measure_status(t, last["value"], self.p)
            c.create_polygon(x - 8, y1 - 8, x + 8, y1 - 8, x, y1 + 2, fill=TEXT, outline="")
            txt = f"Last: {fmt_reading(t['id'], last['value'])}  {label}"
            if x < W - 300:
                c.create_text(max(x, 250), 12, anchor="w", text=txt, fill=col, font=(FONT, 10, "bold"))
            else:
                c.create_text(W - 10, 12, anchor="e", text=txt, fill=col, font=(FONT, 10, "bold"))


    def on_profile_change(self):
        self.answers, self.flag_state, self.step = {}, {}, 0
        self.pulse_var.set("")
        self.day_var.set(str(self.next_day()))
        self.render_step()
        self.refresh_all()
        self.show("home")

    # ------------------------------------------------------------------ sidebar
    def _build_sidebar(self):
        side = tk.Frame(self, bg=SIDE, width=240)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        logo = tk.Canvas(side, width=240, height=92, bg=SIDE, highlightthickness=0)
        logo.pack()
        logo.create_oval(26, 28, 62, 64, fill="#e07a52", outline=ACCENT2, width=2)
        logo.create_arc(26, 28, 62, 64, start=40, extent=90, style="arc", outline="#ffc9a3", width=3)
        logo.create_oval(14, 40, 74, 52, outline=ACCENT, width=2)
        logo.create_text(84, 40, anchor="w", text="ASTRO-VITAL", fill=TEXT, font=(FONT, 15, "bold"))
        logo.create_text(84, 62, anchor="w", text="Health Companion", fill=MUTED, font=(FONT, 9))
        groups = [("MY DAY", [("home", "Home", "\u2302"), ("checkin", "Daily Check-In", "\u271a"),
                              ("routine", "Mission Routine", "\u2611")]),
                  ("TAKE CARE", [("advice", "My Advice", "\u2726"), ("meds", "Medicine Guide", "\u2695"),
                                 ("exercise", "Exercise", "\u26a1"), ("learn", "Learn", "\u270e")]),
                  ("PLAY & TRACK", [("progress", "Progress", "\u25a4"), ("rewards", "Rewards", "\u2605"),
                                    ("crew", "Crew", "\u263b")])]
        for head, items in groups:
            tk.Label(side, text=head, bg=SIDE, fg=mix(MUTED, SIDE, .35), font=(FONT, 8, "bold"),
                     anchor="w").pack(fill="x", padx=22, pady=(12, 2))
            for key, text, glyph in items:
                self._nav_item(side, key, text, glyph)
        bottom = tk.Frame(side, bg=SIDE)
        bottom.pack(side="bottom", fill="x", pady=(2, 6))
        self.prof_canvas = tk.Canvas(bottom, width=216, height=100, bg=SIDE, highlightthickness=0, cursor="hand2")
        self.prof_canvas.pack()
        self.prof_canvas.bind("<Button-1>", lambda e: self.show("crew"))
        self.out_lbl = out = tk.Label(bottom, text="\u23fb   Log out", bg=SIDE, fg=MUTED, font=(FONT, 10, "bold"), cursor="hand2", pady=7)
        out.pack(fill="x", padx=14, pady=(6, 0))
        out.bind("<Button-1>", lambda e: self.logout())
        out.bind("<Enter>", lambda e: out.config(fg=CRIT))
        out.bind("<Leave>", lambda e: out.config(fg=MUTED))
        self.save_pill = Pill(bottom, "Save my progress", self.save_progress_dialog, w=212, h=38, fill=ACCENT2,
                              surface=SIDE, size=10)
        self.clock_lbl = tk.Label(bottom, text="", bg=SIDE, fg=MUTED, font=("Consolas", 10))
        self.clock_lbl.pack(pady=(2, 0))

    def _nav_item(self, parent, key, text, glyph):
        row = tk.Frame(parent, bg=SIDE, cursor="hand2")
        row.pack(fill="x", pady=0)
        bar = tk.Frame(row, bg=SIDE, width=4)
        bar.pack(side="left", fill="y")
        lbl = tk.Label(row, text=f"{glyph}   {text}", bg=SIDE, fg=MUTED, font=(FONT, 11, "bold"),
                       anchor="w", padx=18, pady=6)
        lbl.pack(side="left", fill="x", expand=True)
        badge = tk.Label(row, text="", bg=CRIT, fg="#ffffff", font=(FONT, 8, "bold"), padx=6)

        def hover(on, key=key, row=row, lbl=lbl):
            if self.current != key:
                col = mix(SIDE, CARD, .55) if on else SIDE
                row.config(bg=col)
                lbl.config(bg=col, fg=TEXT if on else MUTED)
        for w in (row, lbl):
            w.bind("<Button-1>", lambda e, k=key: self.show(k))
            w.bind("<Enter>", lambda e, h=hover: h(True))
            w.bind("<Leave>", lambda e, h=hover: h(False))
        self.navs[key] = (row, bar, lbl, badge)

    def show(self, key):
        if self.current == "exercise" and key != "exercise":
            self.stop_cam()
            self.demo.stop()
        if self.current:
            self.pages[self.current].pack_forget()
        self.current = key
        self.pages[key].pack(fill="both", expand=True)
        for k, (row, bar, lbl, badge) in self.navs.items():
            on = k == key
            row.config(bg=CARD if on else SIDE)
            lbl.config(bg=CARD if on else SIDE, fg=TEXT if on else MUTED)
            bar.config(bg=ACCENT if on else SIDE)
        if key == "home":
            self.gauge_now = 0
            self.after(40, self.draw_home)
            self.after(70, self.animate_gauge)
        elif key == "checkin":
            self.after(40, self.draw_progress)
        elif key == "exercise":
            self.demo.start()
        elif key == "progress":
            self.after(40, self.start_chart)
        elif key == "rewards":
            self.after(40, self.draw_rewards)
        elif key == "crew":
            self.after(40, self.draw_crew)
        elif key == "routine":
            self.refresh_routine_list()

    def update_sidebar(self):
        p = self.p
        c = self.prof_canvas
        c.delete("all")
        guest = self.store.is_guest
        lvl, into, need = level_info(p["xp"])
        rrect(c, 2, 2, 214, 98, r=18, fill=CARD, outline=ACCENT2 if guest else LINE)
        draw_avatar(c, 32, 31, 19, p["name"], ENVS[p["env"]]["color"], "av", ring="ring" in p.get("owned", []))
        name = p["name"] if len(p["name"]) <= 15 else p["name"][:14] + "\u2026"
        c.create_text(60, 23, anchor="w", text=name, fill=TEXT, font=(FONT, 11, "bold"))
        c.create_text(60, 41, anchor="w", text=f"Lv {lvl}  \u00b7  Guest, not saved" if guest else
                      f"Lv {lvl}  {title_for(lvl)}", fill=ACCENT2 if guest else MUTED, font=(FONT, 9))
        draw_xp_bar(c, 14, 56, 202, 68, into / need, ACCENT, ACCENT2, "xp")
        c.create_text(16, 84, anchor="w", text=f"\u2726 {gems_of(p)}", fill=ACCENT2, font=(FONT, 10, "bold"))
        draw_shield(c, 82, 84, 7, "#6bb8e8")
        c.create_text(94, 84, anchor="w", text=str(p.get("shields", 0)), fill="#6bb8e8", font=(FONT, 10, "bold"))
        if boost_left(p):
            c.create_text(118, 84, anchor="w", text="x2 XP", fill=ACCENT2, font=(FONT, 9, "bold"))
        st = profile_streak(p)
        draw_flame(c, 184, 84, 8, "fl", hot=st > 0)
        c.create_text(196, 84, anchor="w", text=str(st), fill=WATCH if st else MUTED, font=(FONT, 10, "bold"))
        if guest:
            self.save_pill.pack(before=self.out_lbl, pady=(8, 0))
            self.out_lbl.config(text="\u23fb   Leave guest mode")
        else:
            self.save_pill.pack_forget()
            self.out_lbl.config(text="\u23fb   Log out")
        row, bar, lbl, badge = self.navs["routine"]
        n = len(due_tasks(p))
        if n:
            badge.config(text=str(n))
            badge.pack(side="right", padx=14)
        else:
            badge.pack_forget()

    def _tick_clock(self):
        self.clock_lbl.config(text=dt.datetime.now(dt.timezone.utc).strftime("UTC  %H:%M:%S"))
        self.after(1000, self._tick_clock)

    def refresh_all(self):
        ensure_today(self.p)
        self.update_sidebar()
        self.refresh_advice()
        self.refresh_routine_list()
        self.refresh_progress_table()
        if hasattr(self, "plan_menu") and self.plan_menu.sel == 0:
            self.choose_plan(0)
        self.redraw_current()

    def redraw_current(self):
        k = self.current
        if k == "home":
            self.draw_home()
            self.animate_gauge()
        elif k == "rewards":
            self.draw_rewards()
        elif k == "crew":
            self.draw_crew()
        elif k == "progress":
            self.start_chart()
        elif k == "routine":
            self.show_task(self.task_menu.sel or 0, keep_msg=True)

    # ================================================================== HOME
    def _build_home(self):
        self.home = tk.Canvas(self.content, bg=BG, highlightthickness=0)
        self.home.scroll_canvas = self.home
        self.pages["home"] = self.home
        self.home.bind("<Configure>", lambda e: self.draw_home())

    def _hp(self, text, cmd, x, y, w=140, h=34, anchor="nw", surface=CARD, **kw):
        pill = Pill(self.home, text, cmd, w=w, h=h, surface=surface, size=10, **kw)
        self.hw.append(pill)
        self.home.create_window(x, y, anchor=anchor, window=pill)
        return pill

    def mood_line(self):
        lat = self.latest
        if not lat:
            return "First time here. Let's see how you're doing. It only takes a couple of minutes."
        if lat["time"][:10] != today():
            st = profile_streak(self.p)
            return (f"Your {st}-day streak is waiting for you. Got two minutes?" if st
                    else "I haven't seen you check in today yet. Got two minutes?")
        o = lat["overall"]
        if lat["alerts"]:
            return "Please talk to the flight surgeon today. I mean it."
        if o >= 80:
            return "You're in good shape today. Keep doing what you're doing."
        if o >= 60:
            return "A few things to watch today. Nothing scary, just go easy on yourself."
        return "Rough patch, it happens. Check your advice and take it easy."

    def draw_hero(self, c, x1, y1, x2, y2):
        p = self.p
        rrect(c, x1, y1, x2, y2, r=26, fill=CARD, outline=LINE, tags="hero")
        lvl, into, need = level_info(p["xp"])
        frac = into / need
        cy = (y1 + y2) / 2
        bx, br = x1 + 86, 50
        c.create_oval(bx - br, cy - br, bx + br, cy + br, outline=CARD2, width=10, tags="hero")
        c.create_arc(bx - br, cy - br, bx + br, cy + br, start=90, extent=-max(frac * 359.9, 0.5),
                     style="arc", outline=ACCENT, width=10, tags="hero")
        c.create_text(bx, cy - 6, text=str(lvl), fill=TEXT, font=(FONT, 34, "bold"), tags="hero")
        c.create_text(bx, cy + 26, text="LEVEL", fill=MUTED, font=(FONT, 8, "bold"), tags="hero")
        tx, bx2 = x1 + 170, x2 - 300
        c.create_text(tx, y1 + 34, anchor="w", text=title_for(lvl), fill=TEXT, font=(FONT, 21, "bold"), tags="hero")
        c.create_text(tx, y1 + 60, anchor="w", text=f"{need - into} XP until {title_for(lvl + 1)}",
                      fill=MUTED, font=(FONT, 11), tags="hero")
        by1, by2 = y1 + 78, y1 + 102
        draw_xp_bar(c, tx, by1, bx2, by2, frac, ACCENT, ACCENT2, "hero")
        self.xp_geom = (self.current, tx, by1, bx2, by2, frac)
        c.create_text(tx, y1 + 120, anchor="w", text=f"{into} of {need} XP this level", fill=MUTED,
                      font=(FONT, 10), tags="hero")
        c.create_text(bx2, y1 + 120, anchor="e", text=f"{p['xp']} XP total", fill=MUTED, font=(FONT, 10), tags="hero")
        st = profile_streak(p)
        sx = x2 - 270
        draw_flame(c, sx + 22, y1 + 44, 22, "hero", hot=st > 0)
        c.create_text(sx + 58, y1 + 40, anchor="w", text=str(st), fill=TEXT, font=(FONT, 30, "bold"), tags="hero")
        c.create_text(sx + 58, y1 + 66, anchor="w", text="day streak", fill=MUTED, font=(FONT, 10), tags="hero")
        c.create_text(x2 - 26, y1 + 40, anchor="e", text=f"Best {max(p['stats']['best_streak'], st)}",
                      fill=WATCH, font=(FONT, 10, "bold"), tags="hero")
        sh = p.get("shields", 0)
        draw_shield(c, x2 - 76, y1 + 68, 8, "#6bb8e8", "hero")
        c.create_text(x2 - 62, y1 + 68, anchor="w", text=f"x{sh}", fill="#6bb8e8" if sh else MUTED,
                      font=(FONT, 10, "bold"), tags="hero")
        for i, (letter, done, is_today, shielded) in enumerate(week_activity(p)):
            cx, cyy = sx + 10 + i * 36, y1 + 100
            ring = "#6bb8e8" if shielded else (GOOD if done else LINE)
            c.create_oval(cx - 11, cyy - 11, cx + 11, cyy + 11,
                          fill="#6bb8e8" if shielded else (GOOD if done else CARD2),
                          outline=ACCENT if is_today else ring, width=2, tags="hero")
            if shielded:
                c.create_text(cx, cyy, text="\u2744", fill=INK, font=(FONT, 9, "bold"), tags="hero")
            elif done:
                c.create_text(cx, cyy, text="\u2713", fill="#06231a", font=(FONT, 9, "bold"), tags="hero")
            c.create_text(cx, cyy + 20, text=letter, fill=MUTED, font=(FONT, 8), tags="hero")

    def _quest_rows(self, c, x1, y, x2, step, pillfn):
        q = self.p["quests"]
        for i, (qid, title, pts) in enumerate(QUESTS):
            yy = y + i * step
            done = q["done"].get(qid)
            c.create_oval(x1, yy - 11, x1 + 22, yy + 11, fill=GOOD if done else CARD2,
                          outline=GOOD if done else LINE, width=2)
            if done:
                c.create_text(x1 + 11, yy, text="✓", fill="#06231a", font=(FONT, 10, "bold"))
            c.create_text(x1 + 34, yy, anchor="w", text=title, fill=MUTED if done else TEXT,
                          font=(FONT, 11, "normal" if done else "bold"))
            if qid == "water":
                n, pw = q["water"], 90
                pillfn("+ Drink", self.drink, x2 - pw, yy - 13, pw, 26)
                x0 = x2 - pw - 16 - WATER_GOAL * 15
                for k in range(WATER_GOAL):
                    cx = x0 + k * 15 + 7
                    c.create_oval(cx - 5, yy - 5, cx + 5, yy + 5, fill="#6bb8e8" if k < n else CARD2,
                                  outline="#6bb8e8" if k < n else LINE)
                c.create_text(x0 - 8, yy, anchor="e", text=f"{n}/{WATER_GOAL}", fill=MUTED, font=(FONT, 10))
            else:
                c.create_text(x2, yy, anchor="e", text=f"+{pts} XP", fill=GOOD if done else MUTED,
                              font=(FONT, 10, "bold"))

    def draw_home(self):
        c = self.home
        for w in self.hw:
            w.destroy()
        self.hw = []
        c.delete("all")
        W = max(c.winfo_width(), 960)
        m = 28
        p, lat = self.p, self.latest
        hour = dt.datetime.now().hour
        greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        day = lat["day"] if lat else self.day_var.get()
        who = "astronaut" if self.store.is_guest else p["name"]
        draw_mascot(c, m + 34, 54, .72, "nova", self.mascot_mood(), scarf="scarf" in p.get("owned", []))
        c.create_text(m + 84, 38, anchor="w", text=f"{greet}, {who}", fill=TEXT, font=(HEAD, 25, "bold"))
        c.create_text(m + 84, 74, anchor="w", text=self.mood_line(), fill=MUTED, font=(FONT, 12))
        c.create_text(W - m, 40, anchor="e", text=f"{p['env']}   ·   Day {day}", fill=ENVS[p["env"]]["color"],
                      font=(FONT, 12, "bold"))
        c.create_text(W - m, 66, anchor="e", text=CREW_NOTES[self.tip_seed % len(CREW_NOTES)], fill=mix(MUTED, BG, .2),
                      font=(FONT, 10, "italic"), width=int(W * .42), justify="right")

        # hero (level + xp + streak)
        self.draw_hero(c, m, 112, W - m, 252)
        c.tag_bind("hero", "<Button-1>", lambda e: self.show("rewards"))

        # gauge card
        gx1, gy1, gx2, gy2 = m, 272, m + 330, 592
        rrect(c, gx1, gy1, gx2, gy2, r=26, fill=CARD, outline=LINE)
        c.create_text(gx1 + 24, gy1 + 28, anchor="w", text="OVERALL READINESS", fill=MUTED, font=(FONT, 10, "bold"))
        self.gcx, self.gcy, self.gr = (gx1 + gx2) / 2, gy1 + 168, 104
        self.draw_gauge()
        if lat:
            c.create_text((gx1 + gx2) / 2, gy2 - 24, text=f"Last check-in  {lat['time']}", fill=MUTED, font=(FONT, 9))

        # focus card
        fx1, fy1, fx2, fy2 = gx2 + 16, 272, W - m, 414
        alerts = lat["alerts"] if lat else []
        fill = mix(CARD, CRIT, 0.2) if alerts else CARD
        rrect(c, fx1, fy1, fx2, fy2, r=26, fill=fill, outline=CRIT if alerts else LINE)
        tx = fx1 + 26
        if not lat:
            title, col = "Welcome aboard", ACCENT
            body = "Answer a few simple questions about how you feel. No medical equipment needed."
        elif alerts:
            title, col = "Please get medical advice", CRIT
            body = "\n".join("• " + a for a in alerts[:3]) + "\nContact the flight surgeon now."
        else:
            worst = min(DOMAINS, key=lambda d: lat["scores"][d])
            sc = lat["scores"][worst]
            if sc >= 80:
                title, col = "You are on track", GOOD
                body = random.Random(self.tip_seed).choice(ADVICE[worst]["good"])
            else:
                title, col = f"Today's focus: {worst}", DOMAIN_COLORS[worst]
                body = ADVICE[worst][level_of(sc)][0]
        c.create_text(tx, fy1 + 30, anchor="w", text=title, fill=col, font=(FONT, 15, "bold"))
        c.create_text(tx, fy1 + 52, anchor="nw", text=body, fill=TEXT, font=(FONT, 11), width=fx2 - fx1 - 52)
        self._hp("Check in again" if lat and lat["time"][:10] == today() else "Start today's check-in",
                 lambda: self.show("checkin"), tx, fy2 - 20, w=210, h=38, anchor="sw", surface=fill)

        # quests card
        qy1, qy2 = 430, 592
        rrect(c, fx1, qy1, fx2, qy2, r=26, fill=CARD, outline=LINE, tags="quests")
        q = p["quests"]
        done_n = sum(1 for k, _, _ in QUESTS if q["done"].get(k))
        c.create_text(tx, qy1 + 26, anchor="w", text="TODAY'S QUESTS", fill=MUTED, font=(FONT, 10, "bold"), tags="quests")
        c.create_text(fx2 - 26, qy1 + 26, anchor="e", text=f"{done_n} of {len(QUESTS)} done"
                      + ("   ·   bonus earned" if q.get("bonus") else f"   ·   +{BONUS_XP} XP bonus for all"),
                      fill=GOOD if q.get("bonus") else MUTED, font=(FONT, 10, "bold"), tags="quests")
        self._quest_rows(c, tx, qy1 + 56, fx2 - 26, 30, lambda t, cmd, x, y, w, h: self._hp(
            t, cmd, x, y, w, h, surface=CARD, fill=ACCENT))

        # health area cards
        gap = 14
        cw = (W - 2 * m - 4 * gap) / 5
        y1, y2 = 612, 764
        for i, d in enumerate(DOMAINS):
            x1 = m + i * (cw + gap)
            x2 = x1 + cw
            col = DOMAIN_COLORS[d]
            sc = lat["scores"][d] if lat else 0
            rrect(c, x1, y1, x2, y2, r=22, fill=CARD, outline=LINE, tags="dom")
            rrect(c, x1 + 16, y1 + 16, x1 + 60, y1 + 60, r=14, fill=mix(CARD, col, 0.2), outline="", tags="dom")
            draw_icon(c, d, x1 + 38, y1 + 38, 10, col, mix(CARD, col, 0.2), "dom")
            c.create_text(x1 + 18, y1 + 78, anchor="w", text=d, fill=TEXT, font=(FONT, 11, "bold"), tags="dom")
            c.create_text(x1 + 18, y1 + 108, anchor="w", text=str(sc) if lat else "--",
                          fill=status_of(sc)[1] if lat else MUTED, font=(FONT, 26, "bold"), tags="dom")
            if lat:
                c.create_text(x2 - 16, y1 + 112, anchor="e", text=status_of(sc)[0].title(), fill=MUTED,
                              font=(FONT, 9), tags="dom")
            rrect(c, x1 + 18, y2 - 24, x2 - 18, y2 - 16, r=4, fill=CARD2, outline="", tags="dom")
            if sc > 4:
                rrect(c, x1 + 18, y2 - 24, x1 + 18 + (cw - 36) * sc / 100, y2 - 16, r=4, fill=col, outline="", tags="dom")
        c.tag_bind("dom", "<Button-1>", lambda e: self.show("advice"))
        c.tag_bind("quests", "<Button-1>", lambda e: self.show("rewards"))
        for tag in ("dom", "hero", "quests"):
            c.tag_bind(tag, "<Enter>", lambda e: c.config(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda e: c.config(cursor=""))

        # routine card
        half = (W - 2 * m - 16) / 2
        ry1, ry2 = 784, 984
        rrect(c, m, ry1, m + half, ry2, r=26, fill=CARD, outline=LINE)
        c.create_text(m + 24, ry1 + 28, anchor="w", text="MISSION ROUTINE", fill=MUTED, font=(FONT, 10, "bold"))
        due = due_tasks(p)
        if due:
            for i, (t, late) in enumerate(due[:3]):
                yy = ry1 + 74 + i * 44
                c.create_oval(m + 24, yy - 16, m + 56, yy + 16, fill=mix(CARD, t["color"], .25), outline=t["color"], width=2)
                c.create_text(m + 40, yy, text=t["glyph"], fill=TEXT, font=(FONT, 12, "bold"))
                c.create_text(m + 70, yy - 8, anchor="w", text=t["title"], fill=TEXT, font=(FONT, 11, "bold"))
                sub = "First reading" if not last_measure(p, t["id"]) else \
                    ("Due today" if late == 0 else f"Overdue by {late} day{'s' if late > 1 else ''}")
                c.create_text(m + 70, yy + 10, anchor="w", text=sub, fill=CAUTION if late else MUTED, font=(FONT, 9))
                self._hp("Start", lambda tid=t["id"]: self.open_task(tid), m + half - 24 - 84, yy - 15, 84, 30,
                         fill=ACCENT)
            if len(due) > 3:
                c.create_text(m + 24, ry2 - 22, anchor="w", text=f"+ {len(due) - 3} more in Mission Routine",
                              fill=MUTED, font=(FONT, 10))
        else:
            c.create_text(m + 24, ry1 + 80, anchor="w", text="All caught up", fill=GOOD, font=(FONT, 16, "bold"))
            nxt = min(t["every"] - days_since(last_measure(p, t["id"])["time"]) for t in ROUTINE)
            c.create_text(m + 24, ry1 + 110, anchor="w", text=f"Next reading is due in {max(nxt, 0)} day(s).",
                          fill=MUTED, font=(FONT, 11))

        # environment card
        ex1 = m + half + 16
        env = ENVS[p["env"]]
        rrect(c, ex1, ry1, W - m, ry2, r=26, fill=CARD, outline=LINE)
        c.create_text(ex1 + 24, ry1 + 28, anchor="w", text=p["env"].upper(), fill=env["color"], font=(FONT, 11, "bold"))
        c.create_text(ex1 + 24, ry1 + 48, anchor="w", text=env["sub"], fill=MUTED, font=(FONT, 10))
        self._hp("Change", self.pick_env, W - m - 24 - 90, ry1 + 16, 90, 28, surface=CARD, ghost=True)
        lvl_col = {1: GOOD, 2: GOOD, 3: WATCH, 4: CAUTION, 5: CRIT}
        for i, (name, lv) in enumerate(env["risks"]):
            yy = ry1 + 82 + i * 22
            c.create_text(ex1 + 24, yy, anchor="w", text=name, fill=TEXT, font=(FONT, 10))
            for k in range(5):
                cx = ex1 + 160 + k * 20
                c.create_oval(cx - 7, yy - 7, cx + 7, yy + 7, fill=lvl_col[lv] if k < lv else CARD2,
                              outline=lvl_col[lv] if k < lv else LINE)
        tip = env["tips"][self.tip_seed % len(env["tips"])]
        c.create_text(ex1 + 290, ry1 + 80, anchor="nw", text="GOOD TO KNOW", fill=MUTED, font=(FONT, 9, "bold"))
        c.create_text(ex1 + 290, ry1 + 100, anchor="nw", text=tip, fill=TEXT, font=(FONT, 11),
                      width=max(150, half - 320))

        # trend card + crew card
        ty1, ty2 = 1004, 1180
        tw = int((W - 2 * m - 16) * 0.58)
        rrect(c, m, ty1, m + tw, ty2, r=26, fill=CARD, outline=LINE)
        c.create_text(m + 24, ty1 + 28, anchor="w", text="YOUR TREND", fill=MUTED, font=(FONT, 10, "bold"))
        vals = [e["overall"] for e in p["history"][-14:]]
        if len(vals) >= 2:
            diff = vals[-1] - vals[-2]
            c.create_text(m + tw - 24, ty1 + 28, anchor="e", text=f"{diff:+d} since your last check-in",
                          fill=GOOD if diff >= 0 else CAUTION, font=(FONT, 10, "bold"))
            x0, x1, yy0, yy1 = m + 30, m + tw - 40, ty1 + 56, ty2 - 24
            pts = []
            for i, v in enumerate(vals):
                pts += [x0 + (x1 - x0) * i / (len(vals) - 1), yy1 - (yy1 - yy0) * v / 100]
            c.create_polygon([x0, yy1] + pts + [x1, yy1], fill=mix(CARD, ACCENT, 0.16), outline="")
            c.create_line(pts, fill=ACCENT, width=3, smooth=True)
            c.create_oval(pts[-2] - 6, pts[-1] - 6, pts[-2] + 6, pts[-1] + 6, fill=TEXT, outline=ACCENT, width=3)
        else:
            c.create_text(m + tw / 2, (ty1 + ty2) / 2 + 10, text="Check in on a few days to see your trend.",
                          fill=MUTED, font=(FONT, 11))
        cx1 = m + tw + 16
        rrect(c, cx1, ty1, W - m, ty2, r=26, fill=CARD, outline=LINE, tags="crewcard")
        c.create_text(cx1 + 24, ty1 + 28, anchor="w", text="CREW THIS WEEK", fill=MUTED, font=(FONT, 10, "bold"),
                      tags="crewcard")
        for i, r in enumerate(leaderboard(self.store)[:3]):
            yy = ty1 + 66 + i * 34
            draw_medal(c, cx1 + 36, yy, 12, i + 1, "crewcard")
            c.create_text(cx1 + 58, yy, anchor="w", text=r["name"] + ("  (you)" if r["name"] == p["name"] else ""),
                          fill=TEXT, font=(FONT, 11, "bold"), tags="crewcard")
            c.create_text(W - m - 24, yy, anchor="e", text=f"{r['weekly']} pts", fill=ACCENT, font=(FONT, 11, "bold"),
                          tags="crewcard")
        c.tag_bind("crewcard", "<Button-1>", lambda e: self.show("crew"))
        c.tag_bind("crewcard", "<Enter>", lambda e: c.config(cursor="hand2"))
        c.tag_bind("crewcard", "<Leave>", lambda e: c.config(cursor=""))
        # streak buddy + stardust
        by1, by2 = 1198, 1346
        half2 = (W - 2 * m - 16) / 2
        bd = buddy_info(self.store, p)
        rrect(c, m, by1, m + half2, by2, r=26, fill=CARD, outline=WATCH if bd else LINE, tags="buddy")
        c.create_text(m + 24, by1 + 28, anchor="w", text="STREAK BUDDY", fill=MUTED, font=(FONT, 10, "bold"), tags="buddy")
        if bd:
            bp = self.store.get_profile(bd["name"])
            draw_avatar(c, m + 58, by1 + 86, 28, bd["name"], ENVS.get(bp["env"], ENVS["Space Station"])["color"], "buddy",
                        ring="ring" in bp.get("owned", []))
            c.create_text(m + 102, by1 + 74, anchor="w", text=bd["name"], fill=TEXT, font=(FONT, 15, "bold"), tags="buddy")
            both = bd["me_today"] and bd["buddy_today"]
            status = ("You both checked in today" if both else f"{bd['name']} is waiting for you" if bd["buddy_today"]
                      else f"Waiting for {bd['name']}" if bd["me_today"] else "Neither of you has checked in yet")
            c.create_text(m + 102, by1 + 100, anchor="w", text=status, fill=GOOD if both else MUTED, font=(FONT, 10),
                          tags="buddy")
            draw_flame(c, m + half2 - 110, by1 + 88, 24, "buddy", hot=bd["streak"] > 0)
            c.create_text(m + half2 - 78, by1 + 84, anchor="w", text=str(bd["streak"]), fill=TEXT, font=(FONT, 30, "bold"),
                          tags="buddy")
            c.create_text(m + half2 - 24, by1 + 124, anchor="e", text="joint streak", fill=MUTED, font=(FONT, 9), tags="buddy")
        else:
            c.create_text(m + 24, by1 + 58, anchor="nw", width=half2 - 48, fill=TEXT, font=(FONT, 11), tags="buddy",
                          text="Pick a crewmate. When you both check in on the same day, your joint streak grows.")
            self._hp("Choose a buddy", lambda: self.show("crew"), m + 24, by2 - 22, w=170, h=36, anchor="sw", fill=WATCH)
        sx1 = m + half2 + 16
        rrect(c, sx1, by1, W - m, by2, r=26, fill=CARD, outline=LINE, tags="stardust")
        c.create_text(sx1 + 24, by1 + 28, anchor="w", text="STARDUST & SHIELDS", fill=MUTED, font=(FONT, 10, "bold"),
                      tags="stardust")
        c.create_text(sx1 + 24, by1 + 76, anchor="w", text=f"\u2726 {gems_of(p)}", fill=ACCENT2, font=(FONT, 30, "bold"),
                      tags="stardust")
        c.create_text(sx1 + 24, by1 + 106, anchor="w", text="stardust to spend", fill=MUTED, font=(FONT, 10), tags="stardust")
        draw_shield(c, sx1 + 250, by1 + 70, 14, "#6bb8e8", "stardust")
        c.create_text(sx1 + 274, by1 + 70, anchor="w", text=f"{p.get('shields', 0)} of {SHIELD_MAX} shields", fill=TEXT,
                      font=(FONT, 11, "bold"), tags="stardust")
        c.create_text(sx1 + 274, by1 + 94, anchor="w", fill=ACCENT2 if boost_left(p) else MUTED, font=(FONT, 10),
                      tags="stardust", text=(f"Double XP: {boost_left(p) // 60}:{boost_left(p) % 60:02d} left"
                                            if boost_left(p) else "Earn 1 stardust per 5 XP"))
        self._hp("Open shop", lambda: self.show("rewards"), W - m - 24, by2 - 22, w=130, h=36, anchor="se", fill=ACCENT2)
        for tag in ("buddy", "stardust"):
            c.tag_bind(tag, "<Enter>", lambda e: c.config(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda e: c.config(cursor=""))
        c.tag_bind("buddy", "<Button-1>", lambda e: self.show("crew"))
        c.tag_bind("stardust", "<Button-1>", lambda e: self.show("rewards"))
        c.configure(scrollregion=(0, 0, W, by2 + 30))
        self.draw_shine()

    def pick_env(self):
        menu = tk.Menu(self, tearoff=0, bg=CARD2, fg=TEXT, activebackground=ACCENT, bd=0)
        for e in ENVS:
            menu.add_command(label=f"  {e}  ", command=lambda e=e: self.set_env(e))
        menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())

    def set_env(self, env):
        self.p["env"] = env
        self.store.save()
        self.refresh_all()

    def draw_gauge(self):
        c = self.home
        c.delete("gauge")
        cx, cy, r = self.gcx, self.gcy, self.gr
        lat = self.latest
        v = self.gauge_now
        label, color, _ = status_of(self.gauge_target) if lat else ("NO DATA", MUTED, "")
        box = (cx - r, cy - r, cx + r, cy + r)
        c.create_arc(*box, start=225, extent=-270, style="arc", width=20, outline=CARD2, tags="gauge")
        if v > 0.5:
            for w, t in ((38, 0.07), (30, 0.12)):
                c.create_arc(*box, start=225, extent=-270 * v / 100, style="arc", width=w,
                             outline=mix(CARD, color, t), tags="gauge")
            c.create_arc(*box, start=225, extent=-270 * v / 100, style="arc", width=20, outline=color, tags="gauge")
            for ang in (225, 225 - 270 * v / 100):
                ex, ey = cx + r * math.cos(math.radians(ang)), cy - r * math.sin(math.radians(ang))
                c.create_oval(ex - 10, ey - 10, ex + 10, ey + 10, fill=color, outline="", tags="gauge")
        c.create_text(cx, cy - 8, text=str(int(round(v))) if lat else "--", fill=TEXT, font=(FONT, 56, "bold"), tags="gauge")
        c.create_text(cx, cy + 40, text=label, fill=color, font=(FONT, 14, "bold"), tags="gauge")
        c.create_text(cx, cy + 62, text="out of 100", fill=MUTED, font=(FONT, 9), tags="gauge")

    def animate_gauge(self):
        if self._gjob:
            self.after_cancel(self._gjob)
            self._gjob = None
        self.gauge_target = self.latest["overall"] if self.latest else 0
        self._step_gauge()

    def _step_gauge(self):
        if self.current != "home":
            self._gjob = None
            return
        diff = self.gauge_target - self.gauge_now
        if abs(diff) < 0.6:
            self.gauge_now = self.gauge_target
            self.draw_gauge()
            self._gjob = None
            return
        self.gauge_now += diff * 0.1 if abs(diff) > 6 else (0.6 if diff > 0 else -0.6)
        self.draw_gauge()
        self._gjob = self.after(16, self._step_gauge)

    def draw_shine(self):
        for c in (self.home, getattr(self, "rewards", None)):
            if c is not None:
                c.delete("shine")
        g = self.xp_geom
        if not g or g[0] != self.current or self.current not in ("home", "rewards"):
            return
        c = self.home if self.current == "home" else self.rewards
        _, x1, y1, x2, y2, frac = g
        fx = x1 + (x2 - x1) * frac
        if frac < 0.04:
            return
        pos = x1 + 6 + (self.shimmer % 1.0) * (fx - x1 - 22)
        t = (pos - x1) / max(x2 - x1, 1)
        base = mix(ACCENT, ACCENT2, min(t / max(frac, 0.01), 1))
        for i, a in enumerate((0.25, 0.5, 0.25)):
            xa = pos + i * 5
            if xa + 5 < fx - 6:
                c.create_rectangle(xa, y1 + 5, xa + 5, y2 - 5, fill=mix(base, "#ffffff", a), outline="", tags="shine")

    def _shimmer_loop(self):
        if self.p is not None and self.current in ("home", "rewards"):
            self.shimmer += 0.012
            self.draw_shine()
        self.after(50, self._shimmer_loop)

    # ================================================================== CHECK-IN WIZARD
    def _build_checkin(self):
        p = tk.Frame(self.content, bg=BG)
        self.pages["checkin"] = p
        top = tk.Frame(p, bg=BG)
        top.pack(fill="x", padx=44, pady=(30, 0))
        self.ci_prog = tk.Canvas(top, height=10, bg=BG, highlightthickness=0)
        self.ci_prog.pack(fill="x")
        self.ci_prog.bind("<Configure>", lambda e: self.draw_progress())
        self.ci_count = tk.Label(top, text="", bg=BG, fg=MUTED, font=(FONT, 10))
        self.ci_count.pack(anchor="w", pady=(8, 0))
        self.ci_card = tk.Frame(p, bg=CARD, padx=44, pady=34, highlightthickness=1, highlightbackground=LINE)
        self.ci_card.pack(fill="both", expand=True, padx=44, pady=16)
        self.ci_nav = tk.Frame(p, bg=BG)
        self.ci_nav.pack(fill="x", padx=44, pady=(0, 26))
        self.opt_cards = []
        self.render_step()

    def draw_progress(self):
        c = self.ci_prog
        c.delete("all")
        w = max(c.winfo_width(), 300)
        rrect(c, 0, 0, w, 10, r=5, fill=CARD2, outline="")
        frac = self.step / (len(self.steps) - 1)
        if frac > 0:
            rrect(c, 0, 0, max(14, w * frac), 10, r=5, fill=ACCENT, outline="")
        self.ci_count.config(text="Let's begin" if self.step == 0 else f"Step {self.step} of {len(self.steps) - 1}")

    def render_step(self):
        for w in self.ci_card.winfo_children():
            w.destroy()
        for w in self.ci_nav.winfo_children():
            w.destroy()
        self.opt_cards = []
        card, nav = self.ci_card, self.ci_nav
        kind = self.steps[self.step][0]
        self.draw_progress()
        if kind == "welcome":
            tk.Label(card, text="Daily Health Check-In", bg=CARD, fg=TEXT, font=(HEAD, 28, "bold")).pack(anchor="w")
            tk.Label(card, text=f"Hi {self.p['name']}. Answer a few simple questions about how you feel today.\n"
                                "No medical knowledge or equipment needed. It takes about 2 minutes.",
                     bg=CARD, fg=MUTED, font=(FONT, 13), justify="left").pack(anchor="w", pady=(10, 26))
            tk.Label(card, text="Mission day", bg=CARD, fg=MUTED, font=(FONT, 10, "bold")).pack(anchor="w")
            self._entry(card, self.day_var, 8).pack(anchor="w", ipady=6, pady=(4, 0))
            Pill(nav, "Begin  ›", self.begin, w=170, h=46).pack(side="right")
        elif kind == "q":
            q = self.steps[self.step][1]
            tk.Label(card, text=q["d"].upper(), bg=CARD, fg=DOMAIN_COLORS[q["d"]], font=(FONT, 10, "bold")).pack(anchor="w")
            tk.Label(card, text=q["q"], bg=CARD, fg=TEXT, font=(FONT, 22, "bold"), wraplength=860,
                     justify="left").pack(anchor="w", pady=(8, 4))
            tk.Label(card, text=q["h"], bg=CARD, fg=MUTED, font=(FONT, 12), wraplength=860,
                     justify="left").pack(anchor="w", pady=(0, 30))
            row = tk.Frame(card, bg=CARD)
            row.pack(anchor="w")
            for i, opt in enumerate(q["o"]):
                oc = OptionCard(row, i, opt, self.pick, selected=self.answers.get(q["id"]) == i)
                oc.pack(side="left", padx=(0, 14))
                self.opt_cards.append(oc)
            Pill(nav, "‹  Back", lambda: self.go(-1), w=130, h=44, ghost=True).pack(side="left")
            Pill(nav, "Skip  ›", lambda: self.go(1), w=130, h=44, ghost=True).pack(side="right")
        elif kind == "pulse":
            tk.Label(card, text="OPTIONAL", bg=CARD, fg=ACCENT, font=(FONT, 10, "bold")).pack(anchor="w")
            tk.Label(card, text="Do you know your resting pulse?", bg=CARD, fg=TEXT,
                     font=(FONT, 22, "bold")).pack(anchor="w", pady=(8, 4))
            tk.Label(card, text="Only if your watch or device shows it. You can learn how to measure it in Mission "
                                "Routine. Skip this if you do not know it.", bg=CARD, fg=MUTED, font=(FONT, 12),
                     wraplength=860, justify="left").pack(anchor="w", pady=(0, 24))
            row = tk.Frame(card, bg=CARD)
            row.pack(anchor="w")
            self._entry(row, self.pulse_var, 8).pack(side="left", ipady=8)
            tk.Label(row, text="beats per minute", bg=CARD, fg=MUTED, font=(FONT, 12)).pack(side="left", padx=12)
            Pill(nav, "‹  Back", lambda: self.go(-1), w=130, h=44, ghost=True).pack(side="left")
            Pill(nav, "Next  ›", self.pulse_next, w=150, h=46).pack(side="right")
        else:
            tk.Label(card, text="LAST STEP", bg=CARD, fg=CRIT, font=(FONT, 10, "bold")).pack(anchor="w")
            tk.Label(card, text="Is anything urgent right now?", bg=CARD, fg=TEXT,
                     font=(FONT, 22, "bold")).pack(anchor="w", pady=(8, 4))
            tk.Label(card, text="Tap anything that applies. If none, just continue.", bg=CARD, fg=MUTED,
                     font=(FONT, 12)).pack(anchor="w", pady=(0, 18))
            for f in RED_FLAGS:
                Chip(card, f, CRIT, on_toggle=lambda s, f=f: self.flag_state.__setitem__(f, s),
                     selected=self.flag_state.get(f, False), surface=CARD).pack(anchor="w", pady=4)
            Pill(nav, "‹  Back", lambda: self.go(-1), w=130, h=44, ghost=True).pack(side="left")
            Pill(nav, "See my results  ›", self.submit, w=210, h=46).pack(side="right")

    def begin(self):
        day = self.day_var.get().strip()
        if not day.isdigit() or int(day) < 1:
            messagebox.showwarning("Mission day", "Please enter the mission day as a whole number, for example 45.")
            return
        self.step = 1
        self.render_step()

    def pick(self, idx):
        q = self.steps[self.step][1]
        self.answers[q["id"]] = idx
        for i, oc in enumerate(self.opt_cards):
            oc.set_selected(i == idx)
        at = self.step
        self.after(260, lambda: self.go(1) if self.step == at else None)

    def go(self, delta):
        self.step = max(0, min(len(self.steps) - 1, self.step + delta))
        self.render_step()

    def pulse_next(self):
        raw = self.pulse_var.get().strip()
        if raw:
            try:
                v = float(raw)
            except ValueError:
                messagebox.showwarning("Pulse", "Please enter a number, or leave it empty.")
                return
            if not 20 <= v <= 250:
                messagebox.showwarning("Pulse", "Please enter a pulse between 20 and 250, or leave it empty.")
                return
        self.go(1)

    def submit(self):
        p = self.p
        raw = self.pulse_var.get().strip()
        pulse = float(raw) if raw else None
        flags = [f for f, on in self.flag_state.items() if on]
        res = analyze(self.answers, pulse, flags, p["history"])
        entry = dict(time=dt.datetime.now().strftime("%Y-%m-%d %H:%M"), crew=p["name"],
                     day=self.day_var.get().strip() or "1", scores=res["scores"], overall=res["overall"],
                     pulse=pulse, flags=flags, answers=dict(self.answers), alerts=res["alerts"], notes=res["notes"])
        p["history"].append(entry)
        events = complete_quest(p, "checkin")
        if pulse is not None:
            events += record_measure(p, "pulse", pulse)
        self.answers, self.flag_state, self.step = {}, {}, 0
        self.pulse_var.set("")
        self.render_step()
        self.refresh_advice()
        self.refresh_progress_table()
        self.show("home")
        self.reward(events)
        if entry["alerts"]:
            alerts = list(entry["alerts"])
            self.queue_modal(lambda done: self.show_critical(alerts, done), urgent=True)

    # ================================================================== MISSION ROUTINE
    def _build_routine(self):
        p = tk.Frame(self.content, bg=BG)
        self.pages["routine"] = p
        tk.Label(p, text="Mission Routine", bg=BG, fg=TEXT, font=(HEAD, 25, "bold")).pack(anchor="w", padx=34, pady=(28, 2))
        tk.Label(p, text="Short regular measurements. Each one comes with simple instructions and an explanation.",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack(anchor="w", padx=34, pady=(0, 12))
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=34, pady=(0, 20))
        left = tk.Frame(body, bg=CARD, width=270, padx=10, pady=12, highlightthickness=1, highlightbackground=LINE)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self.task_menu = ListMenu(left, self.show_task)
        self.task_menu.pack(fill="x")
        self.task_detail = tk.Frame(body, bg=CARD, padx=34, pady=26, highlightthickness=1, highlightbackground=LINE)
        self.task_detail.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.task_val = tk.StringVar()

    def refresh_routine_list(self):
        p = self.p
        due = {t["id"] for t, _ in due_tasks(p)}
        sel = self.task_menu.sel or 0
        self.task_menu.set_items([f"{t['glyph']}   {t['title']}" + ("      • due" if t["id"] in due else "")
                                  for t in ROUTINE], sel)

    def open_task(self, tid):
        idx = [t["id"] for t in ROUTINE].index(tid)
        self.show("routine")
        self.task_menu.select(idx, True)

    def show_task(self, i, keep_msg=False):
        t = ROUTINE[i]
        p = self.p
        d = self.task_detail
        for w in d.winfo_children():
            w.destroy()
        self.task_val.set("")
        head = tk.Frame(d, bg=CARD)
        head.pack(fill="x")
        tk.Label(head, text=f"{t['glyph']}  {t['title']}", bg=CARD, fg=TEXT, font=(FONT, 22, "bold")).pack(side="left")
        tk.Label(head, text=f"every {t['every']} day{'s' if t['every'] > 1 else ''}   ·   +{t['xp']} XP", bg=CARD,
                 fg=MUTED, font=(FONT, 10, "bold")).pack(side="right")
        tk.Label(d, text=t["prompt"], bg=CARD, fg=ACCENT, font=(FONT, 12, "bold")).pack(anchor="w", pady=(6, 12))
        cols = tk.Frame(d, bg=CARD)
        cols.pack(fill="x")
        a = tk.Frame(cols, bg=CARD)
        a.pack(side="left", fill="both", expand=True, anchor="n")
        tk.Label(a, text="HOW TO MEASURE", bg=CARD, fg=GOOD, font=(FONT, 10, "bold")).pack(anchor="w")
        for n, s in enumerate(t["steps"], 1):
            tk.Label(a, text=f"{n}.  {s}", bg=CARD, fg=TEXT, font=(FONT, 11), wraplength=330, justify="left",
                     anchor="w").pack(fill="x", pady=3)
        b = tk.Frame(cols, bg=CARD)
        b.pack(side="left", fill="both", expand=True, anchor="n", padx=(20, 0))
        tk.Label(b, text="WHY IT MATTERS", bg=CARD, fg=WATCH, font=(FONT, 10, "bold")).pack(anchor="w")
        tk.Label(b, text=t["why"], bg=CARD, fg=TEXT, font=(FONT, 11), wraplength=300, justify="left").pack(anchor="w", pady=3)
        # range bar
        last = last_measure(p, t["id"])
        bar = tk.Canvas(d, height=96, bg=CARD, highlightthickness=0)
        bar.pack(fill="x", pady=(18, 4))
        bar.bind("<Configure>", lambda e, t=t, last=last: self._range_bar(bar, t, last))
        self.after(30, lambda: self._range_bar(bar, t, last))
        # entry
        row = tk.Frame(d, bg=CARD)
        if t.get("diopter"):
            self.dial = DiopterDial(d, value=(last["value"] if last else 0.0), surface=CARD)
            self.dial.pack(fill="x", pady=(8, 0))
            row.pack(anchor="w", pady=(4, 0))
            Pill(row, "Save reading", lambda: self.save_reading(i), w=170, h=44, surface=CARD).pack(side="left")
            tk.Label(row, text="Drag the handle, click the track, or use \u2212 / + (arrow keys work too).",
                     bg=CARD, fg=MUTED, font=(FONT, 10)).pack(side="left", padx=16)
        else:
            row.pack(anchor="w", pady=(10, 0))
            self._entry(row, self.task_val, 10, 14).pack(side="left", ipady=7)
            tk.Label(row, text=t["unit"], bg=CARD, fg=MUTED, font=(FONT, 11)).pack(side="left", padx=12)
            Pill(row, "Save reading", lambda: self.save_reading(i), w=150, h=42, surface=CARD).pack(side="left", padx=8)
        self.task_msg = tk.Label(d, text="", bg=CARD, fg=MUTED, font=(FONT, 11, "bold"), wraplength=700, justify="left")
        self.task_msg.pack(anchor="w", pady=(10, 0))
        recent = [m for m in p["measures"] if m["task"] == t["id"]][-3:]
        if recent:
            tk.Label(d, text="Recent: " + "   ·   ".join(f"{fmt_reading(t['id'], m['value'])} ({m['time'][5:10]})" for m in reversed(recent)),
                     bg=CARD, fg=MUTED, font=(FONT, 10)).pack(anchor="w", pady=(6, 0))

    def _range_bar(self, c, t, last):
        if t.get("diopter"):
            return self._diopter_bar(c, t, last)
        c.delete("all")
        W = max(c.winfo_width(), 300)
        x1, x2, y1, y2 = 8, W - 8, 30, 52
        lo, hi = t["axis"]

        def px(v):
            return x1 + (x2 - x1) * (max(lo, min(hi, v)) - lo) / (hi - lo)
        c.create_text(x1, 12, anchor="w", text="NORMAL RANGE" if t.get("ranges") else "YOUR READINGS",
                      fill=MUTED, font=(FONT, 9, "bold"))
        if t.get("ranges"):
            for a, b, col, label in t["ranges"]:
                xa, xb = px(a), px(b)
                rrect(c, xa + 1, y1, xb - 1, y2, r=6, fill=col, outline="")
                c.create_text((xa + xb) / 2, y2 + 14, text=label, fill=MUTED, font=(FONT, 8))
        else:
            rrect(c, x1, y1, x2, y2, r=6, fill=CARD2, outline=LINE)
            note = "Compared with your first reading." if t.get("baseline") else "Just for your records."
            c.create_text((x1 + x2) / 2, y2 + 14, text=note, fill=MUTED, font=(FONT, 8))
        if last:
            x = px(last["value"])
            col, label = measure_status(t, last["value"], self.p)
            c.create_polygon(x - 8, y1 - 8, x + 8, y1 - 8, x, y1 + 2, fill=TEXT, outline="")
            c.create_text(min(max(x, 40), W - 60), 12, anchor="c" if False else "w", text=f"Last: {last['value']:g}  {label}",
                          fill=col, font=(FONT, 10, "bold")) if x < W - 200 else \
                c.create_text(x - 10, 12, anchor="e", text=f"Last: {last['value']:g}  {label}", fill=col, font=(FONT, 10, "bold"))

    def save_reading(self, i):
        t = ROUTINE[i]
        if t.get("diopter"):
            v = self.dial.value
        else:
            raw = self.task_val.get().strip().replace(",", ".")
            try:
                v = float(raw)
            except ValueError:
                self.task_msg.config(text="Please type a number.", fg=CAUTION)
                return
            lo, hi = t["axis"]
            if not (lo * 0.5 <= v <= hi * 1.5):
                self.task_msg.config(text=f"That looks unusual. Please double-check the number ({lo} to {hi} is typical).",
                                     fg=CAUTION)
                return
        events = record_measure(self.p, t["id"], v)
        col, label = measure_status(t, v, self.p)
        if t.get("diopter"):
            explain = {ACCENT: "Your first reading is saved as your baseline. Later readings are compared with it.",
                       GOOD: "Steady compared with your baseline. Nice.",
                       WATCH: "A small shift from your baseline. Re-check in a few days and keep an eye on it.",
                       CRIT: "A notable shift from your baseline. Re-check once, and if it stays like this, "
                             "tell the flight surgeon."}
        else:
            explain = {GOOD: "That's in the normal range. Nice.",
                       WATCH: "A little outside normal. Check again later and keep an eye on it.",
                       CRIT: "That's well outside normal. Re-measure after resting. If it stays like this, "
                             "tell the flight surgeon."}
        self.reward(events)
        self.show_task(i)
        self.task_msg.config(text=f"{label}. {explain.get(col, 'Reading saved.')}", fg=col)

    # ================================================================== ADVICE
    def _build_advice(self):
        p = tk.Frame(self.content, bg=BG)
        self.pages["advice"] = p
        tk.Label(p, text="My Advice", bg=BG, fg=TEXT, font=(HEAD, 25, "bold")).pack(anchor="w", padx=34, pady=(28, 2))
        self.adv_sub = tk.Label(p, text="", bg=BG, fg=MUTED, font=(FONT, 12))
        self.adv_sub.pack(anchor="w", padx=34, pady=(0, 10))
        self.adv_scroll = ScrollFrame(p)
        self.adv_scroll.pack(fill="both", expand=True, padx=(34, 20), pady=(0, 16))
        p.scroll_canvas = self.adv_scroll.canvas

    def _banner(self, parent, text, color):
        bg = mix(CARD, color, 0.2)
        b = tk.Frame(parent, bg=bg, highlightthickness=1, highlightbackground=color)
        b.pack(fill="x", pady=5)
        tk.Label(b, text=text, bg=bg, fg=TEXT, font=(FONT, 11, "bold"), wraplength=760, justify="left",
                 anchor="w", padx=16, pady=10).pack(fill="x")

    def refresh_advice(self):
        inner = self.adv_scroll.inner
        for w in inner.winfo_children():
            w.destroy()
        e, p = self.latest, self.p
        env = ENVS[p["env"]]
        if not e:
            self.adv_sub.config(text="Complete a daily check-in to get personal advice.")
            Pill(inner, "Start check-in", lambda: self.show("checkin"), w=200, h=46).pack(anchor="w", pady=10)
        else:
            label, col, sentence = status_of(e["overall"])
            self.adv_sub.config(text=f"{p['name']}  ·  Day {e['day']}  ·  {label.title()}: {sentence}")
            for a in e["alerts"]:
                self._banner(inner, "⚠  URGENT: " + a + " Contact the flight surgeon now.", CRIT)
            for n in e["notes"]:
                self._banner(inner, "ℹ  " + n, WATCH)
        # environment card
        card = tk.Frame(inner, bg=CARD, highlightthickness=1, highlightbackground=LINE)
        card.pack(fill="x", pady=7)
        tk.Frame(card, bg=env["color"], width=6).pack(side="left", fill="y")
        body = tk.Frame(card, bg=CARD)
        body.pack(side="left", fill="both", expand=True, padx=20, pady=14)
        tk.Label(body, text=f"Where you are: {p['env']}", bg=CARD, fg=env["color"], font=(FONT, 15, "bold")).pack(anchor="w")
        for tip in env["tips"]:
            tk.Label(body, text="•  " + tip, bg=CARD, fg=TEXT, font=(FONT, 11), wraplength=740, justify="left",
                     anchor="w").pack(fill="x", pady=3)
        if e:
            for d in sorted(DOMAINS, key=lambda d: e["scores"][d]):
                sc = e["scores"][d]
                lvl = level_of(sc)
                tag = {"good": "On track", "watch": "Keep an eye on this", "high": "Needs attention"}[lvl]
                tcol = {"good": GOOD, "watch": WATCH, "high": CRIT}[lvl]
                card = tk.Frame(inner, bg=CARD, highlightthickness=1, highlightbackground=LINE)
                card.pack(fill="x", pady=7)
                tk.Frame(card, bg=DOMAIN_COLORS[d], width=6).pack(side="left", fill="y")
                body = tk.Frame(card, bg=CARD)
                body.pack(side="left", fill="both", expand=True, padx=20, pady=14)
                head = tk.Frame(body, bg=CARD)
                head.pack(fill="x")
                tk.Label(head, text=d, bg=CARD, fg=DOMAIN_COLORS[d], font=(FONT, 15, "bold")).pack(side="left")
                tk.Label(head, text=f"{sc}/100  ·  {tag}", bg=CARD, fg=tcol, font=(FONT, 11, "bold")).pack(side="right")
                for tip in ADVICE[d][lvl]:
                    tk.Label(body, text="•  " + tip, bg=CARD, fg=TEXT, font=(FONT, 11), wraplength=740,
                             justify="left", anchor="w").pack(fill="x", pady=3)
        row = tk.Frame(inner, bg=BG)
        row.pack(anchor="w", pady=14)
        Pill(row, "Open exercise plan", lambda: self.show("exercise"), w=210, h=44).pack(side="left", padx=(0, 10))
        Pill(row, "Medicine guide", lambda: self.show("meds"), w=180, h=44, ghost=True).pack(side="left")

    # ================================================================== MEDICINE GUIDE
    def _build_meds(self):
        p = tk.Frame(self.content, bg=BG)
        self.pages["meds"] = p
        tk.Label(p, text="Medicine Guide", bg=BG, fg=TEXT, font=(HEAD, 25, "bold")).pack(anchor="w", padx=34, pady=(28, 2))
        tk.Label(p, text="Educational overview of common onboard medical kit options. Always confirm the medicine and "
                         "dose with the flight surgeon.", bg=BG, fg=WATCH, font=(FONT, 11), wraplength=900,
                 justify="left").pack(anchor="w", padx=34, pady=(0, 12))
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=34, pady=(0, 20))
        left = tk.Frame(body, bg=CARD, width=300, padx=10, pady=12, highlightthickness=1, highlightbackground=LINE)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self.med_search = tk.StringVar()
        tk.Entry(left, textvariable=self.med_search, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat",
                 font=(FONT, 12), highlightthickness=2, highlightbackground=LINE,
                 highlightcolor=ACCENT).pack(fill="x", ipady=6, pady=(0, 4))
        tk.Label(left, text="Search: type a symptom", bg=CARD, fg=MUTED, font=(FONT, 9)).pack(anchor="w", pady=(0, 6))
        self.med_menu = ListMenu(left, self.show_med, pady=7)
        self.med_menu.pack(fill="both", expand=True)
        self.med_detail = tk.Frame(body, bg=CARD, padx=34, pady=28, highlightthickness=1, highlightbackground=LINE)
        self.med_detail.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.med_names = list(MEDKIT)
        self.med_search.trace_add("write", lambda *a: self.filter_meds())
        self.filter_meds()

    def filter_meds(self):
        q = self.med_search.get().strip().lower()
        self.med_names = [n for n in MEDKIT if q in n.lower() or any(q in o.lower() for o in MEDKIT[n]["options"])]
        self.med_menu.set_items(self.med_names, 0 if self.med_names else None)
        if self.med_names:
            self.show_med(0)
        else:
            for w in self.med_detail.winfo_children():
                w.destroy()
            tk.Label(self.med_detail, text="No matches found.", bg=CARD, fg=MUTED, font=(FONT, 13)).pack(anchor="w")

    def show_med(self, i):
        if i >= len(self.med_names):
            return
        name = self.med_names[i]
        m = MEDKIT[name]
        d = self.med_detail
        for w in d.winfo_children():
            w.destroy()

        def head(t, col):
            tk.Label(d, text=t, bg=CARD, fg=col, font=(FONT, 11, "bold")).pack(anchor="w", pady=(18, 4))
        tk.Label(d, text=name, bg=CARD, fg=TEXT, font=(FONT, 22, "bold")).pack(anchor="w")
        head("POSSIBLE KIT OPTIONS", GOOD)
        for o in m["options"]:
            tk.Label(d, text="•  " + o, bg=CARD, fg=TEXT, font=(FONT, 12), wraplength=560, justify="left",
                     anchor="w").pack(fill="x", pady=2)
        head("SELF-CARE TIPS", ACCENT)
        tk.Label(d, text=m["notes"], bg=CARD, fg=TEXT, font=(FONT, 12), wraplength=560, justify="left").pack(anchor="w")
        head("CALL THE FLIGHT SURGEON IF", CRIT)
        tk.Label(d, text=m["call"], bg=CARD, fg=TEXT, font=(FONT, 12), wraplength=560, justify="left").pack(anchor="w")

    # ================================================================== EXERCISE
    def _build_exercise(self):
        p = tk.Frame(self.content, bg=BG)
        self.pages["exercise"] = p
        tk.Label(p, text="Exercise", bg=BG, fg=TEXT, font=(HEAD, 25, "bold")).pack(anchor="w", padx=34, pady=(24, 2))
        tk.Label(p, text="Watch the move, follow along, and let the coach cam count your reps (optional).",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack(anchor="w", padx=34, pady=(0, 10))
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=34, pady=(0, 16))

        left = tk.Frame(body, bg=CARD, width=250, padx=8, pady=12, highlightthickness=1, highlightbackground=LINE)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Label(left, text="PLAN", bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=8)
        self.plan_names = ["Auto (best for me)"] + list(PLANS)
        self.plan_menu = ListMenu(left, self.choose_plan, pady=6)
        self.plan_menu.pack(fill="x", pady=(2, 10))
        self.plan_menu.set_items(self.plan_names, 0)
        tk.Label(left, text="STEPS", bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=8)
        self.step_menu = ListMenu(left, self.pick_step, pady=6)
        self.step_menu.pack(fill="x", pady=(2, 6))
        self.demo_var = tk.BooleanVar(value=False)
        tk.Checkbutton(left, text="Quick demo (10 s steps, no XP)", variable=self.demo_var, bg=CARD, fg=MUTED,
                       selectcolor=CARD2, activebackground=CARD, activeforeground=TEXT, font=(FONT, 9),
                       command=lambda: self.reset_timer(keep_idx=True)).pack(anchor="w", padx=6)

        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(14, 0))
        top = tk.Frame(right, bg=BG)
        top.pack(fill="x")
        self.demo = Demonstrator(top, 310, 270)
        self.demo.pack(side="left")
        cam = tk.Frame(top, bg=CARD, highlightthickness=1, highlightbackground=LINE)
        cam.pack(side="left", fill="both", expand=True, padx=(14, 0))
        tk.Label(cam, text="COACH CAM", bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=14, pady=(10, 4))
        self.cam_canvas = tk.Canvas(cam, width=CAM_W, height=CAM_H, bg=CARD2, highlightthickness=0)
        self.cam_canvas.pack(padx=12)
        stats = tk.Frame(cam, bg=CARD)
        stats.pack(fill="x", padx=12, pady=(8, 0))
        self.cam_reps = self._stat(stats, "REPS", "0")
        self.cam_form = self._stat(stats, "FORM", "--")
        self.cam_last = self._stat(stats, "LAST", "--")
        self.cam_status = tk.Label(cam, text="", bg=CARD, fg=MUTED, font=(FONT, 9), wraplength=CAM_W, justify="left")
        self.cam_status.pack(anchor="w", padx=14, pady=(4, 2))
        self.cam_btn = Pill(cam, "Turn on coach cam", self.toggle_cam, w=190, h=36, surface=CARD, size=10)
        self.cam_btn.pack(pady=(2, 10))
        self.draw_cam_idle()

        bottom = tk.Frame(right, bg=CARD, highlightthickness=1, highlightbackground=LINE)
        bottom.pack(fill="x", pady=(14, 0))
        self.tcanvas = tk.Canvas(bottom, width=160, height=160, bg=CARD, highlightthickness=0)
        self.tcanvas.pack(side="left", padx=14, pady=10)
        info = tk.Frame(bottom, bg=CARD)
        info.pack(side="left", fill="both", expand=True, padx=(4, 16), pady=10)
        self.ex_title = tk.Label(info, text="", bg=CARD, fg=ACCENT, font=(FONT, 15, "bold"), anchor="w")
        self.ex_title.pack(fill="x")
        self.ex_desc = tk.Label(info, text="", bg=CARD, fg=TEXT, font=(FONT, 11), wraplength=460, justify="left", anchor="w")
        self.ex_desc.pack(fill="x", pady=(4, 8))
        bf = tk.Frame(info, bg=CARD)
        bf.pack(anchor="w")
        self.start_btn = Pill(bf, "Start", self.toggle_timer, w=120, h=40, fill=GOOD, fg="#06231a", surface=CARD)
        self.start_btn.pack(side="left", padx=(0, 8))
        Pill(bf, "Next step", self.next_step, w=120, h=40, surface=CARD).pack(side="left", padx=4)
        Pill(bf, "Reset", lambda: self.reset_timer(keep_idx=True), w=100, h=40, ghost=True, surface=CARD).pack(side="left", padx=4)

        self.plan, self.plan_name, self.idx, self.remaining, self.total = [], "", 0, 0, 1
        self.running, self.after_id = False, None
        self.choose_plan(0)

    def _stat(self, parent, label, value):
        f = tk.Frame(parent, bg=CARD2, padx=10, pady=4)
        f.pack(side="left", expand=True, fill="x", padx=3)
        tk.Label(f, text=label, bg=CARD2, fg=MUTED, font=(FONT, 8, "bold")).pack()
        v = tk.Label(f, text=value, bg=CARD2, fg=TEXT, font=(FONT, 16, "bold"))
        v.pack()
        return v

    def auto_plan(self):
        lat = self.latest
        env_surface = self.p["env"] == "Moon / Mars Base"
        if not lat:
            return "Partial-Gravity Strength" if env_surface else "Balanced Daily Mix"
        sc = lat["scores"]
        worst = min(DOMAINS, key=lambda d: sc[d])
        if sc[worst] >= 80:
            return "Partial-Gravity Strength" if env_surface else "Balanced Daily Mix"
        if worst == BONE and env_surface:
            return "Partial-Gravity Strength"
        return {BONE: "Bone & Muscle Protection", HEART: "Heart & Cardio", MIND: "Mind Reset",
                SLEEP: "Mind Reset", IMMUNE: "Easy Recovery Day"}[worst]

    def choose_plan(self, i):
        name = self.plan_names[i]
        if name.startswith("Auto"):
            name = self.auto_plan()
        self.plan_name = name
        self.plan = PLANS[name]
        self.step_menu.set_items([f"{n}   ({s // 60} min)" for n, s, _ in self.plan], 0)
        self.idx = 0
        self.reset_timer()

    def _secs(self, s):
        return 10 if self.demo_var.get() else s

    def pick_step(self, i):
        self.idx = i
        self.reset_timer(keep_idx=True)

    def _cancel(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def reset_timer(self, keep_idx=False):
        self._cancel()
        self.running = False
        self.start_btn.set_text("Start")
        if not keep_idx:
            self.idx = 0
        name, secs, desc = self.plan[self.idx]
        self.total = self._secs(secs)
        self.remaining = self.total
        self.step_menu.select(self.idx, False)
        self.ex_title.config(text=name)
        self.ex_desc.config(text=desc)
        self.cur_kind = kind_for(name)
        self.demo.set_kind(self.cur_kind)
        self.coach.set_kind(self.cur_kind)
        self.update_cam_mode_text()
        self.draw_timer()

    def toggle_timer(self):
        if self.running:
            self._cancel()
            self.running = False
            self.start_btn.set_text("Resume")
        else:
            self.running = True
            self.start_btn.set_text("Pause")
            self.after_id = self.after(1000, self.tick)

    def tick(self):
        if not self.running:
            return
        self.remaining -= 1
        if self.remaining <= 0:
            try:
                self.bell()
            except tk.TclError:
                pass
            self.step_finished()
            return
        self.draw_timer()
        self.after_id = self.after(1000, self.tick)

    def step_finished(self):
        """A step's timer reached zero."""
        events = []
        if not self.demo_var.get():
            name = self.plan[self.idx][0]
            add_xp(self.p, 10)
            events.append((f"Step done: {name}", 10))
        self._cancel()
        if self.idx + 1 >= len(self.plan):
            self.running = False
            if not self.demo_var.get():
                st = self.p["stats"]
                st["sessions"] += 1
                st["minutes"] += sum(s for _, s, _ in self.plan) // 60
                grp = PLAN_GROUP.get(self.plan_name)
                if grp:
                    st[grp] += 1
                add_xp(self.p, 60)
                events.append(("Exercise session complete", 60))
                events += complete_quest(self.p, "exercise")
            self.idx = 0
            self.reset_timer()
            if events:
                self.reward(events)
            messagebox.showinfo("Session complete", "Great work! Drink some water and log how you feel at your next check-in.")
            return
        self.idx += 1
        self.reset_timer(keep_idx=True)
        self.running = True
        self.start_btn.set_text("Pause")
        self.after_id = self.after(1000, self.tick)
        if events:
            self.reward(events)

    def next_step(self):
        self._cancel()
        was = self.running
        if self.idx + 1 >= len(self.plan):
            self.idx = 0
            self.reset_timer()
            return
        self.idx += 1
        self.reset_timer(keep_idx=True)
        if was:
            self.running = True
            self.start_btn.set_text("Pause")
            self.after_id = self.after(1000, self.tick)

    def draw_timer(self):
        c = self.tcanvas
        c.delete("all")
        cx, cy, r = 80, 80, 62
        frac = self.remaining / max(self.total, 1)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=CARD2, width=12)
        if frac > 0.002:
            c.create_arc(cx - r, cy - r, cx + r, cy + r, start=90, extent=359.9 * frac, style="arc", width=18,
                         outline=mix(CARD, ACCENT, .15))
            c.create_arc(cx - r, cy - r, cx + r, cy + r, start=90, extent=359.9 * frac, style="arc", width=12, outline=ACCENT)
            ang = 90 + 359.9 * frac
            ex, ey = cx + r * math.cos(math.radians(ang)), cy - r * math.sin(math.radians(ang))
            c.create_oval(ex - 6, ey - 6, ex + 6, ey + 6, fill=TEXT, outline="")
        m, s = divmod(int(self.remaining), 60)
        c.create_text(cx, cy - 6, text=f"{m:02d}:{s:02d}", fill=TEXT, font=("Consolas", 26, "bold"))
        c.create_text(cx, cy + 22, text=f"{self.idx + 1} of {len(self.plan)}", fill=MUTED, font=(FONT, 9))

    # ---------------------------------------------------------------- coach cam
    def update_cam_mode_text(self):
        if self.coach.running:
            if self.coach.mode == "pose" and self.cur_kind in POSE_KINDS:
                txt = "Tracking your joints and scoring form. Stand sideways to the camera for squats and hinges."
            else:
                txt = "Tracking your movement and rhythm for this exercise."
            self.cam_status.config(text=txt, fg=MUTED)

    def draw_cam_idle(self, msg=None):
        c = self.cam_canvas
        c.delete("all")
        c.create_text(CAM_W / 2, CAM_H / 2 - 18, text="Coach cam is off", fill=TEXT, font=(FONT, 13, "bold"))
        c.create_text(CAM_W / 2, CAM_H / 2 + 14, text=msg or "Optional. Video stays on this computer\nand is never saved.",
                      fill=MUTED, font=(FONT, 9), justify="center", width=CAM_W - 30)

    def toggle_cam(self):
        if self.coach.running:
            self.stop_cam()
            return
        self.cam_status.config(text="Starting camera...", fg=MUTED)
        self.update_idletasks()
        ok, msg = self.coach.start()
        if not ok:
            self.cam_status.config(text=msg, fg=CAUTION)
            self.draw_cam_idle("Not available yet")
            return
        self.coach.set_kind(self.cur_kind)
        self.cam_btn.set_text("Turn off camera")
        self.update_cam_mode_text()
        if self.coach.reason:
            self.cam_status.config(text=self.coach.reason + "  " + self.cam_status.cget("text"), fg=WATCH)
        self.cam_tick()

    def cam_tick(self):
        if not self.coach.running:
            return
        try:
            res = self.coach.step()
        except Exception as e:
            self.stop_cam()
            self.cam_status.config(text=f"Camera stopped: {e}", fg=CAUTION)
            return
        if res:
            ppm, st = res
            try:
                self.cam_img = tk.PhotoImage(width=CAM_W, height=CAM_H, data=ppm, format="PPM")
                self.cam_canvas.delete("all")
                self.cam_canvas.create_image(0, 0, anchor="nw", image=self.cam_img)
                self.cam_canvas.create_text(CAM_W - 8, CAM_H - 10, anchor="e", text=st["tip"], fill="#ffffff",
                                            font=(FONT, 9, "bold"))
            except tk.TclError:
                self.stop_cam()
                self.cam_status.config(text="This Tk version cannot show camera frames.", fg=CAUTION)
                return
            self.cam_reps.config(text=str(st["reps"]))
            form = st["form"]
            self.cam_form.config(text=str(form) if st["tracking"] else "--",
                                 fg=GOOD if form >= 75 else WATCH if form >= 50 else CAUTION)
            self.cam_last.config(text=str(st["last"]) if st["last"] is not None else "--")
        self._cam_job = self.after(30, self.cam_tick)

    def stop_cam(self):
        if self._cam_job:
            self.after_cancel(self._cam_job)
            self._cam_job = None
        was = self.coach.running
        self.coach.stop()
        if hasattr(self, "cam_btn"):
            self.cam_btn.set_text("Turn on coach cam")
            self.draw_cam_idle()
            self.cam_reps.config(text="0")
            self.cam_form.config(text="--", fg=TEXT)
            self.cam_last.config(text="--")
        n = self.coach.claim_reps()
        if was and n:
            p = self.p
            p["stats"]["reps"] += n
            pts = min(n * 2, 40)
            add_xp(p, pts)
            self.reward([(f"{n} reps counted with the coach cam", pts)])

    # ================================================================== LEARN
    def _build_learn(self):
        p = tk.Frame(self.content, bg=BG)
        self.pages["learn"] = p
        tk.Label(p, text="Learn", bg=BG, fg=TEXT, font=(HEAD, 25, "bold")).pack(anchor="w", padx=34, pady=(28, 2))
        tk.Label(p, text="Plain-language guides to the health risks of space. Read a card for a little XP.",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack(anchor="w", padx=34, pady=(0, 12))
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=34, pady=(0, 20))
        left = tk.Frame(body, bg=CARD, width=300, padx=10, pady=12, highlightthickness=1, highlightbackground=LINE)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self.learn_menu = ListMenu(left, self.show_learn, pady=8)
        self.learn_menu.pack(fill="x")
        self.learn_menu.set_items([t["title"] for t in LEARN], 0)
        self.learn_detail = tk.Frame(body, bg=CARD, padx=36, pady=28, highlightthickness=1, highlightbackground=LINE)
        self.learn_detail.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.show_learn(0, reward=False)

    def show_learn(self, i, reward=True):
        t = LEARN[i]
        d = self.learn_detail
        for w in d.winfo_children():
            w.destroy()
        tk.Label(d, text=t["title"], bg=CARD, fg=t["color"], font=(FONT, 22, "bold"), wraplength=620,
                 justify="left").pack(anchor="w")
        tk.Label(d, text=t["tldr"], bg=CARD, fg=TEXT, font=(FONT, 14, "bold"), wraplength=620,
                 justify="left").pack(anchor="w", pady=(8, 14))
        if t["id"] == "colors":
            row = tk.Frame(d, bg=CARD)
            row.pack(anchor="w", pady=(0, 14))
            for col, name in ((GOOD, "Nominal"), (WATCH, "Watch"), (CAUTION, "Caution"), (CRIT, "Critical")):
                cv = tk.Canvas(row, width=120, height=40, bg=CARD, highlightthickness=0)
                cv.pack(side="left", padx=(0, 8))
                rrect(cv, 2, 2, 118, 38, r=18, fill=mix(CARD, col, .3), outline=col, width=2)
                cv.create_text(60, 20, text=name, fill=TEXT, font=(FONT, 11, "bold"))
        for para in t["body"]:
            tk.Label(d, text=para, bg=CARD, fg=TEXT, font=(FONT, 12), wraplength=620, justify="left").pack(anchor="w", pady=5)
        tk.Label(d, text="WHAT YOU CAN DO", bg=CARD, fg=GOOD, font=(FONT, 10, "bold")).pack(anchor="w", pady=(16, 4))
        for s in t["do"]:
            tk.Label(d, text="•  " + s, bg=CARD, fg=TEXT, font=(FONT, 12), wraplength=620, justify="left",
                     anchor="w").pack(fill="x", pady=2)
        p = self.p
        if reward and t["id"] not in p["learned"]:
            p["learned"].append(t["id"])
            add_xp(p, 5)
            self.reward([(f"Learned: {t['title']}", 5)])

    # ================================================================== PROGRESS
    def _build_progress(self):
        p = tk.Frame(self.content, bg=BG)
        self.pages["progress"] = p
        tk.Label(p, text="Progress", bg=BG, fg=TEXT, font=(HEAD, 25, "bold")).pack(anchor="w", padx=34, pady=(28, 2))
        tk.Label(p, text="Pick an indicator to see how it changes. The colored bands show what is normal, a watch-out or alert.",
                 bg=BG, fg=MUTED, font=(FONT, 12)).pack(anchor="w", padx=34, pady=(0, 10))
        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=34, pady=(0, 16))
        left = tk.Frame(body, bg=CARD, width=230, padx=8, pady=10, highlightthickness=1, highlightbackground=LINE)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self.ind_menu = ListMenu(left, self.pick_indicator, pady=5)
        self.ind_menu.pack(fill="x")
        self.ind_menu.set_items([i[1] for i in INDICATORS], 0)
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(14, 0))
        cards = tk.Frame(right, bg=BG)
        cards.pack(fill="x")
        self.sum_latest = self._sumcard(cards, "LATEST")
        self.sum_avg = self._sumcard(cards, "AVERAGE")
        self.sum_change = self._sumcard(cards, "CHANGE")
        self.chart = tk.Canvas(right, height=290, bg=BG, highlightthickness=0)
        self.chart.pack(fill="x", pady=(10, 0))
        self.chart.bind("<Configure>", lambda e: self.draw_chart())
        self.chart.bind("<Motion>", self.chart_hover)
        self.chart.bind("<Leave>", lambda e: self.chart.delete("tip"))
        cols = ("time", "day", "overall", "status")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", height=4)
        for c, w in zip(cols, (200, 80, 100, 160)):
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, pady=(10, 6))
        bf = tk.Frame(right, bg=BG)
        bf.pack(anchor="w")
        Pill(bf, "Export report", self.export_report, w=160, h=40).pack(side="left", padx=(0, 8))
        Pill(bf, "Clear my data", self.clear_history, w=150, h=40, fill=CRIT).pack(side="left")

    def _sumcard(self, parent, label):
        f = tk.Frame(parent, bg=CARD, padx=18, pady=10, highlightthickness=1, highlightbackground=LINE)
        f.pack(side="left", expand=True, fill="x", padx=(0, 10))
        tk.Label(f, text=label, bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w")
        v = tk.Label(f, text="--", bg=CARD, fg=TEXT, font=(FONT, 20, "bold"))
        v.pack(anchor="w")
        s = tk.Label(f, text="", bg=CARD, fg=MUTED, font=(FONT, 9))
        s.pack(anchor="w")
        return (v, s)

    def pick_indicator(self, i):
        self.ind_key = INDICATORS[i][0]
        self.start_chart()

    def _ind_data(self):
        key, label, unit, color, axis, bands = IND[self.ind_key]
        data = series(self.p, key)
        return label, unit, color, axis, bands, data[-30:]

    @staticmethod
    def _band_color(bands, v, default):
        for lo, hi, col in bands:
            if lo <= v < hi:
                return col
        return bands[-1][2] if bands and v >= bands[-1][1] else (bands[0][2] if bands else default)

    def start_chart(self):
        if self._chart_job:
            self.after_cancel(self._chart_job)
            self._chart_job = None
        self.chart_prog = 0.0
        self._chart_step()
        self.update_summary()

    def _chart_step(self):
        self.chart_prog = min(1.0, self.chart_prog + 0.07)
        self.draw_chart()
        self._chart_job = self.after(24, self._chart_step) if self.chart_prog < 1 else None

    def update_summary(self):
        label, unit, color, axis, bands, data = self._ind_data()
        (lv, ls), (av, as_), (cv, cs) = self.sum_latest, self.sum_avg, self.sum_change
        if not data:
            for v, s in ((lv, ls), (av, as_), (cv, cs)):
                v.config(text="--", fg=TEXT)
                s.config(text="")
            return
        vals = [v for _, v in data]
        last = vals[-1]
        col = self._band_color(bands, last, color) if bands else color
        lv.config(text=fmt_reading(self.ind_key, last), fg=col)
        ls.config(text=f"{unit}  ·  {data[-1][0][5:16]}")
        av.config(text=f"{sum(vals) / len(vals):+.2f} D" if self.ind_key == "nearpower"
                  else f"{sum(vals) / len(vals):.1f}".rstrip("0").rstrip("."))
        as_.config(text=f"over {len(vals)} reading{'s' if len(vals) > 1 else ''}")
        if len(vals) > 1:
            d = last - vals[0]
            cv.config(text=f"{d:+.2f} D" if self.ind_key == "nearpower" else f"{d:+.1f}".rstrip("0").rstrip("."), fg=TEXT)
            cs.config(text="since your first reading")
        else:
            cv.config(text="--")
            cs.config(text="needs 2 readings")

    def draw_chart(self):
        c = self.chart
        c.delete("all")
        W, H = max(c.winfo_width(), 600), 290
        rrect(c, 0, 0, W, H, r=22, fill=CARD, outline=LINE)
        label, unit, color, axis, bands, data = self._ind_data()
        c.create_text(20, 22, anchor="w", text=f"{label.upper()}  ({unit})", fill=MUTED, font=(FONT, 10, "bold"))
        L, R, T, B = 58, W - 28, 46, H - 34
        vals = [v for _, v in data]
        lo = min([axis[0]] + vals) if vals else axis[0]
        hi = max([axis[1]] + vals) if vals else axis[1]
        self._cg = (L, R, T, B, lo, hi)

        def py(v):
            return B - (B - T) * (v - lo) / (hi - lo or 1)
        for a, b, col in bands:
            ya, yb = py(min(max(b, lo), hi)), py(min(max(a, lo), hi))
            c.create_rectangle(L, ya, R, yb, fill=mix(CARD, col, 0.13), outline="")
        for i in range(5):
            v = lo + (hi - lo) * i / 4
            c.create_line(L, py(v), R, py(v), fill=mix(CARD, LINE, .6))
            c.create_text(L - 10, py(v), anchor="e", text=f"{v:g}" if (hi - lo) > 8 else f"{v:.1f}", fill=MUTED, font=(FONT, 8))
        if not data:
            c.create_text(W / 2, H / 2 + 6, text="No readings yet. Do a check-in or log a measurement in Mission Routine.",
                          fill=MUTED, font=(FONT, 11))
            return
        n = len(data)
        xs = [L + (R - L) * i / (n - 1) if n > 1 else (L + R) / 2 for i in range(n)]
        self._cpts = [(x, py(v), t, v) for x, (t, v) in zip(xs, data)]
        total = max(n - 1, 1) * self.chart_prog
        pts = []
        for i, (x, y, _, _) in enumerate(self._cpts):
            if i <= total:
                pts += [x, y]
            elif i - 1 <= total and pts:
                f = total - (i - 1)
                px_, py_ = self._cpts[i - 1][0], self._cpts[i - 1][1]
                pts += [px_ + (x - px_) * f, py_ + (y - py_) * f]
        if len(pts) >= 4:
            if len(pts) >= 6:
                c.create_polygon([pts[0], B] + pts + [pts[-2], B], fill=mix(CARD, color, .14), outline="")
            c.create_line(pts, fill=color, width=3, smooth=len(pts) >= 6, capstyle="round")
        for i, (x, y, _, v) in enumerate(self._cpts):
            if i <= total:
                col = self._band_color(bands, v, color) if bands else color
                c.create_oval(x - 6, y - 6, x + 6, y + 6, fill=col, outline=CARD, width=2)
        c.create_text(R, 22, anchor="e", text="Hover over a dot for details", fill=mix(MUTED, CARD, .3), font=(FONT, 9))

    def chart_hover(self, e):
        c = self.chart
        c.delete("tip")
        pts = getattr(self, "_cpts", None)
        if not pts or self.chart_prog < 1:
            return
        x, y, t, v = min(pts, key=lambda q: abs(q[0] - e.x))
        if abs(x - e.x) > 40:
            return
        bands = IND[self.ind_key][5]
        col = self._band_color(bands, v, ACCENT) if bands else ACCENT
        c.create_oval(x - 9, y - 9, x + 9, y + 9, outline=col, width=2, tags="tip")
        txt = f"{fmt_reading(self.ind_key, v)}   {t[5:16]}"
        w = len(txt) * 7 + 20
        bx = min(max(x - w / 2, 8), c.winfo_width() - w - 8)
        by = y - 44 if y > 90 else y + 16
        rrect(c, bx, by, bx + w, by + 28, r=10, fill=CARD2, outline=col, tags="tip")
        c.create_text(bx + w / 2, by + 14, text=txt, fill=TEXT, font=(FONT, 10, "bold"), tags="tip")

    def refresh_progress_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for e in reversed(self.p["history"]):
            self.tree.insert("", "end", values=(e["time"], e["day"], e["overall"], status_of(e["overall"])[0].title()))

    def export_report(self):
        e, p = self.latest, self.p
        if not e:
            messagebox.showinfo("No data", "Complete a check-in first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="astro_vital_report.txt",
                                            filetypes=[("Text", "*.txt")])
        if not path:
            return
        lines = ["ASTRO-VITAL HEALTH REPORT", "=" * 40,
                 f"Name: {p['name']}    Environment: {p['env']}    Mission day: {e['day']}    Time: {e['time']}",
                 f"Overall readiness: {e['overall']}/100 ({status_of(e['overall'])[0]})", "", "Health areas:"]
        lines += [f"  {d}: {e['scores'][d]}/100" for d in DOMAINS]
        if p["measures"]:
            lines += ["", "Latest routine readings:"]
            for t in ROUTINE:
                m = last_measure(p, t["id"])
                if m:
                    lines.append(f"  {t['title']}: {fmt_reading(t['id'], m['value'])}"
                             f"{'' if t['id'] == 'nearpower' else ' ' + t['unit']}  ({m['time']})")
        if e["alerts"]:
            lines += ["", "URGENT:"] + ["  - " + a for a in e["alerts"]]
        if e["notes"]:
            lines += ["", "Notices:"] + ["  - " + n for n in e["notes"]]
        lines += ["", "Suggestions:"]
        for d in sorted(DOMAINS, key=lambda d: e["scores"][d]):
            lines.append(f" {d}:")
            lines += ["   - " + t for t in ADVICE[d][level_of(e["scores"][d])]]
        lines += ["", "Educational prototype. Consult the flight surgeon for medical decisions."]
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
            messagebox.showinfo("Saved", f"Report saved to:\n{path}")
        except OSError as err:
            messagebox.showerror("Error", str(err))

    def clear_history(self):
        p = self.p
        if messagebox.askyesno("Clear my data", f"Delete all of {p['name']}'s check-ins, readings, XP and badges? "
                                                "This cannot be undone."):
            fresh = new_profile(p["name"], p["env"])
            for keep in ("auth", "last_login"):
                if keep in p:
                    fresh[keep] = p[keep]
            p.clear()
            p.update(fresh)
            self.store.save()
            self.refresh_all()
            self.show("home")

    # ================================================================== REWARDS
    def _build_rewards(self):
        self.rewards = tk.Canvas(self.content, bg=BG, highlightthickness=0)
        self.rewards.scroll_canvas = self.rewards
        self.pages["rewards"] = self.rewards
        self.rewards.bind("<Configure>", lambda e: self.draw_rewards())
        self.rw = []

    def _rp(self, text, cmd, x, y, w, h, **kw):
        pill = Pill(self.rewards, text, cmd, w=w, h=h, surface=CARD, size=10, **kw)
        self.rw.append(pill)
        self.rewards.create_window(x, y, anchor="nw", window=pill)

    # ================================================================== CREW
    def _build_crew(self):
        self.crew = tk.Canvas(self.content, bg=BG, highlightthickness=0)
        self.crew.scroll_canvas = self.crew
        self.pages["crew"] = self.crew
        self.crew.bind("<Configure>", lambda e: self.draw_crew())
        self.cw = []

    def _cp(self, text, cmd, x, y, w, h, **kw):
        pill = Pill(self.crew, text, cmd, w=w, h=h, surface=kw.pop("surface", CARD), size=10, **kw)
        self.cw.append(pill)
        self.crew.create_window(x, y, anchor="nw", window=pill)

    def cheer(self, name):
        p = self.p
        ch = p.setdefault("cheered", {"date": "", "names": []})
        if ch["date"] != today():
            ch.update(date=today(), names=[])
        if name in ch["names"]:
            self.toast(f"You already cheered {name} today.", MUTED)
            return
        ch["names"].append(name)
        self.store.data["crew"][name]["cheers"] = self.store.data["crew"][name].get("cheers", 0) + 1
        add_xp(p, 3)
        self.reward([(f"You cheered {name}", 3)])

    # ------------------------------------------------------------------ guest mode
    def start_guest(self):
        self._nudges = 0
        self.store.start_guest("Space Station")
        self.start_session(GUEST_KEY)

    def _has_progress(self):
        p = self.p
        return bool(p and (p["history"] or p["measures"] or p["xp"] > 10))

    def confirm_leave(self, then):
        """Run `then` straight away, unless a guest would lose progress. Then ask first."""
        if not self.store.is_guest or not self._has_progress():
            return then()
        m = Modal(self, 500, 380, border=ACCENT2)
        c = tk.Canvas(m.body, width=496, height=376, bg=CARD, highlightthickness=0)
        c.pack()
        for i in range(24):
            c.create_rectangle(0, i * 6, 496, i * 6 + 6, fill=mix(mix(CARD, ACCENT2, .2), CARD, i / 23), outline="")
        draw_mascot(c, 248, 66, 1.0, "nova", "worried", scarf="scarf" in self.p.get("owned", []))
        c.create_text(248, 176, text="Leave without saving?", fill=TEXT, font=(HEAD, 22, "bold"))
        c.create_text(248, 232, width=400, justify="center", fill=mix(TEXT, MUTED, .35), font=(FONT, 11),
                      text=f"You have {self.p['xp']} XP, {gems_of(self.p)} stardust and a {profile_streak(self.p)}-day streak. "
                           "As a guest, they disappear when you go. A free account keeps them safe.")
        c.create_window(150, 312, window=Pill(c, "Save my progress", lambda: (m.close(), self.save_progress_dialog()),
                                              w=210, h=46, fill=ACCENT2, surface=CARD, size=11))
        c.create_window(366, 312, window=Pill(c, "Leave anyway", lambda: (m.close(), then()), w=160, h=46, ghost=True,
                                              surface=CARD, size=11))
        c.create_text(248, 352, text="Esc to stay", fill=mix(MUTED, CARD, .4), font=(FONT, 9))

    def save_progress_dialog(self):
        if not self.store.is_guest:
            return
        m = Modal(self, 480, 560, border=ACCENT2)
        b = m.body
        hdr = tk.Canvas(b, width=476, height=120, bg=CARD, highlightthickness=0)
        hdr.pack()
        for i in range(20):
            hdr.create_rectangle(0, i * 6, 476, i * 6 + 6, fill=mix(mix(CARD, ACCENT2, .22), CARD, i / 19), outline="")
        draw_mascot(hdr, 70, 56, .95, "nova", "cheer", scarf="scarf" in self.p.get("owned", []))
        hdr.create_text(128, 44, anchor="w", text="Keep your progress", fill=TEXT, font=(HEAD, 22, "bold"))
        hdr.create_text(128, 78, anchor="w", width=330, fill=MUTED, font=(FONT, 10),
                        text=f"{self.p['xp']} XP, {gems_of(self.p)} stardust and your streak come with you.")
        vs = [tk.StringVar() for _ in range(3)]
        first = None
        for label, v, secret in (("CHOOSE A USERNAME", vs[0], False), ("PASSWORD", vs[1], True),
                                 ("CONFIRM PASSWORD", vs[2], True)):
            tk.Label(b, text=label, bg=CARD, fg=MUTED, font=(FONT, 9, "bold")).pack(anchor="w", padx=34, pady=(10, 0))
            e = tk.Entry(b, textvariable=v, show="\u2022" if secret else "", bg=CARD2, fg=TEXT, insertbackground=TEXT,
                         relief="flat", font=(FONT, 12), highlightthickness=2, highlightbackground=LINE,
                         highlightcolor=ACCENT)
            e.pack(fill="x", padx=34, pady=(4, 0), ipady=6)
            first = first or e
        err = tk.Label(b, text="8+ characters with a letter and a number.", bg=CARD, fg=MUTED, font=(FONT, 10, "bold"),
                       wraplength=410, justify="left")
        err.pack(anchor="w", padx=34, pady=(10, 0))

        def go(ev=None):
            if vs[1].get() != vs[2].get():
                return err.config(text="The two passwords don't match.", fg=CRIT)
            st, val = self.store.promote_guest(vs[0].get(), vs[1].get())
            if st != "ok":
                return err.config(text=val, fg=CRIT)
            m.close()
            self.update_sidebar()
            self.redraw_current()
            self.toast(f"Saved! You're signed in as {val}.", GOOD)
        for w in b.winfo_children():
            if isinstance(w, tk.Entry):
                w.bind("<Return>", go)
        row = tk.Frame(b, bg=CARD)
        row.pack(anchor="w", padx=34, pady=18)
        Pill(row, "Create account & save", go, w=250, h=46, fill=ACCENT2, surface=CARD, size=11).pack(side="left")
        Pill(row, "Not now", m.close, w=120, h=46, ghost=True, surface=CARD, size=11).pack(side="left", padx=10)
        m.after(80, first.focus_set)

    def show_save_nudge(self, done):
        m = Modal(self, 480, 430, border=ACCENT2, on_close=done)
        c = tk.Canvas(m.body, width=476, height=426, bg=CARD, highlightthickness=0)
        c.pack()
        for i in range(30):
            c.create_rectangle(0, i * 6, 476, i * 6 + 6, fill=mix(mix(CARD, ACCENT2, .25), CARD, i / 29), outline="")
        draw_mascot(c, 238, 84, 1.5, "nova", "cheer", scarf="scarf" in self.p.get("owned", []))
        c.create_text(238, 214, text="Nice work, astronaut!", fill=TEXT, font=(HEAD, 24, "bold"))
        c.create_text(238, 268, width=380, justify="center", fill=mix(TEXT, MUTED, .35), font=(FONT, 11),
                      text=f"You've earned {self.p['xp']} XP and {gems_of(self.p)} stardust. "
                           "Make a free account so it doesn't vanish when you close the app.")
        c.create_window(238, 336, window=Pill(c, "Save my progress", lambda: (m.close(), self.save_progress_dialog()),
                                              w=260, h=48, fill=ACCENT2, surface=CARD, size=12))
        c.create_window(238, 390, window=Pill(c, "Maybe later", m.close, w=160, h=38, ghost=True, surface=CARD, size=10))

    def on_close(self):
        if self.p is None:
            return self._quit()
        self.confirm_leave(self._quit)

    def _quit(self):
        try:
            self.stop_cam()
        except Exception:
            pass
        self.store.save()
        self.destroy()

    # ------------------------------------------------------------------ daily chest, shop, buddy
    def _daily_chest(self):
        p = self.p
        if p.get("last_login") == today():
            self.store.save()
            self.update_sidebar()
            return
        p["last_login"] = today()
        st = profile_streak(p)
        gems = random.Random(f"{p['name']}{today()}").randint(5, 10) + min(st, 10)
        give_gems(p, gems)
        add_xp(p, 5)
        sub = (f"{st}-day streak. Keep it going!" if st else "Do a check-in today to start your streak.") + "\n+5 XP"
        self.queue_modal(lambda done: self.show_celebration(done, "DAILY CHEST", f"+{gems} stardust", sub,
                                                            ACCENT2, "\u2726"))
        self.reward([])

    def buy(self, item_id):
        ok, msg = buy_item(self.p, item_id)
        self.toast(msg, ACCENT2 if ok else CAUTION)
        if ok:
            self.reward([])

    def set_buddy(self, name):
        p = self.p
        if p.get("buddy") == name:
            p["buddy"] = ""
            self.toast(f"{name} is no longer your streak buddy.", MUTED)
        else:
            p["buddy"] = name
            self.toast(f"{name} is your streak buddy. Check in on the same day to grow it.", WATCH)
        self.reward([])

    def mascot_mood(self):
        p, lat = self.p, self.latest
        done_today = bool(lat and lat["time"][:10] == today())
        if lat and lat["alerts"] and done_today:
            return "worried"
        if not done_today:
            return "worried" if profile_streak(p) > 0 else "happy"
        return "cheer" if lat["overall"] >= 80 else "happy"

    # ================================================================== REWARDS
    def draw_rewards(self):
        c = self.rewards
        for w in self.rw:
            w.destroy()
        self.rw = []
        c.delete("all")
        if self.current != "rewards":
            return
        W = max(c.winfo_width(), 900)
        m, p = 34, self.p
        c.create_text(m, 44, anchor="w", text="Rewards", fill=TEXT, font=(HEAD, 25, "bold"))
        c.create_text(m, 76, anchor="w", text="Healthy habits earn XP and stardust. Small things count.", fill=MUTED,
                      font=(FONT, 12))
        rrect(c, W - m - 190, 30, W - m, 66, r=18, fill=CARD, outline=ACCENT2)
        c.create_text(W - m - 95, 48, text=f"\u2726 {gems_of(p)} stardust", fill=ACCENT2, font=(FONT, 12, "bold"))
        self.draw_hero(c, m, 100, W - m, 240)

        c.create_text(m, 272, anchor="w", text="Daily quests", fill=TEXT, font=(HEAD, 16, "bold"))
        rrect(c, m, 292, W - m, 462, r=24, fill=CARD, outline=LINE)
        self._quest_rows(c, m + 28, 332, W - m - 28, 34, lambda t, cmd, x, y, w, h: self._rp(t, cmd, x, y, w, h, fill=ACCENT))
        q = p["quests"]
        c.create_text(W - m - 28, 308, anchor="e",
                      text="Full orbit bonus earned" if q.get("bonus") else f"Finish all four for +{BONUS_XP} XP",
                      fill=GOOD if q.get("bonus") else MUTED, font=(FONT, 10, "bold"))

        c.create_text(m, 494, anchor="w", text="Your last 4 weeks", fill=TEXT, font=(HEAD, 16, "bold"))
        rrect(c, m, 514, W - m, 680, r=24, fill=CARD, outline=LINE)
        by_day = {e["time"][:10]: e["overall"] for e in p["history"]}
        froz = set(p.get("frozen", []))
        for k in range(28):
            d = dt.date.today() - dt.timedelta(days=27 - k)
            row = k // 14
            cx = m + 40 + (k % 14) * ((W - 2 * m - 80) / 14) + 14
            cy = 556 + row * 60
            ov = by_day.get(d.isoformat())
            col = status_of(ov)[1] if ov is not None else ("#6bb8e8" if d.isoformat() in froz else None)
            c.create_oval(cx - 14, cy - 14, cx + 14, cy + 14, fill=mix(CARD, col, .55) if col else CARD2,
                          outline=col if col else LINE, width=2 if d == dt.date.today() else 1)
            c.create_text(cx, cy, text=str(d.day), fill=TEXT if col else MUTED, font=(FONT, 9, "bold"))
        c.create_text(W - m - 28, 534, anchor="e", text="Colors show your status each day. Blue = a shield saved your streak.",
                      fill=MUTED, font=(FONT, 9))

        c.create_text(m, 712, anchor="w", text=f"Badges  ({len(p['badges'])} of {len(BADGES)})", fill=TEXT,
                      font=(HEAD, 16, "bold"))
        cols = 4
        bw = (W - 2 * m - (cols - 1) * 14) / cols
        for i, (bid, name, desc, col, _) in enumerate(BADGES):
            x1 = m + (i % cols) * (bw + 14)
            y1 = 734 + (i // cols) * 112
            have = bid in p["badges"]
            rrect(c, x1, y1, x1 + bw, y1 + 98, r=20, fill=CARD, outline=col if have else LINE, width=2 if have else 1)
            c.create_oval(x1 + 18, y1 + 22, x1 + 66, y1 + 70, fill=mix(CARD, col, .35) if have else CARD2,
                          outline=col if have else LINE, width=3)
            c.create_text(x1 + 42, y1 + 46, text="\u2605" if have else "\u2022", fill=col if have else MUTED,
                          font=(FONT, 18, "bold"))
            c.create_text(x1 + 80, y1 + 36, anchor="w", text=name, fill=TEXT if have else MUTED, font=(FONT, 12, "bold"))
            c.create_text(x1 + 80, y1 + 56, anchor="nw", text=desc, fill=MUTED, font=(FONT, 9), width=bw - 96)
            c.create_text(x1 + bw - 14, y1 + 86, anchor="e", text="Unlocked" if have else "Locked",
                          fill=col if have else mix(MUTED, CARD, .4), font=(FONT, 8, "bold"))
        rows = (len(BADGES) + cols - 1) // cols
        sy = 734 + rows * 112 + 30

        # stardust shop
        c.create_text(m, sy, anchor="w", text="Stardust shop", fill=TEXT, font=(HEAD, 16, "bold"))
        c.create_text(W - m, sy, anchor="e", text=f"You have \u2726 {gems_of(p)}", fill=ACCENT2, font=(FONT, 12, "bold"))
        cw2 = (W - 2 * m - 16) / 2
        owned = p.get("owned", [])
        for i, item in enumerate(SHOP):
            x1 = m + (i % 2) * (cw2 + 16)
            y1 = sy + 26 + (i // 2) * 144
            col = item["color"]
            rrect(c, x1, y1, x1 + cw2, y1 + 128, r=22, fill=CARD, outline=LINE)
            c.create_oval(x1 + 20, y1 + 24, x1 + 76, y1 + 80, fill=mix(CARD, col, .3), outline=col, width=2)
            if item["id"] == "shield":
                draw_shield(c, x1 + 48, y1 + 52, 15, col)
            else:
                c.create_text(x1 + 48, y1 + 52, text=item["glyph"], fill=col, font=(FONT, 22, "bold"))
            c.create_text(x1 + 96, y1 + 30, anchor="w", text=item["name"], fill=TEXT, font=(FONT, 13, "bold"))
            c.create_text(x1 + 96, y1 + 50, anchor="nw", text=item["desc"], fill=MUTED, font=(FONT, 10),
                          width=max(cw2 - 96 - 150, 140))
            note = ""
            if item["id"] == "shield":
                note = f"You hold {p.get('shields', 0)} of {SHIELD_MAX}"
            elif item["id"] == "boost" and boost_left(p):
                note = f"Active: {boost_left(p) // 60}:{boost_left(p) % 60:02d} left"
            if note:
                c.create_text(x1 + 96, y1 + 112, anchor="w", text=note, fill=col, font=(FONT, 9, "bold"))
            if item["id"] in ("ring", "scarf") and item["id"] in owned:
                c.create_text(x1 + cw2 - 26, y1 + 92, anchor="e", text="Owned", fill=GOOD, font=(FONT, 11, "bold"))
            else:
                afford = gems_of(p) >= item["price"]
                self._rp(f"Buy   \u2726 {item['price']}", lambda iid=item["id"]: self.buy(iid), x1 + cw2 - 26 - 124,
                         y1 + 76, 124, 36, fill=ACCENT2, ghost=not afford)
        shop_rows = (len(SHOP) + 1) // 2
        c.configure(scrollregion=(0, 0, W, sy + 26 + shop_rows * 144 + 20))
        self.draw_shine()

    # ================================================================== CREW
    def draw_crew(self):
        c = self.crew
        for w in self.cw:
            w.destroy()
        self.cw = []
        c.delete("all")
        if self.current != "crew":
            return
        W = max(c.winfo_width(), 900)
        m, p = 34, self.p
        guest = self.store.is_guest
        rows = leaderboard(self.store)
        c.create_text(m, 44, anchor="w", text="Crew", fill=TEXT, font=(HEAD, 25, "bold"))
        c.create_text(m, 76, anchor="w", text="Friendly weekly challenges. Ranked by healthy habits, never by health results.",
                      fill=MUTED, font=(FONT, 12))
        # crew goal (left) and streak buddy (right)
        total = sum(r["weekly"] for r in rows)
        goal = max(600, 250 * len(rows))
        gx2 = m + int((W - 2 * m) * 0.58)
        rrect(c, m, 100, gx2, 214, r=24, fill=CARD, outline=LINE)
        c.create_text(m + 28, 130, anchor="w", text="CREW GOAL THIS WEEK", fill=MUTED, font=(FONT, 10, "bold"))
        c.create_text(gx2 - 28, 130, anchor="e", text=f"{total} of {goal} pts", fill=GOOD if total >= goal else TEXT,
                      font=(FONT, 11, "bold"))
        draw_xp_bar(c, m + 28, 150, gx2 - 28, 176, min(total / goal, 1), GOOD, ACCENT, "goal")
        c.create_text(m + 28, 196, anchor="w", text="We win together: every crew member's points count."
                      if total < goal else "Goal reached! Great teamwork.", fill=MUTED, font=(FONT, 10))
        b = buddy_info(self.store, p)
        bx1 = gx2 + 16
        rrect(c, bx1, 100, W - m, 214, r=24, fill=CARD, outline=WATCH if b else LINE)
        c.create_text(bx1 + 24, 130, anchor="w", text="STREAK BUDDY", fill=MUTED, font=(FONT, 10, "bold"))
        if b:
            bp = self.store.get_profile(b["name"])
            draw_avatar(c, bx1 + 48, 168, 22, b["name"], ENVS.get(bp["env"], ENVS["Space Station"])["color"], "bd",
                        ring="ring" in bp.get("owned", []))
            c.create_text(bx1 + 82, 156, anchor="w", text=b["name"], fill=TEXT, font=(FONT, 13, "bold"))
            status = ("You both checked in today" if b["me_today"] and b["buddy_today"] else
                      f"{b['name']} is waiting for you" if b["buddy_today"] else
                      f"Waiting for {b['name']}" if b["me_today"] else "Neither of you has checked in yet")
            c.create_text(bx1 + 82, 178, anchor="w", text=status, fill=GOOD if b["me_today"] and b["buddy_today"] else MUTED,
                          font=(FONT, 9), width=max(W - m - bx1 - 190, 120))
            draw_flame(c, W - m - 84, 160, 16, "bd", hot=b["streak"] > 0)
            c.create_text(W - m - 62, 158, anchor="w", text=str(b["streak"]), fill=TEXT, font=(FONT, 24, "bold"))
            c.create_text(W - m - 24, 194, anchor="e", text="joint streak", fill=MUTED, font=(FONT, 9))
        else:
            c.create_text(bx1 + 24, 150, anchor="nw", width=W - m - bx1 - 48, fill=TEXT, font=(FONT, 11),
                          text="Pick a crewmate below. When you both check in on the same day, your joint streak grows.")

        c.create_text(m, 246, anchor="w", text="Leaderboard", fill=TEXT, font=(HEAD, 16, "bold"))
        top = max((r["weekly"] for r in rows), default=1) or 1
        y = 268
        for i, r in enumerate(rows):
            me = r["name"] == p["name"]
            is_buddy = r["name"] == p.get("buddy")
            rrect(c, m, y, W - m, y + 80, r=20, fill=mix(CARD, ACCENT, .12) if me else CARD,
                  outline=ACCENT if me else (WATCH if is_buddy else LINE), width=2 if (me or is_buddy) else 1)
            draw_medal(c, m + 34, y + 40, 16, i + 1, "row")
            rp = self.store.get_profile(r["name"])
            env_col = ENVS.get(rp["env"], ENVS["Space Station"])["color"]
            draw_avatar(c, m + 82, y + 40, 20, r["name"], env_col, "row", ring=r["ring"])
            c.create_text(m + 114, y + 26, anchor="w", text=r["name"], fill=TEXT, font=(FONT, 13, "bold"))
            tag = "you" if me else ("demo crewmate" if r["demo"] else "")
            if tag:
                c.create_text(m + 114 + len(r["name"]) * 9 + 18, y + 27, anchor="w", text=tag,
                              fill=ACCENT if me else MUTED, font=(FONT, 9, "bold"))
            c.create_text(m + 114, y + 48, anchor="w", text=f"Level {r['level']}  \u00b7  {r['title']}", fill=MUTED,
                          font=(FONT, 10))
            if is_buddy and b:
                c.create_text(m + 114, y + 66, anchor="w", text=f"Buddy  \u00b7  {b['streak']}-day joint streak",
                              fill=WATCH, font=(FONT, 9, "bold"))
            bx1_, bx2_ = m + 330, W - m - 330
            if bx2_ - bx1_ > 120:
                draw_xp_bar(c, bx1_, y + 24, bx2_, y + 46, r["weekly"] / top, ACCENT, ACCENT2, "row")
                c.create_text(bx1_, y + 58, anchor="w", text=f"{r['weekly']} pts this week", fill=MUTED, font=(FONT, 9))
            fx = W - m - 300
            draw_flame(c, fx, y + 40, 14, "row", hot=r["streak"] > 0)
            c.create_text(fx + 20, y + 40, anchor="w", text=f"{r['streak']}", fill=TEXT, font=(FONT, 13, "bold"))
            c.create_text(fx + 56, y + 40, anchor="w", text=f"\u2605 {r['badges']}", fill=WATCH, font=(FONT, 11, "bold"))
            c.create_text(fx + 106, y + 40, anchor="w", text=f"\u2665 {r['cheers']}", fill=CRIT, font=(FONT, 11, "bold"))
            if not me:
                self._cp("Cheer", lambda n=r["name"]: self.cheer(n), W - m - 20 - 100, y + 10, 100, 28, fill=ACCENT)
                self._cp("Buddies \u2713" if is_buddy else "Buddy up", lambda n=r["name"]: self.set_buddy(n),
                         W - m - 20 - 100, y + 42, 100, 28, fill=WATCH, ghost=not is_buddy)
            y += 92
        c.create_text(m, y + 2, anchor="nw",
                      text="Flame = check-in streak    \u2605 = badges    \u2665 = cheers received", fill=MUTED, font=(FONT, 9))
        y += 36
        if guest:
            self._cp("Save my progress", self.save_progress_dialog, m, y, 200, 40, surface=BG, fill=ACCENT2)
            self._cp("Leave guest mode", self.logout, m + 212, y, 180, 40, surface=BG, ghost=True)
            hide = self.store.data.get("hide_demo")
            self._cp("Show demo crew" if hide else "Hide demo crew", self.toggle_demo, m + 404, y, 170, 40, surface=BG, ghost=True)
            note = ("You're using a guest session, so your progress isn't saved. Create a free account to keep your XP, "
                    "streak, stardust and badges. Demo crewmates are sample data so the leaderboard is never empty.")
        else:
            self._cp("Log out", self.logout, m, y, 130, 40, surface=BG, fill=CRIT)
            self._cp("Change password", self.change_password_dialog, m + 142, y, 190, 40, surface=BG, ghost=True)
            hide = self.store.data.get("hide_demo")
            self._cp("Show demo crew" if hide else "Hide demo crew", self.toggle_demo, m + 344, y, 170, 40, surface=BG, ghost=True)
            self._cp("Delete my account", self.delete_account_dialog, m + 526, y, 190, 40, surface=BG, ghost=True)
            note = ("Demo crewmates are sample data so the leaderboard is never empty. Crewmates join by signing up on the "
                    "login screen. Each has their own password-protected profile and appears here alongside you.")
        c.create_text(m, y + 66, anchor="nw", width=W - 2 * m, text=note, fill=MUTED, font=(FONT, 10))
        c.configure(scrollregion=(0, 0, W, y + 130))

    def toggle_demo(self):
        self.store.data["hide_demo"] = not self.store.data.get("hide_demo")
        self.store.save()
        self.draw_crew()


if __name__ == "__main__":
    App().mainloop()
