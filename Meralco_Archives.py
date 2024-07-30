import streamlit as st
import pandas as pd
from datetime import date
import os

# Load the Excel file
file_path = 'C:/Users/MARK/Meralco-Archive-Rates-Dashboard/Historical MERALCO Schedule of Rates reordered columns.xlsx'
df = pd.read_excel(file_path, engine='openpyxl')

# Streamlit application
st.title("Meralco History Rates")

# Initialize session state
if 'filtered_df' not in st.session_state:
    st.session_state['filtered_df'] = pd.DataFrame()
if 'user_input_value' not in st.session_state:
    st.session_state['user_input_value'] = None

# Dropdown for Customer Class
customer_classes = df['Customer Class'].unique().tolist()
selected_class = st.selectbox("Select Customer Class", customer_classes)

mapping = {
    "Residential": "Consumption", 
    "General Service A": "Consumption",
    "General Service B": "Demand",
    "General Power (GP) Secondary": "Demand",
    "GP 13.8 KV and below": "Demand",
    "GP 34.5 KV": "Demand"
}

user_input_type = mapping[selected_class]

if user_input_type == "Consumption": 
    st.session_state['user_input_value'] = st.number_input("Enter Consumption Value", min_value=0.0, format="%.2f")
elif user_input_type == "Demand":
    st.session_state['user_input_value'] = st.number_input("Enter Demand Value", min_value=0.0, format="%.2f")

# Filter by selected Customer Class
df_class = df[df['Customer Class'] == selected_class]

if st.session_state['user_input_value'] is not None:
    # Filter DataFrame based on user input
    user_value = st.session_state['user_input_value']
    
    if user_input_type == "Consumption":
        valid_input = (df_class[f'Lower Limit {user_input_type}'] <= user_value) & (df_class[f'Upper Limit {user_input_type}'] >= user_value)
    elif user_input_type == "Demand":
        valid_input = (df_class[f'Lower Limit {user_input_type}'] <= user_value) & (df_class[f'Upper Limit {user_input_type}'] >= user_value)
    
    if valid_input.any():
        df_demand = df_class[
            (df_class[f'Lower Limit {user_input_type}'] <= user_value) & 
            (df_class[f'Upper Limit {user_input_type}'] >= user_value)
        ].copy()  # Create a copy to avoid SettingWithCopyWarning
    else:
        st.error("Enter a valid value within the specified limits.")
        df_demand = pd.DataFrame()
else:
    df_demand = pd.DataFrame()

# Requested Dates
requested_dates = st.date_input(
    'Select Supply Period Range',
    min_value=date(2012, 1, 1),
    max_value=date.today(),
    value=(date.today() - pd.Timedelta(days=365), date.today())
)

if len(requested_dates) == 2:
    start_date, end_date = requested_dates
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date) + pd.Timedelta(days=1)

    # Convert 'Supply Period' to datetime if it's not already
    if 'Supply Period' in df_demand.columns:
        df_demand = df_demand.copy()  # Ensure df_demand is a copy
        df_demand['Supply Period'] = pd.to_datetime(df_demand['Supply Period'])

        # Filter by selected Supply Period range
        df_period = df_demand[(df_demand['Supply Period'] >= start_date) & (df_demand['Supply Period'] < end_date)]

        if st.button("Submit"):
            if not df_period.empty:
                # Format 'Supply Period' column
                df_period['Supply Period'] = df_period['Supply Period'].dt.strftime('%b-%y')
                
                # Sort by 'Supply Period'
                df_period = df_period.sort_values(by='Supply Period', key=pd.to_datetime)

                st.session_state['filtered_df'] = df_period
                st.write("Filtered Data", df_period[['Customer Class', 'Customer Subclass', 'Supply Period', 'Supply Period Start', 'Supply Period End', 'Generation Charge kWh', 'Transmission Charge kWh', 'Distribution Charge kWh', 'Transmission Charge kW', 'Distribution Charge kW', 'Total per kW']])
                
                st.line_chart(
                    df_period,
                    x="Supply Period",
                    y=["Distribution Charge kW", "Total per kW", "Generation Charge kWh", "Transmission Charge kWh", "Distribution Charge kWh"]
                )
                
                # Provide download option
                if st.download_button(
                    label="Download Filtered Data",
                    data=df_period.to_csv(index=False).encode('utf-8'),
                    file_name='filtered_data.csv',
                    mime='text/csv'
                ):
                    # Reset selections after download
                    st.session_state['filtered_df'] = pd.DataFrame()
                    st.session_state['user_input_value'] = None
                    st.experimental_rerun()
            else:
                st.write("No data available for the selected criteria.")
    else:
        st.error("No valid data available for the specified range.")
else:
    st.error('Please select two dates.')
