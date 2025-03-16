import os
import requests
import asyncio
import aiohttp
import pandas as pd
import sys
import termios
import tty
from bs4 import BeautifulSoup
from tqdm import tqdm

# Target URL
URL = "https://editorial.rottentomatoes.com/guide/popular-movies/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0 Safari/537.36"
}

DATA_CSV = "popular_movies.csv"
DATA_JSON = "popular_movies.json"
PAGE_SIZE = 10  # Number of records per page

def clear_screen():
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")

async def fetch_page(session, url):
    """Fetch HTML content of a webpage asynchronously."""
    async with session.get(url, headers=HEADERS) as response:
        return await response.text()

async def scrape_movies():
    """Mines Rotten Tomatoes' Popular Movies List asynchronously."""
    async with aiohttp.ClientSession() as session:
        html = await fetch_page(session, URL)

    soup = BeautifulSoup(html, "html.parser")
    movies = []

    for movie in tqdm(soup.select(".article_movie_title"), desc="Mining Movies"):
        title = movie.get_text(strip=True)
        score_tag = movie.find_next("span", class_="tMeterScore")
        score = score_tag.get_text(strip=True).replace("%", "") if score_tag else "0"

        try:
            score = int(score)
        except ValueError:
            score = 0  # Handle missing or incorrect scores

        movies.append({"Title": title, "Score": score})

    # Sort movies score (highest to lowest)
    movies = sorted(movies, key=lambda x: x["Score"], reverse=True)

    return movies

def save_data(movies):
    """Saves movie data to CSV and JSON files."""
    df = pd.DataFrame(movies)
    
    df.to_csv(DATA_CSV, index=False)
    df.to_json(DATA_JSON, orient="records", indent=4)

    print(f"\n✅ Data saved successfully as '{DATA_CSV}' and '{DATA_JSON}'.")

def get_keypress():
    """Captures keyboard input for smooth navigation."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

def view_records():
    """Displays extracted movie data with arrow key navigation."""
    if not os.path.exists(DATA_CSV):
        print("\n⚠️ No data found! Please run the scraper first.\n")
        return

    df = pd.read_csv(DATA_CSV)
    df = df.sort_values(by="Score", ascending=False)  # Ensure sorting

    total_movies = len(df)
    current_page = 0

    while True:
        clear_screen()
        print("\n🎬 Extracted Movies (Sorted Best Score First) 🎬 (Page {}/{})\n".format(current_page + 1, (total_movies // PAGE_SIZE) + 1))
        print(f"{'Title':<40}{'Score':<20}")
        print("=" * 60)

        start_idx = current_page * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, total_movies)

        for _, row in df.iloc[start_idx:end_idx].iterrows():
            print(f"{row['Title'][:38]:<40}{row['Score']}%")

        print("\n🔼 (↑ Arrow Key) Page Up  🔽 (↓ Arrow Key) Page Down  ⏎ (Enter to return to menu)")

        key = get_keypress()

        if key == "\x1b":  # Detect arrow keys
            key += get_keypress()
            key += get_keypress()
            if key == "\x1b[A" and current_page > 0:  # Up Arrow (Page Up)
                current_page -= 1
            elif key == "\x1b[B" and end_idx < total_movies:  # Down Arrow (Page Down)
                current_page += 1
        elif key == "\r":  # Enter Key to return to menu
            break

def main():
    """Main menu loop."""
    while True:
        clear_screen()
        print("\n🚀 Movies Data Mining Tool 🚀\n")
        print("")
        print("1️⃣  Start Data Mining (Rotten Tomatoes New Release Movies)")
        print("")
        print("2️⃣  View Extracted Records (Sorted Best Score first)")
        print("")
        print("3️⃣  Exit")
        print("")

        choice = input("\n Select an option (1-3): ").strip()

        if choice == "1":
            clear_screen()
            print("\n⏳ **Starting Web Data Mining..**\n")
            movies = asyncio.run(scrape_movies())

            if movies:
                print(f"\n✅ Successfully mined {len(movies)} movies!\n")
                save_data(movies)
            input("\n🔄 Press Enter to return to the menu...")
        
        elif choice == "2":
            clear_screen()
            view_records()
            input("\n🔄 Press Enter to return to the menu...")

        elif choice == "3":
            print("\n Exiting program. Have a great day!\n")
            break
        
        else:
            print("\n⚠️ Invalid choice. Please enter a number between 1 and 3.")

if __name__ == "__main__":
    main()

