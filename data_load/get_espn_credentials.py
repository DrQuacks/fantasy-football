#!/usr/bin/env python3
"""
get_espn_credentials.py

Helper script to guide users on finding their ESPN credentials.
"""

import os

def print_credentials_guide():
    """Print instructions for finding ESPN credentials."""
    
    print("🔑 ESPN Credentials Guide")
    print("=" * 50)
    print()
    print("To use the free agent collection script, you need three values from ESPN:")
    print()
    print("1. ESPN_LEAGUE_ID")
    print("2. ESPN_S2 (cookie value)")
    print("3. SWID (cookie value)")
    print()
    print("📋 How to find these values:")
    print()
    print("1. Go to your ESPN fantasy football league page")
    print("2. Open your browser's Developer Tools (F12 or right-click → Inspect)")
    print("3. Go to the 'Application' or 'Storage' tab")
    print("4. Look for 'Cookies' → 'https://www.espn.com'")
    print("5. Find these cookie names:")
    print("   - 'espn_s2' (copy the value)")
    print("   - 'SWID' (copy the value)")
    print("6. For LEAGUE_ID: Look at your league URL")
    print("   - URL format: https://fantasy.espn.com/football/league?leagueId=XXXXX")
    print("   - The number after 'leagueId=' is your LEAGUE_ID")
    print()
    print("🔧 Setting environment variables:")
    print()
    print("Option 1: Export in terminal (temporary):")
    print("export ESPN_LEAGUE_ID='your_league_id'")
    print("export ESPN_S2='your_espn_s2_value'")
    print("export SWID='your_swid_value'")
    print()
    print("Option 2: Create a .env file (recommended):")
    print("Create a file named '.env' in your project directory with:")
    print("ESPN_LEAGUE_ID=your_league_id")
    print("ESPN_S2=your_espn_s2_value")
    print("SWID=your_swid_value")
    print()
    print("⚠️  Security Note:")
    print("- Keep these credentials private")
    print("- Don't commit the .env file to git")
    print("- The .env file is already in .gitignore")
    print()
    print("✅ Once you have these values set, you can run:")
    print("python add_free_agents.py")

def check_current_credentials():
    """Check if credentials are currently set."""
    print("🔍 Checking current credentials...")
    print()
    
    league_id = os.getenv("ESPN_LEAGUE_ID")
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("SWID")
    
    print(f"ESPN_LEAGUE_ID: {'✅ Set' if league_id else '❌ Not set'}")
    print(f"ESPN_S2: {'✅ Set' if espn_s2 else '❌ Not set'}")
    print(f"SWID: {'✅ Set' if swid else '❌ Not set'}")
    print()
    
    if all([league_id, espn_s2, swid]):
        print("🎉 All credentials are set! You can run add_free_agents.py")
    else:
        print("❌ Missing credentials. Please follow the guide above.")

if __name__ == "__main__":
    print_credentials_guide()
    print()
    check_current_credentials()

