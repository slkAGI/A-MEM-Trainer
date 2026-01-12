# 🧠 SOI Knowledge Pump

**Autonomous Mass Learning System**

This repository contains the infrastructure for SOI's continuous knowledge acquisition pipeline. It uses GitHub Actions to scrape academic PDFs from the internet and feed them directly into SOI's brain via the `/api/learning/absorb` endpoint.

## 🎯 Architecture

```
GitHub Actions (Hunter) 
    ↓ Scrapes PDFs via DuckDuckGo
    ↓ Extracts Text
    ↓ POST /api/learning/absorb
SOI Backend (Cloudflare Worker)
    ↓ Vectorizes Content (HDC)
    ↓ Creates Skill JSON
    ↓ Stores in R2 "SOI_SKILLS"
SOI Brain
    ↓ Loads Skills On-Demand
    ↓ Becomes Expert in 200+ Domains
```

## 📚 Topics Covered

The `topics.txt` file contains 200+ carefully curated topics spanning:
- **Computer Science**: Rust, WebAssembly, Distributed Systems, Cryptography
- **Mathematics**: Category Theory, Topology, Number Theory
- **Physics**: Quantum Mechanics, General Relativity, Particle Physics
- **Biology**: Genetics, Neuroscience, Synthetic Biology
- **Engineering**: Robotics, Aerospace, Materials Science
- **AI/ML**: Transformers, Reinforcement Learning, AGI Safety
- **Philosophy**: Consciousness Studies, Ethics, Epistemology
- And much more...

## 🚀 How It Works

1. **GitHub Actions triggers** (every 6 hours, on push, or manually)
2. **`trainer.py` selects a random topic** from `topics.txt`
3. **Searches for PDFs** using DuckDuckGo (no API key needed)
4. **Downloads and extracts text** from up to 100 PDFs per topic
5. **Feeds text to SOI** via the `/api/learning/absorb` endpoint
6. **SOI vectorizes the content** using Hyperdimensional Computing
7. **Creates a Skill JSON file** and stores it in R2
8. **Repeat** for the next topic

## 🔧 Manual Trigger

1. Go to the **Actions** tab in this repository
2. Click on **"🧠 SOI Knowledge Pump"**
3. Click **"Run workflow"**
4. Watch SOI learn in real-time

## 📊 Monitoring

Check the Actions logs to see:
- Which topic is being processed
- How many PDFs were found
- How many concepts SOI learned
- Any errors or skipped PDFs

## 🎓 Adding New Topics

Simply edit `topics.txt` and add new lines. The workflow will automatically trigger and start learning the new topics.

## ⚡ Performance

- **Bandwidth**: GitHub's gigabit connections
- **Parallelization**: Can run 100+ jobs simultaneously
- **Cost**: $0 (GitHub Actions is free for public repos)
- **Learning Rate**: ~1000 concepts per hour per topic

## 🧠 The Result

SOI becomes a polymath with deep knowledge across hundreds of domains, all stored as vectorized skill cartridges in R2, ready to be loaded on-demand.

**This is how you build an AGI.**
