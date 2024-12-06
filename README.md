
# Ladsbot

Provides live updates on Dota tournaments.

All commands below require admin privileges to use. 
You can use these commands in any text channel for any server LadsBot is in. 
Once a tournament is being tracked, it’ll check for updates every 15 minutes. 

LadsBot looks for completed series on the series page on Dotabuff. Each Dotabuff series page has 20 series per page, so on initial setup of an ongoing tournament, expect up to 20 messages posted on the first update. 








## Installation

```
  1. Clone the repo
  2. Open the project in VSC
  3. Open the terminal and install required modules: pip install -r requirements.txt
  4. In tokens.py, acquire and place your api tokens for discord and stratz. 
  5. In the terminal, run: python dotabot.py
  6. If it runs, then you're all set! 
```
    
## Terminology

Below are what you need in order to run these commands:

TournamentID: The ID of the tournament. Found on Dotabuff.
![](https://i.imgur.com/3eK0qak.png)

ChannelID: The channel in which you want the discord bot to make the notifications. You can find this by right clicking any channel in your discord server and hitting “Copy Channel ID” 


![alt text](https://i.imgur.com/s9OPcGH.png)

URL: The Dotabuff url of the series page for the tournament.
![](https://imgur.com/ghpdHX0.png)


Message: The message that the bot will say when it posts a series. 
![](https://imgur.com/lQyHOcE.png)
ImageURL: The url for the image that’ll appear in the posts.

Color: The hex value of the color for the embed that’ll appear in the posts. Ex: #eb4034


## Commands

```
!TrackTournament !tracktournament !tt !TT
Sets up a tournament to be tracked in a specific channel. For initial setup, you need to provide the URL. 
If you want to add/switch the channels for announcements afterwards, you can use this command without the URL argument.
 
Usage: 
!TrackTournament <TournamentID> <ChannelID> <URL>
!TrackTournament <TournamentID> <ChannelID> 


```
![](https://i.imgur.com/c1mSMJB.png)

```
!SetTournamentMessage !settournamentmessage !stm !STM
Sets up the message notification whenever a new series is posted for that tournament.
Usage: !SetTournamentMessage <TournamentID> <Message>
```
![](https://i.imgur.com/58P3KGP.png)
```
!SetTournamentEmbed !settournamentembed !ste !STE
Sets up the embed image and color for the tournament.
Usage: !SetTournamentEmbed <TournamentID> <ImageURL> <Color>
```
![](https://i.imgur.com/VULyvbs.png)


```
!RemoveTournament !removetournament !rt !RT
Removes a tournament from being tracked.
Usage: !RemoveTournament <TournamentID>
```
![](https://i.imgur.com/hjmNL9d.png)
```
!RemoveChannel !removechannel !rc !RC
Removes a tournament channel from tracking games.
Usage: !RemoveChannel <TournamentID> <ChannelID>
```
![](https://i.imgur.com/KmyS4kA.png)

## Example

Below is an example for setting up the League of Lads S4 tournament to create notifications 
```
!TrackTournament 17352 1277813986900971520 https://www.dotabuff.com/esports/leagues/17352-league-of-lads-plus-s4/series
!SetTournamentMessage 17352 New Lads Plus Series Listed!
!SetTournamentEmbed 17352 https://i.imgur.com/PnLk1JL.png #40277E
!SetTournamentMode 17352 bo3
```