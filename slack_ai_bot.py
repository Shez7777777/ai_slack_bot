# slack_ai_bot.py
import os
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from flask import Flask, render_template_string, request, jsonify

# Initialize
app = Flask(__name__)

# Setup Slack
def setup_slack():
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    return WebClient(token=slack_token)

# Generate message with AI using direct API call (MORE RELIABLE)
def generate_message(prompt):
    try:
        groq_api_key = os.environ.get('GROQ_API_KEY')
        
        # Direct API call to Groq
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
        client = setup_slack()
        
        # Validate first
        is_valid, validation_msg = validate_message(message_text)
        if not is_valid:
            return False, validation_msg
        
        # Post message
        response = client.chat_postMessage(
            channel=channel_id,
            text=message_text
        )
        
        return True, "Message posted successfully! ✅"
    
    except SlackApiError as e:
        return False, f"Slack error: {e.response['error']}"
    except Exception as e:
        return False, f"Error: {str(e)}"

# HTML Interface
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
        
        .generate-btn:hover {
            background: #4A154B;
            transform: translateY(-2px);
        }
        
        .post-btn {
            background: #2BAC76;
            color: white;
        }
        
        .post-btn:hover {
            background: #1e8f5f;
            transform: translateY(-2px);
        }
        
        .post-btn:disabled {
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Slack Bot</h1>
        <p class="subtitle">AI-powered automatic posting to Slack</p>
        
        <div class="message" id="message"></div>
        
        <div class="input-group">
            <label>📝 Channel ID</label>
            <input type="text" id="channelId" placeholder="e.g., C01234567AB" value="C0A768RCK5W" />
        </div>
        
        <div class="input-group">
            <label>💬 What do you want to post about?</label>
            <textarea id="prompt" placeholder="e.g., 'Post about AI trends' or 'Share productivity tips'"></textarea>
        </div>
        
        <button class="generate-btn" onclick="generatePreview()">✨ Generate Preview with AI</button>
        
        <div class="loading" id="loading">⏳ AI is generating your message...</div>
        
        <div class="preview-box" id="previewBox">
            <div class="preview-header">📋 Preview:</div>
            <div class="preview-content" id="previewContent"></div>
            <div class="char-count" id="charCount"></div>
        </div>
        
        <button class="post-btn" id="postBtn" onclick="postMessage()" disabled>
            🚀 Post to Slack
        </button>
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
        
        function showMessage(text, type) {
            const messageDiv = document.getElementById('message');
            messageDiv.textContent = text;
            messageDiv.className = 'message ' + type + ' show';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt is required'})
        
        message = generate_message(prompt)
        
        # Check if error occurred
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
