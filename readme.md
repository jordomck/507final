Jordan McKay SI 507 final project: owlmap.py

For my final project, I decided to attempt analyzing the data of the Overwatch League.
The Overwatch League is a global competitive gaming circuit where players
from around the world compete to become the best at Overwach,
one of the most popular video games on the planet.

To obtain my results, I scraped the player data from OverwatchLeague.com,
where it was stored in a script to be rendered programmatically.
After obtaining data about every player in the league, I obtain information
about the 20 teams in the league.

The second phase of my project is finding out the latitude and longitude of all
the players' hometowns and all the teams' home stadiums. To accomplish this,
I used the Google Places API.

All information from my requests to the OverwachLeague.com and the Google Places API are
cached, but also are built into an SQL relational database.

This database has three tables:
Players [Id, Name, Tag, TeamId, CityId, Role, HomeCountry]
Teams [Id, Name, CityId]
Cities [Id, Name, Lat, Lng]

Teams each have a city, and Players each have a city and a team.

If you would like to re-download all the data, simply delete both the json cache and the sqlite database.
I estimate that it will take about 60-120 seconds to refill the data repositories.

When my program owlmap.py is executed, the user can choose between a variety
of different ways to explore this data. Follow the on-screen prompts to try it out!

