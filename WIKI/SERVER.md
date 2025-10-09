# Server part

the structure contains information on each segment of the code.

Instagram Pricing Server (Flask App) <br />
├── Dependencies <br />
│   ├── Flask, qrcode, brcode <br />
│   ├── requests, dotenv, re, json, logging, datetime, PIL <br />
│   └── Other stdlib: os, base64, random, io, decimal <br />
│ <br />
├── Environment & Constants <br />
│   ├── .env variables: <br />
│   │   ├── PRICE_PER_POST <br />
│   │   ├── PIXKEY, NAME, CITY, CPF, ZIPCODE <br />
│   └── PRICE_PER_POST (float) <br />
│ <br />
├── Pattern Detection <br />
│   └── PRIVATE_INFO_PATTERNS <br />
│       → Regex patterns for: <br />
│         email, phone, CPF, address, password hints, DOB, etc. <br />
│ <br />
├── Core Features <br />
│ <br />
│   ├── 1. get_instagram_post_count(username) <br />
│   │   → Calls public Instagram API to get post count <br />
│ <br />
│   ├── 2. scan_posts_for_private_info(username) <br />
│   │   → Fetches user feed <br />
│   │   → Scans captions, comments, and image content <br />
│   │   → Uses regex and Roboflow (YOLO) model to detect: <br />
│   │      - Private data in text <br />
│   │      - Credit cards in images <br />
│ <br />
│   ├── 3. detect_cards_in_image(image_url) <br />
│   │   → Sends image to Roboflow YOLO model <br />
│   │   → Returns bounding box & confidence if card found <br />
│ <br />
│   └── 4. scan_text_for_private_info(text, post, results) <br />
│       → Matches regex in caption/comment, stores findings <br />
│ <br />
├── 💸 PIX / QR Code Logic <br />
│ <br />
│   ├── generate_pix_br_code(...) <br />
│   │   → Generates BRCode (static payment) with metadata <br />
│ <br />
│   └── generate_qrcode_image(data) <br />
│       → Converts BRCode string into PNG QR image <br />
│       → Saves to /out/ directory <br />
│ <br />
├── Flask Routes <br />
│ <br />
│   ├── GET / <br />
│   │   → Serves frontend HTML (index.html) <br />
│ <br />
│   ├── GET /access/<QRcode> <br />
│   │   → Returns PNG image file from /out/ folder <br />
│ <br />
│   ├── GET /pricing/<username> <br />
│   │   → Returns: <br />
│   │      - post_count <br />
│   │      - total_price (R$) <br />
│   │      - price_per_post <br />
│ <br />
│   └── POST /payout <br />
│       → Accepts JSON with: <br />
│         - username, amount, description <br />
│       → Generates: <br />
│         - BR Code (string) <br />
│         - QR image (saved locally) <br />
│       → Also triggers private info scan <br />
│       → Returns JSON: <br />
│         - QR Code image path <br />
│         - BR Code text <br />
│         - scan_results <br />
│ <br />
└── Logging & Errors <br />
    ├── Logs to console via `logging` <br />
    ├── Warnings for API errors or card detections <br />
    └── Handles most exceptions with friendly error JSON <br />
