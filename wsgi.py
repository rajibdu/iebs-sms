import sys
import os

project_home = '/home/YOUR_USERNAME/iebs_sms'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['GROQ_API_KEY']    = 'gsk_তোমার_groq_key'     # ← Groq key দাও
os.environ['GEMINI_API_KEY']  = 'AIzaSy_তোমার_gemini_key' # ← Gemini key দাও (backup)
os.environ['SECRET_KEY']      = 'iebs-sms-2024-secret'
os.environ['ADMIN_USERNAME']  = 'admin'
os.environ['ADMIN_PASSWORD']  = 'তোমার_পাসওয়ার্ড'

from app import app as application
