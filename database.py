import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path='scraping_db.sqlite'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                urls TEXT NOT NULL,
                instruction TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                results TEXT,
                errors TEXT,
                domain TEXT DEFAULT 'general',
                comparison TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        ''')
        
        # Add domain and comparison columns if they don't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN domain TEXT DEFAULT "general"')
        except:
            pass
        try:
            cursor.execute('ALTER TABLE tasks ADD COLUMN comparison TEXT')
        except:
            pass
        
        # Add new columns for enhanced features
        new_columns = [
            ('tags', 'TEXT'),
            ('starred', 'INTEGER DEFAULT 0'),
            ('archived', 'INTEGER DEFAULT 0'),
            ('progress', 'TEXT'),
            ('current_url_index', 'INTEGER DEFAULT 0'),
            ('total_urls', 'INTEGER DEFAULT 0'),
            ('estimated_time_remaining', 'INTEGER'),
            ('language', 'TEXT'),
            ('is_scheduled', 'INTEGER DEFAULT 0'),
            ('schedule_type', 'TEXT'),
            ('next_run', 'TEXT')
        ]
        
        for col_name, col_type in new_columns:
            try:
                cursor.execute(f'ALTER TABLE tasks ADD COLUMN {col_name} {col_type}')
            except:
                pass
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                schedule_type TEXT NOT NULL,
                schedule_time TEXT,
                next_run TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_task(self, name: str, urls: List[str], instruction: str, domain: str = 'general') -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tasks (name, urls, instruction, domain, status, created_at)
            VALUES (?, ?, ?, ?, 'processing', ?)
        ''', (name, json.dumps(urls), instruction, domain, datetime.now().isoformat()))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def update_task(self, task_id: int, updates: Dict):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            # Convert complex types to JSON strings for TEXT columns
            if key in ['results', 'errors', 'comparison', 'tags', 'progress']:
                if value is not None:
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    elif value == '':
                        value = None
                else:
                    value = None
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    def get_task(self, task_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        task = dict(zip(columns, row))
        
        # Parse JSON fields
        if task.get('urls'):
            task['urls'] = json.loads(task['urls'])
        if task.get('results'):
            task['results'] = json.loads(task['results'])
        if task.get('errors'):
            task['errors'] = json.loads(task['errors'])
        if task.get('comparison'):
            task['comparison'] = json.loads(task['comparison'])
        
        # Parse tags - ensure it's always an array
        if task.get('tags'):
            try:
                if isinstance(task['tags'], str):
                    task['tags'] = json.loads(task['tags'])
                elif not isinstance(task['tags'], list):
                    task['tags'] = []
            except:
                task['tags'] = []
        else:
            task['tags'] = []
        
        return task
    
    def get_all_tasks(self, filters: Optional[Dict] = None, sort_by: str = 'created_at', sort_order: str = 'DESC', search: Optional[str] = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM tasks WHERE 1=1'
        params = []
        
        # Apply filters
        if filters:
            if filters.get('domain'):
                query += ' AND domain = ?'
                params.append(filters['domain'])
            if filters.get('status'):
                query += ' AND status = ?'
                params.append(filters['status'])
            if filters.get('starred') is not None:
                query += ' AND starred = ?'
                params.append(1 if filters['starred'] else 0)
            if filters.get('archived') is not None:
                query += ' AND archived = ?'
                params.append(1 if filters['archived'] else 0)
            if filters.get('date_from'):
                query += ' AND created_at >= ?'
                params.append(filters['date_from'])
            if filters.get('date_to'):
                query += ' AND created_at <= ?'
                params.append(filters['date_to'])
            if filters.get('tags'):
                query += ' AND tags LIKE ?'
                params.append(f"%{filters['tags']}%")
        
        # Apply search
        if search:
            query += ' AND (name LIKE ? OR urls LIKE ? OR instruction LIKE ?)'
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        # Apply sorting
        valid_sort_fields = ['created_at', 'name', 'status', 'domain', 'completed_at']
        if sort_by in valid_sort_fields:
            query += f' ORDER BY {sort_by} {sort_order}'
        else:
            query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        columns = [desc[0] for desc in cursor.description]
        tasks = []
        
        for row in rows:
            task = dict(zip(columns, row))
            if task.get('urls'):
                task['urls'] = json.loads(task['urls'])
            if task.get('results'):
                task['results'] = json.loads(task['results'])
            if task.get('errors'):
                task['errors'] = json.loads(task['errors'])
            if task.get('comparison'):
                task['comparison'] = json.loads(task['comparison'])
            if task.get('tags'):
                try:
                    if isinstance(task['tags'], str):
                        task['tags'] = json.loads(task['tags'])
                    elif not isinstance(task['tags'], list):
                        task['tags'] = []
                except:
                    task['tags'] = []
            else:
                task['tags'] = []
            if task.get('progress'):
                try:
                    task['progress'] = json.loads(task['progress']) if isinstance(task['progress'], str) else task['progress']
                except:
                    task['progress'] = {}
            tasks.append(task)
        
        return tasks
    
    def delete_task(self, task_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
    
    def delete_tasks_bulk(self, task_ids: List[int]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        placeholders = ','.join('?' * len(task_ids))
        cursor.execute(f'DELETE FROM tasks WHERE id IN ({placeholders})', task_ids)
        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()
        return deleted_count
    
    def toggle_star(self, task_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET starred = NOT starred WHERE id = ?', (task_id,))
        conn.commit()
        cursor.execute('SELECT starred FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else False
    
    def toggle_archive(self, task_id: int) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET archived = NOT archived WHERE id = ?', (task_id,))
        conn.commit()
        cursor.execute('SELECT archived FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else False
    
    def update_tags(self, task_id: int, tags: List[str]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE tasks SET tags = ? WHERE id = ?', (json.dumps(tags), task_id))
        conn.commit()
        conn.close()

