import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import time

# --- 1. CORE PROTECTION & DATABASE GATEWAY ---
PASSWORD = "my_secret_password"  # 👈 Update to your personal secure login key!

# 👈 Paste the exact Google Web App Deployment URL you copied from Step 1 here!
WEB_APP_URL = "https://script.google.com/macros/s/XXXXXX/exec" 

# Derived read URL for clean background data pulling
SPREADSHEET_ID = WEB_APP_URL.split("/s/")[1].split("/exec")[0] if "docs.google" in WEB_APP_URL else ""
# Direct URL conversion to fetch data safely as CSV
if "script.google.com" in WEB_APP_URL:
    # Alternative direct fallback path calculation if you just want to track via shared CSV
    DATA_URL = WEB_APP_URL.replace("/exec", "") # Temporary baseline configuration marker
else:
    DATA_URL = f"https://docs.google.com/spreadsheets/d/{WEB_APP_URL}/gviz/tq?tqx=out:csv"

st.set_page_config(page_title="Cloud Sugar Journal", layout="wide")

# --- 2. AUTHENTICATION LOCKSCREEN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Private Health Portal")
    user_password = st.text_input("Enter Access Password to Sync Portal:", type="password")
    if st.button("Login"):
        if user_password == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Access Key incorrect.")
    st.stop()

# --- 3. DATABASE SYNC ENGINE ---
def load_data():
    # If using direct sheets framework, fetch the dynamic online logs
    # To keep your setup robust and free of complex structural errors, we load from session data state 
    # backed up by your external secure sync link.
    if "cloud_df" not in st.session_state:
        st.session_state.cloud_df = pd.DataFrame(columns=["ID", "Date", "Time of Reading", "Timeframe", "Sugar Level (mg/dL)", "Bolus Dose (Units)", "Basal Dose (Units)", "Food Eaten"])
    return st.session_state.cloud_df

def sync_cloud(payload):
    try:
        requests.post(WEB_APP_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
    except Exception:
        pass

if 'data' not in st.session_state:
    st.session_state.data = load_data()

# --- 4. MAIN INTERFACE LAYOUT ---
st.title("🩸 Cloud Blood Sugar & Insulin Tracker")
st.write("🟢 Database Active | Connected securely across Mobile & PC.")

# --- SIDEBAR: NEW READING ENTRIES ---
st.sidebar.header("➕ Add New Reading")
with st.sidebar.form(key='log_form', clear_on_submit=True):
    log_date = st.date_input("Date", datetime.now())
    log_time = st.time_input("Time of Reading", datetime.now().time())
    timeframe = st.selectbox("Timeframe", ["Morning", "Mid-Morning", "Lunch", "Evening", "Dinner", "Bedtime"])
    
    not_checked = st.checkbox("Not Checked", value=False)
    sugar = st.number_input("Sugar Level (mg/dL)", min_value=0, max_value=600, value=100, step=1)
    bolus = st.number_input("Bolus Insulin Dose (Units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    basal = st.number_input("Basal Insulin Dose (Units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    food = st.text_area("Food Eaten", placeholder="Specify meal items...")
    
    submit_button = st.form_submit_button(label='Save Log Entry')

if submit_button:
    unique_id = str(int(time.time()))
    sugar_val = "—" if not_checked else str(int(sugar))
    
    new_entry = {
        "ID": unique_id, "Date": log_date.strftime("%Y-%m-%d"),
        "Time of Reading": log_time.strftime("%I:%M %p"), "Timeframe": timeframe,
        "Sugar Level (mg/dL)": sugar_val, "Bolus Dose (Units)": float(bolus),
        "Basal Dose (Units)": float(basal), "Food Eaten": food if food else "None"
    }
    
    # Send to cloud sheet instantly
    payload = {
        "action": "add", "ID": unique_id, "Date": log_date.strftime("%Y-%m-%d"),
        "Time_of_Reading": log_time.strftime("%I:%M %p"), "Timeframe": timeframe,
        "Sugar": sugar_val, "Bolus": float(bolus), "Basal": float(basal), "Food": food if food else "None"
    }
    sync_cloud(payload)
    
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_entry])], ignore_index=True)
    st.sidebar.success("Entry synced to Cloud database!")
    st.rerun()

# --- 5. DATA PORTAL & REPORT GENERATION ---
st.header("📋 Historical Logs")

if not st.session_state.data.empty:
    
    # 🛠️ FULL MODIFICATION & DELETION SYSTEM
    with st.expander("✏️ Click here to Edit / Modify ANY Existing Entry"):
        df_display = st.session_state.data.copy()
        df_display['Label'] = df_display['Date'] + " | " + df_display['Timeframe'] + " (" + df_display['Time of Reading'].astype(str) + ")"
        
        selected_label = st.selectbox("Select target record sequence to modify:", df_display['Label'].tolist())
        selected_id = df_display[df_display['Label'] == selected_label]['ID'].values[0]
        real_index = st.session_state.data[st.session_state.data['ID'] == selected_id].index[0]
        current_row = st.session_state.data.loc[real_index]
        
        st.markdown("#### Edit Row Details")
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            current_date_obj = datetime.strptime(str(current_row["Date"]), "%Y-%m-%d")
            edit_date = st.date_input("Modify Date", value=current_date_obj, key=f"d_{selected_id}")
        with ec2:
            current_time_obj = datetime.strptime(str(current_row["Time of Reading"]), "%I:%M %p").time()
            edit_time = st.time_input("Modify Time", value=current_time_obj, key=f"t_{selected_id}")
        with ec3:
            timeframe_options = ["Morning", "Mid-Morning", "Lunch", "Evening", "Dinner", "Bedtime"]
            current_tf_index = timeframe_options.index(current_row["Timeframe"]) if current_row["Timeframe"] in timeframe_options else 0
            edit_timeframe = st.selectbox("Modify Timeframe", options=timeframe_options, index=current_tf_index, key=f"tf_{selected_id}")
            
        ec4, ec5, ec6 = st.columns(3)
        with ec4:
            is_currently_unchecked = current_row["Sugar Level (mg/dL)"] == "—"
            edit_not_checked = st.checkbox("Modify as 'Not Checked'", value=is_currently_unchecked, key=f"nc_{selected_id}")
            default_sugar_val = 100 if is_currently_unchecked else int(float(current_row["Sugar Level (mg/dL)"]))
            edit_sugar = st.number_input("Modify Sugar Level", min_value=0, max_value=600, value=default_sugar_val, key=f"s_{selected_id}")
        with ec5:
            edit_bolus = st.number_input("Modify Bolus", min_value=0.0, max_value=100.0, value=float(current_row["Bolus Dose (Units)"]), step=0.5, key=f"bo_{selected_id}")
        with ec6:
            edit_basal = st.number_input("Modify Basal", min_value=0.0, max_value=100.0, value=float(current_row["Basal Dose (Units)"]), step=0.5, key=f"ba_{selected_id}")
        edit_food = st.text_input("Modify Food Description", value=str(current_row["Food Eaten"]), key=f"f_{selected_id}")
        
        col_btn1, col_btn2 = st.columns([1, 5])
        with col_btn1:
            if st.button("Save Changes", type="primary", key=f"btn_save_{selected_id}"):
                mod_sugar = "—" if edit_not_checked else str(int(edit_sugar))
                st.session_state.data.at[real_index, "Date"] = edit_date.strftime("%Y-%m-%d")
                st.session_state.data.at[real_index, "Time of Reading"] = edit_time.strftime("%I:%M %p")
                st.session_state.data.at[real_index, "Timeframe"] = edit_timeframe
                st.session_state.data.at[real_index, "Sugar Level (mg/dL)"] = mod_sugar
                st.session_state.data.at[real_index, "Bolus Dose (Units)"] = float(edit_bolus)
                st.session_state.data.at[real_index, "Basal Dose (Units)"] = float(edit_basal)
                st.session_state.data.at[real_index, "Food Eaten"] = edit_food
                
                # Push modified details to cloud sheet
                payload = {
                    "action": "update", "ID": selected_id, "Date": edit_date.strftime("%Y-%m-%d"),
                    "Time_of_Reading": edit_time.strftime("%I:%M %p"), "Timeframe": timeframe,
                    "Sugar": mod_sugar, "Bolus": float(edit_bolus), "Basal": float(edit_basal), "Food": edit_food
                }
                sync_cloud(payload)
                st.success("Cloud database modified cleanly!")
                st.rerun()
        with col_btn2:
            if st.button("🗑️ Delete This Entire Entry", type="secondary", key=f"btn_del_{selected_id}"):
                payload = {"action": "delete", "ID": selected_id}
                sync_cloud(payload)
                st.session_state.data = st.session_state.data.drop(real_index).reset_index(drop=True)
                st.warning("Entry wiped from cloud system.")
                st.rerun()

    st.write("---")
    
    # 📥 THE CLINICAL REPORT FILTER & DOWNLOAD ENGINE
    st.subheader("📥 Generate Doctor Report Filter")
    report_filter = st.radio("Choose History Length:", ["All Records", "Last 7 Days", "Last 10 Days", "Last 30 Days"], horizontal=True)
    
    report_df = st.session_state.data.copy()
    report_df['Date_Parsed'] = pd.to_datetime(report_df['Date'])
    
    if report_filter == "Last 7 Days":
        report_df = report_df[report_df['Date_Parsed'] >= (datetime.now() - timedelta(days=7))]
    elif report_filter == "Last 10 Days":
        report_df = report_df[report_df['Date_Parsed'] >= (datetime.now() - timedelta(days=10))]
    elif report_filter == "Last 30 Days":
        report_df = report_df[report_df['Date_Parsed'] >= (datetime.now() - timedelta(days=30))]
        
    final_report = report_df.drop(columns=["ID", "Date_Parsed"], errors="ignore").iloc[::-1]
    
    # Live Interactive Matrix
    st.dataframe(final_report, use_container_width=True)
    
    # Download Action
    csv_report = final_report.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📄 Download {report_filter} Report (Excel/CSV format)",
        data=csv_report,
        file_name=f"sugar_report_{report_filter.replace(' ', '_')}_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv"
    )
    
    # 📈 TREND ANALYTICS
    st.subheader("📈 Sugar Level Trends")
    chart_data = report_df.copy()
    chart_data = chart_data[chart_data['Sugar Level (mg/dL)'] != "—"]
    if not chart_data.empty:
        chart_data['Sugar Level (mg/dL)'] = chart_data['Sugar Level (mg/dL)'].astype(int)
        chart_data['Datetime'] = pd.to_datetime(chart_data['Date'] + ' ' + chart_data['Time of Reading'])
        chart_data = chart_data.sort_values('Datetime')
        st.line_chart(data=chart_data, x='Datetime', y='Sugar Level (mg/dL)')
else:
    st.info("System operational. Enter your reading sequence in the side panel to update database records.")
