from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
import sqlite3
import json
from typing import Dict, List

class TaskScheduler:
    def __init__(self, db, scraper):
        self.db = db
        self.scraper = scraper
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    def schedule_task(self, task_name: str, urls: List[str], instruction: str, 
                     schedule_type: str, schedule_time: str, domain: str = 'general') -> int:
        """Schedule a scraping task."""
        # Create task in database
        task_id = self.db.create_task(task_name, urls, instruction, domain=domain)
        
        # Parse schedule_time
        if schedule_type == 'once':
            # schedule_time should be ISO format datetime
            run_date = datetime.fromisoformat(schedule_time)
            self.scheduler.add_job(
                self._execute_task,
                DateTrigger(run_date=run_date),
                args=[task_id, urls, instruction, domain],
                id=f'task_{task_id}'
            )
        
        elif schedule_type == 'daily':
            # schedule_time should be time format (HH:MM) or datetime-local
            hour, minute = 0, 0
            try:
                # Try parsing as datetime-local first
                if 'T' in schedule_time or len(schedule_time) > 10:
                    dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
                    hour, minute = dt.hour, dt.minute
                else:
                    # Try HH:MM format
                    time_parts = schedule_time.split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                    else:
                        raise ValueError(f"Invalid time format: {schedule_time}")
            except Exception as e:
                raise ValueError(f"Failed to parse schedule_time for daily task: {schedule_time}. Error: {str(e)}")
            
            self.scheduler.add_job(
                self._execute_task,
                CronTrigger(hour=hour, minute=minute),
                args=[task_id, urls, instruction, domain],
                id=f'task_{task_id}',
                replace_existing=True
            )
        
        elif schedule_type == 'weekly':
            # schedule_time should be datetime-local format (includes day)
            hour, minute = 0, 0
            day_of_week = 0  # Default to Monday
            try:
                # Try parsing as datetime-local first
                if 'T' in schedule_time or len(schedule_time) > 10:
                    dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
                    day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
                    hour, minute = dt.hour, dt.minute
                else:
                    # Fallback: try "DAY HH:MM" format
                    parts = schedule_time.split(' ', 1)
                    if len(parts) == 2:
                        day_name, time_str = parts
                        time_parts = time_str.split(':')
                        if len(time_parts) >= 2:
                            hour = int(time_parts[0])
                            minute = int(time_parts[1])
                        else:
                            raise ValueError(f"Invalid time format in: {schedule_time}")
                        
                        day_map = {
                            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                            'friday': 4, 'saturday': 5, 'sunday': 6
                        }
                        day_of_week = day_map.get(day_name.lower(), 0)
                    else:
                        raise ValueError(f"Invalid weekly format: {schedule_time}. Expected 'DAY HH:MM' or datetime-local")
            except Exception as e:
                raise ValueError(f"Failed to parse schedule_time for weekly task: {schedule_time}. Error: {str(e)}")
            
            self.scheduler.add_job(
                self._execute_task,
                CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute),
                args=[task_id, urls, instruction, domain],
                id=f'task_{task_id}',
                replace_existing=True
            )
        
        return task_id
    
    def _execute_task(self, task_id: int, urls: List[str], instruction: str, domain: str = 'general'):
        """Execute a scheduled scraping task."""
        try:
            from domain_analyzer import DomainAnalyzer
            
            results = []
            errors = []
            detected_languages = []
            
            # Get task details
            task = self.db.get_task(task_id)
            if not task:
                return
            
            domain = task.get('domain', 'general')
            domain_prompt = DomainAnalyzer.get_domain_prompt(domain, instruction)
            
            for url in urls:
                try:
                    result = self.scraper.scrape_url(url, domain_prompt, user_instruction=instruction, domain=domain)
                    
                    # Track detected language
                    if result.get('language'):
                        detected_languages.append(result['language'])
                    
                    results.append({
                        'url': url,
                        'status': 'success',
                        'data': result
                    })
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
            
            # Determine primary language
            primary_language = max(set(detected_languages), key=detected_languages.count) if detected_languages else 'en'
            
            # Update task with results
            self.db.update_task(task_id, {
                'status': 'completed',
                'results': results,
                'errors': errors,
                'completed_at': datetime.now().isoformat(),
                'language': primary_language,
                'progress': None,
                'current_url_index': len(urls),
                'estimated_time_remaining': None
            })
        
        except Exception as e:
            self.db.update_task(task_id, {
                'status': 'error',
                'errors': [{'error': str(e)}],
                'completed_at': datetime.now().isoformat()
            })

