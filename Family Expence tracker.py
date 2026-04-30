import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="Family Budget", page_icon="💰", layout="centered")

# JSON Bypass Logic
try:
    # We will put EVERYTHING into one secret called 'service_account'
    creds_dict = json.loads(st.secrets["service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    conn = st.connection("gsheets", type=GSheetsConnection, **creds_dict)
except Exception as e:
    st.error("Waiting for JSON Secrets... Please update the Secrets box.")
    st.stop()

st.title("👨‍👩‍👧‍👦 Family Expense Tracker")

# 4. Input Form
with st.form("entry_form", clear_on_submit=True):
    st.subheader("New Entry")
    
    amount = st.number_input("Amount (₹)", min_value=0.0, step=1.0, format="%.2f")
    
    category = st.selectbox("Category", [
        "Groceries", 
        "Utilities & Bills", 
        "Travel & Transit", 
        "Home Construction", 
        "Education",
        "Dining Out",
        "Medical",
        "Other"
    ])
    
    expense_type = st.radio("Expense Status", ["Planned", "Unplanned"], horizontal=True)
    
    date = st.date_input("Date", datetime.now())
    added_by = st.selectbox("Who is adding this?", ["Manoj", "Wife"])
    note = st.text_input("Note (e.g., 'Sabari Express snacks')")
    
    submit = st.form_submit_button("Save Expense")

    if submit:
        if amount > 0:
            # Create a dataframe for the new row
            new_row = pd.DataFrame([{
                "Date": date.strftime("%Y-%m-%d"),
                "Category": category,
                "Type": expense_type,
                "Amount": amount,
                "Note": note,
                "Added By": added_by
            }])
            
            try:
                # Read current data, append new row, and update sheet
                existing_data = conn.read(worksheet="Sheet1")
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.success(f"✅ Saved: ₹{amount} for {category}")
                st.balloons()
            except Exception as e:
                st.error(f"Error updating Google Sheet: {e}")
        else:
            st.error("Please enter an amount greater than 0.")

# 5. Dashboard Section
st.divider()
st.subheader("📊 Spending Summary")

try:
    # Refresh data for the dashboard
    df = conn.read(worksheet="Sheet1")

    if not df.empty:
        # Data Cleanup
        df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce').fillna(0)
        
        # Key Metrics
        total_spent = df["Amount"].sum()
        unplanned_total = df[df["Type"] == "Unplanned"]["Amount"].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Expenses", f"₹{total_spent:,.2f}")
        col2.metric("Unplanned", f"₹{unplanned_total:,.2f}", delta_color="inverse")

        # Category Chart
        st.write("### Spending by Category")
        category_totals = df.groupby("Category")["Amount"].sum()
        st.bar_chart(category_totals)

        # Recent Transactions Table
        with st.expander("Show Transaction History"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("No data found in Sheet1. Add an entry above to get started!")

except Exception as e:
    st.info("Add your first entry to see the dashboard analytics.")