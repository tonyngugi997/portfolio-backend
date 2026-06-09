# walkthrough.py - CTF / OverTheWire / Cyber Walkthroughs Module
import os
import sqlite3
import json
import markdown
from datetime import datetime
from flask import Blueprint, render_template, abort, request, jsonify

# ============================================================================
# BLUEPRINT SETUP
# ============================================================================

walkthrough_bp = Blueprint('walkthroughs', __name__, url_prefix='/walkthroughs')

# Database configuration
WALKTHROUGH_DB = 'walkthroughs.db'
POSTS_DIR = 'walkthrough_posts'

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def get_walkthrough_db():
    conn = sqlite3.connect(WALKTHROUGH_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_walkthrough_db():
    """Initialize walkthroughs database with all tables"""
    print("🔧 Initializing walkthroughs database...")
    with get_walkthrough_db() as conn:
        cursor = conn.cursor()
        
        # Main walkthroughs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS walkthroughs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                platform TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                completion_date TEXT NOT NULL,
                time_spent TEXT,
                tools_used TEXT,
                tags TEXT,
                content_md TEXT,
                content_html TEXT,
                excerpt TEXT,
                root_flag TEXT,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Steps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS walkthrough_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                walkthrough_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                phase TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                commands TEXT,
                explanation TEXT,
                FOREIGN KEY (walkthrough_id) REFERENCES walkthroughs(id) ON DELETE CASCADE
            )
        ''')
        
        # Resources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS walkthrough_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                walkthrough_id INTEGER NOT NULL,
                resource_type TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                FOREIGN KEY (walkthrough_id) REFERENCES walkthroughs(id) ON DELETE CASCADE
            )
        ''')
        
        # Indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_walkthroughs_category ON walkthroughs(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_walkthroughs_difficulty ON walkthroughs(difficulty)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_walkthroughs_platform ON walkthroughs(platform)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_walkthroughs_completion_date ON walkthroughs(completion_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_steps_walkthrough_id ON walkthrough_steps(walkthrough_id)')
        
        conn.commit()
        print("✅ Walkthroughs database initialized")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_markdown_to_html(content_md):
    if not content_md:
        return ""
    return markdown.markdown(
        content_md,
        extensions=['fenced_code', 'codehilite', 'tables', 'nl2br']
    )

def generate_excerpt(content_md, length=200):
    if not content_md:
        return ""
    plain_text = content_md[:length].strip()
    if len(content_md) > length:
        plain_text += '...'
    return plain_text

def parse_json_field(field):
    if field:
        try:
            return json.loads(field)
        except:
            return []
    return []

def calculate_read_time(content):
    if not content:
        return 1
    words = len(content.split())
    return max(1, round(words / 200))

def extract_walkthrough_frontmatter(content):
    """Extract YAML frontmatter from markdown file"""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            remaining = parts[2].strip()
            metadata = {}
            for line in frontmatter.strip().split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    key = key.strip()
                    val = val.strip()
                    # Handle lists like [item1, item2]
                    if val.startswith('[') and val.endswith(']'):
                        val = [v.strip().strip('"\'') for v in val[1:-1].split(',')]
                    metadata[key] = val
            return metadata, remaining
    return {}, content

# ============================================================================
# MARKDOWN IMPORTER
# ============================================================================

def index_walkthrough_posts():
    """Scan walkthrough_posts/ folder, add/update walkthroughs in DB"""
    print(f"🔍 Scanning folder: {POSTS_DIR}")
    
    if not os.path.exists(POSTS_DIR):
        print(f"❌ Folder does not exist: {POSTS_DIR}")
        os.makedirs(POSTS_DIR)
        print(f"✅ Created folder: {POSTS_DIR}")
        return
    
    files = os.listdir(POSTS_DIR)
    print(f"📄 Found files: {files}")
    
    if not files:
        print("⚠️ No markdown files found in walkthrough_posts/")
        return
    
    db = get_walkthrough_db()
    cursor = db.cursor()
    
    for filename in files:
        if not filename.endswith('.md'):
            print(f"⏭️ Skipping non-md file: {filename}")
            continue
        
        filepath = os.path.join(POSTS_DIR, filename)
        mod_time = os.path.getmtime(filepath)
        slug = filename.replace('.md', '')
        
        print(f"📝 Processing: {filename} -> slug: {slug}")
        
        # Check if already indexed and up to date
        existing = cursor.execute(
            "SELECT slug, updated_at FROM walkthroughs WHERE slug = ?",
            (slug,)
        ).fetchone()
        
        if existing:
            updated_at_str = existing['updated_at'].split('.')[0]
            existing_time = datetime.strptime(updated_at_str, '%Y-%m-%d %H:%M:%S')
            if datetime.fromtimestamp(mod_time) <= existing_time:
                print(f"⏭️ Skipping {filename} (not modified)")
                continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Extract frontmatter
        metadata, content_md = extract_walkthrough_frontmatter(raw_content)
        
        title = metadata.get('title', slug.replace('-', ' ').title())
        category = metadata.get('category', 'ctf')
        platform = metadata.get('platform', 'Unknown')
        difficulty = metadata.get('difficulty', 'Medium')
        completion_date = metadata.get('completion_date', datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d'))
        time_spent = metadata.get('time_spent', '')
        tools_used = json.dumps(metadata.get('tools_used', []))
        tags = json.dumps(metadata.get('tags', []))
        root_flag = metadata.get('root_flag', '')
        
        print(f"   Title: {title}")
        print(f"   Category: {category}")
        print(f"   Difficulty: {difficulty}")
        
        excerpt = generate_excerpt(content_md)
        content_html = render_markdown_to_html(content_md)
        
        cursor.execute('''
            INSERT INTO walkthroughs (
                slug, title, category, platform, difficulty,
                completion_date, time_spent, tools_used, tags,
                content_md, content_html, excerpt, root_flag, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title = excluded.title,
                category = excluded.category,
                platform = excluded.platform,
                difficulty = excluded.difficulty,
                completion_date = excluded.completion_date,
                time_spent = excluded.time_spent,
                tools_used = excluded.tools_used,
                tags = excluded.tags,
                content_md = excluded.content_md,
                content_html = excluded.content_html,
                excerpt = excluded.excerpt,
                root_flag = excluded.root_flag,
                updated_at = excluded.updated_at
        ''', (
            slug, title, category, platform, difficulty,
            completion_date, time_spent, tools_used, tags,
            content_md, content_html, excerpt, root_flag, datetime.now()
        ))
        
        db.commit()
        print(f"✅ Indexed: {filename}")
    
    db.close()
    print("🔍 Indexing complete!")

# ============================================================================
# ROUTES
# ============================================================================

@walkthrough_bp.route('/')
def index():
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    platform = request.args.get('platform')
    
    db = get_walkthrough_db()
    query = "SELECT * FROM walkthroughs WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)
    if platform:
        query += " AND platform = ?"
        params.append(platform)
    
    query += " ORDER BY completion_date DESC"
    
    walkthroughs = db.execute(query, params).fetchall()
    
    # Get filter options for sidebar
    categories = [row['category'] for row in db.execute("SELECT DISTINCT category FROM walkthroughs").fetchall()]
    difficulties = [row['difficulty'] for row in db.execute("SELECT DISTINCT difficulty FROM walkthroughs").fetchall()]
    platforms = [row['platform'] for row in db.execute("SELECT DISTINCT platform FROM walkthroughs").fetchall()]
    
    # Get stats
    total_walkthroughs = db.execute("SELECT COUNT(*) as count FROM walkthroughs").fetchone()['count']
    total_views = db.execute("SELECT SUM(views) as total FROM walkthroughs").fetchone()['total'] or 0
    categories_count = len(categories)
    
    db.close()
    
    return render_template(
        'walkthroughs/index.html',
        walkthroughs=walkthroughs,
        categories=categories,
        difficulties=difficulties,
        platforms=platforms,
        active_category=category,
        active_difficulty=difficulty,
        active_platform=platform,
        total_walkthroughs=total_walkthroughs,
        total_views=total_views,
        categories_count=categories_count,
        avg_difficulty="Med"  # Placeholder, calculate if needed
    )

@walkthrough_bp.route('/<slug>')
def detail(slug):
    db = get_walkthrough_db()
    
    # Increment view count
    db.execute("UPDATE walkthroughs SET views = views + 1 WHERE slug = ?", (slug,))
    db.commit()
    
    walkthrough = db.execute(
        "SELECT * FROM walkthroughs WHERE slug = ?",
        (slug,)
    ).fetchone()
    
    if not walkthrough:
        abort(404)
    
    steps = db.execute(
        "SELECT * FROM walkthrough_steps WHERE walkthrough_id = ? ORDER BY step_number",
        (walkthrough['id'],)
    ).fetchall()
    
    resources = db.execute(
        "SELECT * FROM walkthrough_resources WHERE walkthrough_id = ?",
        (walkthrough['id'],)
    ).fetchall()
    
    db.close()
    
    tools_used = parse_json_field(walkthrough['tools_used'])
    tags = parse_json_field(walkthrough['tags'])
    read_time = calculate_read_time(walkthrough['content_md'])
    
    return render_template(
        'walkthroughs/post.html',
        walkthrough=walkthrough,
        steps=steps,
        resources=resources,
        tools_used=tools_used,
        tags=tags,
        read_time=read_time
    )

@walkthrough_bp.route('/api/stats')
def stats():
    db = get_walkthrough_db()
    total = db.execute("SELECT COUNT(*) as count FROM walkthroughs").fetchone()['count']
    total_views = db.execute("SELECT SUM(views) as total FROM walkthroughs").fetchone()['total'] or 0
    by_category = db.execute("SELECT category, COUNT(*) as count FROM walkthroughs GROUP BY category").fetchall()
    by_difficulty = db.execute("SELECT difficulty, COUNT(*) as count FROM walkthroughs GROUP BY difficulty").fetchall()
    db.close()
    
    return jsonify({
        'total': total,
        'total_views': total_views,
        'by_category': [dict(row) for row in by_category],
        'by_difficulty': [dict(row) for row in by_difficulty]
    })

@walkthrough_bp.route('/api/reindex', methods=['POST'])
def reindex():
    index_walkthrough_posts()
    return jsonify({"status": "ok", "message": "Walkthroughs reindexed"})

# ============================================================================
# JINJA FILTER for parsing JSON in templates
# ============================================================================

def from_json_filter(value):
    """Convert JSON string to Python object for use in templates"""
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

def register_jinja_filters(app):
    app.jinja_env.filters['from_json'] = from_json_filter