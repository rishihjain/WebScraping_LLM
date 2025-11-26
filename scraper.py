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
            
            # Extract Schema.org structured data first (most reliable)
            schema_info = self._extract_schema_org(soup)
            
            # Clean HTML for LLM processing (pass schema_info to avoid duplicate extraction)
            cleaned_html = self._clean_html(soup, schema_info)
            
            if progress_callback:
                progress_callback({'stage': 'extracting', 'message': 'Extracting data with AI...'})
            
            # Use LLM to understand what to extract (multilingual support)
            extracted_data = self._extract_with_llm(cleaned_html, extraction_prompt, url, detected_language, domain)
            
            # Merge Schema.org product data with LLM extraction (Schema.org takes priority)
            if schema_info.get('product_data'):
                product_data = schema_info['product_data']
                # Merge: Schema.org data overrides LLM data for critical fields
                for key, value in product_data.items():
                    if value:  # Only override if Schema.org has a value
                        extracted_data[key] = value

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
            'ar': ['في', 'من', 'إلى', 'على', 'أن', 'هو', 'هي', 'كان', 'كانت', 'مع', 'هذا', 'هذه'],
            # Indian languages
            'hi': ['की', 'के', 'में', 'है', 'हैं', 'को', 'से', 'पर', 'या', 'और', 'यह', 'वह', 'इस', 'उस'],
            'mr': ['चा', 'ची', 'चे', 'मध्ये', 'आहे', 'आणि', 'किंवा', 'हे', 'ते', 'या', 'तो', 'ती'],
            'gu': ['નું', 'ના', 'ની', 'માં', 'છે', 'અને', 'અથવા', 'આ', 'તે', 'એ', 'એક', 'બે'],
            'bn': ['এর', 'এ', 'হয়', 'এবং', 'বা', 'এই', 'সে', 'একটি', 'করে', 'হবে', 'হয়েছে', 'করতে'],
            'te': ['లో', 'కు', 'ని', 'అని', 'మరియు', 'లేదా', 'ఈ', 'ఆ', 'ఒక', 'కు', 'గా', 'చే'],
            'ta': ['ல்', 'க்கு', 'ஐ', 'ஆக', 'மற்றும்', 'அல்லது', 'இந்த', 'அந்த', 'ஒரு', 'செய்ய', 'உள்ளது', 'இருக்கிறது'],
            'kn': ['ದ', 'ದಲ್ಲಿ', 'ಗೆ', 'ಅನ್ನು', 'ಮತ್ತು', 'ಅಥವಾ', 'ಈ', 'ಆ', 'ಒಂದು', 'ಮಾಡಲು', 'ಇದೆ', 'ಆಗಿದೆ'],
            'ml': ['യുടെ', 'ൽ', 'ക്ക്', 'ആണ്', 'ഉം', 'അല്ലെങ്കിൽ', 'ഈ', 'ആ', 'ഒരു', 'ചെയ്യാൻ', 'ഉണ്ട്', 'ആയി'],
            'pa': ['ਦਾ', 'ਦੀ', 'ਦੇ', 'ਵਿੱਚ', 'ਹੈ', 'ਅਤੇ', 'ਜਾਂ', 'ਇਹ', 'ਉਹ', 'ਇੱਕ', 'ਕਰਨ', 'ਲਈ'],
            'or': ['ର', 'ରେ', 'କୁ', 'ହେଉଛି', 'ଏବଂ', 'କିମ୍ବା', 'ଏହି', 'ସେ', 'ଏକ', 'କରିବା', 'ଅଛି', 'ହେବ'],
            'ur': ['کا', 'کی', 'کے', 'میں', 'ہے', 'اور', 'یا', 'یہ', 'وہ', 'ایک', 'کرنے', 'کے لیے']
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
        """Fetch page using Playwright with smart waiting for dynamic content."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            
            try:
                # Load page
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)
                except Exception:
                    # Fallback: just load the page
                    page.goto(url, timeout=60000)
                
                # Wait for critical e-commerce elements (price, rating) to appear
                # This handles Amazon and similar sites that load prices dynamically
                try:
                    # Wait for price or rating elements (up to 10 seconds)
                    # Common selectors for Amazon and other e-commerce sites
                    page.wait_for_selector(
                        'span[class*="price"], span[class*="Price"], .a-price, [data-asin-price], '
                        'span[class*="rating"], [aria-label*="star"], .a-icon-alt, '
                        '[data-hook*="review"], script[type="application/ld+json"]',
                        timeout=10000
                    )
                except Exception:
                    # Continue even if selectors not found (page might not be e-commerce)
                    pass
                
                # Wait for network to settle and dynamic content to load
                page.wait_for_timeout(5000)
                
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
    
    def _extract_schema_org(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract Schema.org structured data (most reliable source for e-commerce data)."""
        schema_data = {}
        
        # Extract JSON-LD scripts (Schema.org)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    schema_type = data.get('@type', 'Unknown')
                    if schema_type not in schema_data:
                        schema_data[schema_type] = []
                    schema_data[schema_type].append(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            schema_type = item.get('@type', 'Unknown')
                            if schema_type not in schema_data:
                                schema_data[schema_type] = []
                            schema_data[schema_type].append(item)
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Extract Product schema data (most important for e-commerce)
        product_data = {}
        if 'Product' in schema_data:
            for product in schema_data['Product']:
                # Extract price
                offers = product.get('offers', {})
                if isinstance(offers, dict):
                    price = offers.get('price') or offers.get('priceCurrency')
                    if price:
                        product_data['price'] = price
                    availability = offers.get('availability')
                    if availability:
                        product_data['availability'] = availability
                elif isinstance(offers, list) and len(offers) > 0:
                    offer = offers[0]
                    if isinstance(offer, dict):
                        price = offer.get('price')
                        if price:
                            product_data['price'] = price
                        availability = offer.get('availability')
                        if availability:
                            product_data['availability'] = availability
                
                # Extract rating
                aggregate_rating = product.get('aggregateRating', {})
                if isinstance(aggregate_rating, dict):
                    rating = aggregate_rating.get('ratingValue')
                    if rating:
                        product_data['rating'] = rating
                    review_count = aggregate_rating.get('reviewCount')
                    if review_count:
                        product_data['reviews_count'] = review_count
                
                # Extract other product fields
                if product.get('name'):
                    product_data['product_name'] = product.get('name')
                if product.get('description'):
                    product_data['description'] = product.get('description')
                if product.get('brand'):
                    brand = product.get('brand')
                    if isinstance(brand, dict):
                        product_data['brand'] = brand.get('name', '')
                    else:
                        product_data['brand'] = str(brand)
        
        return {
            'schema_data': schema_data,
            'product_data': product_data
        }
    
    def _clean_html(self, soup: BeautifulSoup, schema_info: Dict[str, Any] = None) -> str:
        """Clean HTML while preserving critical e-commerce elements (price, rating, reviews)."""
        # Use provided schema_info or extract it
        if schema_info is None:
            schema_info = self._extract_schema_org(soup)
        
        # Remove only truly unnecessary elements (keep JSON-LD scripts for now)
        for script in soup(["style", "noscript"]):
            script.decompose()
        
        # Remove regular scripts but keep JSON-LD
        for script in soup.find_all('script'):
            if script.get('type') != 'application/ld+json':
                script.decompose()
        
        # Get text content with structure
        text_content = []
        
        # PRIORITY 0: Extract code blocks FIRST (before other content) - critical for algorithm/code extraction
        code_blocks = []
        for code_elem in soup.find_all(['pre', 'code', 'textarea']):
            code_text = code_elem.get_text(separator='\n', strip=False)
            if code_text and len(code_text) > 20:  # Only meaningful code blocks
                # Preserve code formatting and indentation
                code_blocks.append(f"CODE_BLOCK: {code_text[:2000]}")  # Limit each block to 2000 chars
        # Add code blocks to text_content (they'll be prioritized)
        text_content.extend(code_blocks[:10])  # Limit to 10 code blocks
        
        # PRIORITY 1: Add Schema.org structured data (most reliable)
        if schema_info.get('schema_data'):
            for schema_type, items in schema_info['schema_data'].items():
                for item in items[:2]:  # Limit to first 2 items per type
                    try:
                        text_content.append(f"STRUCTURED_DATA ({schema_type}): {json.dumps(item, ensure_ascii=False)[:1000]}")
                    except:
                        pass
        
        # PRIORITY 2: Extract price elements (common selectors for e-commerce)
        price_selectors = [
            'span[class*="price"]', 'span[class*="Price"]', 
            'span[id*="price"]', 'div[class*="price"]',
            '.a-price', '.a-offscreen', '[data-asin-price]',
            '[data-price]', '.price', '.product-price'
        ]
        prices_found = set()
        for selector in price_selectors:
            try:
                prices = soup.select(selector)
                for price in prices[:10]:  # Limit to avoid duplicates
                    text = price.get_text(strip=True)
                    if text and any(char.isdigit() for char in text):
                        # Normalize price text
                        price_text = re.sub(r'\s+', ' ', text)
                        if price_text not in prices_found and len(price_text) < 100:
                            prices_found.add(price_text)
                            text_content.append(f"PRICE: {price_text}")
            except Exception:
                pass
        
        # PRIORITY 3: Extract rating elements
        rating_selectors = [
            'span[class*="rating"]', 'span[class*="Rating"]',
            '[aria-label*="star"]', '.a-icon-alt', '[data-rating]',
            '.rating', '[class*="star"]'
        ]
        ratings_found = set()
        for selector in rating_selectors:
            try:
                ratings = soup.select(selector)
                for rating in ratings[:10]:
                    text = rating.get_text(strip=True)
                    aria_label = rating.get('aria-label', '')
                    if aria_label:
                        text = aria_label
                    if text and ('star' in text.lower() or any(char.isdigit() for char in text)):
                        rating_text = re.sub(r'\s+', ' ', text.strip())
                        if rating_text not in ratings_found and len(rating_text) < 100:
                            ratings_found.add(rating_text)
                            text_content.append(f"RATING: {rating_text}")
            except Exception:
                pass
        
        # PRIORITY 4: Extract review count
        review_selectors = [
            'span[class*="review"]', 'span[id*="review"]',
            'a[href*="review"]', '[data-hook*="review"]',
            '[class*="review-count"]', '[id*="review"]'
        ]
        reviews_found = set()
        for selector in review_selectors:
            try:
                reviews = soup.select(selector)
                for review in reviews[:10]:
                    text = review.get_text(strip=True)
                    if text and any(char.isdigit() for char in text):
                        # Look for patterns like "1,234 ratings" or "500+ reviews"
                        if re.search(r'\d+[,\d]*\s*(rating|review|customer)', text, re.IGNORECASE):
                            review_text = re.sub(r'\s+', ' ', text.strip())
                            if review_text not in reviews_found and len(review_text) < 100:
                                reviews_found.add(review_text)
                                text_content.append(f"REVIEWS: {review_text}")
            except Exception:
                pass
        
        # PRIORITY 5: Extract headings (limit to avoid too much content)
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])[:50]
        for heading in headings:
            text = heading.get_text(strip=True)
            if text:
                text_content.append(f"HEADING: {text}")
        
        # PRIORITY 6: Extract paragraphs (limit to most relevant)
        paragraphs = soup.find_all('p')[:100]
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 10:
                text_content.append(f"PARAGRAPH: {text[:500]}")  # Limit paragraph length
        
        # PRIORITY 7: Extract lists
        lists = soup.find_all(['ul', 'ol'])[:20]
        for ul in lists:
            items = [li.get_text(strip=True)[:200] for li in ul.find_all('li')[:50]]
            if items:
                text_content.append(f"LIST: {' | '.join(items)}")
        
        # PRIORITY 8: Extract tables
        tables = soup.find_all('table')[:10]
        for table in tables:
            rows = []
            for tr in table.find_all('tr')[:50]:  # Limit rows
                cells = [td.get_text(strip=True)[:100] for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(' | '.join(cells))
            if rows:
                text_content.append(f"TABLE: {' || '.join(rows)}")
        
        # PRIORITY 9: Extract important links (limit)
        links = soup.find_all('a', href=True)[:50]
        for a in links:
            text = a.get_text(strip=True)
            if text and len(text) < 100:  # Only short link texts
                href = a['href']
                if href.startswith('http') or href.startswith('/'):
                    text_content.append(f"LINK: {text} -> {href}")
        
        result = '\n'.join(text_content)
        
        # Increase limit for LLM (was 10000, now 15000 to include more structured data)
        if len(result) > 15000:
            # Prioritize: keep code blocks, structured data, prices, ratings, reviews, then truncate rest
            priority_lines = [line for line in text_content if any(
                keyword in line for keyword in ['CODE_BLOCK:', 'STRUCTURED_DATA', 'PRICE:', 'RATING:', 'REVIEWS:']
            )]
            other_lines = [line for line in text_content if line not in priority_lines]
            
            # Keep all priority lines + as many other lines as fit
            result_lines = priority_lines
            remaining_chars = 15000 - len('\n'.join(priority_lines))
            for line in other_lines:
                if len('\n'.join(result_lines) + '\n' + line) <= remaining_chars:
                    result_lines.append(line)
                else:
                    break
            result = '\n'.join(result_lines) + "\n... (content truncated)"
        
        return result if result else "No extractable content found on this page."
    
    def _extract_with_llm(self, cleaned_html: str, instruction: str, url: str, language: str = 'en', domain: str = 'general') -> Dict[str, Any]:
        """Use LLM to extract data based on natural language instruction. Supports multilingual content and domain-specific extraction."""
        language_note = f"\nNote: This webpage appears to be in {language.upper()} language. Please extract data accordingly, maintaining the original language of the content unless the user specifically requests translation." if language != 'en' else ""
        
        # Add critical fields emphasis for e-commerce
        critical_fields_note = ""
        if domain == 'ecommerce':
            critical_fields_note = """
CRITICAL EXTRACTION REQUIREMENTS FOR E-COMMERCE:
You MUST extract these fields even if not explicitly requested:
- price: Look in STRUCTURED_DATA first (most reliable), then PRICE tags, or text containing currency symbols (₹, $, €, £, ¥)
- rating: Look in STRUCTURED_DATA, RATING tags, star ratings (e.g., "4.5 out of 5", "4.5 stars"), or numeric ratings
- reviews_count: Look in STRUCTURED_DATA, REVIEWS tags, or numbers followed by "review", "rating", "customer"
- discount: Percentage off, sale price vs regular price, promotional text
- availability: "in stock", "out of stock", "limited stock", availability status

EXTRACTION PRIORITY:
1. STRUCTURED_DATA (JSON-LD) - Most reliable, use this first
2. PRICE, RATING, REVIEWS tags - Explicitly marked in content
3. Text patterns - Currency symbols, star ratings, review counts

If price/rating/reviews are missing, search more carefully. They are often in:
- JSON-LD structured data (check STRUCTURED_DATA tags)
- Span/div elements with price/rating classes
- Data attributes
- Text patterns like "₹", "$", "stars", "out of 5", "ratings", "reviews"

Return these fields even if the user instruction doesn't explicitly ask for them.
"""
        
        # Detect user intent for code, complexity, or use cases
        instruction_lower = instruction.lower()
        needs_code = any(keyword in instruction_lower for keyword in [
            'code', 'algorithm', 'implementation', 'snippet', 'program', 
            'source code', 'coding', 'programming'
        ])
        needs_complexity = any(keyword in instruction_lower for keyword in [
            'complexity', 'big o', 'time complexity', 'space complexity', 
            'o(n)', 'asymptotic', 'performance', 'efficiency'
        ])
        needs_use_cases = any(keyword in instruction_lower for keyword in [
            'use case', 'practical', 'application', 'where to use', 
            'when to use', 'scenario', 'real world', 'practical life'
        ])
        
        # Add specialized extraction requirements
        specialized_extraction_note = ""
        if needs_code:
            specialized_extraction_note += """
CRITICAL: USER REQUESTED CODE/ALGORITHM EXTRACTION
- Extract ALL code blocks, code snippets, and algorithm implementations
- Look for: CODE_BLOCK tags, <pre>, <code>, code blocks, algorithm pseudocode, implementation details
- Preserve code formatting, indentation, and syntax
- Extract complete code, not just descriptions
- Include code in fields like: "code", "algorithm_code", "implementation", "code_snippet"
- If multiple algorithms are mentioned, extract code for each separately
- Code is MANDATORY - extract it even if it's incomplete or partial

"""
        if needs_complexity:
            specialized_extraction_note += """
CRITICAL: USER REQUESTED COMPLEXITY ANALYSIS
- Extract time complexity (Big O notation: O(n), O(n²), O(log n), O(1), etc.)
- Extract space complexity (memory requirements)
- Look for: "O(", "Big O", "time complexity", "space complexity", "asymptotic", "worst case", "best case"
- Extract complexity analysis even if it's informal (e.g., "linear time", "quadratic", "logarithmic")
- Include in fields like: "time_complexity", "space_complexity", "complexity_analysis", "big_o_notation"
- Complexity analysis is MANDATORY - extract it even if it's not explicitly stated

"""
        if needs_use_cases:
            specialized_extraction_note += """
CRITICAL: USER REQUESTED PRACTICAL USE CASES
- Extract real-world applications, use cases, scenarios
- Look for: "use case", "application", "when to use", "practical", "real world", "example", "scenario"
- Extract specific scenarios where the algorithm/technique is applicable
- Include in fields like: "use_cases", "applications", "practical_scenarios", "when_to_use", "real_world_examples"
- Use cases are MANDATORY - extract them even if they're not explicitly listed

"""
        
        prompt = f"""You are a web scraping assistant. Extract data from the following webpage content based on the user's instruction.
{critical_fields_note}
{specialized_extraction_note}
{language_note}

URL: {url}
User Instruction: {instruction}

Webpage Content:
{cleaned_html[:12000]}  # Increased limit to include more structured data

Please extract the requested data and return it as a JSON object. The JSON should have clear field names based on what was requested.

For e-commerce pages, ALWAYS extract:
- product_name (or name)
- price (with currency symbol if available)
- rating (numeric, e.g., 4.5)
- reviews_count (numeric, e.g., 1234)
- discount (if available)
- availability (if available)

Example for e-commerce:
{{
  "product_name": "Product Name",
  "price": "₹1,999",
  "rating": 4.5,
  "reviews_count": 1234,
  "discount": "20% off",
  "availability": "In stock"
}}

For general pages:
{{
  "headings": ["Heading 1", "Heading 2"],
  "content": "Main content..."
}}

Be intelligent about identifying:
- Code blocks and algorithms (look for CODE_BLOCK tags, preserve formatting)
- Tables (return as arrays of objects)
- Lists (return as arrays)
- Prices (extract numbers and currency symbols, handle different currencies: ₹, $, €, £, ¥)
- Reviews (extract review text and ratings)
- Headings (h1, h2, h3, etc.)
- Links
- Complexity notation (Big O, time/space complexity)
- Use cases and practical applications
- Any other structured data

IMPORTANT: 
- If the content is in a language other than English, preserve the original language in the extracted data unless the user specifically requests translation.
- For e-commerce: price, rating, and reviews_count are MANDATORY - extract them even if not explicitly requested.
- Check STRUCTURED_DATA tags first as they contain the most reliable information.

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

