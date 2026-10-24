#!/usr/bin/env python3
from datetime import date

from app import app
from models import db, Exercise, Workout, WorkoutExercise

with app.app_context():
    # Clear children first so reruns never duplicate data
    WorkoutExercise.query.delete()
    Workout.query.delete()
    Exercise.query.delete()

    exercises = [
        Exercise(name="Bench Press", category="strength", equipment_needed=True),
        Exercise(name="Squat", category="strength", equipment_needed=True),
        Exercise(name="Push-ups", category="strength", equipment_needed=False),
        Exercise(name="Running", category="cardio", equipment_needed=False),
        Exercise(name="Plank", category="balance", equipment_needed=False),
        Exercise(name="Hamstring Stretch", category="flexibility", equipment_needed=False),
    ]
    workouts = [
        Workout(date=date(2026, 10, 19), duration_minutes=60, notes="Upper body focus"),
        Workout(date=date(2026, 10, 21), duration_minutes=45, notes="Cardio and core"),
        Workout(date=date(2026, 10, 23), duration_minutes=30, notes=None),
    ]
    db.session.add_all(exercises + workouts)
    db.session.flush()  # assigns ids

    bench, squat, pushups, running, plank, stretch = exercises
    upper, cardio, quick = workouts

    db.session.add_all([
        WorkoutExercise(workout=upper, exercise=bench, reps=8, sets=4),
        WorkoutExercise(workout=upper, exercise=pushups, reps=15, sets=3),
        WorkoutExercise(workout=cardio, exercise=running, duration_seconds=1500),
        WorkoutExercise(workout=cardio, exercise=plank, duration_seconds=60, sets=3),
        WorkoutExercise(workout=quick, exercise=squat, reps=10, sets=3),
        WorkoutExercise(workout=quick, exercise=stretch, duration_seconds=120),
    ])
    db.session.commit()
    print("Database seeded.")
