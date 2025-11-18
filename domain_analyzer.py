"""
Domain-specific analysis templates, reporting, comparison, and Q&A logic.
"""
from typing import Dict, List, Any
import json


class DomainAnalyzer:
    """Handles domain-specific extraction and analysis guidance."""

    DOMAINS = {
        'ecommerce': {
            'name': 'E-Commerce',
            'parameters': [
                'product_name', 'price', 'discount', 'rating', 'reviews_count',
                'availability', 'description', 'features', 'images'
            ],
            'analysis_focus': [
                'pricing signals', 'feature differentiation', 'customer sentiment',
                'availability or shipping info', 'value propositions'
            ],
            'qna_style': 'Answer as a product analyst focused on shopper needs.'
        },
        'news': {
            'name': 'News & Media',
            'parameters': [
                'headline', 'author', 'publish_date', 'content', 'tags',
                'category', 'image', 'summary'
            ],
            'analysis_focus': [
                'story angle', 'sentiment tone', 'source credibility',
                'timeliness', 'topic coverage'
            ],
            'qna_style': 'Answer as an editorial analyst focusing on article details.'
        },
        'business': {
            'name': 'Business & Finance',
            'parameters': [
                'company_name', 'revenue', 'stock_price', 'market_cap', 'employees',
                'location', 'description', 'services'
            ],
            'analysis_focus': [
                'business model', 'financial metrics', 'market positioning',
                'growth signals', 'competitive differentiation'
            ],
            'qna_style': 'Answer as a strategy consultant summarizing business context.'
        },
        'jobs': {
            'name': 'Job Listings',
            'parameters': [
                'job_title', 'company', 'location', 'salary', 'job_type',
                'requirements', 'description', 'posted_date'
            ],
            'analysis_focus': [
                'salary/seniority clues', 'skills requirements', 'location trends',
                'employment type', 'employer highlights'
            ],
            'qna_style': 'Answer as a career coach referencing job details.'
        },
        'real_estate': {
            'name': 'Real Estate',
            'parameters': [
                'property_type', 'price', 'location', 'bedrooms', 'bathrooms',
                'area', 'amenities', 'description'
            ],
            'analysis_focus': [
                'pricing vs location', 'property features', 'unique amenities',
                'market positioning', 'investment highlights'
            ],
            'qna_style': 'Answer as a property analyst comparing real estate listings.'
        },
        'restaurant': {
            'name': 'Restaurant & Food',
            'parameters': [
                'restaurant_name', 'cuisine', 'rating', 'price_range', 'location',
                'menu_items', 'reviews', 'hours'
            ],
            'analysis_focus': [
                'dining experience', 'menu highlights', 'price positioning',
                'customer sentiment', 'unique value props'
            ],
            'qna_style': 'Answer as a food critic who evaluated the listings.'
        },
        'social_media': {
            'name': 'Social Media',
            'parameters': [
                'post_content', 'author', 'timestamp', 'likes', 'shares', 'comments',
                'hashtags', 'mentions', 'media_type', 'engagement_metrics'
            ],
            'analysis_focus': [
                'engagement patterns', 'content themes', 'audience sentiment',
                'viral potential', 'influencer identification'
            ],
            'qna_style': 'Answer as a social media analyst focusing on engagement and trends.'
        },
        'education': {
            'name': 'Education & Courses',
            'parameters': [
                'course_title', 'instructor', 'duration', 'price', 'rating', 'enrollment_count',
                'curriculum', 'prerequisites', 'certification', 'description'
            ],
            'analysis_focus': [
                'course value proposition', 'pricing competitiveness', 'content quality indicators',
                'instructor credibility', 'student outcomes'
            ],
            'qna_style': 'Answer as an education consultant evaluating course offerings.'
        },
        'healthcare': {
            'name': 'Healthcare & Medical',
            'parameters': [
                'provider_name', 'specialty', 'location', 'rating', 'reviews', 'services',
                'insurance_accepted', 'availability', 'credentials', 'contact_info'
            ],
            'analysis_focus': [
                'service quality indicators', 'patient satisfaction', 'accessibility factors',
                'specialization areas', 'trust signals'
            ],
            'qna_style': 'Answer as a healthcare analyst focusing on provider information and patient experience.'
        },
        'travel': {
            'name': 'Travel & Tourism',
            'parameters': [
                'destination', 'accommodation', 'price', 'rating', 'amenities', 'location',
                'availability', 'reviews', 'images', 'booking_info'
            ],
            'analysis_focus': [
                'value for money', 'location advantages', 'amenity comparisons',
                'guest satisfaction', 'booking convenience'
            ],
            'qna_style': 'Answer as a travel advisor comparing destinations and accommodations.'
        },
        'technology': {
            'name': 'Technology & Software',
            'parameters': [
                'product_name', 'version', 'price', 'features', 'specifications', 'reviews',
                'compatibility', 'support', 'license_type', 'documentation'
            ],
            'analysis_focus': [
                'feature differentiation', 'pricing models', 'user satisfaction',
                'technical capabilities', 'market positioning'
            ],
            'qna_style': 'Answer as a technology analyst evaluating software and tech products.'
        },
        'legal': {
            'name': 'Legal Services',
            'parameters': [
                'firm_name', 'practice_areas', 'attorney_names', 'location', 'experience',
                'case_results', 'reviews', 'contact_info', 'consultation_fee'
            ],
            'analysis_focus': [
                'expertise areas', 'client satisfaction', 'success indicators',
                'service accessibility', 'professional credentials'
            ],
            'qna_style': 'Answer as a legal services analyst focusing on firm capabilities and client outcomes.'
        },
        'entertainment': {
            'name': 'Entertainment & Media',
            'parameters': [
                'title', 'genre', 'rating', 'release_date', 'cast', 'director', 'reviews',
                'streaming_platform', 'duration', 'synopsis'
            ],
            'analysis_focus': [
                'content quality', 'audience reception', 'genre trends',
                'platform availability', 'critical acclaim'
            ],
            'qna_style': 'Answer as an entertainment critic analyzing media content and audience response.'
        },
        'sports': {
            'name': 'Sports & Fitness',
            'parameters': [
                'event_name', 'date', 'teams', 'scores', 'venue', 'ticket_price',
                'player_stats', 'league', 'broadcast_info', 'highlights'
            ],
            'analysis_focus': [
                'performance metrics', 'event details', 'ticketing information',
                'fan engagement', 'statistical trends'
            ],
            'qna_style': 'Answer as a sports analyst focusing on events, statistics, and performance data.'
        },
        'automotive': {
            'name': 'Automotive',
            'parameters': [
                'make', 'model', 'year', 'price', 'mileage', 'condition', 'features',
                'location', 'seller_info', 'specifications', 'images'
            ],
            'analysis_focus': [
                'value assessment', 'condition indicators', 'feature comparisons',
                'market pricing', 'seller credibility'
            ],
            'qna_style': 'Answer as an automotive analyst evaluating vehicles and market value.'
        },
        'fashion': {
            'name': 'Fashion & Clothing',
            'parameters': [
                'product_name', 'brand', 'price', 'size', 'color', 'material', 'style',
                'availability', 'reviews', 'images', 'care_instructions'
            ],
            'analysis_focus': [
                'style trends', 'price positioning', 'quality indicators',
                'brand reputation', 'customer satisfaction'
            ],
            'qna_style': 'Answer as a fashion analyst evaluating products and trends.'
        },
        'books': {
            'name': 'Books & Literature',
            'parameters': [
                'title', 'author', 'isbn', 'price', 'rating', 'reviews', 'publication_date',
                'genre', 'publisher', 'page_count', 'description'
            ],
            'analysis_focus': [
                'literary quality', 'reader reception', 'genre classification',
                'pricing comparison', 'author reputation'
            ],
            'qna_style': 'Answer as a literary analyst evaluating books and reader feedback.'
        },
        'events': {
            'name': 'Events & Conferences',
            'parameters': [
                'event_name', 'date', 'location', 'venue', 'ticket_price', 'speakers',
                'agenda', 'attendee_count', 'registration_info', 'description'
            ],
            'analysis_focus': [
                'event value', 'speaker quality', 'networking opportunities',
                'pricing competitiveness', 'attendee experience'
            ],
            'qna_style': 'Answer as an events analyst evaluating conferences and gatherings.'
        },
        'general': {
            'name': 'General',
            'parameters': ['title', 'content', 'images', 'links', 'metadata'],
            'analysis_focus': [
                'content structure', 'key information', 'call-to-action clarity',
                'trust indicators', 'unique insights'
            ],
            'qna_style': 'Answer as a general web analyst summarizing the page.'
        }
    }

    ANALYSIS_TEMPLATE = """
You are an expert analyst reviewing data from a {domain_name} website.
Summarize findings tailored to this domain and the user's instruction.

Extracted Data (JSON):
{extracted_data}

User Instruction:
{instruction}

Domain-Focused Considerations:
- {focus_1}
- {focus_2}
- {focus_3}

Produce STRICT JSON with this schema:
{{
  "summary": "2-3 sentence overview",
  "key_points": ["bullet 1", "bullet 2", "bullet 3"],
  "insights": ["deeper insight 1", "insight 2"],
  "user_request_answer": "direct answer to the instruction",
  "opportunities": ["optional opportunity 1", "optional opportunity 2"],
  "risks": ["optional risk 1", "optional risk 2"],
  "next_steps": ["optional action 1", "optional action 2"]
}}

Return ONLY valid JSON with double quotes.
"""

    QNA_TEMPLATE = """
You are answering a user question about previously scraped {domain_name} websites.

SMART CONTEXT USAGE INSTRUCTIONS:
- You have been provided with data from MULTIPLE websites (see the "websites" array in the context below)
- Analyze the question to determine which websites are relevant:

  **INCLUDE ALL WEBSITES ONLY WHEN:**
  - Question explicitly asks for comparison ("which", "better", "more", "compare", "versus", "vs")
  - Question asks about competitive landscape, market share, or relative positioning
  - Question asks "which company/website" or "which has more/less"
  - Question requires comparing multiple entities

  **FOCUS ON RELEVANT WEBSITE(S) WHEN:**
  - Question is about a specific company, product, or entity (e.g., "NVIDIA", "AMD", specific brand)
  - Question asks "what", "how", "why" about a specific topic without comparison
  - Question is about features, capabilities, or details of one entity
  - Only include other websites if they provide relevant context (e.g., competitive mentions, partnerships)

- Clearly indicate which website each piece of information comes from
- Do NOT include irrelevant information from other websites just because it's available
- If the question is about one company, focus on that company's data unless comparison is needed

Context Data (JSON):
{context}

Question:
{question}

Guidance: {qna_style}

Return JSON:
{{
  "answer": "focused answer that uses only relevant websites. Include comparisons only when the question requires it.",
  "supporting_points": ["evidence 1 from [FULL WEBSITE URL starting with http:// or https://]", "evidence 2 from [FULL WEBSITE URL starting with http:// or https://]"],
  "confidence": "high | medium | low"
}}

IMPORTANT: For supporting_points, always use the FULL URL (e.g., https://www.britannica.com/money/NVIDIA-Corporation) not just the domain name (e.g., britannica.com). The URL should be clickable and complete.
"""

    @staticmethod
    def get_domain_prompt(domain: str, instruction: str = None) -> str:
        """Prompt for the extraction (LLM sees cleaned HTML)."""
        domain_info = DomainAnalyzer.DOMAINS.get(domain, DomainAnalyzer.DOMAINS['general'])
        parameters = ', '.join(domain_info['parameters'])
        user_instruction = instruction or 'Extract all relevant information.'

        return f"""You are an expert data extractor for {domain_info['name']} websites.
Extract the user's requested information plus important {domain_info['name']} signals.

Key fields to look for: {parameters}
User request: {user_instruction}

Return well-structured JSON using arrays where multiple values exist.
Include nested objects if needed (e.g., products, articles, jobs).
Return ONLY valid JSON without markdown fences."""

    @staticmethod
    def get_analysis_prompt(domain: str, extracted_data: Dict[str, Any], instruction: str, language: str = 'en') -> str:
        """Prompt for generating summary/insights/key points. Supports multilingual content."""
        domain_info = DomainAnalyzer.DOMAINS.get(domain, DomainAnalyzer.DOMAINS['general'])
        focus = domain_info['analysis_focus']
        serialized = json.dumps(extracted_data, indent=2, ensure_ascii=False)[:4000]
        
        language_note = f"\nNote: The extracted data may contain content in {language.upper()} language. Please provide analysis in the same language or as requested by the user." if language != 'en' else ""

        return DomainAnalyzer.ANALYSIS_TEMPLATE.format(
            domain_name=domain_info['name'],
            extracted_data=serialized,
            instruction=instruction or 'Summarize the extracted findings.',
            focus_1=focus[0],
            focus_2=focus[1] if len(focus) > 1 else focus[0],
            focus_3=focus[2] if len(focus) > 2 else focus[0],
        ) + language_note

    @staticmethod
    def build_qna_prompt(domain: str, aggregated_results: List[Dict[str, Any]], question: str, user_instruction: str = '') -> str:
        domain_info = DomainAnalyzer.DOMAINS.get(domain, DomainAnalyzer.DOMAINS['general'])
        
        # Add website identifiers and ensure all websites are included
        websites_data = []
        for idx, result in enumerate(aggregated_results, 1):
            url = result.get('url', f'Website {idx}')
            # Extract domain name from URL for better identification
            try:
                from urllib.parse import urlparse
                domain_name = urlparse(url).netloc.replace('www.', '')
            except:
                domain_name = url
            
            websites_data.append({
                'website_number': idx,
                'website_name': domain_name,
                'url': url,
                'extracted_data': result.get('extracted_data', {}),
                'analysis': result.get('analysis', {}),
            })
        
        payload = {
            'domain': domain_info['name'],
            'user_instruction': user_instruction,
            'total_websites': len(aggregated_results),
            'websites': websites_data
        }
        
        # Increase limit and ensure balanced truncation
        data = json.dumps(payload, indent=2, ensure_ascii=False)
        # If too long, try to balance truncation across websites
        if len(data) > 8000:
            # Truncate each website's data proportionally
            max_per_website = 8000 // len(websites_data) if websites_data else 2000
            for website in websites_data:
                if 'extracted_data' in website:
                    extracted_str = json.dumps(website['extracted_data'], ensure_ascii=False)
                    if len(extracted_str) > max_per_website:
                        # Try to keep structure but truncate content
                        try:
                            truncated = extracted_str[:max_per_website]
                            # Try to close any open JSON structures
                            if truncated.count('{') > truncated.count('}'):
                                truncated += '...}'
                            website['extracted_data'] = json.loads(truncated) if truncated.endswith('}') else {'truncated': True, 'preview': truncated[:500]}
                        except:
                            website['extracted_data'] = {'truncated': True, 'preview': extracted_str[:max_per_website]}
            data = json.dumps(payload, indent=2, ensure_ascii=False)[:10000]
        
        return DomainAnalyzer.QNA_TEMPLATE.format(
            domain_name=domain_info['name'],
            context=data,
            question=question,
            qna_style=domain_info['qna_style']
        )

    @staticmethod
    def generate_comparison(all_results: List[Dict[str, Any]], domain: str, user_instruction: str = '') -> Dict[str, Any]:
        """Generate comparison analysis for multiple websites."""
        if len(all_results) < 2:
            return {'message': 'Comparison requires at least 2 websites'}

        domain_info = DomainAnalyzer.DOMAINS.get(domain, DomainAnalyzer.DOMAINS['general'])

        comparison_payload = []
        individual_answers = []
        for result in all_results:
            extracted = result.get('data', {}).get('extracted_data', {})
            analysis = result.get('data', {}).get('analysis', {})
            # Limit extracted data size to prevent timeout
            extracted_str = json.dumps(extracted, indent=2, ensure_ascii=False)
            if len(extracted_str) > 3000:
                extracted_str = extracted_str[:3000] + "... (truncated)"
                try:
                    extracted = json.loads(extracted_str.replace("... (truncated)", ""))
                except:
                    extracted = {"note": "Data too large, summary only"}
            
            comparison_payload.append({
                'url': result.get('url'),
                'summary': analysis.get('summary', ''),
                'key_points': analysis.get('key_points', [])[:5],  # Limit to 5 key points
                'user_request_answer': analysis.get('user_request_answer', ''),
                'extracted_data': extracted
            })
            
            # Collect individual answers for cross-website synthesis
            if analysis.get('user_request_answer'):
                individual_answers.append({
                    'url': result.get('url'),
                    'answer': analysis.get('user_request_answer')
                })
        
        comparison_json = json.dumps(comparison_payload, indent=2, ensure_ascii=False)[:5000]
        individual_answers_json = json.dumps(individual_answers, indent=2, ensure_ascii=False)[:2000]

        # Enhanced comparison prompt with cross-website extraction recommendation
        comparison_prompt = (
            f"You are comparing {len(all_results)} {domain_info['name']} websites.\n\n"
            f"User's Original Request/Instruction: {user_instruction or 'Extract and analyze relevant information from these websites'}\n\n"
            f"Comparison Data (JSON):\n{comparison_json}\n\n"
            f"Individual Website Answers to User Request:\n{individual_answers_json}\n\n"
            "Based on the user's request and the data from all websites, provide a comprehensive comparison.\n\n"
            "IMPORTANT: Generate a cross-website 'user_request_answer' that synthesizes what should be extracted across ALL websites. "
            "This should be more comprehensive than individual answers - it should identify:\n"
            "- Common data patterns across all websites\n"
            "- Unique data available on specific websites\n"
            "- Recommended extraction strategy that works across all sites\n"
            "- Key insights that emerge from comparing the extraction results\n\n"
            "Deliver JSON with:\n"
            "{\n"
            '  "summary": "overall comparison summary (2-3 sentences)",\n'
            '  "user_request_answer": "comprehensive cross-website answer to what should be extracted, synthesizing insights from all websites. This should be actionable and helpful.",\n'
            '  "similarities": ["shared trait 1", "shared trait 2"],\n'
            '  "differences": ["difference 1", "difference 2"],\n'
            '  "websites": {\n'
            '    "url": {\n'
            '      "pros": ["pro 1", "pro 2"],\n'
            '      "cons": ["con 1", "con 2"],\n'
            '      "notable_features": ["feature 1"],\n'
            '      "best_for": "who benefits most",\n'
            '      "score": 0-10\n'
            '    }\n'
            '  },\n'
            '  "comparison_table": {\n'
            '    "metrics": ["metric 1", "metric 2"],\n'
            '    "rows": [\n'
            '      {"metric": "Example", "values": {"url_1": "value", "url_2": "value"}}\n'
            '    ]\n'
            '  },\n'
            '  "extraction_recommendations": {\n'
            '    "common_fields": ["field available on all sites", "another common field"],\n'
            '    "unique_fields": {"url": ["field only on this site"]},\n'
            '    "best_practices": ["recommendation 1", "recommendation 2"]\n'
            '  },\n'
            '  "recommendation": "final takeaway / which site suits which scenario"\n'
            "}\n\n"
            "Return ONLY valid JSON."
        )

        return {
            'prompt': comparison_prompt,
            'domain': domain,
            'website_count': len(all_results),
            'user_instruction': user_instruction
        }

