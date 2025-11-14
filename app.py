import os
import json
import glob
from flask import Flask, render_template, request, jsonify, session, send_file, abort
from functools import wraps
from werkzeug.security import check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Image, PageBreak, Spacer
from PIL import Image as PILImage
import io

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['DATA_DIR'] = os.path.join(os.path.dirname(__file__), 'data')
app.config['CREDENTIALS_FILE'] = os.path.join(os.path.dirname(__file__), 'credentials.json')

# Load credentials
def load_credentials():
    if os.path.exists(app.config['CREDENTIALS_FILE']):
        with open(app.config['CREDENTIALS_FILE'], 'r') as f:
            return json.load(f)
    return {}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_level_from_test_type(test_type):
    """Convert test type to level (AMC10A/B -> AMC10, AMC12A/B -> AMC12)"""
    if test_type.startswith('AMC8'):
        return 'AMC8'
    elif test_type.startswith('AMC10'):
        return 'AMC10'
    elif test_type.startswith('AMC12'):
        return 'AMC12'
    return test_type

def get_problem_number_range(problem_num):
    """Get the range category for a problem number"""
    num = int(problem_num)
    if num <= 10:
        return '1-10'
    elif num <= 15:
        return '11-15'
    elif num <= 20:
        return '16-20'
    else:
        return '21-25'

def load_problem_labels():
    """Load all problem labels from JSON file"""
    labels_path = os.path.join(app.config['DATA_DIR'], 'problem_labels.json')
    with open(labels_path, 'r') as f:
        return json.load(f)

def get_solution_files(test_type, year, problem_num):
    """Get all solution files for a problem"""
    screenshot_dir = os.path.join(app.config['DATA_DIR'], test_type, year, 'screenshot')
    
    # Check both naming patterns: solution_X_Y.png and problem_X_solution_Y.png
    solutions = []
    
    # Pattern 1: solution_X_Y.png
    pattern1 = os.path.join(screenshot_dir, f'solution_{problem_num}_*.png')
    solutions.extend(glob.glob(pattern1))
    
    # Pattern 2: problem_X_solution_Y.png
    pattern2 = os.path.join(screenshot_dir, f'problem_{problem_num}_solution_*.png')
    solutions.extend(glob.glob(pattern2))
    
    # Sort solutions by number
    solutions.sort()
    return solutions

def validate_problem(test_type, year, problem_num, labels):
    """Check if problem has label info and solution files"""
    key = f"{test_type}/{year}/problem_{problem_num}"
    
    # Check if problem has label info
    if key not in labels:
        return False
    
    # Check if problem has at least one solution file
    solutions = get_solution_files(test_type, year, problem_num)
    if not solutions:
        return False
    
    return True

@app.route('/')
def index():
    if 'logged_in' not in session or not session['logged_in']:
        return render_template('login.html')
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    credentials = load_credentials()
    
    # Check if username exists and password matches
    if username in credentials:
        stored_hash = credentials[username]
        # Try to verify as a hashed password (works with pbkdf2, scrypt, argon2, etc.)
        if isinstance(stored_hash, str):
            # Check if it looks like a werkzeug hash (starts with known hash method prefixes)
            is_hash = any(stored_hash.startswith(prefix) for prefix in 
                         ['pbkdf2:', 'scrypt:', 'argon2:', 'bcrypt:'])
            
            if is_hash:
                # It's a hashed password - verify it
                if check_password_hash(stored_hash, password):
                    session['logged_in'] = True
                    session['username'] = username
                    return jsonify({'success': True})
            elif stored_hash == password:
                # Plain text password (for initial setup - should be changed)
                session['logged_in'] = True
                session['username'] = username
                return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/problems', methods=['GET'])
@login_required
def get_problems():
    """Get filtered list of problems"""
    labels = load_problem_labels()
    
    # Get filter parameters
    level = request.args.get('level', '').strip()
    year_from = request.args.get('year_from', '').strip()
    year_to = request.args.get('year_to', '').strip()
    problem_range = request.args.get('problem_range', '').strip()
    primary_category = request.args.get('primary_category', '').strip()
    secondary_category = request.args.get('secondary_category', '').strip()
    
    # Filter problems
    filtered_problems = []
    
    for key, problem_data in labels.items():
        test_type = problem_data['test_type']
        problem_year = problem_data['year']
        problem_num = problem_data['problem_number']
        
        # Check if problem is valid (has solutions and labels)
        if not validate_problem(test_type, problem_year, problem_num, labels):
            continue
        
        # Apply filters
        if level:
            problem_level = get_level_from_test_type(test_type)
            if problem_level != level:
                continue
        
        # Year range filter (both inclusive)
        if year_from or year_to:
            try:
                problem_year_int = int(problem_year)
                year_from_int = int(year_from) if year_from else None
                year_to_int = int(year_to) if year_to else None
                
                # If only one bound is provided, use it for both
                if year_from_int is not None and year_to_int is None:
                    year_to_int = year_from_int
                elif year_to_int is not None and year_from_int is None:
                    year_from_int = year_to_int
                
                # Check if problem year is in range (inclusive)
                if year_from_int is not None and year_to_int is not None:
                    if not (year_from_int <= problem_year_int <= year_to_int):
                        continue
            except (ValueError, TypeError):
                # If year parsing fails, skip this filter
                pass
        
        if problem_range:
            problem_num_range = get_problem_number_range(problem_num)
            if problem_num_range != problem_range:
                continue
        
        if primary_category and problem_data.get('primary_category', '') != primary_category:
            continue
        
        if secondary_category:
            problem_secondary = problem_data.get('secondary_category', '')
            if not problem_secondary or problem_secondary != secondary_category:
                continue
        
        filtered_problems.append({
            'key': key,
            'test_type': test_type,
            'year': problem_year,
            'problem_number': problem_num,
            'primary_category': problem_data.get('primary_category', ''),
            'secondary_category': problem_data.get('secondary_category', ''),
            'display_name': f"{problem_year} {test_type} - Problem {problem_num}"
        })
    
    # Sort according to ordering rules:
    # 1. Level: AMC8, AMC10, AMC12
    # 2. Problem number: 1-25 (ascending)
    # 3. Year: ascending (smaller first)
    # 4. Test type variant: A before B
    def get_sort_key(problem):
        test_type = problem['test_type']
        year = int(problem['year'])
        problem_num = int(problem['problem_number'])
        
        # Level priority: AMC8=1, AMC10=2, AMC12=3
        if test_type.startswith('AMC8'):
            level_priority = 1
        elif test_type.startswith('AMC10'):
            level_priority = 2
        elif test_type.startswith('AMC12'):
            level_priority = 3
        else:
            level_priority = 999
        
        # Test type variant: A=0, B=1 (A comes before B)
        if test_type.endswith('A'):
            variant_priority = 0
        elif test_type.endswith('B'):
            variant_priority = 1
        else:
            variant_priority = 1
        
        return (level_priority, problem_num, year, variant_priority)
    
    filtered_problems.sort(key=get_sort_key)
    
    return jsonify({'problems': filtered_problems})

@app.route('/api/problem/<path:problem_key>', methods=['GET'])
@login_required
def get_problem_details(problem_key):
    """Get details for a specific problem including images"""
    labels = load_problem_labels()
    
    if problem_key not in labels:
        return jsonify({'error': 'Problem not found'}), 404
    
    problem_data = labels[problem_key]
    test_type = problem_data['test_type']
    year = problem_data['year']
    problem_num = problem_data['problem_number']
    
    # Get problem image
    problem_path = os.path.join(app.config['DATA_DIR'], test_type, year, 'screenshot', f'problem_{problem_num}.png')
    if not os.path.exists(problem_path):
        return jsonify({'error': 'Problem image not found'}), 404
    
    # Get solution images
    solution_paths = get_solution_files(test_type, year, problem_num)
    solution_urls = []
    for sol_path in solution_paths:
        rel_path = os.path.relpath(sol_path, app.config['DATA_DIR'])
        solution_urls.append(f'/api/image/{rel_path}')
    
    return jsonify({
        'problem': {
            'key': problem_key,
            'test_type': test_type,
            'year': year,
            'problem_number': problem_num,
            'primary_category': problem_data.get('primary_category', ''),
            'secondary_category': problem_data.get('secondary_category', ''),
            'display_name': f"{year} {test_type} - Problem {problem_num}"
        },
        'problem_image': f'/api/image/{test_type}/{year}/screenshot/problem_{problem_num}.png',
        'solution_images': solution_urls
    })

@app.route('/api/image/<path:image_path>')
@login_required
def serve_image(image_path):
    """Serve problem and solution images"""
    full_path = os.path.join(app.config['DATA_DIR'], image_path)
    
    # Security check: ensure path is within data directory
    if not os.path.abspath(full_path).startswith(os.path.abspath(app.config['DATA_DIR'])):
        abort(403)
    
    if not os.path.exists(full_path):
        abort(404)
    
    return send_file(full_path)

@app.route('/api/filters', methods=['GET'])
@login_required
def get_filter_options():
    """Get available filter options"""
    labels = load_problem_labels()
    
    years = set()
    primary_categories = set()
    secondary_categories = set()
    
    for key, problem_data in labels.items():
        test_type = problem_data['test_type']
        year = problem_data['year']
        problem_num = problem_data['problem_number']
        
        # Only include valid problems
        if not validate_problem(test_type, year, problem_num, labels):
            continue
        
        years.add(year)
        primary_cat = problem_data.get('primary_category', '')
        secondary_cat = problem_data.get('secondary_category', '')
        
        if primary_cat:
            primary_categories.add(primary_cat)
        if secondary_cat:
            secondary_categories.add(secondary_cat)
    
    return jsonify({
        'years': sorted(list(years), reverse=True),
        'primary_categories': sorted(list(primary_categories)),
        'secondary_categories': sorted(list(secondary_categories))
    })

@app.route('/api/worksheet/preview', methods=['GET', 'POST'])
@login_required
def preview_worksheet():
    """Generate preview HTML for worksheet"""
    if request.method == 'GET':
        # Handle GET request with query parameters
        problem_keys_str = request.args.get('problem_keys', '[]')
        try:
            problem_keys = json.loads(problem_keys_str)
        except:
            problem_keys = []
        sheet_name = request.args.get('sheet_name', 'Worksheet')
    else:
        # Handle POST request with JSON
        data = request.get_json() or {}
        problem_keys = data.get('problem_keys', [])
        sheet_name = data.get('sheet_name', 'Worksheet')
    
    labels = load_problem_labels()
    problems = []
    
    for key in problem_keys:
        if key in labels:
            problem_data = labels[key]
            test_type = problem_data['test_type']
            year = problem_data['year']
            problem_num = problem_data['problem_number']
            
            problem_path = f'/api/image/{test_type}/{year}/screenshot/problem_{problem_num}.png'
            problems.append({
                'key': key,
                'display_name': f"{year} {test_type} - Problem {problem_num}",
                'problem_image': problem_path
            })
    
    return render_template('worksheet_preview.html', problems=problems, sheet_name=sheet_name)

@app.route('/api/worksheet/export', methods=['POST'])
@login_required
def export_worksheet():
    """Export worksheet to PDF"""
    data = request.json
    problem_keys = data.get('problem_keys', [])
    sheet_name = data.get('sheet_name', 'Worksheet')
    export_type = data.get('type', 'problems')  # 'problems' or 'solutions'
    
    labels = load_problem_labels()
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    # Add title
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    styles = getSampleStyleSheet()
    title = Paragraph(f"<b>{sheet_name}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.3*inch))
    
    for key in problem_keys:
        if key not in labels:
            continue
        
        problem_data = labels[key]
        test_type = problem_data['test_type']
        year = problem_data['year']
        problem_num = problem_data['problem_number']
        
        if export_type == 'problems':
            # Add problem image
            problem_path = os.path.join(app.config['DATA_DIR'], test_type, year, 'screenshot', f'problem_{problem_num}.png')
            if os.path.exists(problem_path):
                # Add problem label
                label = Paragraph(f"<b>{year} {test_type} - Problem {problem_num}</b>", styles['Normal'])
                story.append(label)
                story.append(Spacer(1, 0.1*inch))
                
                # Add image (auto height based on aspect ratio)
                try:
                    pil_img = PILImage.open(problem_path)
                    img_width, img_height = pil_img.size
                    aspect_ratio = img_height / img_width
                    img = Image(problem_path, width=6*inch, height=6*inch*aspect_ratio)
                    story.append(img)
                except Exception as e:
                    # Fallback if image can't be opened
                    img = Image(problem_path, width=6*inch)
                    story.append(img)
                story.append(Spacer(1, 0.3*inch))
        else:
            # Add solutions
            solution_paths = get_solution_files(test_type, year, problem_num)
            if solution_paths:
                # Add problem label
                label = Paragraph(f"<b>{year} {test_type} - Problem {problem_num} - Solutions</b>", styles['Normal'])
                story.append(label)
                story.append(Spacer(1, 0.1*inch))
                
                for sol_path in solution_paths:
                    if os.path.exists(sol_path):
                        try:
                            pil_img = PILImage.open(sol_path)
                            img_width, img_height = pil_img.size
                            aspect_ratio = img_height / img_width
                            img = Image(sol_path, width=6*inch, height=6*inch*aspect_ratio)
                            story.append(img)
                        except Exception as e:
                            # Fallback if image can't be opened
                            img = Image(sol_path, width=6*inch)
                            story.append(img)
                        story.append(Spacer(1, 0.2*inch))
                
                story.append(Spacer(1, 0.3*inch))
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"{sheet_name}_{export_type}.pdf"
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

