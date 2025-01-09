import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html, dash_table, callback, Output, Input


# Load and inspect the data using read_csv and head
lahd_url = "https://data.lacity.org/api/views/mymu-zi3s/"
lahd_url += "rows.csv?accessType=DOWNLOAD&bom=true&format=true"
lahd = pd.read_csv(lahd_url)

# Store the date stamp
date_stamp = lahd['DATE STAMP'][0][:10]

# Remove rows with CONSTRUCTION TYPE value AQUISITION ONLY, and with 
# HOUSING TYPE value AT-RISK
lahd = lahd.loc[lahd['CONSTRUCTION TYPE'] != 'ACQUISITION ONLY', :]
lahd = lahd.loc[lahd['HOUSING TYPE'] != 'AT-RISK', :]

# Rename some columns
lahd.rename(columns={'TDC': 'TOTAL DEVELOPMENT COST', 
                     'SITE #': 'SITE NUMBER'}, 
            inplace=True)

# Convert data values of the columns LAHD FUNDED, LEVERAGE, 
# TAX EXEMPT CONDUIT BOND, TOTAL DEVELOPMENT COST, and JOBS 
# to float or integer type.
numeric_columns = ['LAHD FUNDED', 'LEVERAGE', 
                   'TAX EXEMPT CONDUIT BOND', 'TOTAL DEVELOPMENT COST']
lahd[numeric_columns] = lahd[numeric_columns].replace(',', '', regex=True)
lahd[numeric_columns] = lahd[numeric_columns].apply(pd.to_numeric, 
                                                    downcast='float', 
                                                    errors='coerce')
lahd[['JOBS']] = lahd[['JOBS']].apply(pd.to_numeric, downcast='integer', 
                                      errors='coerce')

# Convert the values of the following columns to category type. 
categorical_columns = ['APN', 'PROJECT NUMBER', 'DEVELOPMENT STAGE', 
                       'CONSTRUCTION TYPE', 'SITE NUMBER', 'HOUSING TYPE', 
                       'SUPPORTIVE HOUSING', 'IN-SERVICE DATE']
lahd[categorical_columns] = lahd[categorical_columns].astype('category')

# Convert the values of the column DATE FUNDED to Datetime type.
lahd['DATE FUNDED'] = pd.to_datetime(lahd['DATE FUNDED'], 
                                     format="%m/%d/%Y", errors='coerce')

# Group Affordable Housing Projects dataset by PROJECT NUMBER. 
# Use count to count the number of sites per project.
project_count = lahd.groupby('PROJECT NUMBER')['PROJECT NUMBER'].count()

# Drop rows with duplicated values in PROJECT NUMBER, and sort the resulting 
# dataset by PROJECT NUMBER. Assign the dataset to DataFrame lahd_projects.
lahd_projects = lahd.drop_duplicates(
    ['PROJECT NUMBER']).sort_values('PROJECT NUMBER')

# Add columns NUMBER OF SITES, YEAR FUNDED, and COST PER HOUSING UNIT
lahd_projects['NUMBER OF SITES'] = np.array(project_count)
lahd_projects['DATE FUNDED'] = lahd_projects['DATE FUNDED'].astype(str)
lahd_projects['YEAR FUNDED'] = lahd_projects['DATE FUNDED'].apply(
    lambda d: d[:4])
lahd_projects['DATE FUNDED'] = lahd_projects['DATE FUNDED'].apply(
    lambda d: d[:10])
lahd_projects['YEAR FUNDED'] = pd.to_datetime(lahd_projects['YEAR FUNDED'], 
                                              format="%Y", errors='coerce')
tdc = lahd_projects['TOTAL DEVELOPMENT COST']
ptu = lahd_projects['PROJECT TOTAL UNITS']
lahd_projects['COST PER HOUSING UNIT'] = tdc / ptu

# Drop the following columns from lahd_projects.
lahd_projects.drop(['APN', 'NAME', 'SITE ADDRESS', 'SITE NUMBER', 
                    'SITE COMMUNITY', 'SITE UNITS','SH UNITS PER SITE', 
                    'IN-SERVICE DATE', 'PHOTO', 'PROJECT SUMMARY URL', 
                    'CONTRACT NUMBERS', 'DATE STAMP', 'SITE LONGITUDE', 
                    'SITE LATITUDE', 'GPS_COORDS ON MAP', 'DEVELOPER', 
                    'MANAGEMENT COMPANY', 'CONTACT PHONE'], 
          axis='columns', inplace=True)

# Drop the column SITE COUNCIL DISTRICT from lahd_projects
lahd_projects.drop(lahd_projects.columns[3], 
                   axis='columns', inplace=True)

# Create a new DataFrame with the JOBS column dropped.
lahd_projects_no_jobs_column = lahd_projects.drop(['JOBS'], 
                                                  axis='columns')

# Drop all rows with missing values in both lahd_projects and 
# lahd_projects_no_jobs_column
lahd_projects.dropna(inplace=True)
lahd_projects_no_jobs_column.dropna(inplace=True)

app = Dash(__name__)
server = app.server

section1 = [
    # Title and date stamp
    html.H1(children='LAHD Affordable Housing Projects (2003 to Present)', 
            style={'color': 'darkblue'}),
    html.P(f"Data Date Stamp: {date_stamp}", style={'color': 'darkred', 
                                                    'font-size': 20}),
    html.Hr(),
    
    # Display a table of the data
    html.H2("LAHD Affordable Housing Project Dataset", 
            style={'color': 'darkblue'}),
    dash_table.DataTable(data=lahd_projects.to_dict('records'), page_size=8),
    html.Hr(),
    
    # Display a bar plot of TOTAL DEVELOPMENT COST. Create a radio 
    # button to allow users to select a housing category variable.
    html.H2("Total Development Costs by Year", style={'color': 'darkblue'}),
    html.Label('Housing Categories', style={'color': 'darkred', 
                                            'font-size': 20}),
    dcc.RadioItems(options=['HOUSING TYPE', 'CONSTRUCTION TYPE', 
                            'SUPPORTIVE HOUSING'], 
                   value='HOUSING TYPE', id='plot1_input'),
    dcc.Graph(figure={}, id='plot1_output'),
    html.Hr(),
]

section2 = [
    # Display a scatter plot, heat map, and bar plot for a funding source, 
    # project metric, and housing category. Create dropdowns for use 
    # selection.
    html.H2("Funding Source versus Project Metric", 
            style={'color': 'darkblue'}),
    html.Label('Funding Source for Housing', style={'color': 'darkred', 
                                                    'font-size': 20}),
    dcc.Dropdown(options=['LAHD FUNDED', 'LEVERAGE', 
                          'TAX EXEMPT CONDUIT BOND', 
                          'TOTAL DEVELOPMENT COST'], 
                 value='LAHD FUNDED', id='plot2_input'),
    html.Label('Housing Project Metric', style={'color': 'darkred', 
                                                'font-size': 20}),
    dcc.Dropdown(options=['PROJECT TOTAL UNITS', 'JOBS', 
                          'COST PER HOUSING UNIT'], 
                 value='JOBS', id='plot2_input2'),
    html.Label('Housing Categories', style={'color': 'darkred', 
                                            'font-size': 20}),
    dcc.Dropdown(options=['HOUSING TYPE', 'CONSTRUCTION TYPE', 
                          'SUPPORTIVE HOUSING'], 
                 value='HOUSING TYPE', id='plot2_input3'),
    dcc.Graph(figure={}, id='plot2_output'),
    dcc.Graph(figure={}, id='plot2_output2'),
    dcc.Graph(figure={}, id='plot2_output3'),
    html.Hr()
]

section3 = [
    # Display box plots for a funding source or project metric by a 
    # housing category. Create dropdowns for user selection.
    html.H2("Funding and Project Metrics by Housing Category", 
            style={'color': 'darkblue'}),
    html.Label('Housing Project Metrics', style={'color': 'darkred', 
                                                 'font-size': 20}),
    dcc.Dropdown(options=['PROJECT TOTAL UNITS', 'JOBS', 
                          'COST PER HOUSING UNIT', 'LAHD FUNDED', 
                          'LEVERAGE', 'TAX EXEMPT CONDUIT BOND', 
                          'TOTAL DEVELOPMENT COST'], 
                 value='JOBS', id='plot3_input'),
    html.Label('Housing Category 1', style={'color': 'darkred', 
                                            'font-size': 20}),
    dcc.Dropdown(options=['HOUSING TYPE', 'CONSTRUCTION TYPE', 
                          'SUPPORTIVE HOUSING'], 
                 value='HOUSING TYPE', id='plot3_input2'),
    html.Label('Housing Category 2', style={'color': 'darkred', 
                                            'font-size': 20}),
    dcc.Dropdown(options=['ALL', 'HOUSING TYPE', 'CONSTRUCTION TYPE', 
                          'SUPPORTIVE HOUSING'], 
                 value='SUPPORTIVE HOUSING', id='plot3_input3'),
    dcc.Graph(figure={}, id='plot3_output')
]

section4 = [
    # Display map for a funding source or project metric by a 
    # housing category. Create dropdowns for user selection.
    html.H2("Affordable Housing Map by Housing Category", 
            style={'color': 'darkblue'}),
    html.Label('Housing Category', style={'color': 'darkred', 
                                            'font-size': 20}),
    dcc.Dropdown(options=['HOUSING TYPE', 'CONSTRUCTION TYPE', 
                          'SUPPORTIVE HOUSING'], 
                 value='HOUSING TYPE', id='plot4_input1'),
    html.Label('Housing Project Metrics', style={'color': 'darkred', 
                                                 'font-size': 20}),
    dcc.Dropdown(options=['PROJECT TOTAL UNITS', 'NONE', 
                          'LAHD FUNDED', 
                          'LEVERAGE', 'TAX EXEMPT CONDUIT BOND', 
                          'TOTAL DEVELOPMENT COST'], 
                 value='NONE', id='plot4_input2'),
    html.Label('Map Layout', style={'color': 'darkred', 
                                            'font-size': 20}),
    dcc.RadioItems(options=["open-street-map", "carto-voyager", 
                            "carto-darkmatter", "satellite-streets"], 
                   value="open-street-map", id='plot4_input3'),
    dcc.Graph(figure={}, id='plot4_output')
]

# Create the layout of the dashboard
app.layout = html.Div(section1 + section2 + section3 + section4, 
                      style={'font-family': 'system-ui'})

# Define the callback function for the bar plot of TOTAL DEVELOPMENT COST
@callback(
    Output(component_id='plot1_output', component_property='figure'),
    Input(component_id='plot1_input', component_property='value')
)
def update_graph(column_selected):
    fig = px.bar(lahd_projects, x="YEAR FUNDED", y="TOTAL DEVELOPMENT COST", 
                 color=column_selected, barmode='stack', 
                 hover_data={"TOTAL DEVELOPMENT COST": True, 
                             column_selected: True, 
                             "DATE FUNDED": True, "YEAR FUNDED": False, 
                             "PROJECT NUMBER": True},
                 title=f"TOTAL COST and {column_selected} by YEAR FUNDED")
    return fig

# Define the callback function for the scatter plot of the funding source, 
# project metric, and housing category.
@callback(
    Output(component_id='plot2_output', component_property='figure'),
    Input(component_id='plot2_input', component_property='value'), 
    Input(component_id='plot2_input2', component_property='value'),
    Input(component_id='plot2_input3', component_property='value')
)
def update_graph(column1_selected, column2_selected, column3_selected):
    t = f"{column1_selected} versus {column2_selected} by {column3_selected}"
    fig = px.scatter(lahd_projects, x=column2_selected, y=column1_selected, 
                     size="PROJECT TOTAL UNITS", color=column3_selected, 
                     hover_name="PROJECT NUMBER", 
                     title=t)
    return fig

# Define callback for heat map of funding source and project metric.
@callback(
    Output(component_id='plot2_output2', component_property='figure'),
    Input(component_id='plot2_input', component_property='value'), 
    Input(component_id='plot2_input2', component_property='value')
)
def update_graph(column1_selected, column2_selected):
    t = f"{column1_selected} versus {column2_selected}"
    fig = px.density_heatmap(lahd_projects, x=column2_selected, 
                             y=column1_selected,
                             title=t, 
                             text_auto=True, 
                             hover_data={column2_selected: True, 
                                         column1_selected: True, 
                                         "PROJECT NUMBER": True})
    return fig

# Define the callback function for the bar plot of the funding source 
# by YEAR FUNDED and the project metric.
@callback(
    Output(component_id='plot2_output3', component_property='figure'),
    Input(component_id='plot2_input', component_property='value'), 
    Input(component_id='plot2_input2', component_property='value')
)
def update_graph(column1_selected, column2_selected):
    t = f"{column1_selected} and {column2_selected} by YEAR FUNDED"
    fig = px.bar(lahd_projects, x="YEAR FUNDED", y=column1_selected, 
                 color=column2_selected,
                 hover_data={column1_selected: True, column2_selected: True, 
                             "DATE FUNDED": True, "YEAR FUNDED": False, 
                             "PROJECT NUMBER": True},
                 title=t)
    return fig

# Define the callback function for the box plots of the funding source or 
# project metric, grouped by two housing categories.
@callback(
    Output(component_id='plot3_output', component_property='figure'),
    Input(component_id='plot3_input', component_property='value'), 
    Input(component_id='plot3_input2', component_property='value'),
    Input(component_id='plot3_input3', component_property='value')
)
def update_graph(column1_selected, column2_selected, column3_selected):
    if column3_selected == 'ALL':
        fig = px.box(lahd_projects, y=column2_selected, x=column1_selected,
                     hover_name="PROJECT NUMBER", 
                     title=f"{column1_selected} by {column2_selected}")
    else:
        t = f"{column1_selected} by {column2_selected} and {column3_selected}"
        fig = px.box(lahd_projects, y=column2_selected, x=column1_selected,
                     color=column3_selected, hover_name="PROJECT NUMBER", 
                     title=t)
    fig.update_traces(orientation='h')
    return fig

# Define the callback function for the map of affordable housing 
# grouped by a housing category.
@callback(
    Output(component_id='plot4_output', component_property='figure'),
    Input(component_id='plot4_input1', component_property='value'), 
    Input(component_id='plot4_input2', component_property='value'),
    Input(component_id='plot4_input3', component_property='value')
)
def update_graph(column1_selected, column2_selected, map_layout):
    if column2_selected == 'NONE':
        fig = px.scatter_map(lahd, lat='SITE LATITUDE', 
                             lon='SITE LONGITUDE', 
                             center={'lat': 34.088, 'lon': -118.353}, 
                             color=column1_selected,
                             hover_name="PROJECT NUMBER",
                             hover_data={"SITE UNITS": True},
                             title=f"Affordable Housing by {column1_selected}")
    else:
        t = f"Affordable Housing by {column1_selected} and {column2_selected}"
        fig = px.scatter_map(lahd, lat='SITE LATITUDE', 
                             lon='SITE LONGITUDE', 
                             center={'lat': 34.088, 'lon': -118.353}, 
                             color=column1_selected, size=column2_selected,
                             hover_name="PROJECT NUMBER",
                             hover_data={"SITE UNITS": True},
                             title=t)
    fig.update_layout(map_style=map_layout)
    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    return fig

# Run the Dash app
if __name__ == "__main__":
  app.run_server(debug=True, use_reloader=False)
