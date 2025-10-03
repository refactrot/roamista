
# ROAMISTA: Retrieval-Augmented Landmark and Adaptive Visual Itinerary Storytelling Generation

Roamista is a small toolkit and demo-suite for generating travel blogs and itineraries from images and web-scraped travel content. It combines image metadata extraction, image-to-text description generation, web scraping for travel articles, and LLM-backed blog/itinerary generation. The project contains utilities for collecting data, preparing fine-tuning datasets, and a Streamlit demo app called "VISTA Blog Generator" for interactively creating blog posts from images.

This README gives a quick orientation, setup instructions, and pointers to the main modules so you can run the demo or extend the pipelines.

## Features

- Streamlit demo (`src/vista_app.py`) to upload images, view metadata, and generate a human-like travel blog.
- Image description pipeline (`src/image_to_desc.py`, `src/image_to_blog.py`) which uses OpenAI APIs and image metadata.
- Scraper for collecting travel blog content and images from the web (`cron/dataset_web_scraper.py`).
- Fine-tuning / preprocessing helpers for creating JSONL datasets for LLM fine-tuning (`fine_tuning/preprocessing.py`).
- Utilities for image metadata extraction, AI-detection scoring, and POI extraction.

## Quickstart

Prerequisites

- Python 3.9+ (virtualenv recommended)
- An OpenAI-compatible API key and any other API keys used by the scrapers (e.g., SerpAPI).
- Recommended: create a `.env` file at the repository root with the required keys.

Install dependencies

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Environment variables (.env)

Create a `.env` file (or set environment variables) with at least the following:

- OPENAI_API_KEY (or the provider-specific credentials used by `openai`/`OpenAI` client in code)
- SERP_API_KEY (used by `cron/dataset_web_scraper.py` to fetch Google results via SerpAPI)

Example `.env` (do NOT commit your real keys):

```
OPENAI_API_KEY=sk-xxxx
SERP_API_KEY=xxxx
```

Run the Streamlit demo

```powershell
streamlit run src/vista_app.py
```

Open the UI at the URL Streamlit prints (usually http://localhost:8501). Upload images and click "GENERATE BLOG" to run the pipeline.

Note: the demo and many scripts call external APIs and may incur costs. Use API keys and quotas responsibly.

## Project layout

- `src/` — main Python modules and Streamlit app
	- `vista_app.py` — Streamlit front-end demo for generating blogs from images
	- `image_to_blog.py`, `image_to_desc.py` — image-to-text logic and prompts
	- `image_metadata.py` — helpers to extract EXIF, GPS, timestamps
	- other utilities: `ai_detection.py`, `poi.py`, `itinerary.py`
- `cron/` — scraping and data collection scripts (e.g., `dataset_web_scraper.py`)
- `fine_tuning/` — preprocessing and JSONL creation scripts for fine-tuning
- `testset/` — example images used for local testing
- `requirements.txt` — pinned Python dependencies

## Development notes

- The codebase expects API keys in environment variables or a `.env` file. The `python-dotenv` package is in `requirements.txt`.
- Many modules use OpenAI-style client calls (the repo contains example uses of a `OpenAI()` client). Check the code and update models or client usage to match your account and vendor SDK.
- The scraping scripts (`cron/`) are basic and intended for research/data-collection. Respect robots.txt and website terms of service when scraping. Add polite delays and use rate limits.

Testing and validation

- There's no test harness in the repo currently. For quick validation, try the Streamlit app with the `testset/` images or run `fine_tuning/preprocessing.py` on a small sample to check for errors.

Security & privacy

- This project processes image EXIF metadata which can contain sensitive location and timestamp data. Remove or anonymize EXIF data before sharing results.
- Do not commit API keys to version control. Use `.gitignore` to exclude `.env`.
