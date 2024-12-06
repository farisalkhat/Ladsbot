from pathlib import Path
import json

completed_series = Path(__file__).parent / "../db/completed_series.json"
last_match_date = Path(__file__).parent / "../db/last_match_date.json"
tournament_tracker = Path(__file__).parent / "../db/tournament_tracker.json"

async def load_series(self):
    with completed_series.open() as f:
        self.completed_series = json.load(f)

async def save_series(self):
    with completed_series.open('w') as f:
        json.dump(self.completed_series,f,indent=4)

async def load_last_match_date(self):
    with last_match_date.open() as f:
        self.last_match_date = json.load(f)

async def save_last_match_date(self):
    with last_match_date.open('w') as f:
        json.dump(self.last_match_date,f,indent=4)

async def load_tournament_tracker(self):
    with tournament_tracker.open() as f:
        self.tournament_tracker = json.load(f)

async def save_tournament_tracker(self):
    with tournament_tracker.open('w') as f:
        json.dump(self.tournament_tracker,f,indent=4)


