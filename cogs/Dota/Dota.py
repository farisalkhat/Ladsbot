import asyncio
import discord
import aiohttp
from datetime import datetime
from discord.ext.commands import Bot
from discord.ext import commands,tasks
from bs4 import BeautifulSoup
import tokens
import requests
from requests.exceptions import HTTPError
from core import jsondb



token = tokens.stratz_api
url = 'https://api.stratz.com/graphql'
headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'STRATZ_API'
        }


# opendota_query = "https://api.opendota.com/api/leagues/{}/matches?api_key={}".format(14993,tokens.opendota_api)
# opendota_query2 = "https://api.opendota.com/api/leagues?api_key={}".format(tokens.opendota_api)
class Dota(commands.Cog):
    def __init__(self,bot):
        self.bot=bot
        self.stratz_data={}
        self.num_of_matches = 0
        self.ping_dotabuff_now = False
        self.completed_series = []
        self.tournament_tracker = {}
        self.default_timer = 900 #15 minutes
        self.last_match_date = 0
        self.counter = 0 
        self.tracking = True
        self.check_lads_update.start()
        #bot.loop.create_task(self.check_lads_update())
    
    @tasks.loop(minutes=15)
    async def check_lads_update(self):
        #while self.tracking:
            await self.ping_stratz_matches()
            #await self.ping_opendota_matches()
            #await self.fetch_and_post_series()
            #await asyncio.sleep(self.default_timer)
    
    async def fetch_and_post_series(self,tournamentid):
        await jsondb.load_tournament_tracker(self) 
        tournament_url = self.tournament_tracker[tournamentid]['url']

        url = 'https://www.dotabuff.com/esports/leagues/16960-league-of-lads-season-16/series'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(tournament_url, headers=headers) as response:
                    if response.status == 200:
                        text = await response.text()
                        await self.process_series_data(text,tournamentid)
                    else:
                        print(f'Failed to fetch data. Status code: {response.status}')
        except aiohttp.ClientError as e:
            print(f'Error during requests to Dotabuff: {e}')

    async def process_series_data(self,text,tournamentid):
        await jsondb.load_tournament_tracker(self)
        soup = BeautifulSoup(text, 'html.parser')
        new_series = []

        tbody = soup.find('tbody')
        if tbody is None:
            print("No <tbody> found in the document.")
            return

        completed_series1 = tbody.find_all('tr')
        uploaded_series = list(reversed(completed_series1))

        minval = 2
        tournament = self.tournament_tracker[tournamentid]
        tournament_mode = self.tournament_tracker[tournamentid]['tournament_mode']

        color = self.tournament_tracker[tournamentid]['color']
        colour = verifyColor(color)



        if tournament_mode == "bo2":
            minval = 2
        if tournament_mode == "bo3":
            minval = 3
        if tournament_mode=="bo5":
            minval=5


        for channel_id in self.tournament_tracker[tournamentid]['channels'].keys():
            channel = self.tournament_tracker[tournamentid]['channels'][channel_id]
            discord_channel = self.bot.get_channel(int(channel_id))
            for series in uploaded_series:
                #print(series)
                try:
                    series_teams = series.find('td', class_='series-teams')
                    if not series_teams:
                        continue  # Skip rows that don't contain series information

                    series_row = series
                    series_name_tag = series_row.find('a', title=True)
                    if series_name_tag:
                        series_name = series_name_tag['title']

                        if series_name in channel:
                            continue  # Skip this series if it has already been posted

                        series_link = f"https://www.dotabuff.com{series_name_tag['href']}"
                        

                        # Look for the winner element to get the score
                        winner_element = series_row.find('td', class_='winner series-winner')
                        if winner_element:
                            score_element = winner_element.find('div', class_='score-large')
                            if score_element:
                                score = score_element.get_text(strip=True)
                                if score[0]=="2" or score[0]=="3":
                                    #case where a team 2-0/2-1s/3-X in group stage/officials/grands
                                    images = series.findAll('img')           
                                    winner_name = images[0]['alt']
                                elif score[0]=="1":
                                    #case where a team ties, simply gets team name from series_team
                                    team_div = series_teams.find('div', class_='team team-1')
                                    winner_name = team_div.find('span', class_='team-text team-text-full').get_text(strip=True) if team_div else "Unknown"
                            else:
                                
                                # case where game is still TBA. Wrote it for fun but isn't needed probably for now
                                # seems like a lot of people dont know how to properly submit matches so if we dont have this
                                # itll take a while before old matches are posted, but itll also bloat notifications 
                                # and require an additional check to ensure it doesnt get skipped when it is updated again 
                                # Ex. Update posted while a team is 1-0, wont post an update when series finishes 2-0/1-1
                                # with how it currently works.

                                team_one = series_teams.find('div', class_='team team-1')
                                team_one_score = team_one.find('span',class_="team-score-inline").get_text(strip=True)
                                team_two = series_teams.find('div', class_='team team-2')
                                team_two_score = team_two.find('span',class_="team-score-inline").get_text(strip=True)


                                if tournament_mode == "bo3":
                                    if int(team_one_score[1])==2 or int(team_two_score[1])==2:
                                        score = f"{team_one_score[1]} - {team_two_score[1]}"
                                        team_div = series_teams.find('div', class_='team team-1')
                                        winner_name = team_div.find('span', class_='team-text team-text-full').get_text(strip=True) if team_div else "Unknown"
                                    else:
                                        print(f"Match not completed. Skipping...")
                                        continue

                                elif tournament_mode == "bo2":
                                    if int(team_one_score[1]) + int(team_two_score[1])==2:
                                        score = f"{team_one_score[1]} - {team_two_score[1]}"
                                        team_div = series_teams.find('div', class_='team team-1')
                                        winner_name = team_div.find('span', class_='team-text team-text-full').get_text(strip=True) if team_div else "Unknown"
                                    else:
                                        print(f"Match not completed. Skipping...")
                                        continue


                                elif tournament_mode == "bo5":
                                    if int(team_one_score[1])==3 or int(team_two_score[1])==3:
                                        score = f"{team_one_score[1]} - {team_two_score[1]}"
                                        team_div = series_teams.find('div', class_='team team-1')
                                        winner_name = team_div.find('span', class_='team-text team-text-full').get_text(strip=True) if team_div else "Unknown"
                                    else:
                                        print(f"Match not completed. Skipping...")
                                        continue
                                else:
                                    continue
                            

                            # Finding the opponent team
                            opponent_team_div = series_teams.find('div', class_='team team-2')
                            opponent_team_name = opponent_team_div.find('span', class_='team-text team-text-full').get_text(strip=True) if opponent_team_div else "Unknown"

                            message = f'{winner_name} vs {opponent_team_name}\n'
                            description = f"SCORE: {score}\n{series_link}"
                            print(message)
                            embed = discord.Embed(
                                title=tournament['title'],
                                description=message+description,
                                color=colour
                                )
                            embed.set_thumbnail(url=tournament['imageURL'])

                            await discord_channel.send(embed=embed)
                            self.tournament_tracker[tournamentid]['channels'][channel_id].append(series_name)
                            self.tournament_tracker[tournamentid]['ping_dotabuff_now'] = False
                            await jsondb.save_tournament_tracker(self)
                            #print(f'Sent message: {series_name} - {series_link}')
                        else:
                            print(f"No winner element found in {series_name}. Raw HTML: {series_row.prettify()}")
                    else:
                        print(f"No series-name tag found in this row. Skipping...")

                except Exception as e:
                    print(f"Error processing series row: {e}")

            # if len(new_series)==0:
            #     print("No new series added.")
            #     return
        
        await jsondb.save_tournament_tracker(self)


        

    async def ping_stratz_matches(self):
            await jsondb.load_tournament_tracker(self)
            for tournamentid in self.tournament_tracker.keys():
                tournament = self.tournament_tracker[tournamentid]
                print(tournament['query'])
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, headers=headers, json={'query': tournament['query']}) as response:
                            if response.status == 200:
                                data = await response.json()
                                print("Data acquired.")
                            else:
                                print(f'Failed to fetch data. Status code: {response.status}')
                                continue
                except aiohttp.ClientError as e:
                    print(f'Error during requests to Stratz: {e}')
                    continue
                
                
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                print("Checking for updates at {}..".format(now))

                last_match = data['data']['league']['lastMatchDate']
                if tournament['ping_dotabuff_now']== False:
                    if last_match!=tournament['last_match_date']:
                        tournament['last_match_date'] = last_match
                        tournament['ping_dotabuff_now'] = True
                        tournament['counter']=0
                        print("New series found: {}".format(tournament['last_match_date']))
                        print("Will now check for series every 15 minutes.")
                        await jsondb.save_tournament_tracker(self)
                        await self.fetch_and_post_series(tournamentid)
                        continue
                    elif last_match==tournament['last_match_date']:
                        print("No new series found.") 
                        continue
                else:
                    if tournament['last_match_date']!=last_match:
                        tournament['last_match_date'] = last_match
                        tournament['counter']=0
                        print("New match date found. Resetting counter before check..")
                    tournament['counter']+=1
                    await jsondb.save_tournament_tracker(self)
                    await self.fetch_and_post_series(tournamentid)
                    if tournament['counter']==5:
                        tournament['counter'] = 0
                        tournament['ping_dotabuff_now'] = False
                        await jsondb.save_tournament_tracker(self)


    async def ping_opendota_matches(self):
        response = requests.get(opendota_query)
        response.raise_for_status()
        data = response.json()
        print(data)
        
    @commands.command(name='TrackTournament',aliases=['tracktournament','tt','TT'])
    @commands.has_permissions(administrator=True)
    async def track_tournament(self,ctx,*,arg=''):
        """
        Sets up tournament to track in specific channel. 
        Requires admin privileges.
        Usage: !TrackTournament <TournamentID> <ChannelID> <URL>
        """
        await jsondb.load_tournament_tracker(self)
        arg = arg.split(' ')

        try:
            if arg[0].isdigit() and arg[1].isdigit():
                arg[0] = arg[0]
                arg[1] = arg[1]
                print("step 1 cleared!")
            if arg[0] not in self.tournament_tracker.keys():
                if len(arg)!=3:
                    return await ctx.send("Not enough arguments. You need the tournamentID, channelID, and Dotabuff url in that order")
                query = "{league(id:" + arg[0] + "){hasLiveMatches,liveMatches{matchId,radiantTeam{name},direTeam{name},gameTime}lastMatchDate,}}"
                print(query)
                self.tournament_tracker[arg[0]] = {
                    'tournament':arg[0],
                    'channels': {
                        arg[1]:[]
                    },
                    'last_match_date':0,
                    'tournament_mode':'bo2',
                    'query':query,
                    'ping_dotabuff_now':False,
                    'counter':0,
                    'url':arg[2],
                    'title':"New series posted!",
                    'imageURL':'https://i.imgur.com/l1FPKqE.png',
                    'color':"#95240c",
                    'limit':20
                }
                print(self.tournament_tracker)
                await jsondb.save_tournament_tracker(self)
                return await ctx.send("Tournament {} now being tracked in channel {}. ".format(str(arg[0]),str(arg[1])))
            elif arg[1] not in self.tournament_tracker[arg[0]]['channels'].keys():
                self.tournament_tracker[arg[0]]['channels'][arg[1]]=[]
                await jsondb.save_tournament_tracker(self)
                return await ctx.send("Channel {} now tracking tournament {}. ".format(str(arg[1]),str(arg[0])))

            
            

        except:
            return await ctx.send("Invalid tournament id or channel id.")


    @commands.command(name='SetTournamentMessage',aliases=['settournamentmessage','stm','STM'])
    @commands.has_permissions(administrator=True)
    async def set_tournament_message(self,ctx,*,arg=''):
        """
        Sets up the message notification whenever a new series is posted for that tournament.
        Requires admin privileges.
        Usage: !SetTournamentMessage <TournamentID> <Message> 
        """
        await jsondb.load_tournament_tracker(self)
        tournamentid = arg.split(' ')[0]
        message = arg.split(' ')[1:]
        message = " ".join(message)
        try:
            if tournamentid.isdigit():
                if tournamentid in self.tournament_tracker.keys():
                    self.tournament_tracker[tournamentid]['title']= message
                    await jsondb.save_tournament_tracker(self)
                    return await ctx.send('Tournament message set to: "{}"'.format(message))
            else:
                return await ctx.send("Invalid tournament ID")

        except:
            return await ctx.send("Invalid tournament ID")

    
    @commands.command(name='SetTournamentEmbed',aliases=['settournamentembed','ste','STE'])
    @commands.has_permissions(administrator=True)
    async def set_tournament_embed(self,ctx,*,arg=''):
        """
        Sets up the embed image and color for the tournament.
        Requires admin privileges.
        Usage: !SetTournamentEmbed <TournamentID> <ImageURL> <Color>
        """
        await jsondb.load_tournament_tracker(self)
        arg = arg.split(' ')
        if len(arg)!=3:
            return await ctx.send("Not enough arguments. Need tournamentID, imageURL and color in that order.")
        tournamentid = arg[0]
        imageURL = arg[1]
        color = arg[2]
        try:
            if tournamentid.isdigit() and isValidHexaCode(color):
                if tournamentid in self.tournament_tracker.keys():
                    self.tournament_tracker[tournamentid]['imageURL']= imageURL
                    self.tournament_tracker[tournamentid]['color']= color
                    await jsondb.save_tournament_tracker(self)
                    return await ctx.send('Tournament {} imageURL set to: "{}", and color set to:{}'.format(tournamentid,imageURL,color))
                else:
                    return await ctx.send("Invalid tournament ID")
            else:
                return await ctx.send("Invalid tournament ID or color")

        except:
            return await ctx.send("Invalid tournament ID")
    

    @commands.command(name='SetTournamentMode',aliases=['settournamentmode','stmo','STMO'])
    @commands.has_permissions(administrator=True)
    async def set_tournament_mode(self,ctx,*,arg=''):
        """
        Sets up the embed image and color for the tournament.
        Requires admin privileges.
        Usage: !SetTournamentEmbed <TournamentID> <TournamentMode>
        """
        await jsondb.load_tournament_tracker(self)
        arg = arg.split(' ')
        if len(arg)!=2:
            return await ctx.send("Not enough arguments. Need tournamentID and tournament mode (bo2,bo3 or bo5)")
        tournamentid = arg[0]
        tournamentmode = arg[1]
        tournamentmode = tournamentmode.lower()
        try:
            if tournamentid.isdigit():
                if tournamentmode!= "bo2" and tournamentmode!= "bo3" and tournamentmode!= "bo5":
                    return await ctx.send("Invalid tournament mode (must be either bo2, bo3 or bo5)")
                if tournamentid in self.tournament_tracker.keys():
                    self.tournament_tracker[tournamentid]['tournament_mode']= tournamentmode
                    await jsondb.save_tournament_tracker(self)
                    return await ctx.send('Tournament mode set to: "{}"'.format(tournamentmode))
            else:
                return await ctx.send("Invalid tournament ID")

        except:
            return await ctx.send("Invalid tournament ID")


    @commands.command(name='RemoveTournament',aliases=['removetournament','rt','RT'])
    @commands.has_permissions(administrator=True)
    async def remove_tournament(self,ctx,*,arg=''):
        """
        Remove tournament from being tracked.
        Requires admin privileges.
        Usage: !RemoveTournament <TournamentID>
        """
        await jsondb.load_tournament_tracker(self)

        tournamentid = arg

        try:
            if tournamentid.isdigit():
                self.tournament_tracker.pop(tournamentid)
                await jsondb.save_tournament_tracker(self)
                return await ctx.send('Tournament {} is no longer being tracked.'.format(tournamentid))
            else:
                return await ctx.send("Invalid tournament ID")

        except:
            return await ctx.send("Invalid tournament ID")

    @commands.command(name='RemoveChannel',aliases=['removechannel','rc','RC'])
    @commands.has_permissions(administrator=True)
    async def remove_channel(self,ctx,*,arg=''):
        """
        Remove tournament channel from tracking games.
        Requires admin privileges.
        Usage: !RemoveChannel <TournamentID> <ChannelID>
        """
        await jsondb.load_tournament_tracker(self)

        arg  = arg.split(' ')
        if len(arg)!=2:
            return await ctx.send("Incorrect arguments. Must just have tournamentID and channelID")

        tournamentid = arg[0]
        channelid=arg[1]

        try:
            if tournamentid.isdigit() and channelid.isdigit():
                self.tournament_tracker[tournamentid]['channels'].pop(channelid)
                await jsondb.save_tournament_tracker(self)
                return await ctx.send('Tournament {} is no longer being tracked with channel {}.'.format(tournamentid,channelid))
            else:
                return await ctx.send("Invalid tournament or channel ID")

        except:
            return await ctx.send("Invalid tournament ID")



    # @commands.command(name='Start',aliases=['start','st','ST'])
    # @commands.has_permissions(administrator=True)
    # async def start_tracking(self,ctx,*,arg=''):
    #     self.tracking = True




def isValidHexaCode(str):
 
    if (str[0] != '#'):
        return 0
 
    if (not(len(str) == 4 or len(str) == 7)):
        return 0
 
    for i in range(1, len(str)):
        if (not((str[i] >= '0' and str[i] <= '9') or (str[i] >= 'a' and str[i] <= 'f') or (str[i] >= 'A' or str[i] <= 'F'))):
            return 0
 
    return True
def verifyColor(Colour):
    if Colour:
        colorString = Colour
        print(colorString)
        valid = isValidHexaCode(colorString)
        colorString = colorString.replace("#", "")
        if valid:
            colorString = int(colorString,16)
            colorString = discord.Colour(colorString)
            Colour = colorString
        else:
            Colour = 0x585d66
    else:
        Colour = 0x585d66
    return Colour