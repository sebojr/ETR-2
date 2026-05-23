import requests
import pandas as pd
import time
import hashlib
import re

# =========================================================
# CONFIG
# =========================================================

TARGET_COUNT = 2000
DELAY = 5

# =========================================================
# ANONYMIZER
# =========================================================

def anonymize_user(username):
    if not username or username == "[deleted]":
        return "Anonymous"

    return "User_" + hashlib.md5(username.encode()).hexdigest()[:8]

# =========================================================
# TEXT CLEANER
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = text.lower()

    # remove links
    text = re.sub(r"http\S+", "", text)

    # remove special characters
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =========================================================
# HASH GENERATOR
# =========================================================

def make_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

# =========================================================
# MAIN SCRAPER
# =========================================================

def scrape_reddit_topics(target_count=2000):

    queries = [
        "Robin Padilla depression",
        "Robin Padilla mental health",
        "Robin Padilla teens weak",
        "mental health stigma Philippines",
        "Filipino teens depression",
        "Robin Padilla statement",
        "mental health awareness Philippines"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    all_posts = []

    posts_per_query = target_count // len(queries) + 1

    print(f"Scraping ~{target_count} posts across Robin Padilla mental health topics...")

    # =====================================================
    # LOOP THROUGH QUERIES
    # =====================================================

    for query in queries:

        after = None
        collected_for_query = 0
        rate_limit_count = 0

        while collected_for_query < posts_per_query:

            url = f"https://www.reddit.com/search.json?q={query}&sort=new&limit=100"

            if after:
                url += f"&after={after}"

            try:

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=15
                )

                # =================================================
                # RATE LIMIT HANDLING
                # =================================================

                if response.status_code != 200:

                    rate_limit_count += 1

                    print(f"Rate limited on '{query}' | Attempt {rate_limit_count}")

                    time.sleep(15)

                    if rate_limit_count >= 5:
                        print(f"Skipping query: {query}")
                        break

                    continue

                data = response.json()

                children = data.get("data", {}).get("children", [])

                if not children:
                    break

                # =============================================
                # PROCESS POSTS
                # =============================================

                for post in children:

                    post_data = post["data"]

                    title = clean_text(
                        post_data.get("title", "")
                    )

                    text = clean_text(
                        post_data.get("selftext", "")
                    )

                    # combine title + text
                    combined_content = f"{title} {text}".strip()

                    # skip very short posts
                    if len(combined_content) < 20:
                        continue

                    content_hash = make_hash(combined_content)

                    post_info = {

                        "Query_Topic": query,

                        "Content": combined_content,

                        "Subreddit": post_data.get("subreddit", ""),

                        "Score": post_data.get("score", 0),

                        "Num_Comments": post_data.get("num_comments", 0),

                        "URL": post_data.get("url", ""),

                        "Author": anonymize_user(
                            post_data.get("author", "")
                        ),

                        "Hash": content_hash
                    }

                    all_posts.append(post_info)

                    collected_for_query += 1

                    if len(all_posts) >= target_count:
                        break

                after = data.get("data", {}).get("after")

                if not after:
                    break

                time.sleep(DELAY)

            except Exception as e:

                print(f"Error on query '{query}': {e}")

                break

        if len(all_posts) >= target_count:
            break

    # =====================================================
    # CREATE DATAFRAME
    # =====================================================

    df = pd.DataFrame(all_posts)

    print("\nColumns Found:")
    print(df.columns.tolist())

    print(f"\nRows before deduplication: {len(df)}")

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

    if "Hash" in df.columns:
        df = df.drop_duplicates(subset=["Hash"])

    # remove empty content
    df = df.dropna(subset=["Content"])

    # remove short rows
    df = df[df["Content"].str.len() > 20]

    print(f"Rows after deduplication: {len(df)}")

    # =====================================================
    # SAVE CSV
    # =====================================================

    filename = "cleaned_robin_padilla_dataset.csv"

    df.to_csv(
        filename,
        index=False,
        encoding="utf-8"
    )

    print(f"\nDataset saved as: {filename}")

# =========================================================
# RUN PROGRAM
# =========================================================

if __name__ == "__main__":
    scrape_reddit_topics(target_count=2000)