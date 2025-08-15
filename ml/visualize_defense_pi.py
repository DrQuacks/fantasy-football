import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px


def load_defense_pi_data():
    """Load the defense performance indices data."""
    df = pd.read_parquet("data/defense_adjusted_pi.parquet")
    return df


def get_available_teams(df):
    """Get list of available teams."""
    teams = df['defense_team'].dropna().unique()
    return sorted([team for team in teams if team is not None and team != ''])


def get_available_years(df):
    """Get list of available years."""
    return sorted(df['year'].unique())


def get_available_stats(df):
    """Get list of available stats (excluding year and defense_team columns)."""
    exclude_cols = ['year', 'defense_team']
    stat_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Group stats by type (last1, last4, season)
    last1_stats = [col for col in stat_cols if col.startswith('pi_last1_')]
    last4_stats = [col for col in stat_cols if col.startswith('pi_last4_')]
    season_stats = [col for col in stat_cols if col.startswith('pi_season_')]
    
    return {
        'Last Game (pi_last1_)': last1_stats,
        'Last 4 Games (pi_last4_)': last4_stats,
        'Season Average (pi_season_)': season_stats
    }


def create_defense_pi_visualization():
    """Create an interactive visualization for defense performance indices."""
    
    # Load data
    df = load_defense_pi_data()
    
    # Get available options
    teams = get_available_teams(df)
    years = get_available_years(df)
    stat_groups = get_available_stats(df)
    
    # Flatten all stats for the dropdown
    all_stats = []
    for group_name, stats in stat_groups.items():
        all_stats.extend(stats)
    
    # Create the main figure
    fig = go.Figure()
    
    # Add initial data (default to first team, first year, first stat)
    if len(teams) > 0 and len(years) > 0 and len(all_stats) > 0:
        default_team = teams[0]
        default_year = years[0]
        default_stat = all_stats[0]
        
        # Filter data for default selection
        filtered_df = df[(df['defense_team'] == default_team) & (df['year'] == default_year)]
        
        if not filtered_df.empty:
            # Get the stat values (we'll need to create a week column since defense data is aggregated)
            # For now, let's just show the single value for the season
            stat_value = filtered_df[default_stat].iloc[0]
            
            fig.add_trace(go.Scatter(
                x=[1],  # Single point representing the season
                y=[stat_value],
                mode='markers+text',
                text=[f"{stat_value:.3f}"],
                textposition="top center",
                name=f"{default_team} {default_year}",
                marker=dict(size=15, color='blue'),
                showlegend=True
            ))
    
    # Update layout
    fig.update_layout(
        title="Defense Performance Index Visualization",
        xaxis_title="Week (Season Aggregate)",
        yaxis_title="Performance Index",
        height=600,
        updatemenus=[
            # Team dropdown
            dict(
                buttons=[dict(label=team, method="update", 
                             args=[{"visible": [team == t for t in teams]}, {}]) 
                        for team in teams],
                direction="down",
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.02,
                yanchor="top"
            ),
            # Year dropdown
            dict(
                buttons=[dict(label=str(year), method="update", 
                             args=[{"visible": [year == y for y in years]}, {}]) 
                        for year in years],
                direction="down",
                showactive=True,
                x=0.3,
                xanchor="left",
                y=1.02,
                yanchor="top"
            ),
            # Stat dropdown
            dict(
                buttons=[dict(label=stat, method="update", 
                             args=[{"y": [[df[(df['defense_team'] == teams[0]) & (df['year'] == years[0])][stat].iloc[0]]]}, {}]) 
                        for stat in all_stats],
                direction="down",
                showactive=True,
                x=0.5,
                xanchor="left",
                y=1.02,
                yanchor="top"
            )
        ]
    )
    
    # Add horizontal line at y=0 for reference
    fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Baseline (0)")
    
    # Add interpretation guide
    fig.add_annotation(
        text="<b>Performance Index Interpretation:</b><br>" +
             "• Positive values: Defense performs better than expected<br>" +
             "• Negative values: Defense performs worse than expected<br>" +
             "• Values near 0: Defense performs as expected",
        xref="paper", yref="paper",
        x=0, y=-0.15,
        showarrow=False,
        font=dict(size=10),
        bgcolor="lightgray",
        bordercolor="black",
        borderwidth=1
    )
    
    return fig


def create_comparison_visualization():
    """Create a comparison visualization showing multiple teams/years for a selected stat."""
    
    df = load_defense_pi_data()
    teams = get_available_teams(df)
    years = get_available_years(df)
    stat_groups = get_available_stats(df)
    
    # Get season stats for comparison
    season_stats = stat_groups.get('Season Average (pi_season_)', [])
    
    if not season_stats:
        return go.Figure()
    
    # Create subplots for different stat categories
    stat_categories = {
        'Receiving': [s for s in season_stats if 'receiving' in s],
        'Rushing': [s for s in season_stats if 'rushing' in s],
        'Passing': [s for s in season_stats if 'passing' in s],
        'Kicking': [s for s in season_stats if 'FieldGoals' in s or 'ExtraPoints' in s]
    }
    
    # Create subplot layout
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=list(stat_categories.keys()),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Colors for different teams
    colors = px.colors.qualitative.Set3
    
    # Add traces for each category
    for idx, (category, stats) in enumerate(stat_categories.items()):
        row = (idx // 2) + 1
        col = (idx % 2) + 1
        
        if stats:
            # Use the first stat in each category for demonstration
            stat = stats[0]
            
            # Get data for a few teams
            sample_teams = teams[:5] if len(teams) >= 5 else teams
            
            for i, team in enumerate(sample_teams):
                team_data = df[df['defense_team'] == team]
                if not team_data.empty:
                    # Get the most recent year for this team
                    latest_year = team_data['year'].max()
                    value = team_data[team_data['year'] == latest_year][stat].iloc[0]
                    
                    fig.add_trace(
                        go.Bar(
                            x=[team],
                            y=[value],
                            name=f"{team} ({latest_year})",
                            marker_color=colors[i % len(colors)],
                            showlegend=(row == 1 and col == 1)  # Only show legend for first subplot
                        ),
                        row=row, col=col
                    )
    
    # Update layout
    fig.update_layout(
        title="Defense Performance Index Comparison by Category",
        height=800,
        showlegend=True
    )
    
    # Update all subplot axes
    for i in range(1, 3):
        for j in range(1, 3):
            fig.update_xaxes(title_text="Team", row=i, col=j)
            fig.update_yaxes(title_text="Performance Index", row=i, col=j)
            fig.add_hline(y=0, line_dash="dash", line_color="gray", row=i, col=j)
    
    return fig


def main():
    """Main function to run the visualization."""
    print("Loading defense performance indices data...")
    
    # Create the main visualization
    fig1 = create_defense_pi_visualization()
    fig1.show()
    
    # Create comparison visualization
    fig2 = create_comparison_visualization()
    fig2.show()
    
    print("✅ Defense PI visualizations created!")
    print("\nUsage:")
    print("- Use the dropdowns to select different teams, years, and stats")
    print("- Positive PI values indicate the defense performs better than expected")
    print("- Negative PI values indicate the defense performs worse than expected")
    print("- Values near 0 indicate the defense performs as expected")


if __name__ == "__main__":
    main()
