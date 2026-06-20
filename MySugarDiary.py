import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time

# --- FILE CONFIGURATION ---
DB_FILE = "sugar_tracker.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Ensure a completely unique string ID exists for every record
        if 'ID' not in df.columns:
            df['ID'] = [str(int(time.time()) + i) for i in range(len(df))]
        df['Sugar Level (mg/dL)'] = df['Sugar Level (mg/dL)'].fillna("—").astype(str)
        df['Bolus Dose (Units)'] = df['Bolus Dose (Units)'].fillna(0.0).astype(float)
        df['Basal Dose (Units)'] = df['Basal Dose (Units)'].fillna(0.0).astype(float)
        df['Food Eaten'] = df['Food Eaten'].fillna("None").astype(str)
        return df
    else:
        return pd.DataFrame(columns=[
            "ID", "Date", "Time of Reading", "Timeframe", 
            "Sugar Level (mg/dL)", "Bolus Dose (Units)", 
            "Basal Dose (Units)", "Food Eaten"
        ])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- APP UI ---
st.set_page_config(page_title="Blood Sugar & Insulin Tracker", layout="wide")
st.title("🩸 Fully Editable Blood Sugar & Insulin Logger")

# --- SIDEBAR: ADD NEW ENTRY ---
st.sidebar.header("➕ Add New Reading")
with st.sidebar.form(key='log_form', clear_on_submit=True):
    log_date = st.date_input("Date", datetime.now())
    log_time = st.time_input("Time of Reading", datetime.now().time())
    timeframe = st.selectbox("Timeframe", ["Morning", "Mid-Morning", "Lunch", "Evening", "Dinner", "Bedtime"])
    
    not_checked = st.checkbox("Not Checked", value=False)
    sugar = st.number_input("Sugar Level (mg/dL)", min_value=0, max_value=600, value=100, step=1)
    bolus = st.number_input("Bolus Insulin Dose (Units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    basal = st.number_input("Basal Insulin Dose (Units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    food = st.text_area("Food Eaten", placeholder="e.g., Evening tea with biscuits")
    
    submit_button = st.form_submit_button(label='Save Log Entry')

if submit_button:
    unique_id = str(int(time.time())) # Generates a bulletproof timestamp ID
    new_entry = {
        "ID": unique_id,
        "Date": log_date.strftime("%Y-%m-%d"),
        "Time of Reading": log_time.strftime("%I:%M %p"),
        "Timeframe": timeframe,
        "Sugar Level (mg/dL)": "—" if not_checked else str(int(sugar)),
        "Bolus Dose (Units)": float(bolus),
        "Basal Dose (Units)": float(basal),
        "Food Eaten": food if food else "None"
    }
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_entry])], ignore_index=True)
    save_data(st.session_state.data)
    st.sidebar.success("Reading logged successfully!")
    st.rerun()

# --- MAIN PAGE: LOGS & EDITING ---
st.header("📋 Historical Logs")

if not st.session_state.data.empty:
    
    # 🛠️ FIXED UNIVERSAL EDIT SECTION (Uses Unique IDs now)
    with st.expander("✏️ Click here to Edit / Modify ANY Existing Entry"):
        df_display = st.session_state.data.copy()
        # Build label
        df_display['Label'] = df_display['Date'] + " | " + df_display['Timeframe'] + " (" + df_display['Time of Reading'].astype(str) + ")"
        
        # Select entry by label text
        selected_label = st.selectbox("Select the exact entry you want to modify:", df_display['Label'].tolist())
        
        # Find the row ID instead of index number
        selected_id = df_display[df_display['Label'] == selected_label]['ID'].values[0]
        
        # Target the row dynamically using the unique ID
        real_index = st.session_state.data[st.session_state.data['ID'] == selected_id].index[0]
        current_row = st.session_state.data.loc[real_index]
        
        st.markdown("#### Modify Selected Log Details")
        
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            current_date_obj = datetime.strptime(str(current_row["Date"]), "%Y-%m-%d")
            edit_date = st.date_input("Modify Date", value=current_date_obj, key=f"d_{selected_id}")
        with ec2:
            current_time_obj = datetime.strptime(str(current_row["Time of Reading"]), "%I:%M %p").time()
            edit_time = st.time_input("Modify Time of Reading", value=current_time_obj, key=f"t_{selected_id}")
        with ec3:
            timeframe_options = ["Morning", "Mid-Morning", "Lunch", "Evening", "Dinner", "Bedtime"]
            current_tf_index = timeframe_options.index(current_row["Timeframe"]) if current_row["Timeframe"] in timeframe_options else 0
            edit_timeframe = st.selectbox("Modify Timeframe", options=timeframe_options, index=current_tf_index, key=f"tf_{selected_id}")
            
        ec4, ec5, ec6 = st.columns(3)
        with ec4:
            is_currently_unchecked = current_row["Sugar Level (mg/dL)"] == "—"
            edit_not_checked = st.checkbox("Modify as 'Not Checked'", value=is_currently_
