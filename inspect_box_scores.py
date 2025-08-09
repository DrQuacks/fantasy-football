from espn_api.football import League

league = League(league_id=57220027, year=2022, espn_s2="your_espn_s2", swid="your_swid")

week = 1
box_scores = league.box_scores(week)

for matchup in box_scores:
    print(f"\n📅 Week {week} Matchup")

    for player in matchup.home_lineup:  # or matchup.away_lineup
        print(f"▶️ Player: {player.name}")
        print(f"   Slot Position: {player.slot_position}")
        print(f"   Team Opponent: {player.pro_opponent}")
        print(f"   Pro Pos Rank:  {player.pro_pos_rank}")
        print(f"   Game Played:   {player.game_played}")
        print(f"   Game Date:     {player.game_date}")
        print(f"   Bye Week?:     {player.on_bye_week}")
        print(f"   Active?:       {player.active_status}")
        print(f"   Points:        {player.points}")
        print(f"   Projected:     {player.projected_points}")
        print("-" * 40)
    break  # Just first matchup for now
