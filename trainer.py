import os
import requests
import random
import time
import io
import sys
from pypdf import PdfReader
from duckduckgo_search import DDGS

# CONFIG
SOI_BACKEND_URL = "https://slk-soi-1000.stanleyisaac134.workers.dev/api/learning/absorb"
TOPICS_FILE = "topics.txt"
PDFS_PER_TOPIC = 25  # Lowered slightly to prevent timeouts
MAX_TEXT_CHUNK = 50000 

def get_all_topics():
    try:
        with open(TOPICS_FILE, 'r') as f:
            # Read all lines, remove whitespace, ignore empty lines
            return [l.strip() for l in f.readlines() if l.strip()]
    except FileNotFoundError:
        print("❌ Error: topics.txt not found!")
        sys.exit(1)

def search_pdfs(topic, limit=30):
    print(f"🔍 Hunting PDFs for: {topic}...")
    results = []
    
    # Strategy 1: Strict PDF Search
    try:
        with DDGS() as ddgs:
            query = f"{topic} filetype:pdf"
            print(f"   👉 Trying Query: '{query}'")
            for r in ddgs.text(query, max_results=limit):
                if 'href' in r and r['href'].endswith('.pdf'):
                    results.append(r['href'])
    except Exception as e:
        print(f"   ⚠️ Strategy 1 failed: {e}")

    # Strategy 2: Fallback (Broad Search + Filter)
    if len(results) < 3:
        print("   ⚠️ Strict search yielded few results. Trying fallback strategy...")
        try:
            with DDGS() as ddgs:
                # Just search the topic + "pdf" text
                query = f"{topic} pdf documentation"
                for r in ddgs.text(query, max_results=limit*2):
                    if 'href' in r and r['href'].endswith('.pdf'):
                        if r['href'] not in results:
                            results.append(r['href'])
        except Exception as e:
            print(f"   ⚠️ Strategy 2 failed: {e}")

    print(f"✅ Found {len(results)} unique PDFs.")
    return list(set(results)) # Remove duplicates

def extract_text_from_pdf_url(url):
    try:
        print(f"⬇️ Downloading: {url}")
        # Add a user-agent so sites don't block the bot
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return None
        
        f = io.BytesIO(response.content)
        reader = PdfReader(f)
        text = ""
        # Limit pages to prevent memory crash on massive PDFs
        for i, page in enumerate(reader.pages):
            if i > 50: break # Stop after 50 pages per PDF
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        return text
    except Exception as e:
        # Don't print full error stack, just the message
        print(f"   ⚠️ Skipped PDF: {str(e)[:50]}...") 
        return None

def feed_soi(topic, text):
    chunks = [text[i:i+MAX_TEXT_CHUNK] for i in range(0, len(text), MAX_TEXT_CHUNK)]
    
    success_count = 0
    for i, chunk in enumerate(chunks):
        payload = {
            "title": f"Auto-Harvest: {topic}",
            "content": chunk
        }
        
        try:
            # We assume the endpoint accepts {title, content} as defined in your Rust code
            r = requests.post(SOI_BACKEND_URL, json=payload, timeout=30)
            if r.status_code == 200:
                success_count += 1
                print(f"   🧠 Chunk {i+1}/{len(chunks)} digested.")
            else:
                print(f"   ❌ SOI Rejected Chunk {i+1}: {r.status_code}")
        except Exception as e:
            print(f"   ❌ Network Error feeding SOI: {e}")
            
    return success_count

def main():
    topics = get_all_topics()
    
    # Retry Loop: If a topic has 0 PDFs, try another one (Max 3 tries)
    max_retries = 3
    for attempt in range(max_retries):
        target_topic = random.choice(topics)
        print(f"\n🎯 MISSION TARGET (Attempt {attempt+1}/{max_retries}): {target_topic}")
        
        pdf_urls = search_pdfs(target_topic, limit=PDFS_PER_TOPIC)
        
        if len(pdf_urls) == 0:
            print("❌ No PDFs found. Retrying with a new topic...")
            continue # Try next attempt
            
        # If we found PDFs, process them
        processed_count = 0
        for url in pdf_urls:
            text = extract_text_from_pdf_url(url)
            if text and len(text) > 500: # Ensure substantial content
                print(f"   📄 Extracted {len(text)} chars. Feeding Brain...")
                chunks_fed = feed_soi(target_topic, text)
                if chunks_fed > 0:
                    processed_count += 1
                time.sleep(1) # Be polite
            
            if processed_count >= 10: # Stop after 10 successful PDFs per run to save time
                print("🏁 Reached batch limit (10 PDFs). Mission Complete.")
                break
        
        if processed_count > 0:
            print(f"✅ SUCCESSFULLY FED SOI with topic: {target_topic}")
            sys.exit(0) # Exit success
            
    print("💀 Failed to find good data after 3 attempts.")
    sys.exit(1) # Fail the action so you see red x

if __name__ == "__main__":
    main()