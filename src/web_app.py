"""
Web interface for Image Organizer
"""
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json

from app import ImageOrganizerApp
from config import Config

app = Flask(__name__)
image_organizer = ImageOrganizerApp()


@app.route('/')
def index():
    """Home page"""
    stats = image_organizer.db.get_statistics()
    return render_template('index.html', stats=stats)


@app.route('/api/process', methods=['POST'])
def process_folder():
    """API endpoint to process a folder"""
    data = request.json
    folder = data.get('folder', '')
    mode = data.get('mode', 'copy')
    recursive = data.get('recursive', True)
    
    if not folder or not Path(folder).exists():
        return jsonify({'error': 'Invalid folder'}), 400
    
    stats = image_organizer.process_folder(folder, mode, recursive)
    return jsonify(stats)


@app.route('/api/search')
def search_images():
    """API endpoint to search images"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'tag')
    limit = int(request.args.get('limit', 50))
    
    if not query:
        return jsonify([])
    
    results = image_organizer.db.search_images(query, search_type, limit)
    return jsonify(results)


@app.route('/api/tags')
def get_tags():
    """API endpoint to get all tags"""
    tags = image_organizer.db.get_all_tags()
    return jsonify([{'tag': tag, 'count': count} for tag, count in tags])


@app.route('/api/stats')
def get_stats():
    """API endpoint to get statistics"""
    stats = image_organizer.db.get_statistics()
    return jsonify(stats)


@app.route('/api/open_folder')
def open_folder():
    """API endpoint to open organized folder"""
    import subprocess
    subprocess.run(f'explorer "{image_organizer.config.default_dest}"')
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True, port=5000)