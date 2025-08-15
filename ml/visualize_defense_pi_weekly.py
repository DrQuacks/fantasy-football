import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np


def load_weekly_defense_data():
    """Load the weekly defense data to show progression over time."""
    df = pd.read_parquet("data/defense_weekly_stats.parquet")
    return df


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
    """Get list of available stats for weekly visualization."""
    exclude_cols = ['year', 'week', 'defense_team', 'offense_team']
    stat_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Group stats by position
    stat_categories = {
        'Receiving (WR)': [s for s in stat_cols if 'WR' in s and 'receiving' in s],
        'Receiving (RB)': [s for s in stat_cols if 'RB' in s and 'receiving' in s],
        'Receiving (TE)': [s for s in stat_cols if 'TE' in s and 'receiving' in s],
        'Rushing (RB)': [s for s in stat_cols if 'RB' in s and 'rushing' in s],
        'Rushing (QB)': [s for s in stat_cols if 'QB' in s and 'rushing' in s],
        'Rushing (WR)': [s for s in stat_cols if 'WR' in s and 'rushing' in s],
        'Rushing (TE)': [s for s in stat_cols if 'TE' in s and 'rushing' in s],
        'Passing (QB)': [s for s in stat_cols if 'QB' in s and 'passing' in s],
        'Kicking (K)': [s for s in stat_cols if 'K' in s]
    }
    
    return stat_categories


def create_weekly_defense_visualization():
    """Create an interactive visualization showing weekly defense performance."""
    
    # Load weekly data
    df = load_weekly_defense_data()
    
    # Get available options
    teams = get_available_teams(df)
    years = get_available_years(df)
    stat_categories = get_available_stats(df)
    
    # Flatten all stats for the dropdown
    all_stats = []
    for category_name, stats in stat_categories.items():
        all_stats.extend(stats)
    
    # Create the main figure
    fig = go.Figure()
    
    # Add initial data (default to first team, first year, first stat)
    if len(teams) > 0 and len(years) > 0 and len(all_stats) > 0:
        default_team = teams[0]
        default_year = years[0]
        default_stat = all_stats[0]
        
        # Filter data for default selection
        filtered_df = df[(df['defense_team'] == default_team) & (df['year'] == default_year)].sort_values('week')
        
        if not filtered_df.empty:
            fig.add_trace(go.Scatter(
                x=filtered_df['week'],
                y=filtered_df[default_stat],
                mode='lines+markers',
                name=f"{default_team} {default_year}",
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate='<b>Week %{x}</b><br>' +
                            f'{default_stat}: %{{y:.2f}}<br>' +
                            '<extra></extra>'
            ))
    
    # Update layout
    fig.update_layout(
        title="Weekly Defense Performance Visualization",
        xaxis_title="Week",
        yaxis_title="Stat Value",
        height=600,
        hovermode='x unified'
    )
    
    # Add dropdown menus
    fig.update_layout(
        updatemenus=[
            # Team dropdown
            dict(
                buttons=[dict(label=team, method="restyle", 
                             args=[{"y": [df[(df['defense_team'] == team) & (df['year'] == years[0])].sort_values('week')[all_stats[0]]]}]) 
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
                buttons=[dict(label=str(year), method="restyle", 
                             args=[{"y": [df[(df['defense_team'] == teams[0]) & (df['year'] == year)].sort_values('week')[all_stats[0]]]}]) 
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
                buttons=[dict(label=stat, method="restyle", 
                             args=[{"y": [df[(df['defense_team'] == teams[0]) & (df['year'] == years[0])].sort_values('week')[stat]]}]) 
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
    
    return fig


def create_defense_comparison_heatmap():
    """Create a heatmap showing defense performance across different stats and teams."""
    
    df = load_defense_pi_data()
    
    # Get season stats for the heatmap
    exclude_cols = ['year', 'defense_team']
    season_stats = [col for col in df.columns if col.startswith('pi_season_') and col not in exclude_cols]
    
    # Select a few key stats for visualization
    key_stats = [
        'pi_season_receivingYardsWR',
        'pi_season_rushingYardsRB', 
        'pi_season_passingYardsQB',
        'pi_season_madeFieldGoalsK'
    ]
    
    # Filter to most recent year
    latest_year = df['year'].max()
    df_latest = df[df['year'] == latest_year]
    
    # Create heatmap data
    teams = df_latest['defense_team'].values
    stats = key_stats
    
    # Create the heatmap
    z_data = []
    for stat in stats:
        row = []
        for team in teams:
            team_data = df_latest[df_latest['defense_team'] == team]
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
        y=[s.replace('pi_season_', '') for s in stats],
        colorscale='RdBu_r',  # Red-Blue diverging scale
        zmid=0,  # Center the color scale at 0
        text=[[f"{val:.3f}" for val in row] for row in z_data],
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False
    ))
    
    fig.update_layout(
        title=f"Defense Performance Index Heatmap ({latest_year})",
        xaxis_title="Defense Team",
        yaxis_title="Stat Category",
        height=500,
        annotations=[
            dict(
                text="<b>Color Scale:</b><br>Red = Defense performs worse than expected<br>Blue = Defense performs better than expected",
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


def create_defense_trend_analysis():
    """Create a trend analysis showing how defense performance changes over years."""
    
    df = load_defense_pi_data()
    
    # Select a few key stats for trend analysis
    key_stats = [
        'pi_season_receivingYardsWR',
        'pi_season_rushingYardsRB', 
        'pi_season_passingYardsQB'
    ]
    
    # Get a few representative teams
    teams = ['NE', 'BAL', 'SF', 'TB', 'KC']  # Some well-known defensive teams
    
    # Create subplots
    fig = make_subplots(
        rows=len(key_stats), cols=1,
        subplot_titles=[stat.replace('pi_season_', '') for stat in key_stats],
        vertical_spacing=0.1
    )
    
    colors = px.colors.qualitative.Set3
    
    for i, stat in enumerate(key_stats, 1):
        for j, team in enumerate(teams):
            team_data = df[df['defense_team'] == team].sort_values('year')
            if not team_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=team_data['year'],
                        y=team_data[stat],
                        mode='lines+markers',
                        name=f"{team}",
                        line=dict(color=colors[j % len(colors)]),
                        showlegend=(i == 1)  # Only show legend for first subplot
                    ),
                    row=i, col=1
                )
        
        # Add horizontal line at y=0
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=i, col=1)
    
    fig.update_layout(
        title="Defense Performance Trends Over Years",
        height=800,
        showlegend=True
    )
    
    # Update all subplot axes
    for i in range(1, len(key_stats) + 1):
        fig.update_xaxes(title_text="Year", row=i, col=1)
        fig.update_yaxes(title_text="Performance Index", row=i, col=1)
    
    return fig


def main():
    """Main function to run the defense PI visualizations."""
    print("Loading defense performance indices data...")
    
    # Create weekly visualization
    print("Creating weekly defense performance visualization...")
    fig1 = create_weekly_defense_visualization()
    fig1.show()
    
    # Create heatmap comparison
    print("Creating defense performance heatmap...")
    fig2 = create_defense_comparison_heatmap()
    fig2.show()
    
    # Create trend analysis
    print("Creating defense performance trend analysis...")
    fig3 = create_defense_trend_analysis()
    fig3.show()
    
    print("✅ Defense PI visualizations created!")
    print("\nVisualization Guide:")
    print("1. Weekly Performance: Shows how defenses perform week-by-week")
    print("2. Heatmap: Compares different teams across key defensive stats")
    print("3. Trend Analysis: Shows how defensive performance changes over years")
    print("\nPerformance Index Interpretation:")
    print("• Positive values: Defense performs better than expected")
    print("• Negative values: Defense performs worse than expected")
    print("• Values near 0: Defense performs as expected")


if __name__ == "__main__":
    main()
