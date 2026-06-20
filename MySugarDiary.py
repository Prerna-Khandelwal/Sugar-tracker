import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- FILE CONFIGURATION ---
DB_FILE = "sugar_tracker.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Keep sugar level as a string/mixed type so it can store "—" for unchecked entries
        df['Sugar Level (mg/dL)'] = df['Sugar Level (mg/dL)'].fillna("—").astype(str)
        df['Bolus Dose (Units)'] = df['Bolus Dose (Units)'].fillna(0.0).astype(float)
        df['Basal Dose (Units)'] = df['Basal Dose (Units)'].fillna(0.0).astype(float)
        df['Food Eaten'] = df['Food Eaten'].fillna("None").astype(str)
        return df
    else:
        return pd.DataFrame(columns=[
            "Date", "Time of Reading", "Timeframe", 
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
    
    # 🌟 NEW FEATURE: NOT CHECKED OPTION
    not_checked = st.checkbox("Not Checked", value=False, help="Check this if you didn't test your blood sugar this time.")
    sugar = st.number_input("Sugar Level (mg/dL)", min_value=0, max_value=600, value=100, step=1)
    
    bolus = st.number_input("Bolus Insulin Dose (Units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    basal = st.number_input("Basal Insulin Dose (Units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    food = st.text_area("Food Eaten", placeholder="e.g., Evening tea with biscuits")
    
    submit_button = st.form_submit_button(label='Save Log Entry')

if submit_button:
    new_entry = {
        "Date": log_date.strftime("%Y-%m-%d"),
        "Time of Reading": log_time.strftime("%I:%M %p"),
        "Timeframe": timeframe,
        "Sugar Level (mg/dL)": "—" if not_checked else str(int(sugar)), # Stores a dash if unchecked
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
    
    # 🛠️ UNIVERSAL EDIT SECTION
    with st.expander("✏️ Click here to Edit / Modify ANY Existing Entry"):
        df_display = st.session_state.data.copy()
        df_display['Label'] = df_display['Date'] + " | " + df_display['Timeframe'] + " (" + df_display['Time of Reading'].astype(str) + ")"
        
        selected_label = st.selectbox("Select the entry sequence you want to modify:", df_display['Label'].tolist())
        selected_index = df_display[df_display['Label'] == selected_label].index[0]
        
        current_row = st.session_state.data.iloc[selected_index]
        
        st.markdown("#### Modify Selected Log Details")
        
        # Row 1: Time modifications
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            current_date_obj = datetime.strptime(str(current_row["Date"]), "%Y-%m-%d")
            edit_date = st.date_input("Modify Date", value=current_date_obj, key="edit_date_field")
        with ec2:
            current_time_obj = datetime.strptime(str(current_row["Time of Reading"]), "%I:%M %p").time()
            edit_time = st.time_input("Modify Time of Reading", value=current_time_obj, key="edit_time_field")
        with ec3:
            timeframe_options = ["Morning", "Mid-Morning", "Lunch", "Evening", "Dinner", "Bedtime"]
            current_tf_index = timeframe_options.index(current_row["Timeframe"]) if current_row["Timeframe"] in timeframe_options else 0
            edit_timeframe = st.selectbox("Modify Timeframe", options=timeframe_options, index=current_tf_index, key="edit_tf_field")
            
        # Row 2: Level & Food modifications
        ec4, ec5, ec6 = st.columns(3)
        with ec4:
            # Check if the existing record was "Not Checked"
            is_currently_unchecked = current_row["Sugar Level (mg/dL)"] == "—"
            edit_not_checked = st.checkbox("Modify as 'Not Checked'", value=is_currently_unchecked, key="edit_nc_field")
            
            # Default helper value for input if it was originally unchecked
            default_sugar_val = 100 if is_currently_unchecked else int(float(current_row["Sugar Level (mg/dL)"]))
            edit_sugar = st.number_input("Modify Sugar Level (mg/dL)", min_value=0, max_value=600, value=default_sugar_val, key="edit_sug_field")
            
        with ec5:
            edit_bolus = st.number_input("Modify Bolus (Units)", min_value=0.0, max_value=100.0, value=float(current_row["Bolus Dose (Units)"]), step=0.5, key="edit_bol_field")
        with ec6:
            edit_basal = st.number_input("Modify Basal (Units)", min_value=0.0, max_value=100.0, value=float(current_row["Basal Dose (Units)"]), step=0.5, key="edit_bas_field")
            
        edit_food = st.text_input("Modify Food Eaten", value=str(current_row["Food Eaten"]), key="edit_food_field")
        
        # Action Buttons
        col_btn1, col_btn2 = st.columns([1, 5])
        with col_btn1:
            if st.button("Save Changes", type="primary", key="save_mod_btn"):
                st.session_state.data.at[selected_index, "Date"] = edit_date.strftime("%Y-%m-%d")
                st.session_state.data.at[selected_index, "Time of Reading"] = edit_time.strftime("%I:%M %p")
                st.session_state.data.at[selected_index, "Timeframe"] = edit_timeframe
                st.session_state.data.at[selected_index, "Sugar Level (mg/dL)"] = "—" if edit_not_checked else str(int(edit_sugar))
                st.session_state.data.at[selected_index, "Bolus Dose (Units)"] = float(edit_bolus)
                st.session_state.data.at[selected_index, "Basal Dose (Units)"] = float(edit_basal)
                st.session_state.data.at[selected_index, "Food Eaten"] = edit_food
                
                save_data(st.session_state.data)
                st.success("Entry updated successfully!")
                st.rerun()
        with col_btn2:
            if st.button("🗑️ Delete This Entire Entry", type="secondary", key="del_entry_btn"):
                st.session_state.data = st.session_state.data.drop(selected_index).reset_index(drop=True)
                save_data(st.session_state.data)
                st.warning("Entry deleted.")
                st.rerun()

    st.write("---")
    
    # Dynamic Dashboard Display (Newest first)
    st.dataframe(st.session_state.data.iloc[::-1], use_container_width=True)
    
    # Visual Analytics Graph (Slightly altered to skip blank records safely)
    st.subheader("📈 Trend Line")
    chart_data = st.session_state.data.copy()
    # Filter out entries where sugar wasn't checked so the graph line doesn't break
    chart_data = chart_data[chart_data['Sugar Level (mg/dL)'] != "—"]
    
    if not chart_data.empty:
        chart_data['Sugar Level (mg/dL)'] = chart_data['Sugar Level (mg/dL)'].astype(int)
        chart_data['Datetime'] = pd.to_datetime(chart_data['Date'] + ' ' + chart_data['Time of Reading'])
        chart_data = chart_data.sort_values('Datetime')
        st.line_chart(data=chart_data, x='Datetime', y='Sugar Level (mg/dL)')
    else:
        st.info("Log some actual numerical sugar levels to generate the trend graph!")
    
else:
    st.info("No logs found. Use the panel on the left to add your first reading!")
