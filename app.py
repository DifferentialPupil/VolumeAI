import os
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import uuid
from estimator import process_junk_image

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heif', 'heic'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # Generate unique filename to prevent collisions
        unique_id = str(uuid.uuid4())
        extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{unique_id}.{extension}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        try:
            # Process the image
            result = process_junk_image(filepath)
            
            # Store the results in the session for display
            return redirect(url_for('results', job_id=unique_id))
        except Exception as e:
            flash(f"Error processing image: {str(e)}")
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a valid image file.')
    return redirect(url_for('index'))

@app.route('/results/<job_id>')
def results(job_id):
    # This is where we'll display results - need to find the processed data
    try:
        # Use the job_id to find the processed results
        # For this implementation, we'll just pass the output image path
        
        # Assuming process_junk_image saved output to 'junk_output.png'
        output_path = "junk_output.png"
        
        # Run the processing function again
        # In a production system, this should be cached/stored
        uploaded_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(job_id)]
        if not uploaded_files:
            flash("Could not find your uploaded file.")
            return redirect(url_for('index'))
        
        uploaded_file = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_files[0])
        result = process_junk_image(uploaded_file)
        
        return render_template('results.html', 
                              original_image=url_for('uploaded_file', filename=uploaded_files[0]),
                              output_image=url_for('result_file', filename=os.path.basename(result['output_image'])),
                              total_volume=result['total_volume'],
                              volume_range=result['volume_range'],
                              object_volumes=result['object_volumes'])
    except Exception as e:
        flash(f"Error retrieving results: {str(e)}")
        return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/results/images/<filename>')
def result_file(filename):
    return send_from_directory('.', filename)  # Assuming output is saved to the app root directory

if __name__ == '__main__':
    # Debug mode should be disabled in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5001))) 