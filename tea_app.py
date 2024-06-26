import streamlit as st
import pandas as pd
import numpy as np
from graphviz import Digraph

#notes 2

# Define constants
HOURS_PER_YEAR = 8000  # Assuming 8000 operating hours per year

# Create data tables
capex_data = {
    'Equipment': ['Pretreatment Reactor', 'Hydrolysis Tanks', 'Fermentation Tanks', 'Distillation Column', 'Storage Tanks'],
    'Cost (USD)': [1000000, 500000, 750000, 1200000, 300000]
}
capex_df = pd.DataFrame(capex_data)

opex_data = {
    'Item': ['Corn Stover', 'Enzymes', 'Yeast', 'Utilities', 'Labor', 'Maintenance'],
    'Cost (USD/year)': [100000, 50000, 10000, 200000, 300000, 150000]
}
opex_df = pd.DataFrame(opex_data)

# Function to calculate mass flow rates
def calculate_flow_rates(annual_feedstock, process_params):
    hourly_feedstock = annual_feedstock * 1000 / HOURS_PER_YEAR  # Convert to kg/hr
    
    pretreated = hourly_feedstock * process_params['pretreatment_efficiency']
    hydrolyzed = pretreated * process_params['hydrolysis_efficiency']
    fermented = hydrolyzed * 0.5 * process_params['fermentation_efficiency']
    ethanol = fermented * process_params['distillation_efficiency']
    
    ethanol_volume = ethanol / process_params['ethanol_density']
    ethanol_gal_per_hour = ethanol_volume * 0.264172
    
    return {
        'Feedstock': hourly_feedstock,
        'Pretreated': pretreated,
        'Hydrolyzed': hydrolyzed,
        'Fermented': fermented,
        'Ethanol (kg/hr)': ethanol,
        'Ethanol (gal/hr)': ethanol_gal_per_hour
    }

# Visualization function using Graphviz
def visualize_process_flow(flow_rates):
    dot = Digraph()
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box', style='filled', fillcolor='lightblue')
    
    dot.node('Feedstock', f"Feedstock\n{flow_rates['Feedstock']:.2f} kg/hr")
    dot.node('Pretreatment', f"Pretreatment\n{flow_rates['Pretreated']:.2f} kg/hr")
    dot.node('Hydrolysis', f"Hydrolysis\n{flow_rates['Hydrolyzed']:.2f} kg/hr")
    dot.node('Fermentation', f"Fermentation\n{flow_rates['Fermented']:.2f} kg/hr")
    dot.node('Distillation', f"Distillation\n{flow_rates['Ethanol (kg/hr)']:.2f} kg/hr")
    dot.node('Ethanol', f"Ethanol\n{flow_rates['Ethanol (gal/hr)']:.2f} gal/hr")
    
    dot.edge('Feedstock', 'Pretreatment')
    dot.edge('Pretreatment', 'Hydrolysis')
    dot.edge('Hydrolysis', 'Fermentation')
    dot.edge('Fermentation', 'Distillation')
    dot.edge('Distillation', 'Ethanol')
    
    return dot

# Streamlit app
st.title('Interactive Ethanol Production TEA Model')

st.sidebar.header('Process Parameters')
annual_feedstock = st.sidebar.number_input('Annual Feedstock (tons)', min_value=100, max_value=10000, value=1000)
ethanol_price = st.sidebar.number_input('Ethanol Price ($/gal)', min_value=0.5, max_value=5.0, value=2.0)

process_params = {
    'pretreatment_efficiency': st.sidebar.slider('Pretreatment Efficiency', 0.5, 1.0, 0.8),
    'hydrolysis_efficiency': st.sidebar.slider('Hydrolysis Efficiency', 0.5, 1.0, 0.75),
    'fermentation_efficiency': st.sidebar.slider('Fermentation Efficiency', 0.5, 1.0, 0.9),
    'distillation_efficiency': st.sidebar.slider('Distillation Efficiency', 0.5, 1.0, 0.95),
    'ethanol_density': 0.789  # kg/L (fixed)
}

# Calculate results
flow_rates = calculate_flow_rates(annual_feedstock, process_params)
annual_ethanol_production = flow_rates['Ethanol (gal/hr)'] * HOURS_PER_YEAR
annual_revenue = annual_ethanol_production * ethanol_price
total_capex = capex_df['Cost (USD)'].sum()
annual_opex = opex_df['Cost (USD/year)'].sum()

# Display results
st.header('Process Flow Rates')
st.graphviz_chart(visualize_process_flow(flow_rates))

st.header('Financial Metrics')
col1, col2, col3 = st.columns(3)
col1.metric("Annual Ethanol Production", f"{annual_ethanol_production:.2f} gal")
col2.metric("Annual Revenue", f"${annual_revenue:.2f}")
col3.metric("Simple Annual Profit", f"${annual_revenue - annual_opex:.2f}")

st.header('Capital Expenditures')
st.dataframe(capex_df)
st.metric("Total CAPEX", f"${total_capex:.2f}")

st.header('Operational Expenditures')
st.dataframe(opex_df)
st.metric("Annual OPEX", f"${annual_opex:.2f}")

# Simple sensitivity analysis
st.header('Sensitivity Analysis')
sensitivity_option = st.selectbox('Select parameter for sensitivity analysis', 
                                  ['Annual Feedstock', 'Ethanol Price', 'Pretreatment Efficiency', 'Hydrolysis Efficiency', 'Fermentation Efficiency', 'Distillation Efficiency'])

def run_sensitivity_analysis(base_value, param_name, range_percent=20):
    results = []
    for i in range(-range_percent, range_percent + 1, 5):
        multiplier = 1 + (i / 100)
        new_value = base_value * multiplier
        if param_name == 'Annual Feedstock':
            new_flow_rates = calculate_flow_rates(new_value, process_params)
        elif param_name == 'Ethanol Price':
            new_flow_rates = flow_rates
        else:
            new_process_params = process_params.copy()
            new_process_params[param_name.lower().replace(' ', '_')] = new_value
            new_flow_rates = calculate_flow_rates(annual_feedstock, new_process_params)
        
        new_annual_production = new_flow_rates['Ethanol (gal/hr)'] * HOURS_PER_YEAR
        new_revenue = new_annual_production * (new_value if param_name == 'Ethanol Price' else ethanol_price)
        results.append({
            'Change': f"{i}%",
            param_name: new_value,
            'Annual Production (gal)': new_annual_production,
            'Annual Revenue ($)': new_revenue,
            'Simple Annual Profit ($)': new_revenue - annual_opex
        })
    return pd.DataFrame(results)

base_value = annual_feedstock if sensitivity_option == 'Annual Feedstock' else (
    ethanol_price if sensitivity_option == 'Ethanol Price' else process_params[sensitivity_option.lower().replace(' ', '_')]
)
sensitivity_df = run_sensitivity_analysis(base_value, sensitivity_option)
st.line_chart(sensitivity_df.set_index('Change')[['Annual Production (gal)', 'Annual Revenue ($)', 'Simple Annual Profit ($)']])
st.dataframe(sensitivity_df)