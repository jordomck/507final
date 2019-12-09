from secrets import google_places_key
import requests
import json
import sqlite3
import plotly.graph_objs as go
from bs4 import BeautifulSoup

CACHE_FNAME = "owl_cache.json"
DBNAME = "owl_database.db.sqlite"

try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

# if there was no file, no worries. There will be soon!
except:
    CACHE_DICTION = {}


class Player():
    def __init__(self, name="unknown", tag="unknown", role="unknown", hometown = "unknown", team = "unknown"):
        self.name = name
        self.tag = tag
        self.role = role
        self.homeplace = hometown
        self.homecountry = hometown.split(" | ")[0]

        if(self.homecountry == "--"):
            self.homecountry = "United States"
        try:
            self.hometown = hometown.split(" | ")[1]
        except:
            self.hometown = "Los Angeles, CA"
            self.homecountry = "United States"
        self.team = team
        self.formattedHometown = self.hometown + " " + self.homecountry

    def __str__(self):
        return("\n\nTag: " + self.tag + "\nTeam: " + self.team + "\nName: " + self.name + "\nRole: " +
               self.role + "\nHometown: " + self.hometown + "\nHome country: " + self.homecountry
               )

class Team():
    def __init__(self, hometown, teamname):
        self.hometown = hometown
        self.teamname = teamname
        
    def __str__(self):
        return self.hometown + " " + self.teamname

    
class City():
    def __init__(self, lat, lng, name=""):
        self.lat = lat
        self.lng = lng
        self.name = name

    def __str__(self):
        return self.name + ": " + str(self.lng) + ", " + str(self.lat)



def getPlayerInfo():
    url= "https://overwatchleague.com/en-us/players"
    if url in CACHE_DICTION:
        soupText = CACHE_DICTION[url]
    else:
        print("getting player data for " + url + " from web...")
        soupText = requests.get(url, timeout=5).text
        CACHE_DICTION[url] = soupText
        cache_file = open(CACHE_FNAME, "w+")
        cache_file.write(json.dumps(CACHE_DICTION))
        cache_file.close()
        print("Done!")

    soup = BeautifulSoup(soupText, "html.parser")
    scripts = soup.find_all("script", id="__NEXT_DATA__")
    jsonArchive = json.loads(scripts[0].text)

    playerList = jsonArchive["props"]["pageProps"]["blocks"][1]["playerList"]["tableData"]["data"]
    playerObjList = []
    for player in playerList:
        name = player["realName"]
        tag = player["name"]
        hometown = player["hometown"]
        role = player["role"]
        team = player["teamName"]
        playerObj = Player(name, tag, role, hometown, team)
        #print(playerObj)
        playerObjList.append(playerObj)
    return playerObjList

def getTeamInfo(playerObjList):
    teams = []
    for player in playerObjList:
        if player.team not in teams:
            teams.append(player.team)
    teamObjList = []
    for team in teams:
        teamHometown = " ".join(team.split(" ")[:-1])
        teamName = team.split(" ")[-1:][0]
        teamObjList.append(Team(teamHometown, teamName))
        
    return teamObjList


def getCityInfo(playerObjList, teamObjList):
    locsToFind = []
    for player in playerObjList:
        if player.formattedHometown not in locsToFind:
            locsToFind.append(player.formattedHometown)
    for team in teamObjList:
        if team.hometown not in locsToFind:
            locsToFind.append(team.hometown)
    cityObjList = []
    for locRequest in locsToFind:
        override = False
        locRequestOverride = locRequest
        if(locRequest == "Florida"):
            override = True
            locRequestOverride = "Miami"
        elif(locRequest == "Washington"):
            override = True
            locRequestOverride = "Washington D.C."
        
        baseurl = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        if override:
            params = {"key" : google_places_key, "query" : locRequestOverride}
        else:
            params = {"key" :google_places_key, "query" : locRequest}
        fullRequestID = baseurl + locRequestOverride
        if fullRequestID in CACHE_DICTION:
            responseData = CACHE_DICTION[fullRequestID]
        else:
            responseData = requests.get(baseurl, params=params, timeout=5).text
            CACHE_DICTION[fullRequestID] = responseData
            cache_file = open(CACHE_FNAME, 'w+')
            cache_file.write(json.dumps(CACHE_DICTION))
            cache_file.close()
        
        responseDict = json.loads(responseData)
        #print("There were " + str(len(responseDict["results"])) + " results")
        if len(responseDict["results"]) < 1:
            continue
        loc = responseDict["results"][0]
        name = locRequest
        lat = loc["geometry"]["location"]["lat"]
        lng = loc["geometry"]["location"]["lng"]
        city = City(lat, lng, name)
        #print(city)
        cityObjList.append(city)

    return cityObjList 

def initDatabase():
    playerObjList = getPlayerInfo()
    teamObjList = getTeamInfo(playerObjList)
    cityList = getCityInfo(playerObjList, teamObjList)
##    for city in cityList:
##        print(city)
##    for team in teamObjList:
##        print(team)
##    #cities = sortIntoCities(playerObjList)
##
##    for player in playerObjList:
##        print(player)

    #the first step is to destroy the old tables if they're present
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = "DROP TABLE IF EXISTS \'Players\'"
    cur.execute(command)
    command = "DROP TABLE IF EXISTS \'Teams\'"
    cur.execute(command)
    command = "DROP TABLE IF EXISTS \'Cities\'"
    cur.execute(command)
    conn.commit()

    #the Cities table won't have any foreign keys, so let's build that first
    command = """
    CREATE TABLE 'Cities' ('Id' INTEGER PRIMARY KEY AUTOINCREMENT,
    'Name' TEXT NOT NULL, 'Lat' REAL NOT NULL, 'Lng' REAL NOT NULL);
    """
    cur.execute(command)
    conn.commit()

    command = """
    CREATE TABLE 'Teams' ('Id' INTEGER PRIMARY KEY AUTOINCREMENT,
    'Name' TEXT NOT NULL, 'CityId' INTEGER,
    FOREIGN KEY('CityId') REFERENCES 'Cities'('Id'));
    """
    cur.execute(command)
    conn.commit()
    command = """
    CREATE TABLE 'Players' ('Id' INTEGER PRIMARY KEY AUTOINCREMENT,
    'Name' TEXT NOT NULL, 'Tag' TEXT NOT NULL, 'TeamId' INTEGER,
    'CityId' INTEGER, 'Role' TEXT NOT NULL, 'HomeCountry' TEXT NOT NULL, FOREIGN KEY('TeamId') REFERENCES 'Teams'('Id')
    FOREIGN KEY('CityId') REFERENCES 'Cities'('Id'));
    """
    cur.execute(command)
    conn.commit()

    #now we load in the cities
    cityDict = {}
    counter = 1
    for city in cityList:
        cityDict[city.name] = counter
        counter +=1
        toInsert = (city.name, city.lat, city.lng)
        insertion = "INSERT INTO Cities VALUES (NULL, ?, ?, ?)"
        cur.execute(insertion, toInsert)
    conn.commit()

    teamDict = {}
    counter = 1
    for team in teamObjList:
        teamDict[str(team)] = counter
        counter += 1

        cityId = cityDict[team.hometown]
        toInsert = (str(team), cityId)
        insertion = "INSERT INTO Teams VALUES (NULL, ?, ?)"
        cur.execute(insertion, toInsert)
    conn.commit()

    for player in playerObjList:
        #print(player.formattedHometown)
        try:
            cityId = cityDict[player.formattedHometown]
        except:
            cityId = cityDict["Los Angeles, CA United States"]
        teamId = teamDict[player.team]
        toInsert = (player.name, player.tag, teamId, cityId, player.role, player.homecountry)
        insertion = "INSERT INTO Players VALUES(NULL, ?, ?, ?, ?, ?, ?)"
        cur.execute(insertion, toInsert)
    conn.commit()
    conn.close()

def whoIsFrom():
    cityName = input("Please enter a city name.\nExamples: \"Seoul South Korea\", \"Los Angeles, CA United States\"\n")
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Players.Tag FROM Players JOIN Cities ON Players.CityId == Cities.Id
    WHERE Cities.Name == \'""" + cityName + "\'"
    cur.execute(command)
    results = cur.fetchall()
    if len(results) == 0:
        print("No players found for " + cityName)
    else:
        print("Players from " + cityName + ": ")
    for result in results:
        print(result[0])

def whoIsOnThisTeam():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Teams.Name FROM Teams
    """
    cur.execute(command)
    teams = cur.fetchall()
    counter = 1
    for team in teams:
        print(str(counter) + " " + team[0])
        counter += 1
    vouched = False
    while not vouched:
        teamNum = input("Please enter the number of the team you want to list.\n")
        try:
            if int(teamNum) <= 20 and int(teamNum) > 0:
                vouched = True
            else:
                print("Choose a number from the list.")
        except:
            print("There was an error. Try again!")
    teamName = teams[int(teamNum) - 1][0]
    command = """
    SELECT Players.Tag, Players.Name, Players.Role FROM Players JOIN Teams ON Players.TeamId == Teams.Id
    WHERE Teams.Name == \'""" + teamName + "\'"
    cur.execute(command)
    results = cur.fetchall()
    for result in results:
        print(result[0] + " (" + result[1] + ") [" + result[2] + "]")
    return results

def showHometownsOfTeam():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Teams.Name FROM Teams
    """
    cur.execute(command)
    teams = cur.fetchall()
    counter = 1
    for team in teams:
        print(str(counter) + " " + team[0])
        counter += 1
    vouched = False
    while not vouched:
        teamNum = input("Please enter the number of the team you want to map.\n")
        try:
            if int(teamNum) <= 20 and int(teamNum) > 0:
                vouched = True
            else:
                print("Choose a number from the list.")
        except:
            print("There was an error. Try again!")
    teamName = teams[int(teamNum) - 1][0]
    command = """
    SELECT Players.Tag, Players.Name, Cities.Name, Cities.Lat, Cities.Lng FROM Players JOIN Teams ON Players.TeamId == Teams.Id
    JOIN Cities ON Players.CityID == Cities.Id WHERE Teams.Name == \'""" + teamName + "\'"
    cur.execute(command)
    results = cur.fetchall()
    titles = []
    lats = []
    lngs = []
    infos = []
    for result in results:
        if result[2] in infos: #city already in
            #print(result[2])
            idx = infos.index(result[2])
            titles[idx] += ", " + result[0] + " (" + result[1] + ")"
        else:
            
            infos.append(result[2]) #cityname
            titles.append(infos[-1] + ": " + result[0] + " (" + result[1] + ")")
            lats.append(result[3])
            lngs.append(result[4])
    displayLocations(teamName + " Player Hometowns", titles, lats, lngs, infos)
    return [titles, lats, lngs]


def showHometownsOfAllPlayers(skipDisplay=False):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Players.Tag, Players.Name, Cities.Name, Cities.Lat, Cities.Lng, Teams.Name FROM Players JOIN Teams ON Players.TeamId == Teams.Id
    JOIN Cities ON Players.CityID == Cities.Id"""
    cur.execute(command)
    results = cur.fetchall()
    titles = []
    lats = []
    lngs = []
    infos = []
    for result in results:
        if result[2] in infos: #city already in
            #print(result[2])
            idx = infos.index(result[2])
            titles[idx] += ", " + result[0] + " (" + result[5] + ")"
        else:
            
            infos.append(result[2]) #cityname
            titles.append(infos[-1] + ": " + result[0] + " (" + result[5] + ")")
            lats.append(result[3])
            lngs.append(result[4])
    if not skipDisplay:
        displayLocations("All Player Hometowns", titles, lats, lngs, infos)
    conn.close()
    return [titles, lats, lngs, infos]

def showHometownsOfRole():
    print("What role would you like to view?\nThere are three roles:  1 = \'Offense,\' 2 = \'Tank,\' and 3 = \'Support.\'")
    choice = ""
    while choice not in ["1", "2", "3"]:
        choice = input("Enter 1, 2, or 3.\n")
    choice = int(choice)
    role = ["Offense", "Tank", "Support"][choice-1]
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Players.Tag, Players.Name, Cities.Name, Cities.Lat, Cities.Lng FROM Players
    JOIN Cities ON Players.CityID == Cities.Id WHERE Players.Role == \'""" + role + "\'"
    cur.execute(command)
    results = cur.fetchall()
    titles = []
    lats = []
    lngs = []
    infos = []
    for result in results:
        if result[2] in infos: #city already in
            #print(result[2])
            idx = infos.index(result[2])
            titles[idx] += ", " + result[0] + " (" + result[1] + ")"
        else:
            
            infos.append(result[2]) #cityname
            titles.append(infos[-1] + ": " + result[0] + " (" + result[1] + ")")
            lats.append(result[3])
            lngs.append(result[4])
    displayLocations(role + " Player Hometowns", titles, lats, lngs, infos)
    conn.close()

def mostCommonHometowns(skipDisplay=False):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Cities.Name, COUNT(Players.Id) FROM Players JOIN Teams ON Players.TeamId == Teams.Id
    JOIN Cities ON Players.CityID == Cities.Id GROUP BY Cities.Id HAVING COUNT(Players.ID) > 1 ORDER BY COUNT(Players.Id) DESC"""
    cur.execute(command)
    results = cur.fetchall()
    cityNames = []
    playerCounts = []
    for result in results:
        cityNames.append(result[0])
        playerCounts.append(result[1])
    #print(cityNames)
    if not skipDisplay:
        displayBars("Most Common Hometowns", cityNames, playerCounts)
    return [cityNames, playerCounts]

def mostCommonHomeCountries(skipDisplay = False):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Players.HomeCountry, COUNT(Players.Id) FROM Players GROUP BY Players.HomeCountry ORDER BY COUNT(Players.Id) DESC"""
    cur.execute(command)
    results = cur.fetchall()
    countryNames = []
    playerCounts = []
    for result in results:
        countryNames.append(result[0])
        playerCounts.append(result[1])
    #print(cityNames)
    if not skipDisplay:
        displayPie("Most Common Home Nations", countryNames, playerCounts)
    return [countryNames, playerCounts]

def teamRosterSizes(skipDisplay=False):
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Teams.Name, COUNT(Players.Id) FROM Players JOIN Teams ON Players.TeamId == Teams.Id
    GROUP BY Teams.Id ORDER BY COUNT(Players.Id) DESC
    """
    cur.execute(command)
    results = cur.fetchall()
    teamNames = []
    playerCounts = []
    for result in results:
        teamNames.append(result[0])
        playerCounts.append(result[1])
    if not skipDisplay:
        displayBars("Offseason Roster Sizes", teamNames, playerCounts)
    return [teamNames, playerCounts]

def teamHometowns():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    command = """
    SELECT Teams.Name, Cities.Name, Cities.Lat, Cities.Lng FROM Teams JOIN Cities ON Teams.CityId == Cities.Id
    """
    cur.execute(command)
    results = cur.fetchall()
    outputTexts = []
    cityNames = []
    lats = []
    lngs = []
    infos = []
    
    for result in results:
        print(result[1])
        if result[1] in cityNames: #city already in
            idx = cityNames.index(result[1])
            outputTexts[idx] += ", " + result[0]
        else:
            outputTexts.append(result[1] + ": " + result[0])
            cityNames.append(result[1])
            lats.append(result[2])
            lngs.append(result[3])
    displayLocations("Team Home Stadiums", outputTexts, lats, lngs, infos)
    return [outputTexts, lats, lngs, infos]
    

def displayBars(chartTitle, labels, quantities):
    fig = go.Figure([go.Bar(x=labels, y=quantities)])
    fig.update_layout(title=chartTitle)
    fig.show()

def displayPie(chartTitle, labels, quantities):
    fig = go.Figure([go.Pie(labels=labels, values=quantities)])
    fig.update_layout(title=chartTitle)
    fig.show()



def displayLocations(chartTitle, titles, lats, lngs, infos):
    trace1 = dict(
        type = 'scattergeo',
        locationmode = 'ISO-3',
        lon = lngs,
        lat = lats,
        text = titles,
        mode = 'markers',
        marker = dict(
            size = 4,
            symbol = 'circle',
            color = 'red'
        ))
    data = [trace1]

    fig = go.Figure(data=data)

    paddingFactor = .25
    latScale = max(lats) - min(lats)
    lngScale = max(lats) - min(lats)
    latPad = latScale * paddingFactor
    lngPad = lngScale * paddingFactor
    latAxis = [min(lats)-latPad, max(lats)+latPad]
    lngAxis = [min(lngs)-lngPad, max(lngs)+lngPad]
    centerLat = sum(latAxis) / 2
    centerLng = sum(lngAxis) / 2
    
    fig.update_layout(
        title = chartTitle,
        geo = dict(
            lataxis = {'range': latAxis},
            lonaxis = {'range': lngAxis},
            center = {'lat': centerLat, 'lon': centerLng})
        )
    fig.show()
    
def interactivePrompt():
    print("Welcome to Jordan McKay's Interactive Overwatch League Database!")
    print("The Overwatch League is an international competitive gaming league.")
    print("The players come from all over the world,\nand the 20 teams are based in several different countries.")
    print("This database allows analysis of the hometowns\nof all the players and teams in the league,")
    print("as well as methods to stay up-to-date\nabout who is currently on the roster of each team.")
    
    answer = ""
    while not (answer.upper == "QUIT"):
        print("\n\nWhat would you like to do next?")
        print("Please enter the number associated with the option you want.")
        counter = 1
        options = [("Rebuild Database", initDatabase), ("List Players on a Team", whoIsOnThisTeam),
                   ("Display Most Common Hometowns", mostCommonHometowns), ("Show Most Common Home Countries", mostCommonHomeCountries), ("Map Hometowns of a Team", showHometownsOfTeam),
                   ("Map Hometowns of All Players", showHometownsOfAllPlayers),("Map Hometowns by Player Role", showHometownsOfRole), ("Search for Players by Hometown", whoIsFrom), ("Show Current Roster Sizes", teamRosterSizes),
                   ("Map Team Home Stadiums", teamHometowns), ("Quit", quit)]
                   
        for option in options:
            print(str(counter) + ": " + option[0])
            counter += 1
        vouched = False
        while not vouched:
            choice = input("Which one do you want? Enter the number to the left of your desired option.\n")
            try:
                if int(choice) in range(1, 1 + len(options)):
                    vouched = True
                else:
                    print("Choose a number between 1 and " + str(1+len(options) + "!"))
            except:
                print("Enter the number of the option you want!")
                
        #try:
        options[int(choice)-1][1]()
        #except:
        #    print("Please try again.")
    
#whoIsFrom("Philadelphia, PA United States")
#whoIsOnThisTeam()
#print("-------")

#mostCommonHomeCountries()
#showHometownsOfAllPlayers()
#showHometownsOfTeam("Houston Outlaws")
#showHometownsOfRole("Tank")
#showHometownsOfRole("Offense")
#showHometownsOfRole("Support")
#teamRosterSizes()
#teamHometowns()
#mostCommonHometowns()
if __name__=="__main__":
    interactivePrompt()


