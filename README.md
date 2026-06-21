# SYANATY Backend

Python (FastAPI) backend connecting the SYANATY app to Supabase for real
cross-device cloud sync.

## Files

| File | Purpose |
|---|---|
| `main.py` | All API endpoints (auth, cars, parts, history, expenses) |
| `models.py` | Request/response data shapes (validation) |
| `database.py` | Supabase client setup |
| `sql/schema.sql` | Database tables + Row Level Security (already run in Supabase) |
| `requirements.txt` | Python package list |
| `.env` | Your Supabase credentials (keep private, don't commit to a public repo) |

## Run it locally (optional, to test before deploying)

Requires Python 3.10+ on your computer.

```bash
cd syanaty-backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open **http://localhost:8000/docs** in a browser — FastAPI gives you a
free interactive page to test every endpoint without writing any code.

## Deploy to Railway.app (free)

1. Push this `syanaty-backend` folder to a **private GitHub repo** (separate
   from your frontend repo). **Do not upload `.env`** — it contains your
   real Supabase key in plain text; secrets go into Railway's dashboard
   instead, never into git.
2. Go to **railway.app** → sign up (GitHub login is easiest)
3. **New Project** → **Deploy from GitHub repo** → select your backend repo
4. Go to your service's **Settings** tab → **Deploy** section →
   **Custom Start Command**, enter:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
   (Railway's auto-detection doesn't know how to run a FastAPI/ASGI app
   without this — it's required, not optional.)
5. Go to the **Variables** tab and add:
   - `SUPABASE_URL` = `https://doviohjmohkcjrsayaim.supabase.co`
   - `SUPABASE_KEY` = (your anon key)
6. Railway redeploys automatically after saving variables
7. Go to **Settings → Networking → Generate Domain** to get a live public URL like:
   ```
   https://syanaty-backend.up.railway.app
   ```

That URL is what the frontend (`index.html`) will call instead of
`localStorage`.

> **Why not Render or PythonAnywhere?** Render works too, but its free tier
> sleeps after 15 minutes of inactivity (slow first request after idling).
> PythonAnywhere's free tier doesn't support FastAPI at all — it only runs
> WSGI apps (Flask/Django), not ASGI apps. Railway supports FastAPI directly
> and was chosen to avoid rewriting working code.

## API Endpoints

All endpoints except `/auth/signup` and `/auth/login` require:
```
Authorization: Bearer <access_token>
```
(the `access_token` returned from signup/login)

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup` | Create account (email, password, name) — also creates a default car |
| POST | `/auth/login` | Log in, returns access + refresh tokens |
| POST | `/auth/refresh` | Get a new access token using a refresh token |
| GET | `/cars` | List the user's cars |
| POST | `/cars` | Create a car |
| PATCH | `/cars/{id}` | Update a car (name, year, emoji, odometer) |
| DELETE | `/cars/{id}` | Delete a car |
| GET | `/parts?car_id=` | List parts catalog for a car |
| POST | `/parts` | Add a part |
| PATCH | `/parts/{id}` | Edit a part (e.g. mark as replaced) |
| DELETE | `/parts/{id}` | Delete a part |
| GET | `/history?car_id=` | List maintenance history |
| POST | `/history` | Add a history record |
| PATCH | `/history/{id}` | Edit a record |
| DELETE | `/history/{id}` | Delete a record |
| GET | `/expenses?car_id=&month=YYYY-MM` | List a month's transactions |
| POST | `/expenses` | Add a fuel/maintenance expense |
| DELETE | `/expenses/{id}` | Delete an expense |

## Security Notes

- The **anon key** is safe in this `.env` and safe to eventually put in the
  frontend too — it has almost no power on its own. **Row Level Security**
  (already enabled in `sql/schema.sql`) is what actually protects user data:
  even with the anon key, nobody can read or write another user's rows.
- Every endpoint validates the user's `access_token` with Supabase before
  touching the database — there's no way to call the API as a different
  user without their real password-derived token.
- Never put the **service_role** / **secret** key in this file or in any
  frontend code. It bypasses Row Level Security entirely.
