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
PDFS_PER_TOPIC = 25
MAX_TEXT_CHUNK = 50000 

def get_all_topics():
    try:
        with open(TOPICS_FILE, 'r') as f:
            return [l.strip() for l in f.readlines() if l.strip()]
    except FileNotFoundError:
        print("❌ Error: topics.txt not found!")
        sys.exit(1)

def search_pdfs(topic, limit=50):
    print(f"🔍 Hunting PDFs for: {topic}...")
    pdf_links = []
    
    # Strategy: Loose Search + Client-Side Filter
    # We ask for "topic pdf" instead of "filetype:pdf" to avoid bot detection
    queries = [f"{topic} pdf", f"{topic} documentation pdf", f"{topic} whitepaper pdf"]
    
    try:
        with DDGS() as ddgs:
            for query in queries:
                print(f"   👉 Trying Query: '{query}'")
                # Request MORE results (100) so we can filter them ourselves
                results = ddgs.text(query, max_results=100)
                
                for r in results:
                    url = r.get('href', '')
                    # MANUAL FILTER: We check the extension ourselves
                    if url.lower().endswith('.pdf'):
                        if url not in pdf_links:
                            pdf_links.append(url)
                            
                if len(pdf_links) >= limit:
                    break
                    
    except Exception as e:
        print(f"   ⚠️ Search error: {e}")

    print(f"✅ Found {len(pdf_links)} unique PDFs.")
    return pdf_links[:limit]

def extract_text_from_pdf_url(url):
    try:
        print(f"⬇️ Downloading: {url}")
        # Fake User-Agent to look like a Browser, not a Bot
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/pdf'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        f = io.BytesIO(response.content)
        reader = PdfReader(f)
        text = ""
        # Cap at 30 pages to prevent memory crash
        for i, page in enumerate(reader.pages):
            if i > 30: break 
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        return text
    except Exception as e:
        # Suppress massive error logs
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
            r = requests.post(SOI_BACKEND_URL, json=payload, timeout=30)
            if r.status_code == 200:
                success_count += 1
                print(f"   🧠 Chunk {i+1}/{len(chunks)} digested.")
        except Exception as e:
            print(f"   ❌ Network Error feeding SOI: {e}")
            
    return success_count

def main():
    topics = get_all_topics()
    
    # Retry Loop (3 Attempts)
    for attempt in range(3):
        target_topic = random.choice(topics)
        print(f"\n🎯 MISSION TARGET (Attempt {attempt+1}/3): {target_topic}")
        
        pdf_urls = search_pdfs(target_topic)
        
        if not pdf_urls:
            print("❌ No PDFs found. Retrying new topic...")
            continue
            
        processed = 0
        for url in pdf_urls:
            text = extract_text_from_pdf_url(url)
            if text and len(text) > 1000: # Ignore tiny PDFs
                print(f"   📄 Extracted {len(text)} chars. Feeding Brain...")
                if feed_soi(target_topic, text) > 0:
                    processed += 1
                time.sleep(1) # Be polite
            
            if processed >= 5: # Limit to 5 PDFs per run to be safe
                print("🏁 Batch Complete.")
                sys.exit(0)
        
        if processed > 0:
            sys.exit(0)
            
    print("💀 Failed to feed SOI after 3 attempts.")
    sys.exit(1)

if __name__ == "__main__":
    main()