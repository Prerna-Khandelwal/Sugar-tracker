import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- FILE CONFIGURATION ---
DB_FILE = "sugar_tracker.csv"


def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Sugar Level (mg/dL)'] = df['Sugar Level (mg/dL)'].astype(int)
        df['Bolus Dose (Units)'] = df['Bolus Dose (Units)'].astype(float)
        df['Basal Dose (Units)'] = df['Basal Dose (Units)'].astype(float)
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
st.title("🩸 Daily Blood Sugar & Insulin Logger")

# --- SIDEBAR: ADD NEW ENTRY ---
st.sidebar.header("➕ Add New Reading")
with st.sidebar.form(key='log_form', clear_on_submit=True):
    log_date = st.date_input("Date", datetime.now())
    log_time = st.time_input("Time of Reading", datetime.now().time())
    timeframe = st.selectbox("Timeframe", ["Morning", "Mid-Morning", "Lunch", "Evening", "Dinner", "Bedtime"])
    sugar = st.number_input("Sugar Level (mg/dL)", min_value=0, max_value=600, value=100, step=1)
    bolus = st.number_input("Bolus Insulin Dose (Units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    basal = st.number_input("Basal Insulin Dose (Units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
    food = st.text_area("Food Eaten", placeholder="e.g., 2 chapatis, dal, salad")

    submit_button = st.form_submit_button(label='Save Log Entry')

if submit_button:
    new_entry = {
        "Date": log_date.strftime("%Y-%m-%d"),
        "Time of Reading": log_time.strftime("%I:%M %p"),
        "Timeframe": timeframe,
        "Sugar Level (mg/dL)": int(sugar),
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

    # 🛠️ EDIT SECTION
    with st.expander("✏️ Click here to Edit or Correct an Existing Entry"):
        df_display = st.session_state.data.copy()
        df_display['Label'] = df_display['Date'] + " | " + df_display['Timeframe'] + " (" + df_display[
            'Time of Reading'].astype(str) + ")"

        selected_label = st.selectbox("Select the entry you want to modify:", df_display['Label'].tolist())
        selected_index = df_display[df_display['Label'] == selected_label].index[0]

        current_row = st.session_state.data.iloc[selected_index]

        st.markdown("### Edit Entry Details")

        # Row 1: Timestamps & Timeframes
        ec1, ec2, ec3 = st.columns(3)
        with ec1:
            # Parse existing string date back to a datetime object for the input field
            current_date_obj = datetime.strptime(current_row["Date"], "%Y-%m-%d")
            edit_date = st.date_input("Edit Date", value=current_date_obj, key="e_date")
        with ec2:
            # Parse existing string time back to a time object
            current_time_obj = datetime.strptime(current_row["Time of Reading"], "%I:%M %p").time()
            edit_time = st.time_input("Edit Time of Reading", value=current_time_obj, key="e_time")
        with ec3:
            timeframe_options = ["Morning", "Mid-Morning", "Lunch", "Evening", "Dinner", "Bedtime"]
            current_tf_index = timeframe_options.index(current_row["Timeframe"]) if current_row[
                                                                                        "Timeframe"] in timeframe_options else 0
            edit_timeframe = st.selectbox("Edit Timeframe", options=timeframe_options, index=current_tf_index,
                                          key="e_tf")

        # Row 2: Medical Readings & Food
        ec4, ec5, ec6 = st.columns(3)
        with ec4:
            edit_sugar = st.number_input("Edit Sugar Level (mg/dL)", min_value=0, max_value=600,
                                         value=int(current_row["Sugar Level (mg/dL)"]), key="e_sug")
        with ec5:
            edit_bolus = st.number_input("Edit Bolus (Units)", min_value=0.0, max_value=100.0,
                                         value=float(current_row["Bolus Dose (Units)"]), step=0.5, key="e_bol")
        with ec6:
            edit_basal = st.number_input("Edit Basal (Units)", min_value=0.0, max_value=100.0,
                                         value=float(current_row["Basal Dose (Units)"]), step=0.5, key="e_bas")

        edit_food = st.text_input("Edit Food Eaten", value=str(current_row["Food Eaten"]), key="e_foo")

        if st.button("Update This Entry", type="primary"):
            # Commit all edited fields back to the DataFrame row
            st.session_state.data.at[selected_index, "Date"] = edit_date.strftime("%Y-%m-%d")
            st.session_state.data.at[selected_index, "Time of Reading"] = edit_time.strftime("%I:%M %p")
            st.session_state.data.at[selected_index, "Timeframe"] = edit_timeframe
            st.session_state.data.at[selected_index, "Sugar Level (mg/dL)"] = int(edit_sugar)
            st.session_state.data.at[selected_index, "Bolus Dose (Units)"] = float(edit_bolus)
            st.session_state.data.at[selected_index, "Basal Dose (Units)"] = float(edit_basal)
            st.session_state.data.at[selected_index, "Food Eaten"] = edit_food

            save_data(st.session_state.data)
            st.success("Entry completely updated!")
            st.rerun()

    st.write("---")

    # Live Metrics
    latest = st.session_state.data.iloc[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric(label=f"Latest Sugar ({latest['Timeframe']})", value=f"{latest['Sugar Level (mg/dL)']} mg/dL")
    col2.metric(label="Latest Bolus", value=f"{latest['Bolus Dose (Units)']} U")
    col3.metric(label="Latest Basal", value=f"{latest['Basal Dose (Units)']} U")

    # Data View (Newest entries first)
    st.dataframe(st.session_state.data.iloc[::-1], use_container_width=True)

    # Trends
    st.subheader("📈 Sugar Level Trends")
    chart_data = st.session_state.data.copy()
    chart_data['Datetime'] = pd.to_datetime(chart_data['Date'] + ' ' + chart_data['Time of Reading'])
    chart_data = chart_data.sort_values('Datetime')
    st.line_chart(data=chart_data, x='Datetime', y='Sugar Level (mg/dL)')

else:
    st.info("No logs found yet. Use the sidebar on the left to add your first reading!")