from flask import Flask, request, jsonify, send_file, session, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv
import os
from podcastfy.client import generate_podcast
import shutil
from contextlib import contextmanager
import tempfile
from functools import wraps
import jwt
from datetime import datetime, timedelta
from pathlib import Path

# Load environment variables with explicit path and override
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Print loaded environment variables (redacted for security)
print("\n=== Environment Variables Loaded ===")
for key in ['API_TOKEN', 'GEMINI_API_KEY', 'OPENAI_API_KEY', 'ELEVENLABS_API_KEY']:
    value = os.getenv(key)
    if value:
        print(f"{key}: {value[:5]}...{value[-5:]}")
    else:
        print(f"{key}: Not set")

# Create required directories
TEMP_DIR = '/tmp/audio'
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
AUDIO_DIR = os.path.join(STATIC_DIR, 'audio')
TRANSCRIPT_DIR = os.path.join(STATIC_DIR, 'transcripts')

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

app = Flask(__name__,
    static_folder='static',
    static_url_path='/static'
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))

# Load API token after ensuring .env is loaded
API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    raise ValueError("API_TOKEN must be set in .env file")

# Enable CORS in development
if app.debug:
    CORS(app)
    # Serve index.html from root directory in development
    @app.route('/')
    def index():
        return send_file('../index.html')
else:
    # Serve static files in production
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

socketio = SocketIO(app, cors_allowed_origins="*")

def require_api_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'No token provided'}), 401

        if not token.startswith('Bearer '):
            return jsonify({'error': 'Invalid token format'}), 401

        token = token.split('Bearer ')[1]

        if token != API_TOKEN:
            return jsonify({'error': f'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated

@contextmanager
def temporary_env(temp_env):
    """Temporarily set environment variables and restore them afterwards."""
    original_env = dict(os.environ)
    os.environ.update(temp_env)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original_env)

@contextmanager
def temporary_env_file(env_vars):
    """Creates a temporary .env file with the provided variables."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_env:
        # Write variables to temp file
        for key, value in env_vars.items():
            temp_env.write(f"{key}={value}\n")
        temp_env.flush()

        # Store original env file path if it exists
        original_env_path = os.getenv('ENV_FILE')

        try:
            # Set the ENV_FILE environment variable to point to our temp file
            os.environ['ENV_FILE'] = temp_env.name
            yield
        finally:
            # Restore original ENV_FILE if it existed
            if original_env_path:
                os.environ['ENV_FILE'] = original_env_path
            else:
                os.environ.pop('ENV_FILE', None)
            # Clean up temp file
            os.unlink(temp_env.name)

@socketio.on('connect')
def handle_connect():
    print("\n=== Socket Connected ===")
    print(f"Client ID: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print("\n=== Socket Disconnected ===")
    print(f"Client ID: {request.sid}")

@socketio.on('generate_podcast')
def handle_generate_podcast(data):
    session_id = request.sid
    try:
        print(f"\n=== Starting Podcast Generation for session {session_id} ===")
        socketio.emit('status', "Starting podcast generation...", room=session_id)

        # Get the selected TTS model from the frontend
        tts_model = data.get('tts_model', 'edge')
        print(f"\nSelected TTS Model: {tts_model}")

        # Set up API keys based on selected model
        api_key_label = None

        # Always use Google API key from environment for content generation
        google_api_key = os.getenv('GEMINI_API_KEY')
        if not google_api_key:
            raise ValueError("Missing GEMINI_API_KEY in environment variables")

        # Print the API key for debugging (redacted for security)
        print(f"Using Google API key from environment: {google_api_key[:5]}...{google_api_key[-5:]}")

        os.environ['GOOGLE_API_KEY'] = google_api_key
        os.environ['GEMINI_API_KEY'] = google_api_key

        # Set up TTS-specific API keys
        if tts_model in ['gemini', 'geminimulti']:
            api_key_label = 'GEMINI_API_KEY'
        elif tts_model == 'elevenlabs':
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if not api_key:
                raise ValueError("Missing ELEVENLABS_API_KEY in environment variables")
            os.environ['ELEVENLABS_API_KEY'] = api_key
            api_key_label = 'ELEVENLABS_API_KEY'
            print(f"Using ElevenLabs API key from environment: {api_key[:5]}...{api_key[-5:]}")
        elif tts_model == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY in environment variables")

            # Print the API key for debugging (redacted for security)
            print(f"Using OpenAI API key from environment: {api_key[:5]}...{api_key[-5:]}")

            os.environ['OPENAI_API_KEY'] = api_key
            api_key_label = 'OPENAI_API_KEY'
        elif tts_model == 'edge':
            # No API key required for Edge TTS
            api_key_label = None

        conversation_config = {
            'creativity': float(data.get('creativity', 0.7)),
            'conversation_style': data.get('conversation_style', []),
            'roles_person1': data.get('roles_person1', 'Interviewer'),
            'roles_person2': data.get('roles_person2', 'Subject matter expert'),
            'dialogue_structure': data.get('dialogue_structure', []),
            'podcast_name': data.get('name'),
            'podcast_tagline': data.get('tagline'),
            'output_language': data.get('output_language', 'English'),
            'user_instructions': data.get('user_instructions'),
            'engagement_techniques': data.get('engagement_techniques', []),
            'text_to_speech': {
                'temp_audio_dir': TEMP_DIR,
                'ending_message': "Thank you for listening to this episode.",
                'default_tts_model': tts_model,
                'audio_format': 'mp3'
            }
        }

        socketio.emit('status', "Generating podcast content...", room=session_id)
        socketio.emit('progress', {'progress': 30, 'message': 'Generating podcast content...'}, room=session_id)

        # Add image_paths parameter if provided
        image_paths = data.get('image_urls', [])

        # Force the TTS model in the conversation_config as well
        conversation_config['text_to_speech']['default_tts_model'] = tts_model

        print(f"Calling generate_podcast with URLs: {data.get('urls', [])}")
        result = generate_podcast(
            urls=data.get('urls', []),
            conversation_config=conversation_config,
            tts_model=tts_model,
            longform=bool(data.get('is_long_form', False)),
            api_key_label=api_key_label,  # This tells podcastfy which env var to use
            image_paths=image_paths if image_paths else None  # Only pass if not empty
        )

        print(f"Podcast generation completed. Result type: {type(result)}")
        print(f"Result: {result}")

        socketio.emit('status', "Processing audio...", room=session_id)
        socketio.emit('progress', {'progress': 90, 'message': 'Processing final audio...'}, room=session_id)

        # Handle the result
        if isinstance(result, str) and os.path.isfile(result):
            filename = f"podcast_{os.urandom(8).hex()}.mp3"
            output_path = os.path.join(TEMP_DIR, filename)
            shutil.copy2(result, output_path)
            print(f"Copied audio file to: {output_path}")
            socketio.emit('progress', {'progress': 100, 'message': 'Podcast generation complete!'}, room=session_id)
            socketio.emit('complete', {
                'audioUrl': f'/audio/{filename}',
                'transcript': None
            }, room=session_id)
            print(f"Successfully emitted complete event with audio URL: /audio/{filename}")
        elif hasattr(result, 'audio_path'):
            filename = f"podcast_{os.urandom(8).hex()}.mp3"
            output_path = os.path.join(TEMP_DIR, filename)
            shutil.copy2(result.audio_path, output_path)
            print(f"Copied audio file from {result.audio_path} to: {output_path}")
            socketio.emit('progress', {'progress': 100, 'message': 'Podcast generation complete!'}, room=session_id)
            socketio.emit('complete', {
                'audioUrl': f'/audio/{filename}',
                'transcript': result.details if hasattr(result, 'details') else None
            }, room=session_id)
            print(f"Successfully emitted complete event with audio URL: /audio/{filename}")
        else:
            error_msg = f'Invalid result format. Result type: {type(result)}, Result: {result}'
            print(f"Error: {error_msg}")
            socketio.emit('error', {'message': error_msg}, room=session_id)

    except Exception as e:
        print(f"\nError in handle_generate_podcast: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        try:
            socketio.emit('error', {'message': str(e)}, room=session_id)
        except Exception as emit_error:
            print(f"Error sending error message: {str(emit_error)}")

@socketio.on('generate_news_podcast')
def handle_generate_news_podcast(data):
    # Create a unique session ID for this request
    session_id = request.sid
    print(f"\n=== Starting News Podcast Generation for session {session_id} ===")

    # Send initial status
    try:
        socketio.emit('status', "Starting news podcast generation...", room=session_id)
    except Exception as e:
        print(f"Error sending initial status: {str(e)}")

    try:
        # Get topics from request
        topics = data.get('topics')
        if not topics:
            socketio.emit('error', {'message': "No topics provided"}, room=session_id)
            return

        # Get language from request (default to English)
        output_language = data.get('output_language', 'English')

        print(f"Topics: {topics}")
        print(f"Language: {output_language}")

        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            error_msg = "Missing GEMINI_API_KEY in environment variables"
            print(error_msg)
            socketio.emit('error', {'message': error_msg}, room=session_id)
            return

        # Print the API key for debugging (redacted for security)
        print(f"Using Google API key from environment: {api_key[:5]}...{api_key[-5:]}")

        # Set environment variables
        os.environ['GOOGLE_API_KEY'] = api_key
        os.environ['GEMINI_API_KEY'] = api_key

        # Test the API key
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            # List available models to help with debugging
            print("\n=== Available Gemini Models ===")
            for model in genai.list_models():
                if "generateContent" in model.supported_generation_methods:
                    print(f"Model: {model.name}")

            # Use the model name that works with the API
            model = genai.GenerativeModel('gemini-1.5-pro')
            test_response = model.generate_content("Test message")
            print("\n=== API Test Successful with gemini-1.5-pro ===")
        except Exception as e:
            error_msg = f"API Test Failed: {str(e)}"
            print(f"\n=== {error_msg} ===")
            socketio.emit('error', {'message': error_msg}, room=session_id)
            return

        # Send progress updates
        socketio.emit('status', "Generating news podcast...", room=session_id)
        socketio.emit('progress', {'progress': 30, 'message': 'Generating content...'}, room=session_id)

        # Use a different function for news podcasts
        print(f"\n=== Generating podcast for topic: {topics} ===")

        # Create a simple transcript about the topic using Gemini
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Use the model name that works with the API
        model = genai.GenerativeModel('gemini-1.5-pro')

        # Create a prompt for generating a podcast transcript
        prompt = f"""
        Create a podcast transcript about {topics} in {output_language}.

        The podcast should be a conversation between a Host and an Expert.

        Format the transcript as follows:
        Host: [Host's dialogue in {output_language}]
        Expert: [Expert's dialogue in {output_language}]

        The podcast should include:
        1. An introduction to the topic
        2. A detailed discussion with interesting facts
        3. A summary and conclusion

        Make it engaging, educational, and about 5-10 minutes long when read aloud.
        The entire transcript should be in {output_language}.
        """

        # Generate the transcript
        response = model.generate_content(prompt)
        transcript = response.text

        # Save the transcript to a file
        import uuid
        transcript_id = uuid.uuid4().hex
        transcript_path = os.path.join(TEMP_DIR, f"transcript_{transcript_id}.txt")

        with open(transcript_path, "w") as f:
            f.write(transcript)

        print(f"Transcript saved to {transcript_path}")

        # Generate audio using OpenAI TTS
        audio_path = os.path.join(TEMP_DIR, f"podcast_{transcript_id}.mp3")

        try:
            from openai import OpenAI

            # Initialize the OpenAI client with the API key from environment
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                raise ValueError("Missing OpenAI API key in environment variables")

            openai_client = OpenAI(api_key=openai_api_key)

            # Process the transcript to create a more concise version for TTS
            # Extract a summary from the transcript
            lines = transcript.split('\n')
            summary_lines = []

            # Get the first few lines from the transcript as an introduction
            intro_count = 0
            for line in lines:
                if line.strip() and (line.startswith("Host:") or line.startswith("Expert:")):
                    summary_lines.append(line)
                    intro_count += 1
                    if intro_count >= 4:  # Get first 4 exchanges
                        break

            # Create a summary text
            summary_text = "\n".join(summary_lines)

            # Generate audio from the summary
            print("Generating audio with OpenAI TTS...")
            socketio.emit('status', "Generating audio with OpenAI TTS...", room=session_id)
            socketio.emit('progress', {'progress': 60, 'message': 'Creating podcast audio...'}, room=session_id)

            # Limit the input text to avoid exceeding OpenAI's limits
            # For non-English languages, we'll use the transcript directly
            if output_language != "English":
                # Just use the first part of the transcript directly (in the target language)
                # This ensures the audio is actually in the selected language
                input_text = transcript[:4000] if len(transcript) > 4000 else transcript
            else:
                # For English, we'll create a custom intro
                welcome_message = "Welcome to our podcast about"
                input_text = f"{welcome_message} {topics}. Here's a preview:\n\n{summary_text}\n\nThe full podcast is available in the transcript."
                # Truncate if too long (OpenAI has a limit)
                if len(input_text) > 4000:
                    input_text = input_text[:4000] + "..."

            # Select the appropriate voice based on language
            voice = "onyx"  # Default voice for English

            # Map languages to appropriate voices
            # OpenAI's voices have different characteristics for different languages
            voice_map = {
                "English": "onyx",
                "Spanish": "alloy",
                "French": "alloy",
                "German": "alloy",
                "Italian": "alloy",
                "Portuguese": "alloy",
                "Dutch": "alloy",
                "Russian": "alloy",
                "Japanese": "alloy",
                "Chinese": "alloy",
                "Korean": "alloy",
                "Arabic": "alloy",
                "Hindi": "alloy"
            }

            # Get the appropriate voice for the language
            if output_language in voice_map:
                voice = voice_map[output_language]

            print(f"Using voice '{voice}' for language '{output_language}'")
            print(f"First 100 chars of input text: {input_text[:100]}...")

            # Create the speech
            response = openai_client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=input_text
            )

            # Save the audio file
            try:
                with open(audio_path, "wb") as f:
                    # Get the content and write it to the file
                    for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
                print(f"Successfully saved audio to {audio_path}")
            except Exception as save_error:
                print(f"Error saving audio file: {str(save_error)}")
                # Try an alternative method
                try:
                    audio_data = response.content
                    with open(audio_path, "wb") as f:
                        f.write(audio_data)
                    print(f"Successfully saved audio using alternative method to {audio_path}")
                except Exception as alt_error:
                    print(f"Alternative save method also failed: {str(alt_error)}")
                    raise

            print(f"Audio saved to {audio_path}")

        except Exception as e:
            print(f"Error generating audio with OpenAI: {str(e)}")

            # Create a simple text file with the error
            error_path = os.path.join(TEMP_DIR, f"error_{transcript_id}.txt")
            with open(error_path, "w") as f:
                f.write(f"Error generating audio: {str(e)}")

            # Try to use a static sample file as fallback
            static_sample = os.path.join("static", "sample.mp3")
            if os.path.exists(static_sample):
                import shutil
                shutil.copy(static_sample, audio_path)
                print(f"Using static sample file: {static_sample}")
            else:
                # Create an empty audio file
                with open(audio_path, "wb") as f:
                    f.write(b"")
                print(f"Created empty audio file: {audio_path}")

        # Use the audio file as the result
        result = audio_path

        socketio.emit('status', "Processing audio...", room=session_id)
        socketio.emit('progress', {'progress': 90, 'message': 'Processing final audio...'}, room=session_id)

        # Handle the result
        try:
            # Import shutil here to ensure it's available in this scope
            import shutil

            if isinstance(result, str) and os.path.isfile(result):
                filename = f"news_podcast_{os.urandom(8).hex()}.mp3"
                output_path = os.path.join(TEMP_DIR, filename)
                shutil.copy2(result, output_path)
                socketio.emit('progress', {'progress': 100, 'message': 'Podcast generation complete!'}, room=session_id)
                socketio.emit('complete', {
                    'audioUrl': f'/audio/{filename}',
                    'transcript': transcript
                }, room=session_id)
                print(f"Successfully emitted complete event with audio URL: /audio/{filename}")
            elif hasattr(result, 'audio_path'):
                filename = f"news_podcast_{os.urandom(8).hex()}.mp3"
                output_path = os.path.join(TEMP_DIR, filename)
                shutil.copy2(result.audio_path, output_path)
                socketio.emit('complete', {
                    'audioUrl': f'/audio/{filename}',
                    'transcript': result.details if hasattr(result, 'details') else transcript
                }, room=session_id)
                print(f"Successfully emitted complete event with audio URL: /audio/{filename}")
            else:
                error_msg = 'Invalid result format'
                print(f"Error: {error_msg}")
                socketio.emit('error', {'message': error_msg}, room=session_id)
        except Exception as e:
            error_msg = f"Error in result handling: {str(e)}"
            print(error_msg)
            socketio.emit('error', {'message': error_msg}, room=session_id)

    except Exception as e:
        print(f"\nError in handle_generate_news_podcast: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

        # Provide a more user-friendly error message
        if "podcastfy" in str(e).lower():
            error_msg = "Error with podcast generation library. Please try again with a different topic."
        elif "api key" in str(e).lower():
            error_msg = "API key error. Please check your API key configuration."
        else:
            error_msg = f"Error generating podcast: {str(e)}"

        try:
            socketio.emit('error', {'message': error_msg}, room=session_id)
            print(f"Emitted error message: {error_msg}")
        except Exception as emit_error:
            print(f"Error sending error message: {str(emit_error)}")

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    # Check all possible audio paths
    possible_paths = [
        os.path.join('data/audio', filename),
        os.path.join(AUDIO_DIR, filename),
        os.path.join(TEMP_DIR, filename),  # Add TEMP_DIR to the list of possible paths
        # Add any additional mounted volume paths here
        "/app/data/audio/" + filename,
    ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Serving audio from: {path}")
            return send_file(path)

    # Debug information
    print(f"Audio file not found: {filename}")
    print(f"Checked paths: {possible_paths}")
    print(f"TEMP_DIR contents: {os.listdir(TEMP_DIR) if os.path.exists(TEMP_DIR) else 'TEMP_DIR not found'}")

    return jsonify({'error': 'Audio file not found'}), 404

@app.route('/api/generate-from-transcript', methods=['POST'])
@require_api_token
def generate_from_transcript():
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'transcript' not in data:
            return jsonify({'error': 'Missing transcript in request body'}), 400

        # Extract parameters from request
        transcript = data['transcript']
        # Get the selected TTS model from the request
        tts_model = data.get('tts_model', 'edge')
        print(f"\nSelected TTS Model: {tts_model}")

        # Create temporary transcript file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write(transcript)
            transcript_path = temp_file.name

        print(f"Created temporary transcript file: {transcript_path}")

        # Build conversation config from request data or use defaults
        conversation_config = {
            'creativity': float(data.get('creativity', 0.7)),
            'conversation_style': data.get('conversation_style', ['casual']),
            'roles_person1': data.get('roles_person1', 'Host'),
            'roles_person2': data.get('roles_person2', 'Guest'),
            'dialogue_structure': data.get('dialogue_structure', ['Introduction', 'Content', 'Conclusion']),
            'podcast_name': data.get('podcast_name', 'Custom Transcript Podcast'),
            'podcast_tagline': data.get('podcast_tagline', ''),
            'output_language': data.get('output_language', 'English'),
            'user_instructions': data.get('user_instructions', ''),
            'engagement_techniques': data.get('engagement_techniques', []),
            'text_to_speech': {
                'temp_audio_dir': 'data/audio',  # Let podcastfy use its default
                'ending_message': data.get('ending_message', "Thank you for listening to this episode."),
                'default_tts_model': tts_model,
                'audio_format': 'mp3',
                'output_directories': {
                    'audio': 'data/audio',
                    'transcripts': 'data/transcripts'
                }
            }
        }

        # Set up API keys if needed
        api_key_label = None

        # Always use Google API key from environment for content generation
        google_api_key = os.getenv('GEMINI_API_KEY')
        if not google_api_key:
            return jsonify({'error': 'Missing GEMINI_API_KEY in environment variables'}), 400

        # Print the API key for debugging (redacted for security)
        print(f"Using Google API key from environment: {google_api_key[:5]}...{google_api_key[-5:]}")

        os.environ['GOOGLE_API_KEY'] = google_api_key
        os.environ['GEMINI_API_KEY'] = google_api_key

        # Set up TTS-specific API keys
        if tts_model in ['gemini', 'geminimulti', 'gemini-2.0-flash']:
            api_key_label = 'GEMINI_API_KEY'
        elif tts_model == 'elevenlabs':
            api_key = os.getenv('ELEVENLABS_API_KEY')
            if not api_key:
                return jsonify({'error': 'Missing ELEVENLABS_API_KEY in environment variables'}), 400
            os.environ['ELEVENLABS_API_KEY'] = api_key
            api_key_label = 'ELEVENLABS_API_KEY'
            print(f"Using ElevenLabs API key from environment: {api_key[:5]}...{api_key[-5:]}")
        elif tts_model == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return jsonify({'error': 'Missing OPENAI_API_KEY in environment variables'}), 400

            # Print the API key for debugging (redacted for security)
            print(f"Using OpenAI API key from environment: {api_key[:5]}...{api_key[-5:]}")

            os.environ['OPENAI_API_KEY'] = api_key
            api_key_label = 'OPENAI_API_KEY'
        elif tts_model == 'edge':
            # No API key required for Edge TTS
            api_key_label = None

        # Force the TTS model in the conversation_config as well
        conversation_config['text_to_speech']['default_tts_model'] = tts_model

        # Generate the podcast
        result = generate_podcast(
            transcript_file=transcript_path,
            conversation_config=conversation_config,
            tts_model=tts_model,
            api_key_label=api_key_label
        )

        # Clean up temporary file
        try:
            os.unlink(transcript_path)
            print(f"Cleaned up temporary transcript file: {transcript_path}")
        except Exception as e:
            print(f"Warning: Could not delete temporary file {transcript_path}: {e}")

        # Handle the result
        if isinstance(result, str):
            return jsonify({
                'success': True,
                'audio_url': f'/audio/{os.path.basename(result)}',
            })
        elif hasattr(result, 'audio_path'):
            print(f"Audio file path: {result.audio_path}")
            print(f"File exists: {os.path.exists(result.audio_path)}")
            return jsonify({
                'success': True,
                'audio_url': f'/audio/{os.path.basename(result.audio_path)}',
                'transcript': result.details if hasattr(result, 'details') else None
            })
        else:
            return jsonify({'error': 'Invalid result format'}), 500

    except Exception as e:
        print(f"\nError in generate_from_transcript: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-env', methods=['GET'])
def test_env():
    """Test endpoint to verify environment variables"""
    return jsonify({
        'api_token_set': bool(API_TOKEN),
        'api_token_length': len(API_TOKEN) if API_TOKEN else 0,
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8082))
    socketio.run(app,
                 host='0.0.0.0',
                 port=port,
                 debug=False,  # Set to False in production
                 allow_unsafe_werkzeug=True)