#!/usr/bin/env python3
"""
Test script to verify we can get stats for David Moore using the free_agents method.
"""

from espn_api.football import League

def test_david_moore():
    """Test getting David Moore's stats as a free agent."""
    
    # Connect to league
    league = League(league_id=57220027, year=2019)
    
    # Get free agents for WR position
    fa = league.free_agents(16, 500, 'WR')
    
    # Find David Moore
    david_moore = None
    for p in fa:
        if p.name == "David Moore":
            david_moore = p
            break
    
    if david_moore:
        print(f"Found David Moore: {david_moore.name}")
        print(f"Player ID: {david_moore.playerId}")
        print(f"Position: {david_moore.position}")
        print(f"Team: {getattr(david_moore, 'team', 'N/A')}")
        print(f"Pro Team: {getattr(david_moore, 'proTeam', 'N/A')}")
        print(f"Stats: {david_moore.stats}")
        
        if david_moore.stats:
            print("\nStats keys:")
            for key in david_moore.stats.keys():
                print(f"  {key}: {type(david_moore.stats[key])}")
        else:
            print("No stats found")
    else:
        print("David Moore not found in free agents")

if __name__ == "__main__":
    test_david_moore()

