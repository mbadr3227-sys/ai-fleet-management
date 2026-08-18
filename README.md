# AI Fleet Management

A Flask application for managing a small vehicle fleet — drivers, vans, daily
allocations, and availability — with an AI assistant that answers questions
about the fleet in plain English.

## The AI assistant

Most "AI features" bolted onto CRUD apps forward the user's question straight
to a language model and hope for the best. This one doesn't.

When a question comes in, the app first queries the database for the current
fleet state — how many drivers and vans exist, which vans are assigned today,
which are still free — and passes that as context alongside the question. The
model answers from real data rather than from whatever it happens to
remember.

Ask *"how many vans are available today?"* and the answer reflects the actual
allocation table, not a guess.

## Features

| Area | What it does |
|---|---|
| Drivers | Add, edit, and remove drivers with contact details and licence class |
| Vans | Register vehicles and track their status |
| Availability | Record which drivers are working which days |
| Driver portal | Drivers log in, claim an available van for the day, and leave notes |
| Allocations | See today's assignments, or search the history by date |
| AI assistant | Natural-language questions answered from live database state |

A van already claimed for today is filtered out of the available list, so two
drivers can't book the same vehicle.

## Running it

```bash
pip install -r requirements.txt
cp .env.example .env        # then add your OpenAI API key
python app.py
```

The app runs on `http://127.0.0.1:5000`. The database is created and seeded
with sample drivers and vans on first run — no setup step required.

The AI assistant needs an OpenAI API key. Without one the rest of the
application still works; only that page reports the missing key.

## Built with

Python · Flask · SQLite · OpenAI API · Jinja2

## Notes

All database queries are parameterised rather than string-formatted, so user
input can't alter the shape of a query.

The driver portal uses a simple email plus ID check and is not intended as
production authentication — it exists to demonstrate the allocation workflow
from the driver's side.