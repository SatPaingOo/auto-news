# Auto News Fetcher with Gemini API and Google Sheets

This project automatically fetches news using the Gemini API and saves the results to Google Sheets. It is scheduled to run via GitHub Actions.

## Features

- Fetches news from Gemini API
- Saves news data to Google Sheets
- Runs automatically on a schedule using GitHub Actions

## Setup

1. Add your Gemini API key and Google Sheets credentials to GitHub repository secrets.
2. Configure the Google Sheet for data storage.
3. Edit the script as needed for your news source and sheet structure.

## Usage

- The workflow runs automatically based on the schedule defined in `.github/workflows/news_fetch.yml`.
- You can also trigger it manually from the Actions tab.

## Files

- `news_fetcher.py`: Main script to fetch and save news
- `.github/workflows/news_fetch.yml`: GitHub Actions workflow

## Requirements

- Python 3.8+
- `requests`, `google-auth`, `gspread` (installed automatically)

## License

MIT
