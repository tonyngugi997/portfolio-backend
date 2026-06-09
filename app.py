import os
import sqlite3
import json
import markdown
from datetime import datetime
from flask import Flask, render_template, abort, request, jsonify, redirect

# Import walkthroughs module
from walkthrough import walkthrough_bp, init_walkthrough_db, index_walkthrough_posts
from walkthrough import register_jinja_filters

app = Flask(__name__)
DATABASE = 'notes.db'
POSTS_DIR = 'posts'

# ============================================================================
# NOTES DATABASE FUNCTIONS
# ============================================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                tags TEXT,
                excerpt TEXT,
                content_md TEXT,
                content_html TEXT,
                read_time INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
from flask import send_from_directory

@app.route('/sitemap.xml')
def serve_sitemap():
    return send_from_directory('.', 'sitemap.xml')

@app.route('/robots.txt')
def serve_robots():
    return send_from_directory('.', 'robots.txt')
def calculate_read_time(content):
    words = len(content.split())
    return max(1, round(words / 200))

def extract_frontmatter(content):
    """Extract --- frontmatter if exists, return (metadata, remaining_content)"""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            remaining = parts[2].strip()
            metadata = {}
            for line in frontmatter.strip().split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    metadata[key.strip()] = val.strip()
            return metadata, remaining
    return {}, content

def index_posts():
    """Scan posts/ folder, add/update notes in DB"""
    if not os.path.exists(POSTS_DIR):
        os.makedirs(POSTS_DIR)
        return
    
    db = get_db()
    cursor = db.cursor()
    
    for filename in os.listdir(POSTS_DIR):
        if not filename.endswith('.md'):
            continue
        
        filepath = os.path.join(POSTS_DIR, filename)
        mod_time = os.path.getmtime(filepath)
        
        slug = filename.replace('.md', '')
        
        # Check if already indexed and up to date
        existing = cursor.execute(
            "SELECT slug, updated_at FROM notes WHERE slug = ?", 
            (slug,)
        ).fetchone()
        
        if existing:
            # Handle microseconds in timestamp
            updated_at_str = existing['updated_at'].split('.')[0]
            existing_time = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
            if datetime.fromtimestamp(mod_time) <= existing_time:
                continue  # Skip if not changed
        
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Extract frontmatter
        metadata, content_md = extract_frontmatter(raw_content)
        
        title = metadata.get('title', slug.replace('-', ' ').title())
        date = metadata.get('date', datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d'))
        tags = metadata.get('tags', '')
        
        # Generate excerpt (first 150 chars of content)
        excerpt = content_md[:150].strip() + '...'
        
        # Convert markdown to HTML
        content_html = markdown.markdown(content_md, extensions=['fenced_code', 'codehilite', 'tables'])
        
        read_time = calculate_read_time(content_md)
        
        # Upsert into database
        cursor.execute('''
            INSERT INTO notes (slug, title, date, tags, excerpt, content_md, content_html, read_time, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                date = excluded.date,
                tags = excluded.tags,
                excerpt = excluded.excerpt,
                content_md = excluded.content_md,
                content_html = excluded.content_html,
                read_time = excluded.read_time,
                updated_at = excluded.updated_at
        ''', (slug, title, date, tags, excerpt, content_md, content_html, read_time, datetime.now()))
        
        db.commit()
    
    db.close()

# ============================================================================
# ROUTES
# ============================================================================

# HOMEPAGE
@app.route('/')
def homepage():
    try:
        return render_template('index.html')
    except:
        return redirect('/notes')

# NOTES INDEX (blog list)
@app.route('/notes')
def notes_index():
    index_posts()
    db = get_db()
    posts = db.execute(
        "SELECT slug, title, date, tags, excerpt, read_time FROM notes ORDER BY date DESC"
    ).fetchall()
    db.close()
    return render_template('notes_index.html', posts=posts)

# SINGLE NOTE
@app.route('/notes/<slug>')
def notes_post(slug):
    index_posts()
    db = get_db()
    post = db.execute(
        "SELECT slug, title, date, tags, content_html, read_time FROM notes WHERE slug = ?",
        (slug,)
    ).fetchone()
    db.close()
    if not post:
        abort(404)
    return render_template('notes_posts.html', post=post)

# SKILLS PAGE
@app.route('/skills')
def skills():
    return render_template('skills.html')

# PROJECTS PAGE
@app.route('/projects')
def projects():
    return render_template('projects.html')

# ABOUT PAGE
@app.route('/about')
def about():
    return render_template('about.html')

# CONTACT PAGE
@app.route('/contact')
def contact():
    return render_template('contact.html')

# REINDEX API (notes)
@app.route('/notes/api/reindex', methods=['POST'])
def reindex():
    index_posts()
    return jsonify({"status": "ok", "message": "Posts reindexed"})

# ============================================================================
# REGISTER WALKTHROUGHS BLUEPRINT
# ============================================================================

app.register_blueprint(walkthrough_bp)
register_jinja_filters(app)

# ============================================================================
# INITIALIZATION FUNCTION (UPDATED)
# ============================================================================

def init_all():
    """Initialize all databases and index all content"""
    init_db()                       # notes.db
    init_walkthrough_db()           # walkthroughs.db
    index_posts()                   # scan posts/ for notes
    index_walkthrough_posts()       # scan walkthrough_posts/ for walkthroughs
    print("✅ All systems initialized: notes.db + walkthroughs.db")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    init_all()
    app.run(debug=True)
