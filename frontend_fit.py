import streamlit as st
import pandas as pd
import uuid
from datetime import date, timedelta
import plotly.express as px
from backend_fit import (
    create_tables, get_user,
    add_workout, get_workouts, get_workout_metrics,
    add_meal, get_meals, get_meal_metrics, get_macro_breakdown,
    add_progress, get_progress_entries,
    get_calorie_balance
)

# --- PAGE SETUP & INITIALIZATION ---
st.set_page_config(page_title="Fitness Tracker", layout="wide")
create_tables()

# NOTE: A real app would have a login system. For this example, we'll use a hardcoded user_id.
CURRENT_USER_ID = "12345"
USER_GOAL_WEIGHT = 75.0 # Example goal weight in kg

# --- Helper functions for UI components ---
def show_workout_metrics(user_id):
    total_workouts, total_duration, avg_duration, total_calories = get_workout_metrics(user_id)
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Total Workouts", total_workouts if total_workouts else 0)
    with metric_col2:
        st.metric("Total Duration (min)", total_duration if total_duration else 0)
    with metric_col3:
        st.metric("Total Calories Burned", total_calories if total_calories else 0)

def show_nutrition_metrics(user_id):
    total_meals, total_calories, avg_calories = get_meal_metrics(user_id)
    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric("Total Meals Logged", total_meals if total_meals else 0)
    with metric_col2:
        st.metric("Total Calories Consumed", total_calories if total_calories else 0)

# --- APP LAYOUT ---
st.title("💪 Personal Fitness Tracker")
tabs = st.tabs(["📊 Dashboard", "🏋️ Workouts", "🍔 Nutrition", "📈 Progress"])

# --- DASHBOARD TAB ---
with tabs[0]:
    st.header("Dashboard & Insights")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Workout Summary")
        show_workout_metrics(CURRENT_USER_ID)
    with col2:
        st.subheader("Nutrition Summary")
        show_nutrition_metrics(CURRENT_USER_ID)
    
    st.subheader("Goals & Progress")
    progress_data = get_progress_entries(CURRENT_USER_ID)
    if progress_data:
        df_progress = pd.DataFrame(progress_data, columns=['progress_id', 'user_id', 'date', 'weight', 'body_fat', 'notes'])
        current_weight = df_progress['weight'].iloc[-1]
        weight_to_go = max(0, current_weight - USER_GOAL_WEIGHT)
        st.metric("Weight to Goal", f"{weight_to_go:.2f} kg to go!")
    
    st.subheader("Weekly Calorie Balance")
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    calories_consumed, calories_burned = get_calorie_balance(CURRENT_USER_ID, start_of_week, today)
    
    balance = calories_burned - calories_consumed
    st.info(f"Your net calorie balance this week is **{balance}** calories.")
    
    st.subheader("Visualizations")
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        st.subheader("Weight Trend Over Time")
        if progress_data:
            df_progress['date'] = pd.to_datetime(df_progress['date'])
            fig_weight = px.line(df_progress, x='date', y='weight', title='Weight Trend')
            st.plotly_chart(fig_weight)
        else:
            st.info("No progress data to display weight trend.")
            
    with viz_col2:
        st.subheader("Weekly Macro Breakdown")
        macros = get_macro_breakdown(CURRENT_USER_ID, start_of_week, today)
        if macros and any(m is not None for m in macros):
            df_macros = pd.DataFrame([macros], columns=['Proteins', 'Carbs', 'Fats'])
            fig_macros = px.pie(df_macros.T, values=0, names=df_macros.columns, title='Macro Breakdown')
            st.plotly_chart(fig_macros)
        else:
            st.info("No meal data for macro breakdown.")

# --- WORKOUTS TAB ---
with tabs[1]:
    st.header("Log Workouts")
    with st.form("workout_form", clear_on_submit=True):
        workout_date = st.date_input("Date", value=date.today())
        workout_type = st.selectbox("Type", ["Cardio", "Strength"])
        duration = st.number_input("Duration (minutes)", min_value=1)
        calories = st.number_input("Calories Burned", min_value=1)
        if st.form_submit_button("Add Workout"):
            add_workout(str(uuid.uuid4()), CURRENT_USER_ID, workout_date, workout_type, duration, calories)
            st.success("Workout logged!")
            st.rerun()
            
    st.subheader("Workout History")
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        filter_type = st.selectbox("Filter by Type", ["All", "Cardio", "Strength"])
    with col_filter2:
     sort_by = st.selectbox("Sort by", ["workout_date", "calories_burned", "duration_minutes"])
     order_label = st.radio("Order", ["Descending", "Ascending"])
     sort_order = "DESC" if order_label == "Descending" else "ASC"

    
    workouts_data = get_workouts(CURRENT_USER_ID, filter_type if filter_type != "All" else None, sort_by=sort_by, sort_order=sort_order)
    if workouts_data:
        df_workouts = pd.DataFrame(workouts_data, columns=['workout_id', 'user_id', 'workout_date', 'type', 'duration_minutes', 'calories_burned'])
        st.dataframe(df_workouts[['workout_date', 'type', 'duration_minutes', 'calories_burned']])
    else:
        st.info("No workouts logged yet.")
        
# --- NUTRITION TAB ---
with tabs[2]:
    st.header("Log Meals")
    with st.form("meal_form", clear_on_submit=True):
        meal_date = st.date_input("Date", value=date.today())
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack"])
        calories = st.number_input("Calories", min_value=1)
        col_macros1, col_macros2, col_macros3 = st.columns(3)
        with col_macros1:
            proteins = st.number_input("Proteins (g)", min_value=0)
        with col_macros2:
            carbs = st.number_input("Carbs (g)", min_value=0)
        with col_macros3:
            fats = st.number_input("Fats (g)", min_value=0)
        if st.form_submit_button("Add Meal"):
            add_meal(str(uuid.uuid4()), CURRENT_USER_ID, meal_date, meal_type, calories, proteins, carbs, fats)
            st.success("Meal logged!")
            st.rerun()
    
    st.subheader("Meal History")
    meals_data = get_meals(CURRENT_USER_ID)
    if meals_data:
        df_meals = pd.DataFrame(meals_data, columns=['meal_id', 'user_id', 'meal_date', 'meal_type', 'calories', 'proteins', 'carbs', 'fats'])
        st.dataframe(df_meals[['meal_date', 'meal_type', 'calories', 'proteins', 'carbs', 'fats']])
    else:
        st.info("No meals logged yet.")

# --- PROGRESS TAB ---
with tabs[3]:
    st.header("Track Your Progress")
    with st.form("progress_form", clear_on_submit=True):
        progress_date = st.date_input("Date", value=date.today())
        weight = st.number_input("Current Weight (kg)", min_value=1.0, format="%.2f")
        body_fat = st.number_input("Body Fat (%)", min_value=0.0, max_value=100.0, format="%.2f")
        notes = st.text_area("Notes", "How are you feeling?")
        if st.form_submit_button("Log Progress"):
            add_progress(str(uuid.uuid4()), CURRENT_USER_ID, progress_date, weight, body_fat, notes)
            st.success("Progress logged!")
            st.rerun()

    st.subheader("Progress History")
    progress_data = get_progress_entries(CURRENT_USER_ID)
    if progress_data:
        df_progress = pd.DataFrame(progress_data, columns=['progress_id', 'user_id', 'date', 'weight', 'body_fat', 'notes'])
        st.dataframe(df_progress[['date', 'weight', 'body_fat', 'notes']])
    else:
        st.info("No progress entries yet.")