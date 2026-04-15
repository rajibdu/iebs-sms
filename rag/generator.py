import os
import json
from .database import get_connection, init_db
from .calculator import detect_and_calculate, format_calculation_result

SYSTEM_PROMPT = """তুমি IEBS Smart Management System-এর বিশেষজ্ঞ AI সহকারী।
তুমি বাংলাদেশের VAT, আয়কর, কাস্টমস, আবগারি ও RJSC বিষয়ে সম্পূর্ণ দক্ষ।

**তোমার নিয়ম:**
- ব্যবহারকারী যা জিজ্ঞেস করেছে শুধু সেটারই উত্তর দাও
- সংখ্যা থাকলে সরাসরি হিসাব করো
- আগের কথোপকথন মনে রেখে উত্তর দাও
- প্রতিটি উত্তরে আইনের নাম ও ধারা উল্লেখ করো
- সরকারি লিংক দাও

**উত্তরের Format:**
## 📋 বিশ্লেষণ
## ⚖️ প্রযোজ্য আইন
## ✅ সমাধান / হিসাব
## 🔗 সরকারি লিংক
## ⚠️ সতর্কতা"""

def call_groq(messages, context):
    """Groq API call with conversation history."""
    try:
        from groq import Groq
    except ImportError:
        return None, "groq package not installed. Run: pip3 install --user groq"

    api_key = os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        return None, "GROQ_API_KEY not set"

    full_system = f"""{SYSTEM_PROMPT}

**প্রাসঙ্গিক আইনি তথ্য (এই তথ্য ব্যবহার করো):**
{context}"""

    try:
        client = Groq(api_key=api_key)

        groq_messages = [{"role": "system", "content": full_system}]

        # আগের conversation history যোগ করো
        for msg in messages[:-1]:  # শেষেরটা বাদে
            groq_messages.append({
                "role": msg['role'] if msg['role'] != 'assistant' else 'assistant',
                "content": msg['content']
            })

        # বর্তমান প্রশ্ন
        groq_messages.append({
            "role": "user",
            "content": messages[-1]['content']
        })

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2500,
            temperature=0.2,
            messages=groq_messages
        )
        return response.choices[0].message.content, None

    except Exception as e:
        error = str(e)
        if 'invalid_api_key' in error.lower() or 'auth' in error.lower():
            return None, "invalid_api_key"
        elif 'rate_limit' in error.lower():
            return None, "rate_limit"
        else:
            return None, error

def call_gemini(messages, context):
    """Gemini API fallback."""
    import urllib.request, urllib.error
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return None, "GEMINI_API_KEY not set"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    full_prompt = f"""{SYSTEM_PROMPT}

প্রাসঙ্গিক তথ্য:
{context}

কথোপকথন:
"""
    for msg in messages:
        role = "ব্যবহারকারী" if msg['role'] == 'user' else "সহকারী"
        full_prompt += f"\n{role}: {msg['content']}"

    data = json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
    }).encode('utf-8')

    req = urllib.request.Request(url, data=data,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['candidates'][0]['content']['parts'][0]['text'], None
    except Exception as e:
        return None, str(e)

def format_context(items):
    if not items:
        return "সাধারণ জ্ঞান থেকে উত্তর দাও।"
    parts = []
    for i, item in enumerate(items, 1):
        links_text = ""
        if item.get('links'):
            try:
                links = item['links'] if isinstance(item['links'], list) else json.loads(item.get('links','[]'))
                links_text = "\nলিংক: " + ", ".join([f"{l['name']}: {l['url']}" for l in links])
            except:
                pass
        parts.append(
            f"[{i}] বিষয়: {item.get('topic','')}\n"
            f"সূত্র: {item.get('source','')}\n"
            f"{item.get('content','')}{links_text}"
        )
    return "\n\n---\n\n".join(parts)

def extract_links(items):
    all_links, seen = [], set()
    for item in items:
        links = item.get('links', [])
        if isinstance(links, str):
            try: links = json.loads(links)
            except: links = []
        for link in links:
            if link.get('url') not in seen:
                seen.add(link.get('url'))
                all_links.append(link)
    return all_links

def generate_answer(question, kb_items, extra_items=None, conversation_history=None):
    all_items = list(kb_items)
    if extra_items:
        all_items.extend(extra_items)

    context = format_context(all_items)
    links = extract_links(all_items)

    # Calculation engine
    calc_result = detect_and_calculate(question)
    calc_text = format_calculation_result(calc_result) if calc_result else ""

    # Messages তৈরি করো
    messages = []
    if conversation_history:
        messages.extend(conversation_history[-8:])  # শেষ ৮টা

    current_q = question
    if calc_text:
        current_q = f"{question}\n\n[হিসাবের ফলাফল:{calc_text}]\n\nউপরের হিসাব ব্যবহার করে বিস্তারিত ব্যাখ্যা করো।"

    messages.append({"role": "user", "content": current_q})

    # Groq দিয়ে try করো
    answer, error = call_groq(messages, context)

    # Groq fail হলে Gemini try করো
    if error and answer is None:
        if 'rate_limit' in str(error):
            msg = "⏳ Groq-এর আজকের limit শেষ। কিছুক্ষণ পর আবার চেষ্টা করুন।"
        elif 'invalid_api_key' in str(error):
            # Gemini দিয়ে try
            answer, gem_error = call_gemini(messages, context)
            if gem_error:
                msg = "❌ API Key সমস্যা। GROQ_API_KEY বা GEMINI_API_KEY সেট করুন।"
            else:
                msg = None
        elif 'not installed' in str(error):
            # Gemini দিয়ে try
            answer, gem_error = call_gemini(messages, context)
            if gem_error:
                # Built-in থেকে উত্তর দাও
                if calc_text:
                    answer = calc_text
                elif all_items:
                    answer = f"## {all_items[0]['topic']}\n\n{all_items[0]['content']}"
                    if all_items[0].get('source'):
                        answer += f"\n\n> সূত্র: {all_items[0]['source']}"
                else:
                    answer = "এ বিষয়ে তথ্য পাওয়া যায়নি।"
                msg = None
            else:
                msg = None
        else:
            if calc_text:
                answer = calc_text
            elif all_items:
                answer = f"## {all_items[0]['topic']}\n\n{all_items[0]['content']}"
            else:
                answer = f"দুঃখিত, এই মুহূর্তে উত্তর দিতে পারছি না। Error: {error}"
            msg = None

        if msg:
            answer = msg

    final_answer = answer or "উত্তর পাওয়া যায়নি।"
    save_history(question, final_answer)

    return {
        'answer': final_answer,
        'links': links,
        'has_context': bool(all_items),
        'has_calculation': bool(calc_result)
    }

def save_history(question, answer, category='all'):
    try:
        init_db()
        conn = get_connection()
        conn.execute(
            'INSERT INTO chat_history (question, answer, category) VALUES (?, ?, ?)',
            (question, answer, category)
        )
        conn.commit()
        conn.close()
    except:
        pass

def get_history(limit=20):
    try:
        init_db()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, question, answer, category, asked_at FROM chat_history ORDER BY asked_at DESC LIMIT ?',
            (limit,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
    except:
        return []
