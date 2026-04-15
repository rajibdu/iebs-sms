import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from rag import (
    init_db, search_knowledge, get_all_knowledge,
    search_extra, add_extra, get_all_extra, delete_extra,
    generate_answer, get_history
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'iebs-sms-2024-secret')

# Railway-এ /tmp ব্যবহার করো, local-এ data/ ব্যবহার করো
data_dir = '/tmp/iebs_data' if os.environ.get('RAILWAY_ENVIRONMENT') else 'data'
os.makedirs(data_dir, exist_ok=True)

init_db()

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'iebs@2024')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized', 'login_required': True}), 401
        return f(*args, **kwargs)
    return decorated

# ─── Pages ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = True
            return redirect(url_for('admin'))
        else:
            error = 'ভুল Username বা Password!'
    return render_template('login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin():
    items = get_all_extra()
    return render_template('admin.html', items=items)

# ─── Chat API ──────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    question = data.get('question', '').strip()
    category = data.get('category', 'all')
    conversation_history = data.get('history', [])

    if not question:
        return jsonify({'error': 'প্রশ্ন লিখুন'}), 400

    kb_items = search_knowledge(question, category)
    extra_items = search_extra(question, category)
    result = generate_answer(
        question, kb_items, extra_items,
        conversation_history=conversation_history
    )
    return jsonify(result)

# ─── Admin API ─────────────────────────────────────────

@app.route('/api/admin/add', methods=['POST'])
@api_login_required
def admin_add():
    data = request.get_json()
    keywords = [k.strip() for k in data.get('keywords', '').split(',') if k.strip()]
    links = []
    if data.get('link_name') and data.get('link_url'):
        links = [{"name": data['link_name'], "url": data['link_url']}]
    success, msg = add_extra(
        category=data.get('category', 'general'),
        topic=data.get('topic', ''),
        keywords=keywords,
        content=data.get('content', ''),
        source=data.get('source', ''),
        links=links
    )
    return jsonify({'success': success, 'message': msg})

@app.route('/api/admin/items')
@api_login_required
def admin_items():
    return jsonify(get_all_extra())

@app.route('/api/admin/delete/<int:item_id>', methods=['DELETE'])
@api_login_required
def admin_delete(item_id):
    ok = delete_extra(item_id)
    return jsonify({'success': ok})

@app.route('/api/history')
@api_login_required
def history():
    return jsonify(get_history(30))

@app.route('/api/stats')
def stats():
    kb_count = len(get_all_knowledge())
    extra_count = len(get_all_extra())
    groq_ready = bool(os.environ.get('GROQ_API_KEY'))
    gemini_ready = bool(os.environ.get('GEMINI_API_KEY'))
    return jsonify({
        'builtin': kb_count,
        'extra': extra_count,
        'total': kb_count + extra_count,
        'api_ready': groq_ready or gemini_ready,
        'groq': groq_ready,
        'gemini': gemini_ready
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
