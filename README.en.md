# 🔖 Twitter Bookmarks → Notion Auto-Organizer

A tool that automatically collects your Twitter(X) bookmarks, categorizes them by keyword, and saves them to a Notion database.  
Built with vibe coding.

---

## ✨ What does it do?

- Fetches all your Twitter bookmarks at once
- Automatically categorizes them by keyword
- Saves them to a Notion database for easy search & filtering
- On subsequent runs, only fetches newly added bookmarks (no duplicates)
- If you have an AI API key, it can re-classify anything that landed in "Other"

---

## 📋 Requirements

| Item | Required | Notes |
|------|----------|-------|
| Windows PC | Required | |
| Python 3.8+ | Required | See installation below |
| Twitter(X) account | Required | Must be logged in |
| Notion account | Required | |
| OpenAI or Gemini API key | Optional | Only needed for AI re-classification |

---

## 🚀 Installation & Setup

### Step 1. Install Python

Skip this step if Python is already installed.

1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.x.x"
3. Run the installer

> ⚠️ **Important:** Check **"Add Python to PATH"** at the bottom of the installer screen!

---

### Step 2. Download files

Click **Code → Download ZIP** at the top right of this page, then extract the archive.

> ⚠️ **If Windows blocks the file as "unsafe":** Right-click the zip → **Properties** → check **"Unblock"** at the bottom → OK. Then extract.

---

### Step 3. Initial setup (one time only)

Double-click **`setup.bat`** inside the extracted folder.

It will guide you through entering the required values one by one.

---

#### 🐦 How to get your Twitter tokens

> These are cookie values that keep you logged in. Do not share them with anyone.

1. Log in to **x.com** on Chrome or Edge
2. Press **F12** to open Developer Tools
3. Click the **Application** tab
4. Left sidebar: **Cookies** → **https://x.com**
5. Find **`ct0`** in the list and copy its Value
6. Find **`auth_token`** in the list and copy its Value

> 💡 If your tokens expire (after logout or password change), just re-run `setup.bat` to update them.

---

#### 📝 How to get your Notion token

1. Go to https://www.notion.so/my-integrations (Notion login required)
2. Click **"+ Create new integration"**
3. Enter any name (e.g. `TwitterBookmarks`) → **Submit**
4. Click **Show** next to **"Internal Integration Secret"** → copy the value

---

#### 📄 How to get your Notion page ID

You need a Notion page where the bookmark database will be created. You can create a new one.

1. Open the target page in Notion
2. Click **`...`** in the top-right corner
3. **Connections** → click your integration name to connect it
4. Check the URL in your browser:
   ```
   https://www.notion.so/page-name-abc123def456abc123def456abc123de
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                   These 32 characters are the page ID
   ```

---

### Step 4. Run

After setup, just double-click **`run.bat`** every time.

```
====================================================
  Twitter Bookmark Pipeline
====================================================

  1. Sync bookmarks   (fetch new bookmarks from Twitter)
  2. Classify         (auto-categorize bookmarks)
  3. Notion upload    (save to Notion DB)
  4. Run all          (1 → 2 → 3 at once)
  5. AI reclassify    (reclassify 'Other' with OpenAI/Gemini)
  6. Full reclassify  (reset classifications and start over)
  0. Quit
```

First time? Select **4 (Run all)**. After that, running 4 periodically will only add new bookmarks.

---

## 📁 Categories — default settings, add keywords to expand each category

| Category | Description |
|----------|-------------|
| Beauty & Skincare | Skincare routines, makeup, haircare, etc. |
| Fitness & Diet | Home workouts, exercise routines, diet tips |
| Study & Learning | Study methods, exam prep, learning resources |
| Humor & Memes | Funny tweets, memes, relatable content |
| Fashion & Style | Outfit recommendations, lookbooks, shopping |
| Art & Illustration | Drawing tips, coloring tutorials, art references (KO/EN/JA) |
| Cooking & Recipes | Easy recipes, meal prep, home cooking |
| Life Tips & Info | Life hacks, useful information, practical tips |
| Tech & Tools | AI tools, coding, automation, development |
| Motivation & Quotes | Quotes, self-improvement, inspirational content |
| Fandom & Fan culture | Fan art, cosplay, idols, anime, 2D/3D content |
| Other | Anything that doesn't fit the above |

Default keywords are pre-configured. Open `categories.json` with a text editor to add more keywords to any category.

---

## 🤖 AI Re-classification (optional)

If many tweets end up in "Other," AI can take another pass at classifying them.  
**You only need one of OpenAI or Gemini.** Everything else works without it.

- Get OpenAI key: https://platform.openai.com/api-keys
- Get Gemini key: https://aistudio.google.com/app/apikey

Re-run `setup.bat` to enter your key, or open the `.env` file in a text editor and add it directly:

```
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
```

---

## ❓ FAQ

**Q. I get "python is not recognized as an internal or external command..."**  
→ You didn't check "Add Python to PATH" during installation. Uninstall Python and reinstall, making sure to check that box.

**Q. Token error / bookmarks won't load**  
→ Logging out of Twitter or changing your password invalidates the tokens. Re-run `setup.bat` to enter new ones.

**Q. Notion upload isn't working**  
→ Make sure your Integration is connected to the Notion page. (Page `...` menu → Connections)

**Q. Old bookmarks are being uploaded again**  
→ The `uploaded_ids.json` file tracks what's been uploaded. If it gets deleted, duplicates will appear. Don't delete this file.

**Q. I entered an AI key but getting an error**  
→ Open `.env` in a text editor and check that `OPENAI_API_KEY` or `GEMINI_API_KEY` is correct. No spaces or quotes around the value.

---

## 📂 File structure

All files must be in **the same folder**.

```
twitter-bookmark-notion/
├── setup.bat                  ← Initial setup (run once)
├── run.bat                    ← Run this every time
├── setup_wizard.py            Setup wizard (called by setup.bat)
├── run_menu.py                Main menu (called by run.bat)
├── bookmark_sync.py           Twitter bookmark fetcher
├── classify_bookmarks.py      Keyword-based auto classifier
├── reclassify_ai.py           AI re-classifier (OpenAI/Gemini)
├── setup_and_upload.py        Notion DB creation & upload
├── categories.json            Category & keyword configuration
│
│   ← Files below are auto-generated (do not touch)
├── .env                       Saved tokens
├── bookmarks.jsonl            Fetched bookmarks
├── classified_bookmarks.jsonl Classified bookmarks
├── uploaded_ids.json          Notion upload log (deleting causes duplicates)
└── notion_db_id.txt           Generated Notion DB ID
```

---

## ⚠️ Notes

- This tool uses Twitter's internal API. It may stop working if Twitter changes their API.
- Your Twitter tokens (`ct0`, `auth_token`) are equivalent to your login credentials. Never share your `.env` file or upload it to GitHub.
- For personal use only.

---

## 📜 License

MIT License — free for personal and non-commercial use.  
made by [@ryuri-r](https://github.com/ryuri-r)
