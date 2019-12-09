import unittest
from owlmap import *

class TestPlayer(unittest.TestCase):

    def testDefaultValues(self):
        player = Player()
        self.assertEqual(str(player),
"""\n\nTag: unknown
Team: unknown
Name: unknown
Role: unknown
Hometown: Los Angeles, CA
Home country: United States""")

    def testFilledValues(self):
        player = Player(name="Jordan McKay", tag = "MrMacduggan",
                        role="Tank", hometown="United States | Ann Arbor, MI",
                        team="Boston Uprising")
        self.assertEqual(str(player),
"""\n\nTag: MrMacduggan
Team: Boston Uprising
Name: Jordan McKay
Role: Tank
Hometown: Ann Arbor, MI
Home country: United States""")


class TestGetters(unittest.TestCase):

    def testGetPlayerInfo(self):
        playerList = getPlayerInfo()
        assert(len(playerList) > 100)
        foundGeguri=False
        for player in playerList:
            assert type(player) == Player
            if player.tag == "Geguri":
                foundGeguri = True
        assert(foundGeguri)

    def testGetTeamInfo(self):
        teams = getTeamInfo(getPlayerInfo())
        assert len(teams) == 20
        foundNYXL = False
        for team in teams:
            assert type(team) == Team
            if team.teamname == "Excelsior" and team.hometown == "New York":
                foundNYXL = True
        assert foundNYXL

class TestDatamanip(unittest.TestCase):

    def testShowHometownsOfAllPlayers(self):
        hometowns = showHometownsOfAllPlayers(skipDisplay=True)
        assert len(hometowns[0]) > 40
        assert "Morrow, OH United States: Muma (Houston Outlaws)" in hometowns[0]
        assert len(hometowns[0]) == len(hometowns[1])
        assert len(hometowns[1]) == len(hometowns[2])
        

    def testMostCommonHometowns(self):
        mostCommon = mostCommonHometowns(skipDisplay=True)
        assert "Moscow Russia" not in mostCommon[0]
        assert "Seoul South Korea" == mostCommon[0][0]
        for playerCount in mostCommon[1]:
            assert playerCount > 1

    def testMostCommonHomeCountries(self):
        mostCommon = mostCommonHomeCountries(skipDisplay=True)
        assert "Russia" in mostCommon[0]
        assert "South Korea" == mostCommon[0][0]
        for playerCount in mostCommon[1]:
            assert playerCount > 0

    def testRosterSizes(self):
        sizes = teamRosterSizes(skipDisplay=True)
        assert len(sizes[0]) == 20
        maximum = 200
        for count in sizes[1]:
            assert maximum >= count
            maximum = count



unittest.main()
