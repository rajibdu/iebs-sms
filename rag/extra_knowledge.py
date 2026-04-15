import json
from .database import get_connection, init_db

def search_extra(query, category='all'):
    """Admin-added extra knowledge থেকে search।"""
    try:
        init_db()
        conn = get_connection()
        cursor = conn.cursor()

        query_lower = query.lower()
        words = [w for w in query_lower.split() if len(w) > 1]

        if not words:
            conn.close()
            return []

        conditions = ' OR '.join(['content LIKE ? OR topic LIKE ? OR keywords LIKE ?' for _ in words])
        params = []
        for w in words:
            params.extend([f'%{w}%', f'%{w}%', f'%{w}%'])

        if category != 'all':
            conditions = f"({conditions}) AND category = ?"
            params.append(category)

        cursor.execute(
            f'SELECT * FROM extra_knowledge WHERE {conditions} LIMIT 5',
            params
        )
        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            item = dict(row)
            try:
                item['links'] = json.loads(item.get('links') or '[]')
            except Exception:
                item['links'] = []
            try:
                item['keywords'] = json.loads(item.get('keywords') or '[]')
            except Exception:
                item['keywords'] = []
            results.append(item)
        return results
    except Exception:
        return []

def add_extra(category, topic, keywords, content, source, links):
    """Admin থেকে extra knowledge যোগ করো।"""
    try:
        init_db()
        conn = get_connection()
        conn.execute(
            'INSERT INTO extra_knowledge (category, topic, keywords, content, source, links) VALUES (?, ?, ?, ?, ?, ?)',
            (category, topic, json.dumps(keywords), content, source, json.dumps(links))
        )
        conn.commit()
        conn.close()
        return True, "সফলভাবে যোগ হয়েছে"
    except Exception as e:
        return False, str(e)

def get_all_extra():
    try:
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM extra_knowledge ORDER BY added_at DESC')
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []

def delete_extra(item_id):
    try:
        conn = get_connection()
        conn.execute('DELETE FROM extra_knowledge WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
