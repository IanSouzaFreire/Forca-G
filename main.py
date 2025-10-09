import qrcode
from brcode import BRCode
import requests
import re
import json
import logging
import flask
from typing import Optional, List, Dict
from io import BytesIO
import base64
from datetime import datetime
from PIL import Image
import os
from decimal import Decimal
from random import randint
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# R$
PRICE_PER_POST = float(os.getenv('PRICE_PER_POST') or 0.5)

# Patterns for detecting private information
PRIVATE_INFO_PATTERNS = {
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phone': r'\b(?:\+?55[-.\s]?)?\(?\d{2}\)?[-.\s]?\d{4,5}[-.\s]?\d{4}\b',
    'cpf': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    'credit_card': r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
    'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
    'address': r'\b(?:rua|avenida|av\.|alameda|travessa|pça|praça|passagem|viela|beco|rodovia|estrada|caminho|estr\.)\s+[^,\n]+,?\s*\d+\b',
    'date_of_birth': r'\b(?:0[1-9]|[12][0-9]|3[01])/(?:0[1-9]|1[0-2])/(?:19|20)\d{2}\b',
    'password_hint': r'\b(?:senha|password|pwd|pass)[\s:=]+[^\s\n]+\b',
}


#
# YOLO Card Detection
#

ROBOFLOW_API_KEY = "YOUR_ROBOFLOW_API_KEY"  # Set this from environment variable
ROBOFLOW_MODEL_ID = "project-r3vnb/card-zwthj"
ROBOFLOW_API_URL = "https://detect.roboflow.com"


def detect_cards_in_image(image_url: str) -> Optional[Dict]:
    """
    Use YOLO model via Roboflow API to detect credit cards in an image.
    Makes direct HTTP requests to Roboflow's inference endpoint.
    
    Args:
        image_url (str): URL of the image to analyze
    
    Returns:
        dict: Detection results with cards found, or None on failure
    """
    try:
        logger.info(f"Analyzing image with YOLO model: {image_url}")
        
        # Download image and prepare for inference
        img_response = requests.get(image_url, timeout=10)
        img_response.raise_for_status()
        
        # Make inference request to Roboflow
        inference_url = f"{ROBOFLOW_API_URL}/infer"
        
        files = {
            'file': ('image.jpg', img_response.content, 'image/jpeg')
        }
        
        params = {
            'api_key': ROBOFLOW_API_KEY,
            'model': ROBOFLOW_MODEL_ID
        }
        
        response = requests.post(
            inference_url,
            files=files,
            params=params,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        if result and 'predictions' in result:
            predictions = result['predictions']
            
            if len(predictions) > 0:
                logger.warning(f"Found {len(predictions)} card(s) in image")
                return {
                    "cards_detected": len(predictions),
                    "predictions": predictions,
                    "image_url": image_url,
                    "confidence_scores": [p.get('confidence', 0) for p in predictions]
                }
        
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching or analyzing image: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing Roboflow response: {e}")
        return None
    except Exception as e:
        logger.error(f"Error detecting cards in image: {e}")
        return None


def get_instagram_post_count(username: str) -> Optional[int]:
    """
    Get the number of posts for a specific Instagram account using the Instagram API.
    
    Args:
        username (str): Instagram username (without @)
    
    Returns:
        int: Number of posts, or None if user not found or error occurs
    """
    try:
        # Using Instagram's public API endpoint
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-IG-App-ID": "936619743392459"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'ok' and 'data' in data:
            user_data = data['data'].get('user', {})
            post_count = user_data.get('edge_owner_to_timeline_media', {}).get('count')
            
            if post_count is not None:
                return int(post_count)
        
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Instagram profile: {e}")
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Error parsing Instagram data: {e}")
        return None


def scan_posts_for_private_info(username: str) -> Dict[str, any]:
    """
    Scan all posts from an Instagram account for potentially private information.
    
    Args:
        username (str): Instagram username (without @)
    
    Returns:
        dict: Scan results with findings organized by information type
    """
    results = {
        "username": username,
        "scan_timestamp": datetime.now().isoformat(),
        "total_posts_scanned": 0,
        "findings": {category: [] for category in PRIVATE_INFO_PATTERNS.keys()},
        "card_detections": [],
        "summary": {}
    }
    
    try:
        logger.info(f"Starting private information scan for @{username}")
        
        # Get user ID first
        url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "X-IG-App-ID": "936619743392459"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'ok' or 'data' not in data:
            logger.warning(f"Could not get user data for @{username}")
            return results
        
        user_id = data['data']['user']['id']
        
        # Fetch posts
        posts_url = f"https://www.instagram.com/api/v1/user/{user_id}/feed/"
        
        has_next = True
        end_cursor = None
        max_iterations = 10  # Limit to prevent excessive requests
        iteration = 0
        
        while has_next and iteration < max_iterations:
            try:
                params = {}
                if end_cursor:
                    params['max_id'] = end_cursor
                
                posts_response = requests.get(posts_url, headers=headers, params=params, timeout=10)
                posts_response.raise_for_status()
                posts_data = posts_response.json()
                
                if 'items' not in posts_data:
                    break
                
                for post in posts_data.get('items', []):
                    results["total_posts_scanned"] += 1
                    
                    # Scan caption
                    caption = post.get('caption', {}).get('text', '') or ''
                    scan_text_for_private_info(caption, post, results)
                    
                    # Scan image with YOLO if it's an image post
                    if post.get('media_type') == 1:  # 1 = image, 8 = carousel
                        image_url = post.get('image_versions2', {}).get('candidates', [{}])[0].get('url')
                        if image_url:
                            card_detection = detect_cards_in_image(image_url)
                            if card_detection:
                                card_detection["post_id"] = post.get('id')
                                card_detection["post_url"] = f"https://www.instagram.com/p/{post.get('code', 'unknown')}"
                                results["card_detections"].append(card_detection)
                    
                    # Scan comments
                    comments = post.get('comments_disabled', False)
                    if not comments and 'preview_comments' in post:
                        for comment in post.get('preview_comments', []):
                            comment_text = comment.get('text', '')
                            scan_text_for_private_info(comment_text, post, results, 'comment')
                
                # Check for pagination
                has_next = posts_data.get('more_available', False)
                end_cursor = posts_data.get('next_max_id', None)
                iteration += 1
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error fetching posts page: {e}")
                break
        
        # Generate summary
        for category, findings in results["findings"].items():
            if findings:
                results["summary"][category] = {
                    "count": len(findings),
                    "sample": findings[0] if findings else None
                }
        
        logger.info(f"Completed scan for @{username}. Found {sum(len(v) for v in results['findings'].values())} items with potential private information and {len(results['card_detections'])} card detection(s)")
        
        return results
        
    except Exception as e:
        logger.error(f"Error scanning posts for private information: {e}")
        results["error"] = str(e)
        return results


def scan_text_for_private_info(text: str, post: Dict, results: Dict, source: str = 'caption') -> None:
    """
    Scan text for private information patterns and add findings to results.
    
    Args:
        text (str): Text to scan
        post (dict): Post object containing metadata
        results (dict): Results dictionary to update
        source (str): Source of the text (caption or comment)
    """
    if not text:
        return
    
    post_id = post.get('id', 'unknown')
    post_url = f"https://www.instagram.com/p/{post.get('code', 'unknown')}"
    
    for info_type, pattern in PRIVATE_INFO_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        for match in matches:
            finding = {
                "detected_value": match,
                "source": source,
                "post_id": post_id,
                "post_url": post_url,
                "context": text[:100] + "..." if len(text) > 100 else text,
                "timestamp": datetime.now().isoformat()
            }
            results["findings"][info_type].append(finding)


#
# PIX/QR Code
#


def generate_pix_br_code(
    receiver_name: str,
    receiver_city: str,
    pix_key: str,
    receiver_cpf: str,
    zipcode: str,
    description: str,
    amount: float,
    IP: str
) -> Optional[str]:
    """
    Generate a PIX BR Code (static QR code with fixed amount) using brcode library.
    
    Args:
        receiver_name (str): Name of the receiver
        receiver_city (str): City of the receiver
        pix_key (str): PIX key (CPF, CNPJ, email, phone, or UUID)
        receiver_cpf (str): CPF or identification of receiver
        zipcode (str): Zipcode of receiver
        description (str): Payment description
        amount (float): Fixed amount in R$
    
    Returns:
        str: BR Code (EMV QR Code string), or None on failure
    """
    try:
        # Create BRCode instance with static payment (valor fixo)
        br_code = BRCode(
            name=receiver_name,
            city=receiver_city,
            amount=Decimal(amount),
            description=description,
            key=pix_key,
            transaction_id=f"[{IP}]{datetime.now()}",

        )
        
        # Generate the payload
        payload = str(br_code)
        logger.info(f"PIX BR Code generated successfully")
        return payload
        
    except Exception as e:
        logger.error(f"Error generating PIX BR Code: {e}")
        return None


def generate_qrcode_image(
    data: str,
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white"
) -> Optional[str]:
    """
    Generate and save a QR code image using pure qrcode library (no PIL/Pillow).
    
    Args:
        data (str): Data to encode in QR code
        output_path (str): Path to save QR code image
        box_size (int): Size of each box in pixels
        border (int): Border size in boxes
        fill_color (str): QR code color
        back_color (str): Background color
    
    Returns:
        str: Base64 encoded image string, or None on failure
    """
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")

        out_path = f"{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}-r{randint(0, 10**5)}-r{randint(0, 10**5)}.png"
        img.save("out/" + out_path)


        return out_path
        
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return None


#
# Flask App
#


app = flask.Flask(__name__)


@app.route("/", methods=['GET'])
def get_ui():
    """Serve the main UI page"""
    try:
        with open("app/index.html", 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error("index.html not found")
        return "Error: UI file not found", 404
    except Exception as e:
        logger.error(f"Error loading UI: {e}")
        return "Error loading UI", 500


@app.route("/access/<QRcode>", methods=['GET'])
def access_file(QRcode):
    return flask.Response(open("out/" + QRcode, 'rb').read(), mimetype='image/png')


@app.route("/pricing/<insta>", methods=['GET'])
def get_pricing(insta: str):
    """Get Instagram post count and calculate pricing"""
    try:
        post_count = get_instagram_post_count(insta)
        
        if post_count is None:
            return {"error": "Could not fetch Instagram data"}, 404
        
        price = post_count * PRICE_PER_POST
        
        return {
            "username": insta,
            "post_count": post_count,
            "price_per_post": PRICE_PER_POST,
            "total_price": price
        }, 200
        
    except Exception as e:
        logger.error(f"Error in pricing endpoint: {e}")
        return {"error": str(e)}, 500


@app.route("/payout", methods=['POST'])
def generate_qrcode():
    """Generate PIX QR code for payment"""
    try:
        request_data = flask.request.get_json()
        
        if not request_data:
            return {"error": "Invalid request body"}, 400
        
        # Extract PIX parameters from request
        receiver_name = os.getenv('NAME') or 'a'
        receiver_city = os.getenv('CITY') or 'a'
        pix_key = os.getenv('PIXKEY') or 'a'
        receiver_cpf = os.getenv('CPF') or 'a'
        zipcode = os.getenv('ZIPCODE') or 'a'
        description = request_data.get('description', 'Doação com valor fixo')
        amount = float(request_data.get('amount', 15.0))
        username = request_data.get('username', 'undefined')
        
        # Generate PIX BR Code using dedicated library
        br_code = generate_pix_br_code(
            receiver_name=receiver_name,
            receiver_city=receiver_city,
            pix_key=pix_key,
            receiver_cpf=receiver_cpf,
            zipcode=zipcode,
            description=description,
            amount=amount,
            IP=str(flask.request.remote_addr)
        )
        
        if not br_code:
            return {"error": "Failed to generate PIX BR Code"}, 500
        
        # Generate QR code image
        qr_base64 = generate_qrcode_image(
            data=br_code
        )
        
        if not qr_base64:
            return {"error": "Failed to generate QR code"}, 500
        
        # NOTE: In production, integrate with actual payment confirmation system
        # For now, we execute the scan immediately after QR code generation
        # as a proof of concept
        if username:
            logger.info(f"Payment initiated for @{username}, initiating post scan")
            scan_results = scan_posts_for_private_info(username)
        else:
            scan_results = None
        
        return {
            "br_code": br_code,
            "qr_code": f"data:image/png;base64,{qr_base64}",
            "receiver_name": receiver_name,
            "amount": amount,
            "status": "success",
            "scan_results": scan_results
        }, 200
        
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return {"error": f"Invalid parameters: {str(e)}"}, 400
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True)