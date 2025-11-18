import os
import json
import re
from typing import Dict, List, Any

import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from domain_analyzer import DomainAnalyzer

class WebScraper:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        # Use gemini-1.5-flash for faster, free API access
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def scrape_url(self, url: str, extraction_prompt: str, user_instruction: str = '', domain: str = 'general', progress_callback=None) -> Dict[str, Any]:
        """
        Scrape a URL based on natural language instruction.
        Returns structured data extracted from the page.
        Supports multilingual websites.
        """
        try:
            if progress_callback:
                progress_callback({'stage': 'fetching', 'message': f'Fetching {url}...'})
            
            # Fetch page content
            html_content = self._fetch_page(url)
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Detect language
            detected_language = self._detect_language(soup)
            
            if progress_callback:
                progress_callback({'stage': 'cleaning', 'message': f'Processing content (Language: {detected_language})...'})
            
            # Clean HTML for LLM processing
            cleaned_html = self._clean_html(soup)
            
            if progress_callback:
                progress_callback({'stage': 'extracting', 'message': 'Extracting data with AI...'})
            
            # Use LLM to understand what to extract (multilingual support)
            extracted_data = self._extract_with_llm(cleaned_html, extraction_prompt, url, detected_language)

            if progress_callback:
                progress_callback({'stage': 'analyzing', 'message': 'Generating insights...'})

            # Build domain-specific analysis package
            analysis = self._generate_analysis(domain, extracted_data, user_instruction or extraction_prompt, detected_language)

            return {
                'extracted_data': extracted_data,
                'analysis': analysis,
                'url': url,
                'domain': domain,
                'language': detected_language
            }
        
        except Exception as e:
            raise Exception(f"Error scraping {url}: {str(e)}")
    
    def _detect_language(self, soup: BeautifulSoup) -> str:
        """Detect the primary language of the webpage."""
        # Check HTML lang attribute
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            lang = html_tag.get('lang')
            # Return ISO 639-1 code (first 2 characters)
            return lang[:2].lower() if len(lang) >= 2 else 'en'
        
        # Check meta tags
        meta_lang = soup.find('meta', attrs={'http-equiv': 'Content-Language'})
        if meta_lang and meta_lang.get('content'):
            lang = meta_lang.get('content')
            return lang[:2].lower() if len(lang) >= 2 else 'en'
        
        # Try to detect from content (simple heuristic)
        text_content = soup.get_text()[:500]  # Sample first 500 chars
        
        # Common language patterns
        language_patterns = {
            'es': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le'],
            'fr': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour'],
            'de': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf'],
            'it': ['il', 'di', 'che', 'e', 'la', 'a', 'per', 'è', 'in', 'un', 'sono', 'le'],
            'pt': ['o', 'de', 'a', 'e', 'do', 'da', 'em', 'um', 'para', 'é', 'com', 'não'],
            'ru': ['в', 'и', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а', 'то'],
            'zh': ['的', '一', '是', '在', '不', '了', '有', '和', '人', '这', '中', '大'],
            'ja': ['の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ', 'さ'],
            'ko': ['이', '가', '을', '를', '에', '의', '와', '과', '도', '로', '에서', '부터'],
            'ar': ['في', 'من', 'إلى', 'على', 'أن', 'هو', 'هي', 'كان', 'كانت', 'مع', 'هذا', 'هذه']
        }
        
        text_lower = text_content.lower()
        scores = {}
        for lang, patterns in language_patterns.items():
            score = sum(1 for pattern in patterns if pattern in text_lower)
            scores[lang] = score
        
        if scores:
            detected = max(scores, key=scores.get)
            if scores[detected] > 2:  # Threshold
                return detected
        
        # Default to English
        return 'en'
    
    def _fetch_page(self, url: str) -> str:
        """Fetch page content using Playwright for JavaScript-rendered pages."""
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # First, try with Playwright (for JavaScript-heavy sites)
        try:
            return self._fetch_with_playwright(url)
        except Exception as playwright_error:
            # If Playwright fails (timeout, blocked, etc.), try with requests as fallback
            try:
                return self._fetch_with_requests(url)
            except Exception as requests_error:
                # If both fail, raise the original Playwright error with context
                raise Exception(f"Failed to fetch page with browser automation: {str(playwright_error)}. Also tried simple HTTP request but failed: {str(requests_error)}")
    
    def _fetch_with_playwright(self, url: str) -> str:
        """Fetch page using Playwright (handles JavaScript)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            try:
                # Try with networkidle first, but with longer timeout
                try:
                    page.goto(url, wait_until='networkidle', timeout=60000)
                except Exception:
                    # Fallback: try with domcontentloaded (faster, less reliable)
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=60000)
                        # Wait for network to settle
                        page.wait_for_timeout(5000)
                    except Exception:
                        # Last resort: just load the page
                        page.goto(url, timeout=60000)
                        page.wait_for_timeout(5000)
                
                # Wait a bit more for dynamic content
                page.wait_for_timeout(3000)
                html_content = page.content()
            except Exception as e:
                error_msg = str(e)
                if 'timeout' in error_msg.lower():
                    raise Exception(f"Page took too long to load (timeout: 60s). The website might be slow or blocking automated access.")
                raise Exception(f"Failed to load page: {error_msg}")
            finally:
                browser.close()
            
            if not html_content or len(html_content) < 100:
                raise Exception("Page content is too short or empty. The page might be blocked, require authentication, or have anti-bot protection.")
            
            return html_content
    
    def _fetch_with_requests(self, url: str) -> str:
        """Fallback: Fetch page using requests library (faster, but no JavaScript execution)."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # Create session with retry strategy
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        try:
            response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            html_content = response.text
            
            if not html_content or len(html_content) < 100:
                raise Exception("Page content is too short or empty.")
            
            return html_content
        except requests.exceptions.Timeout:
            raise Exception("Request timed out after 30 seconds.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {str(e)}")
    
    def _clean_html(self, soup: BeautifulSoup) -> str:
        """Clean HTML to remove scripts, styles, and unnecessary elements."""
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link", "noscript"]):
            script.decompose()
        
        # Get text content with structure
        text_content = []
        
        # Extract headings (limit to avoid too much content)
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])[:50]
        for heading in headings:
            text = heading.get_text(strip=True)
            if text:
                text_content.append(f"HEADING: {text}")
        
        # Extract paragraphs (limit to most relevant)
        paragraphs = soup.find_all('p')[:100]
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 10:
                text_content.append(f"PARAGRAPH: {text[:500]}")  # Limit paragraph length
        
        # Extract lists
        lists = soup.find_all(['ul', 'ol'])[:20]
        for ul in lists:
            items = [li.get_text(strip=True)[:200] for li in ul.find_all('li')[:50]]
            if items:
                text_content.append(f"LIST: {' | '.join(items)}")
        
        # Extract tables
        tables = soup.find_all('table')[:10]
        for table in tables:
            rows = []
            for tr in table.find_all('tr')[:50]:  # Limit rows
                cells = [td.get_text(strip=True)[:100] for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(' | '.join(cells))
            if rows:
                text_content.append(f"TABLE: {' || '.join(rows)}")
        
        # Extract important links (limit)
        links = soup.find_all('a', href=True)[:50]
        for a in links:
            text = a.get_text(strip=True)
            if text and len(text) < 100:  # Only short link texts
                href = a['href']
                if href.startswith('http') or href.startswith('/'):
                    text_content.append(f"LINK: {text} -> {href}")
        
        result = '\n'.join(text_content)
        
        # Limit total content size for LLM
        if len(result) > 10000:
            result = result[:10000] + "\n... (content truncated)"
        
        return result if result else "No extractable content found on this page."
    
    def _extract_with_llm(self, cleaned_html: str, instruction: str, url: str, language: str = 'en') -> Dict[str, Any]:
        """Use LLM to extract data based on natural language instruction. Supports multilingual content."""
        language_note = f"\nNote: This webpage appears to be in {language.upper()} language. Please extract data accordingly, maintaining the original language of the content unless the user specifically requests translation." if language != 'en' else ""
        
        prompt = f"""You are a web scraping assistant. Extract data from the following webpage content based on the user's instruction.
{language_note}

URL: {url}
User Instruction: {instruction}

Webpage Content:
{cleaned_html[:8000]}  # Limit content to avoid token limits

Please extract the requested data and return it as a JSON object. The JSON should have clear field names based on what was requested.
For example, if the user asks for "product names and prices", return:
{{
  "product_names": ["Product 1", "Product 2"],
  "prices": ["$10", "$20"]
}}

If the user asks for "all headings", return:
{{
  "headings": ["Heading 1", "Heading 2"]
}}

Be intelligent about identifying:
- Tables (return as arrays of objects)
- Lists (return as arrays)
- Prices (extract numbers and currency symbols, handle different currencies)
- Reviews (extract review text and ratings)
- Headings (h1, h2, h3, etc.)
- Links
- Any other structured data

IMPORTANT: If the content is in a language other than English, preserve the original language in the extracted data unless the user specifically requests translation.

Return ONLY valid JSON, no additional text or markdown formatting."""

        try:
            response = self._call_llm(prompt)
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = re.sub(r'^```json\s*', '', response_text)
                response_text = re.sub(r'^```\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
            
            # Parse JSON response
            try:
                extracted_data = json.loads(response_text)
                return extracted_data
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    try:
                        extracted_data = json.loads(json_match.group())
                        return extracted_data
                    except json.JSONDecodeError:
                        pass
                
                # Return raw text if JSON parsing fails
                return {'raw_content': response_text, 'error': 'Could not parse as structured JSON'}
        
        except Exception as e:
            # If we have response_text, try one more time to extract JSON
            if 'response_text' in locals():
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
            raise Exception(f"LLM extraction error: {str(e)}")
    
    def _generate_analysis(self, domain: str, extracted_data: Dict[str, Any], instruction: str, language: str = 'en') -> Dict[str, Any]:
        """Generate structured analysis (summary, insights, key points). Supports multilingual content."""
        prompt = DomainAnalyzer.get_analysis_prompt(domain, extracted_data, instruction, language)
        try:
            response = self._call_llm(prompt)
            text = response.text.strip()
            if text.startswith('```'):
                text = re.sub(r'^```json\s*', '', text)
                text = re.sub(r'^```\s*', '', text)
                text = re.sub(r'\s*```$', '', text)
            return json.loads(text)
        except Exception as e:
            return {
                'summary': 'Could not generate structured analysis.',
                'key_points': [],
                'insights': [f'Error: {str(e)}'],
                'user_request_answer': '',
                'opportunities': [],
                'risks': [],
                'next_steps': []
            }
    
    def generate_comparison(self, all_results: List[Dict[str, Any]], domain: str, user_instruction: str = '') -> Dict[str, Any]:
        """Generate comparison analysis for multiple websites."""
        comparison_info = DomainAnalyzer.generate_comparison(all_results, domain, user_instruction)
        prompt = comparison_info['prompt']
        
        # Try multiple times with exponential backoff for comparison (it's a larger task)
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                response = self._call_llm(prompt)
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```'):
                    response_text = re.sub(r'^```json\s*', '', response_text)
                    response_text = re.sub(r'^```\s*', '', response_text)
                    response_text = re.sub(r'\s*```$', '', response_text)
                
                # Parse JSON response
                try:
                    comparison_data = json.loads(response_text)
                    return comparison_data
                except json.JSONDecodeError:
                    # Try to extract JSON from response
                    json_match = re.search(r'\{[\s\S]*\}', response_text)
                    if json_match:
                        try:
                            comparison_data = json.loads(json_match.group())
                            return comparison_data
                        except:
                            pass
                    
                    # Return text if JSON parsing fails
                    return {
                        'raw_comparison': response_text,
                        'error': 'Could not parse comparison as structured JSON'
                    }
            except Exception as e:
                error_msg = str(e)
                if '504' in error_msg or 'timeout' in error_msg.lower():
                    if attempt < max_attempts - 1:
                        import time
                        wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                        print(f"Comparison attempt {attempt + 1} timed out. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {
                            'error': f'Comparison timed out after {max_attempts} attempts. The comparison may be too complex. Try with fewer URLs or simpler content.',
                            'partial_data': 'You can still view individual website analyses above.'
                        }
                else:
                    return {'error': f'Comparison generation failed: {error_msg}'}
        
        return {'error': 'Comparison generation failed after all retry attempts'}

    def answer_question(
        self,
        domain: str,
        aggregated_results: List[Dict[str, Any]],
        question: str,
        user_instruction: str = ''
    ) -> Dict[str, Any]:
        """Answer a user question using stored analysis context."""
        prompt = DomainAnalyzer.build_qna_prompt(domain, aggregated_results, question, user_instruction)
        try:
            response = self._call_llm(prompt)
            text = response.text.strip() if response.text else ""
            
            # Check if response is empty
            if not text:
                return {
                    'answer': 'Unable to answer right now: The AI model returned an empty response. Please try again.',
                    'supporting_points': [],
                    'confidence': 'low'
                }
            
            # Remove markdown code blocks if present
            if text.startswith('```'):
                text = re.sub(r'^```json\s*', '', text)
                text = re.sub(r'^```\s*', '', text)
                text = re.sub(r'\s*```$', '', text)
            
            # Try to parse JSON
            try:
                return json.loads(text)
            except json.JSONDecodeError as json_err:
                # Try to extract JSON from the response
                json_match = re.search(r'\{[\s\S]*\}', text)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # Return error with raw response for debugging
                return {
                    'answer': f'Unable to parse AI response as JSON. Raw response: {text[:200]}...',
                    'supporting_points': [],
                    'confidence': 'low',
                    'error': f'JSON parsing error: {str(json_err)}'
                }
        except Exception as e:
            error_msg = str(e)
            # Check if it's a JSON parsing error
            if 'Expecting value' in error_msg or 'JSON' in error_msg:
                return {
                    'answer': 'Unable to answer right now: The AI response was invalid. Please try asking the question again.',
                    'supporting_points': [],
                    'confidence': 'low',
                    'error': error_msg
                }
            return {
                'answer': f'Unable to answer right now: {error_msg}',
                'supporting_points': [],
                'confidence': 'low'
            }

    def _call_llm(self, prompt: str):
        """Call Gemini with basic retry for transient errors."""
        attempts = 2
        last_error = None
        for attempt in range(attempts):
            try:
                return self.model.generate_content(prompt)
            except Exception as e:
                last_error = e
                if 'timeout' not in str(e).lower() and '504' not in str(e):
                    break
        raise last_error or Exception("LLM call failed")

