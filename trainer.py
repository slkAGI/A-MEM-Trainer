import os
import requests
import random
import time
import io
import sys
import arxiv
import wikipedia
from pypdf import PdfReader

# CONFIG
SOI_BACKEND_URL = "https://slk-soi-1000.stanleyisaac134.workers.dev/api/learning/absorb"
TOPICS_FILE = "topics.txt"
MAX_TEXT_CHUNK = 50000 

def get_all_topics():
    try:
        with open(TOPICS_FILE, 'r') as f:
            return [l.strip() for l in f.readlines() if l.strip()]
    except FileNotFoundError:
        print("❌ Error: topics.txt not found!")
        sys.exit(1)

def feed_soi(topic, text, source_type):
    chunks = [text[i:i+MAX_TEXT_CHUNK] for i in range(0, len(text), MAX_TEXT_CHUNK)]
    success_count = 0
    
    for i, chunk in enumerate(chunks):
        payload = {
            "title": f"Auto-Harvest: {topic} ({source_type})",
            "content": chunk
        }
        try:
            r = requests.post(SOI_BACKEND_URL, json=payload, timeout=30)
            if r.status_code == 200:
                success_count += 1
                print(f"   🧠 Chunk {i+1}/{len(chunks)} digested.")
            else:
                print(f"   ❌ SOI Rejected Chunk {i+1}: {r.status_code}")
        except Exception as e:
            print(f"   ❌ Network Error feeding SOI: {e}")
            
    return success_count

# --- STRATEGY 1: ARXIV (Scientific Papers) ---
def hunt_arxiv(topic):
    print(f"🔬 Searching ArXiv for: {topic}...")
    client = arxiv.Client()
    search = arxiv.Search(
        query = topic,
        max_results = 100,
        sort_by = arxiv.SortCriterion.Relevance
    )

    results = []
    try:
        for r in client.results(search):
            print(f"   📄 Found Paper: {r.title}")
            # Download PDF to memory
            pdf_data = requests.get(r.pdf_url).content
            
            # Extract Text
            f = io.BytesIO(pdf_data)
            reader = PdfReader(f)
            text = ""
            for page in reader.pages[:30]: # Limit to first 30 pages
                extracted = page.extract_text()
                if extracted: text += extracted + "\n"
            
            if len(text) > 1000:
                print(f"   ⬇️ Extracted {len(text)} chars. Feeding...")
                feed_soi(topic, text, "ArXiv Paper")
                results.append(r.title)
                
            time.sleep(1) # Be polite
    except Exception as e:
        print(f"   ⚠️ ArXiv Error: {e}")

    return len(results)

# --- STRATEGY 2: WIKIPEDIA (General Knowledge) ---
def hunt_wikipedia(topic):
    print(f"📚 Searching Wikipedia for: {topic}...")
    try:
        # Get the page
        page = wikipedia.page(topic, auto_suggest=True)
        print(f"   📖 Found Page: {page.title}")
        
        content = page.content
        if len(content) > 1000:
            print(f"   ⬇️ Extracted {len(content)} chars. Feeding...")
            feed_soi(topic, content, "Wikipedia")
            return 1
    except wikipedia.exceptions.DisambiguationError as e:
        # If ambiguous, pick the first option
        try:
            first_option = e.options[0]
            print(f"   twisted path -> {first_option}")
            hunt_wikipedia(first_option)
            return 1
        except:
            return 0
    except Exception as e:
        print(f"   ⚠️ Wikipedia Error: {e}")
    
    return 0

def main():
    topics = get_all_topics()
    
    # Try up to 3 topics if one fails
    for attempt in range(3):
        target_topic = random.choice(topics)
        print(f"\n🎯 MISSION TARGET (Attempt {attempt+1}/3): {target_topic}")
        
        # 1. Try ArXiv (Best for your technical list)
        success_count = hunt_arxiv(target_topic)
        
        if success_count > 0:
            print(f"✅ SUCCESSFULLY FED SOI with {success_count} papers on {target_topic}")
            sys.exit(0)
            
        # 2. If ArXiv empty, Try Wikipedia (Best for general concepts)
        print("   ⚠️ ArXiv yielded nothing. Switching to Wikipedia...")
        if hunt_wikipedia(target_topic) > 0:
            print(f"✅ SUCCESSFULLY FED SOI with Wikipedia entry for {target_topic}")
            sys.exit(0)
            
        print("❌ Both sources failed. Picking new topic...")

    print("💀 Failed to feed SOI after 3 attempts.")
    sys.exit(1)

if __name__ == "__main__":
    main()