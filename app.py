import streamlit as st
import pandas as pd
import math
from pathlib import Path
import altair as alt



# ---------------------- App Config ----------------------
st.set_page_config(
    page_title='GDP Dashboard',
    page_icon=':earth_americas:',
    layout='wide'
)

   
# ---------------------- Load Data ----------------------
@st.cache_data
def get_gdp_data():
    """Load and tidy World Bank GDP data."""

    DATA_FILENAME = "world_gdp.csv"

    raw_gdp_df = pd.read_csv(DATA_FILENAME, skiprows=4, na_values=['..'])
    
    MIN_YEAR = 1960
    MAX_YEAR = 2024
    
    # Keep only relevant columns
    year_cols = [str(y) for y in range(MIN_YEAR, MAX_YEAR + 1)]
    raw_gdp_df = raw_gdp_df[['Country Name', 'Country Code'] + year_cols]
    


     # The data above has columns like:
    # - Country Name
    # - Country Code
    # - GDP for 1960
    # - ...
    # - GDP for 2024


    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP


    # Pivot year columns into long format
    gdp_df = raw_gdp_df.melt(
        id_vars=['Country Name', 'Country Code'],
        value_vars=year_cols,
        var_name='Year',
        value_name='GDP'
    )
    
    # Convert Year to numeric
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])
    
    return gdp_df

gdp_df = get_gdp_data()




# ---------------------- Sidebar Filters ----------------------
st.sidebar.header("Filter Data")

# Year range slider
min_year = int(gdp_df['Year'].min())
max_year = int(gdp_df['Year'].max())
from_year, to_year = st.sidebar.slider(
    'Select Year Range:',
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Country selection
countries = gdp_df['Country Code'].unique()
selected_countries = st.sidebar.multiselect(
    'Select Countries:',
    options=countries,
    default=['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN']
)

# ---------------------- Filter Data ----------------------
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries)) &
    (gdp_df['Year'] >= from_year) &
    (gdp_df['Year'] <= to_year)
]

# ---------------------- GDP Line Chart ----------------------
st.markdown("## GDP Over Time")
st.markdown("---")

if filtered_gdp_df.empty:
    st.warning("No data available for the selected countries and years.")
else:
    chart = (
        alt.Chart(filtered_gdp_df)
        .mark_line()
        .encode(
            x='Year:O',
            y='GDP:Q',
            color='Country Code:N',
            tooltip=['Country Name', 'Year', 'GDP']
        )
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)

# ---------------------- GDP Metrics ----------------------
st.markdown(f"## GDP in {to_year}")
st.markdown("---")

first_year_df = gdp_df[gdp_df['Year'] == from_year]
last_year_df = gdp_df[gdp_df['Year'] == to_year]

cols = st.columns(4)
for i, country in enumerate(selected_countries):
    col = cols[i % 4]
    with col:
        # Get GDP values (in billions)
        try:
            first_gdp = first_year_df[first_year_df['Country Code'] == country]['GDP'].iat[0] / 1e9
        except IndexError:
            first_gdp = float('nan')
        try:
            last_gdp = last_year_df[last_year_df['Country Code'] == country]['GDP'].iat[0] / 1e9
        except IndexError:
            last_gdp = float('nan')
        
        # Calculate growth
        if math.isnan(first_gdp) or first_gdp == 0:
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f"{last_gdp / first_gdp:,.2f}x"
            delta_color = 'normal'
        
        # Display metric
        st.metric(
            label=f"{country} GDP",
            value=f"{last_gdp:,.0f}B" if not math.isnan(last_gdp) else 'n/a',
            delta=growth,
            delta_color=delta_color
        )
