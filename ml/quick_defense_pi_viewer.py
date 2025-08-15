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


def create_defense_heatmap(df):
    """Create a heatmap showing defense performance across teams and key stats."""
    
    # Get the most recent year
    latest_year = df['year'].max()
    df_latest = df[df['year'] == latest_year]
    
    # Select key stats for visualization
    key_stats = [
        'pi_season_receivingYardsWR',
        'pi_season_rushingYardsRB', 
        'pi_season_passingYardsQB',
        'pi_season_madeFieldGoalsK'
    ]
    
    # Get top teams (first 10 for readability)
    teams = get_available_teams(df_latest)[:10]
    
    # Create heatmap data
    z_data = []
    for stat in key_stats:
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
        y=[s.replace('pi_season_', '') for s in key_stats],
        colorscale='RdBu_r',  # Red-Blue diverging scale
        zmid=0,  # Center the color scale at 0
        text=[[f"{val:.3f}" for val in row] for row in z_data],
        texttemplate="%{text}",
        textfont={"size": 12},
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>Team: %{x}<br>PI: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Defense Performance Index Heatmap ({latest_year})<br><sub>Top 10 Teams - Key Defensive Metrics</sub>",
        xaxis_title="Defense Team",
        yaxis_title="Stat Category",
        height=500,
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


def create_team_comparison(df):
    """Create a comparison chart showing top teams across key stats."""
    
    # Get the most recent year
    latest_year = df['year'].max()
    df_latest = df[df['year'] == latest_year]
    
    # Select key stats and top teams
    key_stats = [
        'pi_season_receivingYardsWR',
        'pi_season_rushingYardsRB', 
        'pi_season_passingYardsQB'
    ]
    
    teams = get_available_teams(df_latest)[:5]  # Top 5 teams
    
    # Create subplots
    fig = make_subplots(
        rows=len(key_stats), cols=1,
        subplot_titles=[s.replace('pi_season_', '') for s in key_stats],
        vertical_spacing=0.1
    )
    
    colors = px.colors.qualitative.Set3
    
    for i, stat in enumerate(key_stats, 1):
        for j, team in enumerate(teams):
            team_data = df_latest[df_latest['defense_team'] == team]
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
        title=f"Defense Performance Comparison ({latest_year})<br><sub>Top 5 Teams - Key Defensive Metrics</sub>",
        height=600,
        showlegend=True,
        barmode='group'
    )
    
    # Update all subplot axes
    for i in range(1, len(key_stats) + 1):
        fig.update_xaxes(title_text="Team", row=i, col=1)
        fig.update_yaxes(title_text="Performance Index", row=i, col=1)
    
    return fig


def create_trend_analysis(df):
    """Create a trend analysis showing how defense performance changes over years."""
    
    # Select key stats and representative teams
    key_stats = [
        'pi_season_receivingYardsWR',
        'pi_season_rushingYardsRB', 
        'pi_season_passingYardsQB'
    ]
    
    teams = ['NE', 'BAL', 'SF', 'TB', 'KC']  # Well-known defensive teams
    
    # Create subplots
    fig = make_subplots(
        rows=len(key_stats), cols=1,
        subplot_titles=[s.replace('pi_season_', '') for s in key_stats],
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
        title="Defense Performance Trends Over Years<br><sub>Key Defensive Teams - Performance Evolution</sub>",
        height=600,
        showlegend=True
    )
    
    # Update all subplot axes
    for i in range(1, len(key_stats) + 1):
        fig.update_xaxes(title_text="Year", row=i, col=1)
        fig.update_yaxes(title_text="Performance Index", row=i, col=1)
    
    return fig


def main():
    """Main function to show defense PI visualizations."""
    
    print("🏈 Defense Performance Index Quick Viewer")
    print("=" * 40)
    
    # Load data
    print("Loading defense performance data...")
    df = load_defense_pi_data()
    
    teams = get_available_teams(df)
    years = get_available_years(df)
    
    print(f"\n📊 Available Data:")
    print(f"   Teams: {len(teams)} teams")
    print(f"   Years: {years}")
    print(f"   Latest year: {years[-1]}")
    
    print(f"\n🎯 Creating visualizations...")
    
    # Create and show heatmap
    print("1. Creating defense performance heatmap...")
    heatmap_fig = create_defense_heatmap(df)
    heatmap_fig.show()
    
    # Create and show team comparison
    print("2. Creating team comparison chart...")
    comparison_fig = create_team_comparison(df)
    comparison_fig.show()
    
    # Create and show trend analysis
    print("3. Creating trend analysis...")
    trend_fig = create_trend_analysis(df)
    trend_fig.show()
    
    print(f"\n✅ All visualizations created!")
    print(f"\n🔍 What to look for:")
    print(f"• Teams with consistently positive PI values (blue) are strong defensively")
    print(f"• Teams with negative PI values (red) struggle in those areas")
    print(f"• The heatmap gives you a quick overview of defensive strengths/weaknesses")
    print(f"• Trends show how defensive performance changes over time")
    print(f"• Values near 0 (white) indicate the defense performs as expected")


if __name__ == "__main__":
    main()


