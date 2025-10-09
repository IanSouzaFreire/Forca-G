# Client part

to make easy visualization, it is included the given tree-like structure.

CLIENT <br />
├── Dependencies <br />
│   └── jQuery 3.7.1 (CDN) <br />
│ <br />
├── Constants <br />
│   ├── API_HOST and API_PROTOCOL <br />
│   ├── DOM Elements: <br />
│   │   ├── #cp-btn → "Verificar Preço" button <br />
│   │   ├── #payout-btn → "Gerar PIX" button <br />
│   │   ├── #usrID → input field <br />
│   │   ├── #response → message area <br />
│   │   └── #pricingInfo, #qrSection → info display areas <br />
│   └── currentPricing = null <br />
│ <br />
├── Utility Functions <br />
│   ├── strEmpty(str) <br />
│   │   → Checks if a string is empty or whitespace <br />
│ <br />
│   ├── showResponse(message, type) <br />
│   │   → Shows feedback (success / error / loading) <br />
│ <br />
│   └── clearResponse() <br />
│       → Hides messages, pricing info, and QR section <br />
│ <br />
├── Button Actions <br />
│ <br />
│   ├── "Verificar Preço" (Check Price) <br />
│   │   → Validates input <br />
│   │   → Calls GET /pricing/:username <br />
│   │   → Shows price details or error <br />
│ <br />
│   ├── "Gerar PIX" (Generate PIX) <br />
│   │   → Uses currentPricing <br />
│   │   → Calls POST /payout <br />
│   │   → Shows QR code and BR code <br />
│ <br />
│   └── Pressing Enter in input <br />
│       → Triggers "Verificar Preço" button <br />
│ <br />
├── API Calls <br />
│ <br />
│   ├── GET /pricing/:username <br />
│   │   → Returns: <br />
│   │      - username <br />
│   │      - post_count <br />
│   │      - price_per_post <br />
│   │      - total_price <br />
│   │   → Updates UI with pricing info <br />
│ <br />
│   └── POST /payout <br />
│       → Sends: <br />
│          - description <br />
│          - amount <br />
│          - username <br />
│       → Returns: <br />
│          - qr_code (image path) <br />
│          - br_code (text) <br />
│       → Displays PIX QR and code <br />
│ <br />
└── UI Updates <br />
    ├── Pricing info → #pricingInfo <br />
    ├── QR code → #qrSection, #qrcode, #brCode <br />
    ├── User messages → #responseSection, #response <br />
