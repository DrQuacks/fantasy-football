import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
from plotly.offline import plot
import webbrowser
import os


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


def create_multi_team_comparison(selected_teams, selected_years, selected_stats, df):
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


def main():
    """Main function to run the interactive defense PI explorer."""
    
    print("🏈 Interactive Defense Performance Index Explorer")
    print("=" * 50)
    
    # Load data
    print("Loading defense performance data...")
    df = load_defense_pi_data()
    weekly_df = load_weekly_defense_data()
    
    # Get available options
    teams = get_available_teams(df)
    years = get_available_years(df)
    stat_categories = get_available_stats(df)
    
    print(f"\n📊 Available Data:")
    print(f"   Teams: {len(teams)} teams")
    print(f"   Years: {years}")
    print(f"   Stats: {sum(len(stats) for stats in stat_categories.values())} different metrics")
    
    # Create HTML file with interactive controls
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Defense Performance Index Explorer</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .controls {{ background: #f5f5f5; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .control-group {{ margin: 10px 0; }}
            label {{ font-weight: bold; margin-right: 10px; }}
            select, input {{ padding: 5px; margin: 5px; }}
            button {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
            .chart-container {{ margin: 20px 0; }}
            .info {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>🏈 Defense Performance Index Explorer</h1>
        
        <div class="info">
            <h3>📈 Performance Index Interpretation:</h3>
            <ul>
                <li><strong>Positive values (Blue):</strong> Defense performs better than expected</li>
                <li><strong>Negative values (Red):</strong> Defense performs worse than expected</li>
                <li><strong>Values near 0 (White):</strong> Defense performs as expected</li>
            </ul>
        </div>
        
        <div class="controls">
            <h3>🎛️ Visualization Controls</h3>
            
            <div class="control-group">
                <label>Teams:</label>
                <select id="teamSelect" multiple size="5">
                    {''.join(f'<option value="{team}">{team}</option>' for team in teams)}
                </select>
                <button onclick="selectAllTeams()">Select All</button>
                <button onclick="clearTeams()">Clear All</button>
            </div>
            
            <div class="control-group">
                <label>Years:</label>
                <select id="yearSelect" multiple size="3">
                    {''.join(f'<option value="{year}">{year}</option>' for year in years)}
                </select>
                <button onclick="selectAllYears()">Select All</button>
                <button onclick="clearYears()">Clear All</button>
            </div>
            
            <div class="control-group">
                <label>Stats:</label>
                <select id="statSelect" multiple size="8">
                    {''.join(f'<option value="{stat}">{stat.replace("pi_season_", "Season: ").replace("pi_last4_", "Last 4: ").replace("pi_last1_", "Last Game: ")}</option>' for category, stats in stat_categories.items() for stat in stats)}
                </select>
                <button onclick="selectAllStats()">Select All</button>
                <button onclick="clearStats()">Clear All</button>
            </div>
            
            <div class="control-group">
                <label>Chart Type:</label>
                <select id="chartType">
                    <option value="comparison">Team Comparison (Bar Chart)</option>
                    <option value="heatmap">Heatmap</option>
                    <option value="trends">Trends Over Years</option>
                    <option value="weekly">Weekly Progression</option>
                </select>
                <button onclick="updateChart()">Update Chart</button>
            </div>
        </div>
        
        <div id="chartContainer" class="chart-container">
            <p>Select teams, years, and stats above, then click "Update Chart" to see the visualization.</p>
        </div>
        
        <script>
            // Default selections
            document.getElementById('teamSelect').value = ['NE', 'BAL', 'SF', 'TB', 'KC'];
            document.getElementById('yearSelect').value = [{years[-1]}];
            document.getElementById('statSelect').value = ['pi_season_receivingYardsWR', 'pi_season_rushingYardsRB', 'pi_season_passingYardsQB'];
            
            function selectAllTeams() {{
                const select = document.getElementById('teamSelect');
                for (let option of select.options) {{
                    option.selected = true;
                }}
            }}
            
            function clearTeams() {{
                document.getElementById('teamSelect').value = [];
            }}
            
            function selectAllYears() {{
                const select = document.getElementById('yearSelect');
                for (let option of select.options) {{
                    option.selected = true;
                }}
            }}
            
            function clearYears() {{
                document.getElementById('yearSelect').value = [];
            }}
            
            function selectAllStats() {{
                const select = document.getElementById('statSelect');
                for (let option of select.options) {{
                    option.selected = true;
                }}
            }}
            
            function clearStats() {{
                document.getElementById('statSelect').value = [];
            }}
            
            function updateChart() {{
                const teams = Array.from(document.getElementById('teamSelect').selectedOptions).map(opt => opt.value);
                const years = Array.from(document.getElementById('yearSelect').selectedOptions).map(opt => parseInt(opt.value));
                const stats = Array.from(document.getElementById('statSelect').selectedOptions).map(opt => opt.value);
                const chartType = document.getElementById('chartType').value;
                
                if (teams.length === 0 || years.length === 0 || stats.length === 0) {{
                    document.getElementById('chartContainer').innerHTML = '<p style="color: red;">Please select at least one team, year, and stat.</p>';
                    return;
                }}
                
                // For now, show a placeholder - in a real implementation, this would call Python functions
                document.getElementById('chartContainer').innerHTML = `
                    <div style="background: #f0f0f0; padding: 20px; border-radius: 5px;">
                        <h3>Chart Preview</h3>
                        <p><strong>Selected:</strong></p>
                        <ul>
                            <li>Teams: ${{teams.join(', ')}}
                            <li>Years: ${{years.join(', ')}}
                            <li>Stats: ${{stats.length}} selected
                            <li>Chart Type: ${{chartType}}
                        </ul>
                        <p><em>This is a preview. The actual interactive chart would be generated here.</em></p>
                    </div>
                `;
            }}
        </script>
    </body>
    </html>
    """
    
    # Save HTML file
    html_file = "defense_pi_explorer.html"
    with open(html_file, 'w') as f:
        f.write(html_content)
    
    print(f"\n✅ Interactive explorer created!")
    print(f"📁 File saved as: {html_file}")
    print(f"🌐 Opening in browser...")
    
    # Open in browser
    webbrowser.open(f'file://{os.path.abspath(html_file)}')
    
    print(f"\n🎯 Quick Start Guide:")
    print(f"1. Select teams from the dropdown (try: NE, BAL, SF, TB, KC)")
    print(f"2. Choose years (try: {years[-1]} for most recent)")
    print(f"3. Pick stats (try: pi_season_receivingYardsWR, pi_season_rushingYardsRB)")
    print(f"4. Choose chart type:")
    print(f"   • Team Comparison: Bar chart comparing teams")
    print(f"   • Heatmap: Color-coded grid showing performance across teams/stats")
    print(f"   • Trends Over Years: Line chart showing performance changes")
    print(f"   • Weekly Progression: Week-by-week performance")
    print(f"5. Click 'Update Chart' to see the visualization")
    
    print(f"\n🔍 What to look for:")
    print(f"• Teams with consistently positive PI values are strong defensively")
    print(f"• Teams with negative PI values struggle in those areas")
    print(f"• The heatmap gives you a quick overview of defensive strengths/weaknesses")
    print(f"• Trends show how defensive performance changes over time")


if __name__ == "__main__":
    main()



