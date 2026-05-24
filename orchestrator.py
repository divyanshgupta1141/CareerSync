#!/usr/bin/env python3
"""
Automated Application Orchestrator

This tool scrapes a job description from a URL, compares it against a master resume,
and uses an LLM to generate a tailored resume profile and cold outreach email.
It utilizes a Single-Shot architecture to evaluate matches, extract keywords,
tailor the resume, and write the outreach email in a single OpenRouter API call.

--------------------------------------------------------------------------------
MOCK MASTER RESUME (Divyansh Gupta - AI Engineer)
--------------------------------------------------------------------------------
DIVYANSH GUPTA
San Francisco, CA | divyansh@example.com | +1 (555) 019-2834 | linkedin.com/in/divyansh-gupta | github.com/divyansh-gupta

PROFESSIONAL SUMMARY
Highly skilled and innovative AI Systems Engineer and Python Developer with 4+ years of experience designing, building, and deploying production-ready machine learning models, large language model (LLM) agents, and robust web applications. Expertise in Retrieval-Augmented Generation (RAG) architectures, LLM fine-tuning, agentic workflows, and high-performance backend systems. Proven track record of optimizing model inference, implementing scalable data ingestion pipelines, and delivering developer-centric tools.

TECHNICAL SKILLS
* Programming Languages: Python (Expert), SQL, JavaScript/TypeScript, Bash, HTML/CSS
* AI & Machine Learning: PyTorch, TensorFlow, Hugging Face Transformers, LangChain, LlamaIndex, OpenAI API, Anthropic API, OpenRouter
* Vector Databases & Search: Pinecone, Milvus, ChromaDB, Qdrant, Elasticsearch, pgvector
* Backend & Cloud: FastAPI, Flask, Django, Node.js, AWS (S3, EC2, ECS, Lambda, SageMaker), Docker, Kubernetes, CI/CD (GitHub Actions)
* Frontend: React.js, Next.js, HTML5, CSS3, TailwindCSS
* Developer Tools: Git, VS Code, Postman, Linux, Playwright (Web Scraping/Automation)

PROFESSIONAL EXPERIENCE

Senior AI Engineer | InnovateAI Solutions, San Francisco, CA
June 2024 – Present
* Architected and deployed a multi-agent RAG system using LangChain and pgvector, reducing customer support response time by 45% and achieving a 92% answer accuracy rate.
* Fine-tuned open-source LLMs (Llama-3, Mistral) on domain-specific datasets using QLoRA and PEFT, improving model alignment and performance by 18% on proprietary evaluation benchmarks.
* Optimized LLM inference latency by 30% by containerizing workloads with Docker and deploying them on AWS ECS with auto-scaling configured via GPU metrics.
* Led a team of 3 engineers in building an automated document ingestion pipeline processing 10k+ multi-format files (PDF, HTML, Docx) daily using Playwright and unstructured data parsers.

AI Software Engineer | TechGenix Corp, Austin, TX
August 2022 – May 2024
* Developed backend microservices using FastAPI and PostgreSQL to support real-time data processing for a predictive maintenance IoT dashboard.
* Integrated OpenAI and Anthropic APIs into core SaaS products, developing custom prompt engineering templates and agent chains that increased user engagement by 25%.
* Built automated web scrapers using Playwright and BeautifulSoup to collect market intelligence, handling dynamic JavaScript content and bypassing anti-bot systems.
* Maintained clean, modular, and PEP-8 compliant codebases with 90%+ unit test coverage using pytest.

Junior Software Developer | ByteBuilders Ltd, New Delhi, India
June 2021 – July 2022
* Built and styled responsive web interfaces using React.js and TailwindCSS, collaborating closely with UI/UX designers.
* Designed and optimized complex SQL queries and database schemas in PostgreSQL, improving query execution time by 20%.
* Developed RESTful API endpoints using Flask to support user authentication and file upload functionalities.

PROJECTS

CreatorBazaar Dashboard (Full-Stack AI Project)
* Developed an analytics dashboard for creators, scraping public data using Playwright to track performance metrics across multiple platforms.
* Integrated an LLM-powered content recommendation engine that analyzes creator trends and suggests personalized video topics and script outlines.
* Stack: Python, FastAPI, React, TailwindCSS, PostgreSQL, Playwright.

Auto-Agentic Outreach Pipeline
* Built a local CLI utility that automates outreach by scanning industry forums, extracting key discussions, and generating context-aware response drafts.
* Achieved 95% reduction in manual tracking by storing and matching target contacts using Qdrant vector database.
* Stack: Python, LlamaIndex, Qdrant, OpenRouter API.

EDUCATION

Bachelor of Technology in Computer Science & Engineering
Delhi Technological University (DTU), New Delhi, India | Graduated: May 2021
--------------------------------------------------------------------------------
"""

import os
import re
import sys
import json
import requests
from playwright.sync_api import sync_playwright

# Constants
DEFAULT_MODEL = "gemini-1.5-flash"
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

# Inline mock resume data used as backup/generator if master_resume.txt doesn't exist
MOCK_RESUME_TEXT = """DIVYANSH GUPTA
San Francisco, CA | divyansh@example.com | +1 (555) 019-2834 | linkedin.com/in/divyansh-gupta | github.com/divyansh-gupta

PROFESSIONAL SUMMARY
Highly skilled and innovative AI Systems Engineer and Python Developer with 4+ years of experience designing, building, and deploying production-ready machine learning models, large language model (LLM) agents, and robust web applications. Expertise in Retrieval-Augmented Generation (RAG) architectures, LLM fine-tuning, agentic workflows, and high-performance backend systems. Proven track record of optimizing model inference, implementing scalable data ingestion pipelines, and delivering developer-centric tools.

TECHNICAL SKILLS
* Programming Languages: Python (Expert), SQL, JavaScript/TypeScript, Bash, HTML/CSS
* AI & Machine Learning: PyTorch, TensorFlow, Hugging Face Transformers, LangChain, LlamaIndex, OpenAI API, Anthropic API, OpenRouter
* Vector Databases & Search: Pinecone, Milvus, ChromaDB, Qdrant, Elasticsearch, pgvector
* Backend & Cloud: FastAPI, Flask, Django, Node.js, AWS (S3, EC2, ECS, Lambda, SageMaker), Docker, Kubernetes, CI/CD (GitHub Actions)
* Frontend: React.js, Next.js, HTML5, CSS3, TailwindCSS
* Developer Tools: Git, VS Code, Postman, Linux, Playwright (Web Scraping/Automation)

PROFESSIONAL EXPERIENCE

Senior AI Engineer | InnovateAI Solutions, San Francisco, CA
June 2024 – Present
* Architected and deployed a multi-agent RAG system using LangChain and pgvector, reducing customer support response time by 45% and achieving a 92% answer accuracy rate.
* Fine-tuned open-source LLMs (Llama-3, Mistral) on domain-specific datasets using QLoRA and PEFT, improving model alignment and performance by 18% on proprietary evaluation benchmarks.
* Optimized LLM inference latency by 30% by containerizing workloads with Docker and deploying them on AWS ECS with auto-scaling configured via GPU metrics.
* Led a team of 3 engineers in building an automated document ingestion pipeline processing 10k+ multi-format files (PDF, HTML, Docx) daily using Playwright and unstructured data parsers.

AI Software Engineer | TechGenix Corp, Austin, TX
August 2022 – May 2024
* Developed backend microservices using FastAPI and PostgreSQL to support real-time data processing for a predictive maintenance IoT dashboard.
* Integrated OpenAI and Anthropic APIs into core SaaS products, developing custom prompt engineering templates and agent chains that increased user engagement by 25%.
* Built automated web scrapers using Playwright and BeautifulSoup to collect market intelligence, handling dynamic JavaScript content and bypassing anti-bot systems.
* Maintained clean, modular, and PEP-8 compliant codebases with 90%+ unit test coverage using pytest.

Junior Software Developer | ByteBuilders Ltd, New Delhi, India
June 2021 – July 2022
* Built and styled responsive web interfaces using React.js and TailwindCSS, collaborating closely with UI/UX designers.
* Designed and optimized complex SQL queries and database schemas in PostgreSQL, improving query execution time by 20%.
* Developed RESTful API endpoints using Flask to support user authentication and file upload functionalities.

PROJECTS

CreatorBazaar Dashboard (Full-Stack AI Project)
* Developed an analytics dashboard for creators, scraping public data using Playwright to track performance metrics across multiple platforms.
* Integrated an LLM-powered content recommendation engine that analyzes creator trends and suggests personalized video topics and script outlines.
* Stack: Python, FastAPI, React, TailwindCSS, PostgreSQL, Playwright.

Auto-Agentic Outreach Pipeline
* Built a local CLI utility that automates outreach by scanning industry forums, extracting key discussions, and generating context-aware response drafts.
* Achieved 95% reduction in manual tracking by storing and matching target contacts using Qdrant vector database.
* Stack: Python, LlamaIndex, Qdrant, OpenRouter API.

EDUCATION

Bachelor of Technology in Computer Science & Engineering
Delhi Technological University (DTU), New Delhi, India | Graduated: May 2021"""


def read_master_resume(filepath: str) -> str:
    """Reads the master resume text from the specified file path.

    If the file does not exist, it creates it with mock resume data first.

    Args:
        filepath: The path to the master resume file.

    Returns:
        The content of the master resume as a string.
    """
    if not os.path.exists(filepath):
        print(f"[INFO] Master resume file not found at '{filepath}'. Creating mock resume file...")
        try:
            # Ensure the directory exists
            dir_name = os.path.dirname(filepath)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(MOCK_RESUME_TEXT.strip())
            print(f"[INFO] Mock resume written successfully to '{filepath}'.")
        except Exception as e:
            print(f"[WARNING] Failed to write mock resume file: {e}")
            print("[INFO] Falling back to memory-loaded mock resume.")
            return MOCK_RESUME_TEXT.strip()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content.strip()
    except Exception as e:
        print(f"[ERROR] Failed to read master resume from '{filepath}': {e}")
        sys.exit(1)


def scrape_job_description(url: str) -> str:
    """Scrapes the text content of a job description URL using Playwright.

    Implements anti-bot evasion techniques (stealth init scripts, custom headers,
    arguments) and automatically falls back to headed mode if headless mode is
    blocked or yields insufficient text. Also extracts text from nested iframes.

    Args:
        url: The web URL of the job posting.

    Returns:
        A cleaned string of text containing the job description.
    """
    def run_scraper(is_headless: bool) -> str:
        with sync_playwright() as p:
            # Launch chromium with anti-fingerprinting arguments
            browser = p.chromium.launch(
                headless=is_headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certificate-errors",
                ]
            )
            
            # Configure realistic context variables
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False,
                locale="en-US",
                timezone_id="America/Los_Angeles",
                permissions=["geolocation"],
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                }
            )
            
            page = context.new_page()
            
            # Add anti-bot bypass init script to spoof navigator properties
            stealth_script = """
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            
            // Spoof chrome object
            window.chrome = {
                app: {
                    isInstalled: false,
                    InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' },
                    RunningState: { CANNOT_RUN: 'cannot_run', RUNNING: 'running', CAN_RUN: 'can_run' }
                },
                runtime: {},
                loadTimes: () => {},
                csi: () => {}
            };
            
            // Spoof plugins length
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'PDF Viewer' },
                    { name: 'Chrome PDF Viewer' },
                    { name: 'Chromium PDF Viewer' }
                ]
            });
            
            // Spoof languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            """
            page.add_init_script(stealth_script)
            
            # Navigate with DOM content loaded wait and 45s timeout
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            
            # Additional wait to let network requests resolve and prevent dynamic scripts from failing
            page.wait_for_timeout(4000)
            
            # Human-mimicking scroll to trigger lazy loading of description details
            try:
                for i in range(4):
                    page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {i/4});")
                    page.wait_for_timeout(500)
            except Exception as scroll_err:
                print(f"[WARNING] Scroll simulation failed: {scroll_err}")
                
            # Extract inner text of the <body>
            body_text = page.locator("body").inner_text()
            
            # Extract text from any nested iframes (common on Workday/Taleo)
            try:
                iframe_texts = []
                for frame in page.frames:
                    if frame != page.main_frame:
                        try:
                            frame_text = frame.locator("body").inner_text()
                            if frame_text.strip():
                                iframe_texts.append(frame_text.strip())
                        except Exception:
                            pass
                if iframe_texts:
                    body_text += "\n\n" + "\n\n".join(iframe_texts)
            except Exception as iframe_err:
                print(f"[WARNING] Frame text extraction failed: {iframe_err}")
            
            browser.close()
            
            # Clean up excessive whitespace, carriage returns, and empty lines
            cleaned_text = re.sub(r'\r\n', '\n', body_text)
            cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
            cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)
            
            return cleaned_text.strip()

    # Step 1: Attempt Headless Scraping
    print(f"[INFO] Attempting to scrape job description in headless mode from: {url}")
    try:
        scraped_content = run_scraper(is_headless=True)
        
        # Check if content looks like a bot block page or is empty
        lower_content = scraped_content.lower()
        is_blocked = (
            "access denied" in lower_content or 
            "captcha" in lower_content or
            "security check" in lower_content or
            "please enable javascript" in lower_content or
            "checking your browser" in lower_content or
            len(scraped_content) < 300
        )
        
        if is_blocked:
            raise RuntimeError("Headless mode was blocked or returned insufficient page content.")
            
        return scraped_content
        
    except Exception as headless_err:
        print(f"[WARNING] Headless scraping failed or was blocked: {headless_err}")
        print("[INFO] Falling back to HEADED mode (visible browser window)...")
        
        # Step 2: Fallback to Headed Scraping
        try:
            scraped_content = run_scraper(is_headless=False)
            
            # Double check headed results as well
            lower_content = scraped_content.lower()
            if "access denied" in lower_content or len(scraped_content) < 200:
                print("[WARNING] Headed mode also returned minimal content or blocked page.")
                
            return scraped_content
        except Exception as headed_err:
            print(f"[ERROR] Headed scraping also failed: {headed_err}")
            raise headed_err


def analyze_and_tailor(job_description_text: str, master_resume_text: str, api_key: str) -> dict:
    """Invokes the Gemini API in a Single-Shot call to analyze the job description,

    evaluate match score, extract missing keywords, tailor professional summary & achievements,
    and generate a cold outreach email.

    Args:
        job_description_text: The cleaned text from the job board.
        master_resume_text: The candidate's master resume.
        api_key: The Gemini API key.

    Returns:
        A dictionary matching the required output JSON schema.
    """
    print("[INFO] Running single-shot LLM analysis via Gemini...")
    
    system_prompt = (
        "You are an expert technical recruiter and professional resume writer.\n"
        "Your task is to analyze a job description against a candidate's master resume and generate a "
        "tailored resume profile and cold outreach email.\n\n"
        "You MUST respond ONLY with a valid JSON object matching this exact schema:\n"
        "{\n"
        '  "match_score": <int 1-100>,\n'
        '  "missing_keywords": ["keyword1", "keyword2"],\n'
        '  "tailored_resume_summary": "<A 3-sentence tailored professional summary matching the candidate\'s actual experience to the job requirements>",\n'
        '  "tailored_achievements": ["<Bullet 1 highlighting matched skills>", "<Bullet 2>", "<Bullet 3>"],\n'
        '  "cold_outreach_email": "<A professional, concise email to the hiring manager applying for the role, referencing specific alignments>"\n'
        "}\n\n"
        "CRITICAL RULES:\n"
        "1. Do not include any introductory or concluding text, explanations, or markdown code blocks (like ```json). Just return the raw JSON object.\n"
        "2. Ensure all keys and string values are properly escaped and valid in JSON.\n"
        "3. Base all claims on facts present in the master resume. Do not hallucinate credentials."
    )
    
    user_prompt = (
        f"--- CANDIDATE MASTER RESUME ---\n{master_resume_text}\n\n"
        f"--- TARGET JOB DESCRIPTION ---\n{job_description_text}\n"
    )
    
    url = GEMINI_URL_TEMPLATE.format(model=DEFAULT_MODEL, api_key=api_key)
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ],
        "systemInstruction": {
            "parts": [
                {"text": system_prompt}
            ]
        },
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
        
        response_json = response.json()
        if "error" in response_json:
            raise RuntimeError(f"Gemini API error: {response_json['error'].get('message')}")
            
        raw_content = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Robust extraction in case the model ignored instructions and wrapped in code blocks
        json_content = raw_content
        if json_content.startswith("```"):
            # Remove leading markdown wrappers
            json_content = re.sub(r'^```(?:json)?\s*', '', json_content)
            # Remove trailing markdown wrappers
            json_content = re.sub(r'\s*```$', '', json_content)
            
        parsed_data = json.loads(json_content.strip())
        
        # Verify required keys exist
        required_keys = [
            "match_score", 
            "missing_keywords", 
            "tailored_resume_summary", 
            "tailored_achievements", 
            "cold_outreach_email"
        ]
        for key in required_keys:
            if key not in parsed_data:
                raise KeyError(f"Missing required key '{key}' in LLM JSON response.")
                
        return parsed_data
        
    except requests.exceptions.HTTPError as he:
        print(f"[ERROR] HTTP error calling Gemini API: {he}")
        if response is not None:
            print(f"[ERROR] API Response: {response.text}")
        raise he
    except json.JSONDecodeError as jde:
        print("[ERROR] Failed to parse JSON response from the LLM.")
        print(f"[ERROR] Raw content received: {raw_content}")
        raise jde
    except Exception as e:
        print(f"[ERROR] Unexpected error during LLM analysis: {e}")
        raise e


def save_results(json_data: dict, company_name: str) -> str:
    """Parses the LLM's JSON output and saves it as a cleanly formatted Markdown file.

    Args:
        json_data: The parsed dictionary response from the LLM.
        company_name: Name of the target company.

    Returns:
        The file path of the saved Markdown file.
    """
    # Clean the company name for filename usage
    safe_company_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', company_name.lower().strip())
    filename = f"tailored_application_{safe_company_name}.md"
    
    match_score = json_data.get("match_score", 0)
    missing_keywords = json_data.get("missing_keywords", [])
    summary = json_data.get("tailored_resume_summary", "")
    achievements = json_data.get("tailored_achievements", [])
    email = json_data.get("cold_outreach_email", "")
    
    # Generate progress bar representation of match score
    progress_blocks = int(match_score / 10)
    progress_bar = "🟩" * progress_blocks + "⬜" * (10 - progress_blocks)
    
    # Format list fields
    formatted_keywords = "\n".join([f"- **{kw}**" for kw in missing_keywords]) if missing_keywords else "*None identified.*"
    formatted_achievements = "\n".join([f"- {ach}" for ach in achievements])
    
    markdown_content = f"""# Tailored Job Application Pack: {company_name}

## 📊 Compatibility Assessment

- **Target Company:** {company_name}
- **Resume Match Score:** `{match_score}/100`  
  {progress_bar}

### 🔍 Missing Keywords & Skill Gaps
The LLM identified the following high-priority skills/keywords present in the job description that are missing or underrepresented in your master resume:
{formatted_keywords}

---

## 📄 Tailored Resume Profile

### Professional Summary
> *{summary}*

### Tailored Key Achievements
Replace or update your experience bullet points with these tailored versions:
{formatted_achievements}

---

## ✉️ Cold Outreach Email
*Copy and personalize this email to send to the hiring manager or recruiter.*

```text
Subject: Exploring AI Systems Engineer opportunities at {company_name} - Divyansh Gupta

{email}
```
"""
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(markdown_content.strip() + "\n")
        print(f"[INFO] Tailored application saved successfully to '{filename}'")
        return filename
    except Exception as e:
        print(f"[ERROR] Failed to save Markdown output file '{filename}': {e}")
        raise e


def load_env_file():
    """Loads environment variables from a local .env file if it exists."""
    env_path = ".env"
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            val = parts[1].strip()
                            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                                val = val[1:-1]
                            os.environ[key] = val
        except Exception as e:
            print(f"[WARNING] Could not parse .env file: {e}")


def main():
    """Main execution block of the pipeline."""
    # Load local .env variables if present
    load_env_file()

    print("=" * 60)
    print("        AUTOMATED APPLICATION ORCHESTRATOR")
    print("=" * 60)
    
    # Fetch Gemini API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARNING] 'GEMINI_API_KEY' environment variable not set.")
        api_key = input("Please enter your Gemini API Key (or press Enter to exit): ").strip()
        if not api_key:
            print("[ERROR] API Key is required. Exiting.")
            sys.exit(1)
            
    # Gather job URL and company name inputs
    url = input("Enter Job Description URL: ").strip()
    if not url:
        print("[ERROR] Job URL cannot be empty. Exiting.")
        sys.exit(1)
        
    company_name = input("Enter Company Name: ").strip()
    if not company_name:
        print("[ERROR] Company Name cannot be empty. Exiting.")
        sys.exit(1)
        
    resume_path = os.path.join("data", "master_resume.txt")
    
    try:
        # Step 1: Read Master Resume
        master_resume = read_master_resume(resume_path)
        
        # Step 2: Scrape Job Description
        job_description = scrape_job_description(url)
        
        # Step 3: Run LLM Reasoning
        result_json = analyze_and_tailor(job_description, master_resume, api_key)
        
        # Step 4: Save Tailored Output
        output_file = save_results(result_json, company_name)
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Pipeline completed successfully!")
        print(f"[SUCCESS] Output file: {os.path.abspath(output_file)}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
