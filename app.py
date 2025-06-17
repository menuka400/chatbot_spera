from flask import Flask, render_template, request, jsonify, send_from_directory
from ai_ml_chatbot import AIMLChatbot
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Check for required environment variables
if not os.getenv("GROQ_API_KEY"):
    print("Warning: GROQ_API_KEY not found in environment variables.")
    print("Please check your .env file or set the environment variable.")

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'md'}

# Initialize AI/ML chatbot
try:
    ai_ml_chatbot = AIMLChatbot()
    print("✅ AI/ML Chatbot initialized successfully!")
except Exception as e:
    print(f"❌ Error initializing chatbot: {e}")
    ai_ml_chatbot = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        if ai_ml_chatbot is None:
            return jsonify({'response': 'Chatbot is not properly initialized. Please check your API keys and configuration.'}), 500
        
        user_message = request.json['message']
        response = ai_ml_chatbot.get_response(user_message)
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'response': 'I encountered an error processing your query. Could you please try again?'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            # Create uploads directory if it doesn't exist
            if not os.path.exists('uploads'):
                os.makedirs('uploads')
            
            # Save the file
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'filename': file.filename
            })
    except Exception as e:
        print(f"Error in upload endpoint: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)