# slack_ai_bot.py (Updated with OAuth)
import os
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, render_template_string, request, jsonify, redirect, session

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'ai-slack-bot-secret-key-2025-xyz-12345')

# Store user tokens in memory (in production, use a database)
user_tokens = {}

# Slack OAuth Configuration
SLACK_CLIENT_ID = os.environ.get('SLACK_CLIENT_ID')
SLACK_CLIENT_SECRET = os.environ.get('SLACK_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'https://your-app.onrender.com/slack/oauth_redirect')

# Get Slack client for current user
def get_slack_client():
    user_id = session.get('user_id')
    if not user_id or user_id not in user_tokens:
        return None
    return WebClient(token=user_tokens[user_id]['access_token'])

# Check if user is authenticated
def is_authenticated():
    user_id = session.get('user_id')
    return user_id and user_id in user_tokens

# Generate message with AI
def generate_message(prompt):
    try:
        groq_api_key = os.environ.get('GROQ_API_KEY')
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {groq_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an expert content creator. Create engaging, professional messages based on the user prompt. Keep it concise and impactful. Add relevant emojis where appropriate.'
                    },
                    {
                        'role': 'user',
                        'content': f'Create a message about: {prompt}'
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 500
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content'].strip()
            message = message.replace('"', '').replace("'", "")
            return message
        else:
            return f"Error: API returned status {response.status_code}"
            
    except Exception as e:
        return f"Error generating message: {str(e)}"

# Validate message
def validate_message(message_text):
    if not message_text or len(message_text.strip()) == 0:
        return False, "Message cannot be empty"
    
    if message_text.startswith("Error"):
        return False, message_text
    
    if len(message_text) > 3000:
        return False, f"Message too long ({len(message_text)} characters, max 3000)"
    
    return True, "Valid"

# Post to Slack
def post_to_slack(message_text, channel_id):
    try:
        client = get_slack_client()
        if not client:
            return False, "Please authorize with Slack first"
        
        is_valid, validation_msg = validate_message(message_text)
        if not is_valid:
            return False, validation_msg
        
        response = client.chat_postMessage(
            channel=channel_id,
            text=message_text
        )
        
        return True, "Message posted successfully! ✅"
    
    except SlackApiError as e:
        return False, f"Slack error: {e.response['error']}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# HTML Interface with OAuth
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AI Slack Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #4A154B 0%, #611f69 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        h1 {
            color: #4A154B;
            margin-bottom: 10px;
            font-size: 32px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }
        
        .auth-section {
            background: #f8f8f8;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .auth-section.connected {
            background: #d4edda;
            border-color: #c3e6cb;
        }
        
        .auth-status {
            font-weight: 600;
            margin-bottom: 15px;
            font-size: 18px;
        }
        
        .auth-status.connected {
            color: #155724;
        }
        
        .auth-status.disconnected {
            color: #721c24;
        }
        
        .slack-btn {
            display: inline-block;
            background: #4A154B;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .slack-btn:hover {
            background: #611f69;
            transform: translateY(-2px);
        }
        
        .logout-btn {
            background: #dc3545;
            border: none;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 10px;
        }
        
        .logout-btn:hover {
            background: #c82333;
        }
        
        .workspace-info {
            margin-top: 15px;
            color: #155724;
            font-size: 14px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
        }
        
        input, textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        input:focus, textarea:focus {
            outline: none;
            border-color: #4A154B;
        }
        
        input:disabled, textarea:disabled {
            background: #f5f5f5;
            cursor: not-allowed;
        }
        
        textarea {
            resize: vertical;
            min-height: 120px;
            font-family: inherit;
        }
        
        button {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 10px;
        }
        
        .generate-btn {
            background: #611f69;
            color: white;
        }
        
        .generate-btn:hover:not(:disabled) {
            background: #4A154B;
            transform: translateY(-2px);
        }
        
        .post-btn {
            background: #2BAC76;
            color: white;
        }
        
        .post-btn:hover:not(:disabled) {
            background: #1e8f5f;
            transform: translateY(-2px);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .preview-box {
            background: #f8f8f8;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            display: none;
        }
        
        .preview-box.show {
            display: block;
        }
        
        .preview-header {
            font-weight: 600;
            color: #4A154B;
            margin-bottom: 10px;
        }
        
        .preview-content {
            color: #333;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        
        .char-count {
            text-align: right;
            color: #666;
            font-size: 14px;
            margin-top: 10px;
        }
        
        .message {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: none;
        }
        
        .message.show {
            display: block;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .loading {
            display: none;
            text-align: center;
            color: #666;
            margin: 10px 0;
        }
        
        .loading.show {
            display: block;
        }
        
        .disabled-overlay {
            opacity: 0.5;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Slack Bot</h1>
        <p class="subtitle">AI-powered automatic posting to Slack</p>
        
        <!-- Authentication Section -->
        <div class="auth-section {% if authenticated %}connected{% endif %}">
            {% if authenticated %}
                <div class="auth-status connected">✅ Connected to Slack</div>
                <div class="workspace-info">
                    Workspace: {{ workspace_name }}<br>
                    Team: {{ team_name }}
                </div>
                <button class="logout-btn" onclick="logout()">Disconnect</button>
            {% else %}
                <div class="auth-status disconnected">🔐 Not Connected</div>
                <p style="margin-bottom: 15px; color: #666;">
                    Connect your Slack workspace to start posting
                </p>
                <a href="/slack/install" class="slack-btn">
                    <img src="https://platform.slack-edge.com/img/add_to_slack.png" 
                         alt="Add to Slack" 
                         style="vertical-align: middle; height: 40px;">
                </a>
            {% endif %}
        </div>
        
        <div class="{% if not authenticated %}disabled-overlay{% endif %}">
            <div class="message" id="message"></div>
            
            <div class="input-group">
                <label>📝 Channel ID</label>
                <input type="text" 
                       id="channelId" 
                       placeholder="e.g., C01234567AB" 
                       {% if not authenticated %}disabled{% endif %} />
                <small style="color: #666; font-size: 12px;">
                    💡 Right-click channel → View channel details → Copy Channel ID
                </small>
            </div>
            
            <div class="input-group">
                <label>💬 What do you want to post about?</label>
                <textarea id="prompt" 
                          placeholder="e.g., 'Post about AI trends' or 'Share productivity tips'"
                          {% if not authenticated %}disabled{% endif %}></textarea>
            </div>
            
            <button class="generate-btn" 
                    onclick="generatePreview()" 
                    {% if not authenticated %}disabled{% endif %}>
                ✨ Generate Preview with AI
            </button>
            
            <div class="loading" id="loading">⏳ AI is generating your message...</div>
            
            <div class="preview-box" id="previewBox">
                <div class="preview-header">📋 Preview:</div>
                <div class="preview-content" id="previewContent"></div>
                <div class="char-count" id="charCount"></div>
            </div>
            
            <button class="post-btn" 
                    id="postBtn" 
                    onclick="postMessage()" 
                    disabled>
                🚀 Post to Slack
            </button>
        </div>
    </div>
    
    <script>
        let generatedMessage = '';
        
        async function generatePreview() {
            const prompt = document.getElementById('prompt').value;
            const channelId = document.getElementById('channelId').value;
            
            if (!prompt.trim()) {
                showMessage('Please enter what you want to post about', 'error');
                return;
            }
            
            if (!channelId.trim()) {
                showMessage('Please enter your Slack Channel ID', 'error');
                return;
            }
            
            document.getElementById('loading').classList.add('show');
            document.getElementById('message').classList.remove('show');
            
            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    generatedMessage = data.message;
                    document.getElementById('previewContent').textContent = generatedMessage;
                    document.getElementById('charCount').textContent = 
                        `${generatedMessage.length} characters`;
                    document.getElementById('previewBox').classList.add('show');
                    document.getElementById('postBtn').disabled = false;
                    showMessage('Message generated successfully! Review and post.', 'success');
                } else {
                    showMessage(data.error || 'Failed to generate message', 'error');
                }
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
            } finally {
                document.getElementById('loading').classList.remove('show');
            }
        }
        
        async function postMessage() {
            const channelId = document.getElementById('channelId').value;
            
            if (!generatedMessage) {
                showMessage('Please generate a message first', 'error');
                return;
            }
            
            document.getElementById('postBtn').disabled = true;
            document.getElementById('postBtn').textContent = '⏳ Posting...';
            
            try {
                const response = await fetch('/post', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: generatedMessage,
                        channel_id: channelId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('✅ Message posted to Slack successfully!', 'success');
                    document.getElementById('prompt').value = '';
                    document.getElementById('previewBox').classList.remove('show');
                    generatedMessage = '';
                } else {
                    showMessage(data.error || 'Failed to post message', 'error');
                    document.getElementById('postBtn').disabled = false;
                }
            } catch (error) {
                showMessage('Error: ' + error.message, 'error');
                document.getElementById('postBtn').disabled = false;
            } finally {
                document.getElementById('postBtn').textContent = '🚀 Post to Slack';
            }
        }
        
        async function logout() {
            if (confirm('Are you sure you want to disconnect from Slack?')) {
                window.location.href = '/slack/logout';
            }
        }
        
        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = text;
            messageDiv.className = 'message ' + type + ' show';
        }
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def home():
    authenticated = is_authenticated()
    workspace_name = ""
    team_name = ""
    
    if authenticated:
        user_id = session.get('user_id')
        workspace_name = user_tokens[user_id].get('team_name', 'Unknown')
        team_name = user_tokens[user_id].get('team_id', 'Unknown')
    
    return render_template_string(
        HTML_TEMPLATE, 
        authenticated=authenticated,
        workspace_name=workspace_name,
        team_name=team_name
    )

@app.route('/slack/install')
def slack_install():
    # Redirect user to Slack OAuth page
    slack_auth_url = (
        f"https://slack.com/oauth/v2/authorize?"
        f"client_id={SLACK_CLIENT_ID}&"
        f"scope=chat:write,channels:read&"
        f"redirect_uri={REDIRECT_URI}"
    )
    return redirect(slack_auth_url)

@app.route('/slack/oauth_redirect')
def slack_oauth_redirect():
    # Get the authorization code from Slack
    code = request.args.get('code')
    
    if not code:
        return "Error: No authorization code received", 400
    
    try:
        # Exchange code for access token
        response = requests.post(
            'https://slack.com/api/oauth.v2.access',
            data={
                'client_id': SLACK_CLIENT_ID,
                'client_secret': SLACK_CLIENT_SECRET,
                'code': code,
                'redirect_uri': REDIRECT_URI
            }
        )
        
        data = response.json()
        
        if not data.get('ok'):
            return f"Error: {data.get('error', 'Unknown error')}", 400
        
        # Store the token for this user
        team_id = data['team']['id']
        user_tokens[team_id] = {
            'access_token': data['access_token'],
            'team_id': data['team']['id'],
            'team_name': data['team']['name']
        }
        
        # Store user ID in session
        session['user_id'] = team_id
        
        return redirect('/')
        
    except Exception as e:
        return f"Error during OAuth: {str(e)}", 500

@app.route('/slack/logout')
def slack_logout():
    user_id = session.get('user_id')
    if user_id and user_id in user_tokens:
        del user_tokens[user_id]
    session.clear()
    return redirect('/')

@app.route('/generate', methods=['POST'])
def generate():
    if not is_authenticated():
        return jsonify({'success': False, 'error': 'Please authorize with Slack first'})
    
    try:
        data = request.json
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt is required'})
        
        message = generate_message(prompt)
        
        if message.startswith("Error"):
            return jsonify({'success': False, 'error': message})
        
        return jsonify({
            'success': True,
            'message': message
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/post', methods=['POST'])
def post():
    if not is_authenticated():
        return jsonify({'success': False, 'error': 'Please authorize with Slack first'})
    
    try:
        data = request.json
        message = data.get('message', '')
        channel_id = data.get('channel_id', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'})
        
        if not channel_id:
            return jsonify({'success': False, 'error': 'Channel ID is required'})
        
        success, result_message = post_to_slack(message, channel_id)
        
        return jsonify({
            'success': success,
            'message': result_message if success else None,
            'error': None if success else result_message
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

