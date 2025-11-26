from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import io

from scraper import WebScraper
from database import Database
from domain_analyzer import DomainAnalyzer

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize components
db = Database()
scraper = WebScraper()
domain_analyzer = DomainAnalyzer()
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend', 'dist')


def _rows_from_result(result: dict) -> list:
    """Flatten a result payload for CSV text export."""
    rows = []
    base = {'url': result.get('url', '')}
    data = result.get('data', {}) or {}
    extracted = data.get('extracted_data', {}) or {}
    analysis = data.get('analysis', {}) or {}

    def _push(field, value):
        if value is None or value == '':
            return
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = str(value)
        rows.append({**base, 'field': field, 'value': value_str})

    for key, value in extracted.items():
        _push(f'extracted.{key}', value)

    for key in ['summary', 'user_request_answer']:
        _push(f'analysis.{key}', analysis.get(key))

    for list_key in ['key_points', 'insights', 'opportunities', 'risks', 'next_steps']:
        if analysis.get(list_key):
            _push(
                f'analysis.{list_key}',
                '; '.join(str(item) for item in analysis[list_key]),
            )

    return rows

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve React build if available, otherwise show API status."""
    if path.startswith('api'):
        return jsonify({'message': 'API endpoint'}), 404
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        if path and os.path.exists(os.path.join(FRONTEND_DIST, path)):
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return jsonify({'message': 'AI Scraper API running. Build the frontend to serve UI.'})

@app.route('/api/domains', methods=['GET'])
def get_domains():
    """Get available domains for analysis."""
    domains = {}
    for key, value in DomainAnalyzer.DOMAINS.items():
        domains[key] = {
            'name': value['name'],
            'parameters': value.get('parameters', []),
            'analysis_focus': value.get('analysis_focus', []),
            'description': value.get('description', f"{value['name']} focused analysis"),
        }
    return jsonify({'domains': domains})

@app.route('/api/scrape', methods=['POST'])
def scrape():
    try:
        data = request.json
        urls = data.get('urls', [])
        instruction = data.get('instruction', 'Extract all text content from the page')
        domain = data.get('domain', 'general')
        enable_comparison = data.get('enable_comparison', False)
        task_name = data.get('task_name', f'Scrape {len(urls)} URL(s)')
        tags = data.get('tags', [])
        is_scheduled = data.get('is_scheduled', False)
        schedule_type = data.get('schedule_type')
        schedule_time = data.get('schedule_time')
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        # Validate domain
        if domain not in DomainAnalyzer.DOMAINS:
            domain = 'general'
        
        # Create task in database
        task_id = db.create_task(task_name, urls, instruction, domain)
        
        # Update task with additional fields
        update_data = {
            'total_urls': len(urls),
            'current_url_index': 0
        }
        if tags:
            update_data['tags'] = tags
        if is_scheduled:
            update_data['is_scheduled'] = 1
            update_data['schedule_type'] = schedule_type
            if schedule_time:
                update_data['next_run'] = schedule_time
        db.update_task(task_id, update_data)
        
        # Start scraping with domain-specific prompts and progress tracking
        results = []
        errors = []
        start_time = datetime.now()
        detected_languages = []
        
        for idx, url in enumerate(urls):
            try:
                # Update progress
                progress = {
                    'current': idx + 1,
                    'total': len(urls),
                    'current_url': url,
                    'stage': 'scraping',
                    'message': f'Scraping URL {idx + 1}/{len(urls)}: {url}'
                }
                db.update_task(task_id, {
                    'current_url_index': idx + 1,
                    'progress': progress
                })
                
                # Get domain-specific prompt
                domain_prompt = DomainAnalyzer.get_domain_prompt(domain, instruction)
                
                # Progress callback
                def progress_callback(update):
                    progress['stage'] = update.get('stage', 'scraping')
                    progress['message'] = update.get('message', progress['message'])
                    progress['current'] = idx + 1
                    progress['total'] = len(urls)
                    progress['current_url'] = url
                    db.update_task(task_id, {'progress': progress, 'current_url_index': idx + 1})
                
                result = scraper.scrape_url(url, domain_prompt, user_instruction=instruction, domain=domain, progress_callback=progress_callback)
                
                # Track detected language
                if result.get('language'):
                    detected_languages.append(result['language'])
                
                results.append({
                    'url': url,
                    'status': 'success',
                    'data': result
                })
                
                # Estimate time remaining
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time_per_url = elapsed / (idx + 1)
                remaining_urls = len(urls) - (idx + 1)
                estimated_remaining = int(avg_time_per_url * remaining_urls)
                db.update_task(task_id, {'estimated_time_remaining': estimated_remaining})
                
            except Exception as e:
                errors.append({
                    'url': url,
                    'error': str(e)
                })
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Generate comparison if requested and multiple successful results
        comparison = None
        if enable_comparison and len(urls) > 1:
            successful_results = [r for r in results if r.get('status') == 'success']
            if len(successful_results) >= 2:
                try:
                    db.update_task(task_id, {
                        'progress': {
                            'stage': 'comparing',
                            'message': 'Generating comparison...',
                            'current': len(urls),
                            'total': len(urls)
                        }
                    })
                    comparison = scraper.generate_comparison(successful_results, domain, user_instruction=instruction)
                except Exception as e:
                    comparison = {'error': f'Comparison generation failed: {str(e)}'}
        
        # Determine primary language
        primary_language = max(set(detected_languages), key=detected_languages.count) if detected_languages else 'en'
        
        # Update task with results
        task_data = {
            'status': 'completed',
            'results': results,
            'errors': errors,
            'completed_at': datetime.now().isoformat(),
            'domain': domain,
            'comparison': comparison,
            'language': primary_language,
            'progress': None,  # Clear progress
            'current_url_index': len(urls),
            'estimated_time_remaining': None
        }
        db.update_task(task_id, task_data)
        
        return jsonify({
            'task_id': task_id,
            'status': 'completed',
            'results': results,
            'errors': errors,
            'comparison': comparison,
            'domain': domain,
            'language': primary_language
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        # Get query parameters for filtering and sorting
        filters = {}
        if request.args.get('domain'):
            filters['domain'] = request.args.get('domain')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('starred') is not None:
            filters['starred'] = request.args.get('starred').lower() == 'true'
        if request.args.get('archived') is not None:
            filters['archived'] = request.args.get('archived').lower() == 'true'
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        if request.args.get('tags'):
            filters['tags'] = request.args.get('tags')
        
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'DESC').upper()
        search = request.args.get('search')
        
        tasks = db.get_all_tasks(filters=filters if filters else None, sort_by=sort_by, sort_order=sort_order, search=search)
        return jsonify({'tasks': tasks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task = db.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        return jsonify(task)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/ask', methods=['POST'])
def ask_task_question(task_id):
    """Answer user questions about a completed task."""
    try:
        task = db.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        if task.get('status') != 'completed':
            return jsonify({'error': 'Task is not completed yet'}), 400
        
        data = request.json or {}
        question = data.get('question', '').strip()
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        successful_results = [
            result for result in task.get('results', [])
            if result.get('status') == 'success'
        ]
        if not successful_results:
            return jsonify({'error': 'No successful results to answer from'}), 400
        
        aggregated_context = []
        for result in successful_results:
            aggregated_context.append({
                'url': result.get('url'),
                'extracted_data': result.get('data', {}).get('extracted_data'),
                'analysis': result.get('data', {}).get('analysis'),
            })
        
        answer = scraper.answer_question(
            domain=task.get('domain', 'general'),
            aggregated_results=aggregated_context,
            question=question,
            user_instruction=task.get('instruction', '')
        )
        
        # Post-process supporting points to convert domain references to full URLs
        if answer.get('supporting_points'):
            url_mapping = {}
            for result in successful_results:
                url = result.get('url', '')
                if url:
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc.replace('www.', '')
                        url_mapping[domain] = url
                        # Also map without .com/.org etc
                        domain_base = domain.split('.')[0] if '.' in domain else domain
                        url_mapping[domain_base] = url
                    except:
                        pass
            
            processed_points = []
            for point in answer['supporting_points']:
                # Try to find domain references and replace with full URLs
                processed_point = point
                for domain, full_url in url_mapping.items():
                    # Replace patterns like "(britannica.com)" or "[britannica.com]" with full URL
                    import re
                    # Pattern: (domain.com) or [domain.com]
                    pattern1 = rf'\(({re.escape(domain)})\)'
                    pattern2 = rf'\[({re.escape(domain)})\]'
                    processed_point = re.sub(pattern1, f'({full_url})', processed_point, flags=re.IGNORECASE)
                    processed_point = re.sub(pattern2, f'[{full_url}]', processed_point, flags=re.IGNORECASE)
                    # Pattern: domain.com (without parentheses)
                    pattern3 = rf'\b{re.escape(domain)}\b'
                    if domain in processed_point and full_url not in processed_point:
                        processed_point = re.sub(pattern3, full_url, processed_point, flags=re.IGNORECASE, count=1)
                processed_points.append(processed_point)
            answer['supporting_points'] = processed_points
        
        return jsonify(answer)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/progress', methods=['GET'])
def get_task_progress(task_id):
    """Get current progress of a task."""
    try:
        task = db.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        progress = task.get('progress', {})
        # Ensure progress has current and total
        if not progress or not isinstance(progress, dict):
            progress = {}
        
        # Use current_url_index and total_urls if progress doesn't have current/total
        if 'current' not in progress:
            progress['current'] = task.get('current_url_index', 0)
        if 'total' not in progress:
            progress['total'] = task.get('total_urls', 0)
        
        return jsonify({
            'task_id': task_id,
            'progress': progress,
            'current_url_index': task.get('current_url_index', 0),
            'total_urls': task.get('total_urls', 0),
            'estimated_time_remaining': task.get('estimated_time_remaining'),
            'status': task.get('status')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    try:
        success = db.delete_task(task_id)
        if success:
            return jsonify({'message': 'Task deleted successfully'})
        else:
            return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/bulk-delete', methods=['POST'])
def bulk_delete_tasks():
    """Delete multiple tasks."""
    try:
        data = request.json
        task_ids = data.get('task_ids', [])
        if not task_ids:
            return jsonify({'error': 'No task IDs provided'}), 400
        
        deleted_count = db.delete_tasks_bulk(task_ids)
        return jsonify({'message': f'{deleted_count} task(s) deleted successfully', 'deleted_count': deleted_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/star', methods=['POST'])
def toggle_star_task(task_id):
    """Toggle star status of a task."""
    try:
        starred = db.toggle_star(task_id)
        return jsonify({'starred': bool(starred), 'message': 'Task starred' if starred else 'Task unstarred'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/archive', methods=['POST'])
def toggle_archive_task(task_id):
    """Toggle archive status of a task."""
    try:
        archived = db.toggle_archive(task_id)
        return jsonify({'archived': bool(archived), 'message': 'Task archived' if archived else 'Task unarchived'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/tags', methods=['PUT'])
def update_task_tags(task_id):
    """Update tags for a task."""
    try:
        data = request.json
        tags = data.get('tags', [])
        if not isinstance(tags, list):
            return jsonify({'error': 'Tags must be a list'}), 400
        
        db.update_tags(task_id, tags)
        return jsonify({'message': 'Tags updated successfully', 'tags': tags})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/rerun', methods=['POST'])
def rerun_task(task_id):
    """Re-run analysis for an existing task."""
    try:
        task = db.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        data = request.json or {}

        def normalize_urls(value):
            if not value:
                return []
            if isinstance(value, list):
                return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]
            if isinstance(value, str):
                return [item.strip() for item in value.splitlines() if item.strip()]
            return []

        def normalize_tags(value):
            if not value:
                return []
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            if isinstance(value, str):
                return [item.strip() for item in value.split(',') if item.strip()]
            return []

        override_urls = normalize_urls(data.get('urls'))
        urls = override_urls if override_urls else (task.get('urls') or [])
        if not urls:
            return jsonify({'error': 'No URLs found in task'}), 400

        instruction_override = data.get('instruction')
        instruction = (
            instruction_override.strip()
            if isinstance(instruction_override, str) and instruction_override.strip()
            else task.get('instruction', 'Extract all text content from the page')
        )

        domain_override = data.get('domain')
        domain_candidate = (
            domain_override.strip()
            if isinstance(domain_override, str) and domain_override.strip()
            else task.get('domain', 'general')
        )
        domain = domain_candidate if domain_candidate in DomainAnalyzer.DOMAINS else 'general'

        task_name_override = data.get('task_name')
        if isinstance(task_name_override, str) and task_name_override.strip():
            task_name = task_name_override.strip()
        else:
            task_name = task.get('name') or f'Task #{task_id}'

        tags_override = data.get('tags')
        if tags_override is not None:
            tags = normalize_tags(tags_override)
        else:
            tags = task.get('tags') or []

        comparison_data = task.get('comparison')
        enable_comparison_override = data.get('enable_comparison')
        if enable_comparison_override is None:
            if comparison_data and isinstance(comparison_data, dict):
                enable_comparison = 'error' not in comparison_data
            else:
                enable_comparison = len(urls) > 1
        else:
            enable_comparison = bool(enable_comparison_override)

        # Reset task status and clear old results
        db.update_task(task_id, {
            'status': 'processing',
            'name': task_name,
            'urls': urls,
            'instruction': instruction,
            'domain': domain,
            'tags': tags,
            'results': None,
            'errors': None,
            'comparison': None,
            'completed_at': None,
            'progress': None,
            'current_url_index': 0,
            'total_urls': len(urls),
            'estimated_time_remaining': None
        })
        
        # Start scraping with domain-specific prompts and progress tracking
        results = []
        errors = []
        start_time = datetime.now()
        detected_languages = []
        
        for idx, url in enumerate(urls):
            try:
                # Update progress
                progress = {
                    'current': idx + 1,
                    'total': len(urls),
                    'current_url': url,
                    'stage': 'scraping',
                    'message': f'Scraping URL {idx + 1}/{len(urls)}: {url}'
                }
                db.update_task(task_id, {
                    'current_url_index': idx + 1,
                    'progress': progress
                })
                
                # Get domain-specific prompt
                domain_prompt = DomainAnalyzer.get_domain_prompt(domain, instruction)
                
                # Progress callback
                def progress_callback(update):
                    progress['stage'] = update.get('stage', 'scraping')
                    progress['message'] = update.get('message', progress['message'])
                    progress['current'] = idx + 1
                    progress['total'] = len(urls)
                    progress['current_url'] = url
                    db.update_task(task_id, {'progress': progress, 'current_url_index': idx + 1})
                
                result = scraper.scrape_url(url, domain_prompt, user_instruction=instruction, domain=domain, progress_callback=progress_callback)
                
                # Track detected language
                if result.get('language'):
                    detected_languages.append(result['language'])
                
                results.append({
                    'url': url,
                    'status': 'success',
                    'data': result
                })
                
                # Estimate time remaining
                elapsed = (datetime.now() - start_time).total_seconds()
                avg_time_per_url = elapsed / (idx + 1)
                remaining_urls = len(urls) - (idx + 1)
                estimated_remaining = int(avg_time_per_url * remaining_urls)
                db.update_task(task_id, {'estimated_time_remaining': estimated_remaining})
                
            except Exception as e:
                errors.append({
                    'url': url,
                    'error': str(e)
                })
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        # Generate comparison if enabled and we have at least 2 successful results
        comparison = None
        if enable_comparison and len(urls) > 1:
            successful_results = [r for r in results if r.get('status') == 'success']
            if len(successful_results) >= 2:
                try:
                    db.update_task(task_id, {
                        'progress': {
                            'stage': 'comparing',
                            'message': 'Generating comparison...',
                            'current': len(urls),
                            'total': len(urls)
                        }
                    })
                    comparison = scraper.generate_comparison(successful_results, domain, user_instruction=instruction)
                except Exception as e:
                    comparison = {'error': f'Comparison generation failed: {str(e)}'}
        
        # Determine primary language
        primary_language = max(set(detected_languages), key=detected_languages.count) if detected_languages else 'en'
        
        # Update task with results
        db.update_task(task_id, {
            'results': json.dumps(results),
            'errors': json.dumps(errors),
            'status': 'completed' if results else 'error',
            'completed_at': datetime.now().isoformat(),
            'language': primary_language,
            'progress': None,
            'estimated_time_remaining': None
        })
        
        # Save comparison if generated
        if comparison:
            db.update_task(task_id, {'comparison': json.dumps(comparison)})
        
        return jsonify({
            'task_id': task_id,
            'message': 'Analysis re-run completed successfully',
            'status': 'completed' if results else 'error'
        })
        
    except Exception as e:
        db.update_task(task_id, {'status': 'error'})
        return jsonify({'error': str(e)}), 500

@app.route('/api/schedule', methods=['POST'])
def schedule_task():
    """Schedule a recurring scraping task."""
    try:
        from scheduler import TaskScheduler
        scheduler = TaskScheduler(db, scraper)
        
        data = request.json
        task_name = data.get('task_name', 'Scheduled Task')
        urls = data.get('urls', [])
        instruction = data.get('instruction', 'Extract all text content from the page')
        schedule_type = data.get('schedule_type')  # 'once', 'daily', 'weekly'
        schedule_time = data.get('schedule_time')
        domain = data.get('domain', 'general')
        tags = data.get('tags', [])
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        if not schedule_type or not schedule_time:
            return jsonify({'error': 'Schedule type and time are required'}), 400
        
        task_id = scheduler.schedule_task(task_name, urls, instruction, schedule_type, schedule_time, domain)
        
        # Update task with domain and tags
        update_data = {'domain': domain, 'is_scheduled': 1, 'schedule_type': schedule_type}
        if schedule_time:
            update_data['next_run'] = schedule_time
        if tags:
            update_data['tags'] = tags
        db.update_task(task_id, update_data)
        
        return jsonify({
            'task_id': task_id,
            'message': 'Task scheduled successfully',
            'schedule_type': schedule_type,
            'next_run': schedule_time
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<int:task_id>/<format>', methods=['GET'])
def download_results(task_id, format):
    try:
        task = db.get_task(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        results = task.get('results', [])
        if not results:
            return jsonify({'error': 'No results available'}), 404
        
        if format == 'json':
            output = json.dumps(results, indent=2, ensure_ascii=False)
            return send_file(
                io.BytesIO(output.encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'task_{task_id}_results.json'
            )
        
        elif format == 'csv':
            import pandas as pd
            from io import StringIO
            
            rows = []
            for result in results:
                if result.get('status') == 'success':
                    rows.extend(_rows_from_result(result))
            
            if not rows:
                return jsonify({'error': 'No data to export'}), 404
            
            df = pd.DataFrame(rows)
            output = StringIO()
            df.to_csv(output, index=False)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'task_{task_id}_results.csv'
            )
        
        elif format == 'txt':
            output_lines = []
            for result in results:
                output_lines.append(f"URL: {result.get('url', 'N/A')}")
                output_lines.append(f"Status: {result.get('status', 'N/A')}")
                if result.get('status') == 'success':
                    data = result.get('data', {})
                    analysis = data.get('analysis', {})
                    output_lines.append(f"Summary: {analysis.get('summary', 'N/A')}")
                    output_lines.append(f"Key Points: {', '.join(analysis.get('key_points', []) or ['N/A'])}")
                    output_lines.append(f"Insights: {', '.join(analysis.get('insights', []) or ['N/A'])}")
                    output_lines.append(f"Answer: {analysis.get('user_request_answer', 'N/A')}")
                else:
                    output_lines.append(f"Error: {result.get('error', 'Unknown error')}")
                output_lines.append("-" * 80)
            
            output = '\n'.join(output_lines)
            return send_file(
                io.BytesIO(output.encode('utf-8')),
                mimetype='text/plain',
                as_attachment=True,
                download_name=f'task_{task_id}_results.txt'
            )
        
        else:
            return jsonify({'error': 'Invalid format. Use json, csv, or txt'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

