import psycopg2
import streamlit as st
from datetime import date
from decimal import Decimal

# --- DATABASE CONNECTION ---
def get_db_connection():
    """Establishes and caches a connection to the PostgreSQL database."""
    # NOTE: Replace these with your actual database credentials
    return psycopg2.connect(
        host="localhost",
        database="Fitness_tracker",
        user="postgres",
        password="5432"
    )

# --- DATABASE SETUP ---
def create_tables():
    """Creates all required tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(255) PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email VARCHAR(255),
            goals TEXT,
            start_weight DECIMAL(5, 2),
            current_weight DECIMAL(5, 2)
        );
        CREATE TABLE IF NOT EXISTS workouts (
            workout_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(user_id),
            workout_date DATE NOT NULL,
            type VARCHAR(50) NOT NULL,
            duration_minutes INTEGER,
            calories_burned INTEGER
        );
        CREATE TABLE IF NOT EXISTS meals (
            meal_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(user_id),
            meal_date DATE NOT NULL,
            meal_type VARCHAR(20) NOT NULL,
            calories INTEGER,
            proteins INTEGER,
            carbs INTEGER,
            fats INTEGER
        );
        CREATE TABLE IF NOT EXISTS progress (
            progress_id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(user_id),
            date DATE NOT NULL,
            weight DECIMAL(5, 2),
            body_fat DECIMAL(5, 2),
            notes TEXT
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

# --- USER CRUD ---
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    return user_data

# --- WORKOUTS CRUD & AGGREGATIONS ---
def add_workout(workout_id, user_id, workout_date, workout_type, duration, calories):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO workouts (workout_id, user_id, workout_date, type, duration_minutes, calories_burned) VALUES (%s, %s, %s, %s, %s, %s)",
        (workout_id, user_id, workout_date, workout_type, duration, calories)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_workouts(user_id, workout_type=None, start_date=None, end_date=None, sort_by='workout_date', sort_order='DESC'):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM workouts WHERE user_id = %s"
    params = [user_id]
    if workout_type:
        query += " AND type = %s"
        params.append(workout_type)
    if start_date:
        query += " AND workout_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND workout_date <= %s"
        params.append(end_date)
    query += f" ORDER BY {sort_by} {sort_order}"
    cursor.execute(query, tuple(params))
    workouts = cursor.fetchall()
    cursor.close()
    conn.close()
    return workouts

def get_workout_metrics(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(duration_minutes), AVG(duration_minutes), SUM(calories_burned) FROM workouts WHERE user_id = %s", (user_id,))
    metrics = cursor.fetchone()
    cursor.close()
    conn.close()
    return metrics

# --- NUTRITION CRUD & AGGREGATIONS ---
def add_meal(meal_id, user_id, meal_date, meal_type, calories, proteins, carbs, fats):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO meals (meal_id, user_id, meal_date, meal_type, calories, proteins, carbs, fats) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (meal_id, user_id, meal_date, meal_type, calories, proteins, carbs, fats)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_meals(user_id, meal_type=None, start_date=None, end_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM meals WHERE user_id = %s"
    params = [user_id]
    if meal_type:
        query += " AND meal_type = %s"
        params.append(meal_type)
    if start_date:
        query += " AND meal_date >= %s"
        params.append(start_date)
    if end_date:
        query += " AND meal_date <= %s"
        params.append(end_date)
    query += " ORDER BY meal_date DESC"
    cursor.execute(query, tuple(params))
    meals = cursor.fetchall()
    cursor.close()
    conn.close()
    return meals

def get_meal_metrics(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(calories), AVG(calories) FROM meals WHERE user_id = %s", (user_id,))
    metrics = cursor.fetchone()
    cursor.close()
    conn.close()
    return metrics

def get_macro_breakdown(user_id, start_date, end_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(proteins), SUM(carbs), SUM(fats) FROM meals WHERE user_id = %s AND meal_date >= %s AND meal_date <= %s",
        (user_id, start_date, end_date)
    )
    macros = cursor.fetchone()
    cursor.close()
    conn.close()
    return macros

# --- PROGRESS CRUD & AGGREGATIONS ---
def add_progress(progress_id, user_id, date, weight, body_fat, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO progress (progress_id, user_id, date, weight, body_fat, notes) VALUES (%s, %s, %s, %s, %s, %s)",
        (progress_id, user_id, date, weight, body_fat, notes)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_progress_entries(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM progress WHERE user_id = %s ORDER BY date ASC", (user_id,))
    progress_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return progress_data

# --- COMBINED INSIGHTS ---
def get_calorie_balance(user_id, start_date, end_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(calories) FROM meals WHERE user_id = %s AND meal_date >= %s AND meal_date <= %s",
        (user_id, start_date, end_date)
    )
    calories_consumed = cursor.fetchone()[0] or 0
    cursor.execute(
        "SELECT SUM(calories_burned) FROM workouts WHERE user_id = %s AND workout_date >= %s AND workout_date <= %s",
        (user_id, start_date, end_date)
    )
    calories_burned = cursor.fetchone()[0] or 0
    cursor.close()
    conn.close()
    return calories_consumed, calories_burned