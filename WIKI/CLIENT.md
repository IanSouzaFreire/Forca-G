# Client part

to make easy visualization, it is included the given tree-like structure.

📦 CLIENT
├── Dependencies
│   └── jQuery 3.7.1 (CDN)
│
├── Constants
│   ├── API_HOST and API_PROTOCOL
│   ├── DOM Elements:
│   │   ├── #cp-btn → "Verificar Preço" button
│   │   ├── #payout-btn → "Gerar PIX" button
│   │   ├── #usrID → input field
│   │   ├── #response → message area
│   │   └── #pricingInfo, #qrSection → info display areas
│   └── currentPricing = null
│
├── Utility Functions
│   ├── strEmpty(str)
│   │   → Checks if a string is empty or whitespace
│
│   ├── showResponse(message, type)
│   │   → Shows feedback (success / error / loading)
│
│   └── clearResponse()
│       → Hides messages, pricing info, and QR section
│
├── Button Actions
│
│   ├── "Verificar Preço" (Check Price)
│   │   → Validates input
│   │   → Calls GET /pricing/:username
│   │   → Shows price details or error
│
│   ├── "Gerar PIX" (Generate PIX)
│   │   → Uses currentPricing
│   │   → Calls POST /payout
│   │   → Shows QR code and BR code
│
│   └── Pressing Enter in input
│       → Triggers "Verificar Preço" button
│
├── API Calls
│
│   ├── GET /pricing/:username
│   │   → Returns:
│   │      - username
│   │      - post_count
│   │      - price_per_post
│   │      - total_price
│   │   → Updates UI with pricing info
│
│   └── POST /payout
│       → Sends:
│          - description
│          - amount
│          - username
│       → Returns:
│          - qr_code (image path)
│          - br_code (text)
│       → Displays PIX QR and code
│
└── UI Updates
    ├── Pricing info → #pricingInfo
    ├── QR code → #qrSection, #qrcode, #brCode
    ├── User messages → #responseSection, #response
