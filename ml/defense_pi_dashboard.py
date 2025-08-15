import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, callback
import webbrowser
import threading
import time


def load_defense_pi_data():
    """Load the defense performance indices data."""
    df = pd.read_parquet("data/defense_adjusted_pi.parquet")
    return df


def load_weekly_defense_data():
    """Load the weekly defense data."""
    df = pd.read_parquet("data/defense_weekly_stats.parquet")
    return df


def get_available_teams(df):
    """Get list of available teams."""
    teams = df['defense_team'].dropna().unique()
    return sorted([team for team in teams if team is not None and team != ''])


def get_available_years(df):
    """Get list of available years."""
    return sorted(df['year'].unique())


def get_available_stats(df):
    """Get list of available stats grouped by category."""
    exclude_cols = ['year', 'defense_team']
    stat_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Group stats by type and position
    stat_categories = {
        'Last Game Performance': [s for s in stat_cols if s.startswith('pi_last1_')],
        'Last 4 Games Average': [s for s in stat_cols if s.startswith('pi_last4_')],
        'Season Average': [s for s in stat_cols if s.startswith('pi_season_')]
    }
    
    return stat_categories


def create_defense_heatmap(selected_teams, selected_years, selected_stats, df):
    """Create a heatmap showing defense performance across teams and stats."""
    
    # Filter data based on selections
    filtered_df = df[
        (df['defense_team'].isin(selected_teams)) & 
        (df['year'].isin(selected_years))
    ].copy()
    
    if filtered_df.empty:
        return go.Figure()
    
    # For heatmap, we'll use the most recent year if multiple years selected
    if len(selected_years) > 1:
        latest_year = filtered_df['year'].max()
        filtered_df = filtered_df[filtered_df['year'] == latest_year]
    
    # Create heatmap data
    teams = filtered_df['defense_team'].values
    stats = selected_stats
    
    z_data = []
    for stat in stats:
        row = []
        for team in teams:
            team_data = filtered_df[filtered_df['defense_team'] == team]
            if not team_data.empty:
                value = team_data[stat].iloc[0]
                row.append(value)
            else:
                row.append(0)
        z_data.append(row)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=teams,
        y=[s.replace('pi_season_', '').replace('pi_last4_', '').replace('pi_last1_', '') for s in stats],
        colorscale='RdBu_r',  # Red-Blue diverging scale
        zmid=0,  # Center the color scale at 0
        text=[[f"{val:.3f}" for val in row] for row in z_data],
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>Team: %{x}<br>PI: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Defense Performance Index Heatmap<br><sub>Teams: {', '.join(selected_teams)} | Year: {filtered_df['year'].iloc[0] if not filtered_df.empty else 'N/A'}</sub>",
        xaxis_title="Defense Team",
        yaxis_title="Stat Category",
        height=400 + (len(stats) * 20),
        annotations=[
            dict(
                text="<b>Color Scale:</b><br>🔴 Red = Defense performs worse than expected<br>🔵 Blue = Defense performs better than expected<br>⚪ White = Defense performs as expected",
                xref="paper", yref="paper",
                x=1.02, y=0.5,
                showarrow=False,
                font=dict(size=10),
                bgcolor="lightgray",
                bordercolor="black",
                borderwidth=1
            )
        ]
    )
    
    return fig


def create_team_comparison(selected_teams, selected_years, selected_stats, df):
    """Create a comparison chart showing multiple teams across selected stats."""
    
    # Filter data based on selections
    filtered_df = df[
        (df['defense_team'].isin(selected_teams)) & 
        (df['year'].isin(selected_years))
    ].copy()
    
    if filtered_df.empty:
        return go.Figure()
    
    # Create subplots - one for each stat
    fig = make_subplots(
        rows=len(selected_stats), cols=1,
        subplot_titles=[stat.replace('pi_season_', '').replace('pi_last4_', '').replace('pi_last1_', '') for stat in selected_stats],
        vertical_spacing=0.1,
        specs=[[{"secondary_y": False}] for _ in selected_stats]
    )
    
    colors = px.colors.qualitative.Set3
    
    for i, stat in enumerate(selected_stats, 1):
        for j, team in enumerate(selected_teams):
            team_data = filtered_df[filtered_df['defense_team'] == team]
            if not team_data.empty:
                # Get the most recent year for this team if multiple years selected
                if len(selected_years) > 1:
                    latest_year = team_data['year'].max()
                    team_data = team_data[team_data['year'] == latest_year]
                
                if not team_data.empty:
                    value = team_data[stat].iloc[0]
                    
                    fig.add_trace(
                        go.Bar(
                            x=[team],
                            y=[value],
                            name=f"{team}",
                            marker_color=colors[j % len(colors)],
                            showlegend=(i == 1),  # Only show legend for first subplot
                            hovertemplate=f'<b>{team}</b><br>{stat}: %{{y:.3f}}<extra></extra>'
                        ),
                        row=i, col=1
                    )
        
        # Add horizontal line at y=0 for reference
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=i, col=1)
    
    fig.update_layout(
        title=f"Defense Performance Comparison<br><sub>Teams: {', '.join(selected_teams)} | Years: {', '.join(map(str, selected_years))}</sub>",
        height=200 * len(selected_stats),
        showlegend=True,
        barmode='group'
    )
    
    # Update all subplot axes
    for i in range(1, len(selected_stats) + 1):
        fig.update_xaxes(title_text="Team", row=i, col=1)
        fig.update_yaxes(title_text="Performance Index", row=i, col=1)
    
    return fig


def create_trend_analysis(selected_teams, selected_stats, df):
    """Create a trend analysis showing how defense performance changes over years."""
    
    # Filter data based on selections
    filtered_df = df[df['defense_team'].isin(selected_teams)].copy()
    
    if filtered_df.empty:
        return go.Figure()
    
    # Create subplots - one for each stat
    fig = make_subplots(
        rows=len(selected_stats), cols=1,
        subplot_titles=[stat.replace('pi_season_', '').replace('pi_last4_', '').replace('pi_last1_', '') for stat in selected_stats],
        vertical_spacing=0.1
    )
    
    colors = px.colors.qualitative.Set3
    
    for i, stat in enumerate(selected_stats, 1):
        for j, team in enumerate(selected_teams):
            team_data = filtered_df[filtered_df['defense_team'] == team].sort_values('year')
            if not team_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=team_data['year'],
                        y=team_data[stat],
                        mode='lines+markers',
                        name=f"{team}",
                        line=dict(color=colors[j % len(colors)], width=3),
                        marker=dict(size=8),
                        showlegend=(i == 1),  # Only show legend for first subplot
                        hovertemplate=f'<b>{team}</b><br>Year: %{{x}}<br>{stat}: %{{y:.3f}}<extra></extra>'
                    ),
                    row=i, col=1
                )
        
        # Add horizontal line at y=0
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=i, col=1)
    
    fig.update_layout(
        title=f"Defense Performance Trends Over Years<br><sub>Teams: {', '.join(selected_teams)}</sub>",
        height=200 * len(selected_stats),
        showlegend=True
    )
    
    # Update all subplot axes
    for i in range(1, len(selected_stats) + 1):
        fig.update_xaxes(title_text="Year", row=i, col=1)
        fig.update_yaxes(title_text="Performance Index", row=i, col=1)
    
    return fig


def create_weekly_progression(selected_teams, selected_years, selected_stats, weekly_df):
    """Create a weekly progression chart showing how defenses perform week-by-week."""
    
    # Filter weekly data based on selections
    filtered_df = weekly_df[
        (weekly_df['defense_team'].isin(selected_teams)) & 
        (weekly_df['year'].isin(selected_years))
    ].copy()
    
    if filtered_df.empty:
        return go.Figure()
    
    # For weekly data, we'll focus on one stat at a time for clarity
    if len(selected_stats) > 1:
        selected_stats = [selected_stats[0]]  # Just use the first stat
    
    stat = selected_stats[0]
    
    # Create the figure
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, team in enumerate(selected_teams):
        for year in selected_years:
            team_data = filtered_df[(filtered_df['defense_team'] == team) & (filtered_df['year'] == year)].sort_values('week')
            if not team_data.empty:
                fig.add_trace(go.Scatter(
                    x=team_data['week'],
                    y=team_data[stat],
                    mode='lines+markers',
                    name=f"{team} {year}",
                    line=dict(color=colors[i % len(colors)], width=3),
                    marker=dict(size=8),
                    hovertemplate=f'<b>{team} {year}</b><br>Week %{{x}}<br>{stat}: %{{y:.2f}}<extra></extra>'
                ))
    
    fig.update_layout(
        title=f"Weekly Defense Performance: {stat.replace('pi_season_', '').replace('pi_last4_', '').replace('pi_last1_', '')}<br><sub>Teams: {', '.join(selected_teams)} | Years: {', '.join(map(str, selected_years))}</sub>",
        xaxis_title="Week",
        yaxis_title="Stat Value",
        height=500,
        hovermode='x unified'
    )
    
    # Add horizontal line at y=0 if the data crosses zero
    if filtered_df[stat].min() <= 0 <= filtered_df[stat].max():
        fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Baseline")
    
    return fig


def create_dashboard():
    """Create the Dash dashboard."""
    
    # Load data
    df = load_defense_pi_data()
    weekly_df = load_weekly_defense_data()
    
    # Get available options
    teams = get_available_teams(df)
    years = get_available_years(df)
    stat_categories = get_available_stats(df)
    
    # Flatten stats for dropdown
    all_stats = []
    for category_name, stats in stat_categories.items():
        all_stats.extend(stats)
    
    # Create Dash app
    app = dash.Dash(__name__)
    
    app.layout = html.Div([
        html.H1("🏈 Defense Performance Index Dashboard", style={'textAlign': 'center'}),
        
        html.Div([
            html.H3("📈 Performance Index Interpretation:", style={'color': '#2c3e50'}),
            html.Ul([
                html.Li("🔵 Positive values: Defense performs better than expected"),
                html.Li("🔴 Negative values: Defense performs worse than expected"),
                html.Li("⚪ Values near 0: Defense performs as expected")
            ])
        ], style={'backgroundColor': '#ecf0f1', 'padding': '15px', 'borderRadius': '5px', 'margin': '10px 0'}),
        
        html.Div([
            html.H3("🎛️ Controls", style={'color': '#2c3e50'}),
            
            html.Div([
                html.Label("Teams:"),
                dcc.Dropdown(
                    id='team-dropdown',
                    options=[{'label': team, 'value': team} for team in teams],
                    value=teams[:5],  # Default to first 5 teams
                    multi=True,
                    style={'width': '100%'}
                )
            ], style={'margin': '10px 0'}),
            
            html.Div([
                html.Label("Years:"),
                dcc.Dropdown(
                    id='year-dropdown',
                    options=[{'label': str(year), 'value': year} for year in years],
                    value=[years[-1]],  # Default to most recent year
                    multi=True,
                    style={'width': '100%'}
                )
            ], style={'margin': '10px 0'}),
            
            html.Div([
                html.Label("Stats:"),
                dcc.Dropdown(
                    id='stat-dropdown',
                    options=[{'label': stat.replace('pi_season_', 'Season: ').replace('pi_last4_', 'Last 4: ').replace('pi_last1_', 'Last Game: '), 'value': stat} for stat in all_stats],
                    value=all_stats[:3],  # Default to first 3 stats
                    multi=True,
                    style={'width': '100%'}
                )
            ], style={'margin': '10px 0'}),
            
            html.Div([
                html.Label("Chart Type:"),
                dcc.Dropdown(
                    id='chart-type-dropdown',
                    options=[
                        {'label': 'Team Comparison (Bar Chart)', 'value': 'comparison'},
                        {'label': 'Heatmap', 'value': 'heatmap'},
                        {'label': 'Trends Over Years', 'value': 'trends'},
                        {'label': 'Weekly Progression', 'value': 'weekly'}
                    ],
                    value='heatmap',
                    style={'width': '100%'}
                )
            ], style={'margin': '10px 0'})
            
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'margin': '20px 0'}),
        
        html.Div([
            dcc.Graph(id='main-chart')
        ], style={'margin': '20px 0'})
        
    ], style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'})
    
    @app.callback(
        Output('main-chart', 'figure'),
        [Input('team-dropdown', 'value'),
         Input('year-dropdown', 'value'),
         Input('stat-dropdown', 'value'),
         Input('chart-type-dropdown', 'value')]
    )
    def update_chart(selected_teams, selected_years, selected_stats, chart_type):
        if not selected_teams or not selected_years or not selected_stats:
            return go.Figure()
        
        if chart_type == 'heatmap':
            return create_defense_heatmap(selected_teams, selected_years, selected_stats, df)
        elif chart_type == 'comparison':
            return create_team_comparison(selected_teams, selected_years, selected_stats, df)
        elif chart_type == 'trends':
            return create_trend_analysis(selected_teams, selected_stats, df)
        elif chart_type == 'weekly':
            return create_weekly_progression(selected_teams, selected_years, selected_stats, weekly_df)
        else:
            return go.Figure()
    
    return app


def main():
    """Main function to run the dashboard."""
    
    print("🏈 Defense Performance Index Dashboard")
    print("=" * 40)
    
    # Load data to show available options
    df = load_defense_pi_data()
    teams = get_available_teams(df)
    years = get_available_years(df)
    stat_categories = get_available_stats(df)
    
    print(f"\n📊 Available Data:")
    print(f"   Teams: {len(teams)} teams")
    print(f"   Years: {years}")
    print(f"   Stats: {sum(len(stats) for stats in stat_categories.values())} different metrics")
    
    print(f"\n🚀 Starting dashboard...")
    print(f"   The dashboard will open in your browser automatically.")
    print(f"   If it doesn't open, go to: http://127.0.0.1:8050")
    
    # Create and run the dashboard
    app = create_dashboard()
    
    # Open browser automatically
    def open_browser():
        time.sleep(1.5)  # Wait for server to start
        webbrowser.open('http://127.0.0.1:8050')
    
    threading.Thread(target=open_browser).start()
    
    # Run the app
    app.run_server(debug=False, host='127.0.0.1', port=8050)


if __name__ == "__main__":
    main()


