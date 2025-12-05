"""
Flask web application for Archive.org Wrapped
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import zipfile
import tempfile
import shutil
from werkzeug.utils import secure_filename
from analyze import ListeningHistoryAnalyzer
from generate_wrapped import WrappedPresentation
import json
import urllib.request
import random

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs('static/generated', exist_ok=True)

def get_random_audio_url(recording_id):
    """Get a random audio track URL from Archive.org recording (excluding track 01)"""
    try:
        # Fetch metadata from Archive.org
        metadata_url = f"https://archive.org/metadata/{recording_id}"
        with urllib.request.urlopen(metadata_url, timeout=5) as response:
            metadata = json.loads(response.read())
        
        # Find all MP3 files, excluding track 01
        mp3_files = []
        if 'files' in metadata:
            for file in metadata['files']:
                filename = file.get('name', '')
                # Look for MP3 files, exclude track 01
                if filename.endswith('.mp3') and not any(x in filename.lower() for x in ['01.mp3', 't01.', 'd1t01', 's1t01']):
                    mp3_files.append(filename)
        
        if mp3_files:
            # Pick a random track
            selected_file = random.choice(mp3_files)
            # Return Archive.org download URL
            return f"https://archive.org/download/{recording_id}/{selected_file}"
        
        return None
    except Exception as e:
        print(f"Could not fetch audio for {recording_id}: {e}")
        return None

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Server is running'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and generate wrapped"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        data_dir = os.path.join(temp_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        try:
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            
            # Extract if it's a zip file
            if filename.endswith('.zip'):
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(data_dir)
            else:
                # If not a zip, assume it's a single file
                shutil.copy(filepath, data_dir)
            
            # Check if we have the required files
            required_files = ['ListeningHistorySummary.tsv', 'Favorites.tsv', 'DetailedListeningHistory.json']
            files_found = os.listdir(data_dir)
            
            # Look for files in subdirectories if not in root
            if not any(f in files_found for f in required_files):
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        if file in required_files:
                            shutil.copy(os.path.join(root, file), data_dir)
            
            # Verify we have at least the main file
            if not os.path.exists(os.path.join(data_dir, 'ListeningHistorySummary.tsv')):
                return jsonify({
                    'success': False,
                    'error': 'Could not find ListeningHistorySummary.tsv in the uploaded file. Please make sure you uploaded a valid Archive.org listening history export.'
                }), 400
            
            # Generate wrapped
            print("Starting data analysis...")
            analyzer = ListeningHistoryAnalyzer(data_dir)
            analyzer.load_data()
            
            # Get stats for response
            print("Calculating statistics...")
            stats = analyzer.get_stats_summary()
            
            # Get top show for audio
            print("Fetching audio...")
            top_shows = analyzer.get_top_shows(1)
            audio_url = None
            if len(top_shows) > 0:
                recording_id = top_shows.iloc[0].get('recording_id', None)
                if recording_id:
                    try:
                        audio_url = get_random_audio_url(recording_id)
                    except Exception as e:
                        print(f"Could not get audio: {e}")
            
            # Generate slides
            print("Generating slides (this may take 1-2 minutes)...")
            output_dir = os.path.join('static', 'generated')
            os.makedirs(output_dir, exist_ok=True)
            presentation = WrappedPresentation(analyzer)
            presentation.output_dir = output_dir
            
            try:
                presentation.generate_all()
            except Exception as e:
                print(f"Error generating slides: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Error generating slides: {str(e)}'
                }), 500
            
            # Get list of generated slides
            print("Finalizing...")
            slides = sorted([f for f in os.listdir(output_dir) if f.endswith('.png')])
            
            if not slides:
                return jsonify({
                    'success': False,
                    'error': 'No slides were generated. Please try again.'
                }), 500
            
            response_data = {
                'success': True,
                'stats': {
                    'total_hours': round(stats['total_hours'], 1),
                    'total_artists': stats['unique_artists'],
                    'total_shows': stats['unique_shows'],
                    'total_sessions': stats['total_sessions']
                },
                'slides': slides
            }
            
            if audio_url:
                response_data['audio_url'] = audio_url
            
            return jsonify(response_data), 200
            
        except Exception as inner_e:
            print(f"Error processing file: {str(inner_e)}")
            return jsonify({
                'success': False,
                'error': f'Error processing file: {str(inner_e)}'
            }), 500
            
        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Upload error: {str(e)}'
        }), 500

@app.route('/slides/<filename>')
def serve_slide(filename):
    """Serve generated slide images"""
    return send_from_directory('static/generated', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
