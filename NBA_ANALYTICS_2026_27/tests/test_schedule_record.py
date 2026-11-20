import unittest

from collectors.nba_stats import _has_unassigned_team, _schedule_record


class TestScheduleRecord(unittest.TestCase):
    def setUp(self):
        self.base = {
            "gameId": "0022600001",
            "homeTeam_teamId": 1610612738,
            "awayTeam_teamId": 1610612751,
            "gameDate": "2026-11-20",
            "gameStatus": 1,
            "gameStatusText": "7:30 pm ET",
        }

    def test_regular_matchup_is_parsed(self):
        self.assertFalse(_has_unassigned_team(self.base))
        game = _schedule_record(self.base)
        self.assertIsNotNone(game)
        self.assertEqual(game["home_team_id"], 1610612738)
        self.assertEqual(game["away_team_id"], 1610612751)

    def test_pending_home_team_is_detected(self):
        row = dict(self.base, homeTeam_teamId=0)
        self.assertTrue(_has_unassigned_team(row))

    def test_pending_away_team_is_detected(self):
        row = dict(self.base, awayTeam_teamId=0)
        self.assertTrue(_has_unassigned_team(row))

    def test_missing_ids_are_not_mistaken_for_zero(self):
        row = dict(self.base, homeTeam_teamId=None)
        self.assertFalse(_has_unassigned_team(row))


if __name__ == "__main__":
    unittest.main()
