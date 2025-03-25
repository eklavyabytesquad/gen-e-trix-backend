from flask import Flask, request, jsonify
import io
import base64
import json
from datetime import datetime
import os
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Cryptocurrency icons (Unicode symbols)
CRYPTO_ICONS = {
    'btc': '₿',
    'eth': 'Ξ',
    'usdt': '₮',
    'sol': 'S',
    'bnb': 'B',
}

# Colors for a more professional look
COLORS = {
    'primary': (16, 185, 129),       # Green for headers
    'secondary': (45, 55, 72),       # Dark slate for text
    'accent': (99, 102, 241),        # Indigo for highlights
    'light': (249, 250, 251),        # Almost white for backgrounds
    'dark': (17, 24, 39),            # Almost black for text
    'muted': (156, 163, 175),        # Gray for secondary text
    'success': (16, 185, 129),       # Green for success indicators
    'warning': (245, 158, 11),       # Amber for warnings
    'error': (239, 68, 68),          # Red for errors
}

def get_better_font(size=12):
    """
    Attempt to get a better font than the default
    Falls back to default if necessary
    """
    try:
        # Try to use a nicer built-in font
        return ImageFont.truetype("arial.ttf", size)
    except IOError:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except IOError:
            # Fall back to default font
            return ImageFont.load_default()

def create_contract_image(payment_data):
    """
    Creates a visually appealing contract image based on payment data
    
    Args:
        payment_data (dict): Contains amount, sender, receiver, date, time, and cryptocurrency type
        
    Returns:
        bytes: Base64 encoded PNG image
    """
    # Extract payment data
    amount = payment_data.get('amount', 0)
    sender = payment_data.get('sender', 'Unknown')
    receiver = payment_data.get('receiver', 'Unknown')
    timestamp = payment_data.get('timestamp', datetime.now().isoformat())
    currency_type = payment_data.get('currency', 'btc').lower()
    currency_name = payment_data.get('currencyName', 'Bitcoin')
    currency_symbol = payment_data.get('currencySymbol', 'BTC')
    
    # Format addresses for display (show only first 6 and last 4 characters)
    def format_address(address):
        if len(address) > 10:
            return f"{address[:6]}...{address[-4:]}"
        return address
    
    sender_formatted = format_address(sender)
    receiver_formatted = format_address(receiver)
    
    # Generate a unique transaction ID
    tx_id = ''.join(random.choice('0123456789abcdef') for _ in range(16))
    
    # Parse timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        date_str = dt.strftime('%b %d, %Y')
        time_str = dt.strftime('%I:%M %p')
    except (ValueError, TypeError):
        date_str = "Unknown Date"
        time_str = "Unknown Time"
    
    # Create image with higher resolution
    width, height = 900, 600
    image = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    
    # Create a rounded rectangle background
    background = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(background)
    
    # Draw a rounded rectangle (simulated with multiple shapes)
    radius = 20
    bg_draw.rectangle([(radius, 0), (width - radius, height)], fill=COLORS['light'])
    bg_draw.rectangle([(0, radius), (width, height - radius)], fill=COLORS['light'])
    bg_draw.pieslice([(0, 0), (radius * 2, radius * 2)], 180, 270, fill=COLORS['light'])
    bg_draw.pieslice([(width - radius * 2, 0), (width, radius * 2)], 270, 360, fill=COLORS['light'])
    bg_draw.pieslice([(0, height - radius * 2), (radius * 2, height)], 90, 180, fill=COLORS['light'])
    bg_draw.pieslice([(width - radius * 2, height - radius * 2), (width, height)], 0, 90, fill=COLORS['light'])
    
    # Add a subtle gradient overlay
    for y in range(height):
        opacity = int(255 * (1 - y / height * 0.4))
        bg_draw.line([(0, y), (width, y)], fill=(255, 255, 255, opacity))
    
    # Paste background onto main image
    image.paste(background, (0, 0), background)
    draw = ImageDraw.Draw(image)
    
    # Get better fonts
    title_font = get_better_font(32)
    header_font = get_better_font(24)
    regular_font = get_better_font(20)
    small_font = get_better_font(16)
    tiny_font = get_better_font(12)
    icon_font = get_better_font(36)
    
    # Draw header background
    header_height = 100
    header_bg = Image.new('RGBA', (width, header_height), COLORS['primary'])
    header_draw = ImageDraw.Draw(header_bg)
    
    # Add subtle header pattern
    for i in range(0, width, 20):
        header_draw.line([(i, 0), (i + 10, header_height)], fill=(255, 255, 255, 10), width=5)
    
    # Paste header background
    image.paste(header_bg, (0, 0), header_bg)
    
    # Draw blockchain logo circle in top left
    circle_size = 60
    circle_pos = (50, 50)
    draw.ellipse([(circle_pos[0] - circle_size//2, circle_pos[1] - circle_size//2), 
                 (circle_pos[0] + circle_size//2, circle_pos[1] + circle_size//2)], 
                 fill=(255, 255, 255))
    
    # Draw cryptocurrency icon in the circle
    icon = CRYPTO_ICONS.get(currency_type, 'Ð')
    icon_w = draw.textlength(icon, font=icon_font)
    draw.text((circle_pos[0] - icon_w/2, circle_pos[1] - 18), icon, font=icon_font, fill=COLORS['primary'])
    
    # Draw title
    draw.text((circle_pos[0] + circle_size//2 + 20, 30), "Payment Contract", font=title_font, fill=(255, 255, 255))
    draw.text((circle_pos[0] + circle_size//2 + 20, 70), f"{date_str} · {time_str}", font=small_font, fill=(220, 255, 220))
    
    # Draw "BLOCKCHAIN BASED CONTRACT" at top right
    blockchain_text = "BLOCKCHAIN BASED CONTRACT"
    blockchain_w = draw.textlength(blockchain_text, font=small_font)
    draw.text((width - blockchain_w - 30, 30), blockchain_text, font=small_font, fill=(255, 255, 255))
    
    # Draw decorative horizontal lines
    line_y = header_height + 40
    draw.line([(50, line_y), (width-50, line_y)], fill=COLORS['muted'], width=1)
    
    # Draw transaction ID
    draw.text((50, line_y + 15), f"Transaction ID: {tx_id}", font=tiny_font, fill=COLORS['muted'])
    
    # Draw security badge
    badge_text = "BLOCKCHAIN SECURED"
    badge_w = draw.textlength(badge_text, font=tiny_font)
    badge_x = width - badge_w - 50
    draw.text((badge_x, line_y + 15), badge_text, font=tiny_font, fill=COLORS['success'])
    
    # Draw amount section with a highlight box
    amount_y = line_y + 60
    amount_box_height = 100
    amount_box = Image.new('RGBA', (width - 100, amount_box_height), (240, 253, 244))
    image.paste(amount_box, (50, amount_y), amount_box)
    
    draw.text((70, amount_y + 15), "Amount", font=header_font, fill=COLORS['secondary'])
    
    # Draw amount with currency symbol
    amount_text = f"{amount} {currency_symbol}"
    draw.text((70, amount_y + 50), amount_text, font=title_font, fill=COLORS['primary'])
    
    # Draw currency name
    currency_text = f"({currency_name})"
    amount_w = draw.textlength(amount_text, font=title_font)
    draw.text((80 + amount_w, amount_y + 55), currency_text, font=regular_font, fill=COLORS['muted'])
    
    # Draw sender and receiver information
    info_y = amount_y + amount_box_height + 30
    
    # From section
    draw.text((70, info_y), "From", font=header_font, fill=COLORS['secondary'])
    draw.text((70, info_y + 40), sender_formatted, font=regular_font, fill=COLORS['dark'])
    
    # To section
    draw.text((70, info_y + 90), "To", font=header_font, fill=COLORS['secondary'])
    draw.text((70, info_y + 130), receiver_formatted, font=regular_font, fill=COLORS['dark'])
    
    # Draw verification section
    verify_y = info_y + 190
    draw.line([(50, verify_y), (width-50, verify_y)], fill=COLORS['muted'], width=1)
    
    # Add verification seal
    seal_size = 80
    seal_x = width - 120
    seal_y = verify_y + 20
    
    # Draw seal background
    draw.ellipse([(seal_x - seal_size//2, seal_y - seal_size//2), 
                 (seal_x + seal_size//2, seal_y + seal_size//2)], 
                 outline=COLORS['success'], width=2)
    
    # Draw inner circles for seal decoration
    draw.ellipse([(seal_x - seal_size//2 + 10, seal_y - seal_size//2 + 10), 
                 (seal_x + seal_size//2 - 10, seal_y + seal_size//2 - 10)], 
                 outline=COLORS['success'], width=1)
    
    # Add checkmark in seal
    draw.text((seal_x - 10, seal_y - 20), "✓", font=get_better_font(40), fill=COLORS['success'])
    
    # Add verification text
    draw.text((seal_x - 35, seal_y + 20), "VERIFIED", font=small_font, fill=COLORS['success'])
    
    # Add explanatory text
    verify_text = "This document certifies that a blockchain transaction has been initiated."
    draw.text((70, verify_y + 30), verify_text, font=small_font, fill=COLORS['dark'])
    
    # Add timestamp verification
    time_verify = f"Timestamp: {date_str} {time_str} UTC"
    draw.text((70, verify_y + 60), time_verify, font=small_font, fill=COLORS['muted'])
    
    # Add footer
    footer_y = height - 40
    footer_text = "This is an electronic representation of a blockchain transaction. Verify on-chain for final confirmation."
    draw.text((width//2 - draw.textlength(footer_text, font=tiny_font)//2, footer_y), 
              footer_text, font=tiny_font, fill=COLORS['muted'])
    
    # Convert image to base64
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return img_str

@app.route('/generate-contract', methods=['POST', 'GET'])
def generate_contract():
    # Get payment data from request (either POST JSON or GET parameters)
    try:
        if request.method == 'POST':
            payment_data = request.json
        else:  # GET request
            payment_data = {
                'amount': request.args.get('amount', type=float),
                'sender': request.args.get('sender'),
                'receiver': request.args.get('receiver'),
                'timestamp': request.args.get('timestamp'),
                'currency': request.args.get('currency'),
                'currencyName': request.args.get('currencyName'),
                'currencySymbol': request.args.get('currencySymbol')
            }
            
            # Handle empty values
            payment_data = {k: v for k, v in payment_data.items() if v is not None}
    except Exception as e:
        return jsonify({"error": f"Invalid request data: {str(e)}"}), 400
    
    # Validate required fields
    required_fields = ['amount', 'sender', 'receiver']
    missing_fields = [field for field in required_fields if field not in payment_data]
    
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400
    
    # Set defaults for optional fields
    if 'timestamp' not in payment_data:
        payment_data['timestamp'] = datetime.now().isoformat()
    if 'currency' not in payment_data:
        payment_data['currency'] = 'eth'
    if 'currencyName' not in payment_data:
        currency_names = {
            'btc': 'Bitcoin',
            'eth': 'Ethereum',
            'usdt': 'Tether',
            'sol': 'Solana',
            'bnb': 'Binance Coin'
        }
        payment_data['currencyName'] = currency_names.get(payment_data['currency'].lower(), 'Cryptocurrency')
    if 'currencySymbol' not in payment_data:
        currency_symbols = {
            'btc': 'BTC',
            'eth': 'ETH',
            'usdt': 'USDT',
            'sol': 'SOL',
            'bnb': 'BNB'
        }
        payment_data['currencySymbol'] = currency_symbols.get(payment_data['currency'].lower(), payment_data['currency'].upper())
    
    try:
        # Create the contract image
        base64_image = create_contract_image(payment_data)
        
        # Check if the parameter 'download' is present in the request
        download = request.args.get('download', 'false').lower() == 'true'
        
        if download and request.method == 'GET':
            # Decode the base64 string back to binary
            image_data = base64.b64decode(base64_image)
            
            # Generate a filename based on transaction details
            filename = f"blockchain_contract_{payment_data['currency']}_{payment_data['amount']}.png"
            
            # Create a response with the image data
            response = app.response_class(
                response=image_data,
                status=200,
                mimetype='image/png'
            )
            
            # Add Content-Disposition header to trigger download
            response.headers.set('Content-Disposition', f'attachment; filename="{filename}"')
            
            return response
        else:
            # Return the image as base64 JSON
            return jsonify({
                "success": True,
                "image": f"data:image/png;base64,{base64_image}"
            })
    
    except Exception as e:
        return jsonify({"error": f"Error generating contract: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "message": "Blockchain Contract API is running",
        "version": "1.1.0",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Provide a simple HTML interface for testing the API"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Blockchain Contract Generator</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9fafb;
                color: #1f2937;
            }
            h1 {
                color: #10b981;
                border-bottom: 2px solid #10b981;
                padding-bottom: 10px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input, select {
                width: 100%;
                padding: 8px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 16px;
            }
            button {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #059669;
            }
            #result {
                margin-top: 20px;
            }
            img {
                max-width: 100%;
                border-radius: 8px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .container {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            }
            .api-info {
                background-color: #f3f4f6;
                border-left: 4px solid #10b981;
                padding: 15px;
                margin: 20px 0;
                border-radius: 0 4px 4px 0;
            }
            code {
                background-color: #e5e7eb;
                padding: 2px 4px;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Blockchain Contract Generator</h1>
            
            <div class="api-info">
                <p>This API generates visual blockchain payment contracts.</p>
                <p>You can use either:</p>
                <ul>
                    <li>POST request with JSON data</li>
                    <li>GET request with URL parameters</li>
                </ul>
                <p>Example GET URL: <code>/generate-contract?amount=0.15&sender=0x123...&receiver=0x456...</code></p>
            <p>To directly download the image, add <code>&download=true</code> to the URL.</p>
            </div>
            
            <form id="contractForm">
                <div class="form-group">
                    <label for="amount">Amount:</label>
                    <input type="number" id="amount" name="amount" step="0.000001" required placeholder="0.15">
                </div>
                
                <div class="form-group">
                    <label for="sender">Sender Address:</label>
                    <input type="text" id="sender" name="sender" required placeholder="0x71C7656EC7ab88b098defB751B7401B5f6d8976F">
                </div>
                
                <div class="form-group">
                    <label for="receiver">Receiver Address:</label>
                    <input type="text" id="receiver" name="receiver" required placeholder="0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199">
                </div>
                
                <div class="form-group">
                    <label for="currency">Cryptocurrency:</label>
                    <select id="currency" name="currency">
                        <option value="eth">Ethereum (ETH)</option>
                        <option value="btc">Bitcoin (BTC)</option>
                        <option value="usdt">Tether (USDT)</option>
                        <option value="sol">Solana (SOL)</option>
                        <option value="bnb">Binance Coin (BNB)</option>
                    </select>
                </div>
                
                <button type="submit">Generate Contract</button>
            </form>
            
            <div id="result"></div>
            
            <script>
                document.getElementById('contractForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const amount = document.getElementById('amount').value;
                    const sender = document.getElementById('sender').value;
                    const receiver = document.getElementById('receiver').value;
                    const currency = document.getElementById('currency').value;
                    
                    // Create URL with parameters for GET request
                    const url = `/generate-contract?amount=${amount}&sender=${encodeURIComponent(sender)}&receiver=${encodeURIComponent(receiver)}&currency=${currency}&timestamp=${new Date().toISOString()}`;
                    
                    // Add direct download button
                    const downloadUrl = `${url}&download=true`;
                    
                    try {
                        const response = await fetch(url);
                        const data = await response.json();
                        
                        if (data.success && data.image) {
                            document.getElementById('result').innerHTML = `
                                <h2>Generated Contract</h2>
                                <img src="${data.image}" alt="Blockchain Contract">
                                <div style="margin-top: 15px;">
                                    <a href="${downloadUrl}" class="download-btn" style="background-color: #10b981; color: white; padding: 10px 15px; border-radius: 4px; text-decoration: none; display: inline-block;">
                                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 5px;">
                                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                            <polyline points="7 10 12 15 17 10"></polyline>
                                            <line x1="12" y1="15" x2="12" y2="3"></line>
                                        </svg>
                                        Download Contract
                                    </a>
                                </div>
                                <p>You can click the download button or right-click to save this image</p>
                            `;
                        } else {
                            document.getElementById('result').innerHTML = `
                                <h2>Error</h2>
                                <p>${data.error || 'Unknown error occurred'}</p>
                            `;
                        }
                    } catch (error) {
                        document.getElementById('result').innerHTML = `
                            <h2>Error</h2>
                            <p>${error.message}</p>
                        `;
                    }
                });
            </script>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    # Run app with host='0.0.0.0' to make it publicly accessible
    app.run(host='0.0.0.0', port=port, debug=True)
