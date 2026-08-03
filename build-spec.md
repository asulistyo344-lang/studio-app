# ANOM-AI-SaaS — Claude Code Build Spec
# Studio Backend + React Webapp
# Date: July 2026

---

## CONTEXT — EXISTING VPS SETUP (DO NOT CONFLICT)

VPS: 43.134.107.159 (Tencent Cloud, Singapore, 2GB RAM)
OS: Ubuntu 22.04

RUNNING SERVICES — DO NOT TOUCH:
  nebula-api      → port 8000  → /root/workspace/nebula-app
  aura-backend    → port 8002  → /root/workspace/aura-app
  boost-backend   → port 8004  → /root/workspace/boost-app

NEW SERVICE:
  studio-backend  → port 8006  → /root/workspace/studio-app

SHARED INFRASTRUCTURE:
  PostgreSQL: running, has nebula_db + boost_db
    → Create new DB: studio_db (separate, no conflicts)
  Redis: running on default port 6379
    → Boost uses DB 2, Nebula uses DB 0, Aura uses DB 1
    → Studio uses DB 3
  Nginx: running, proxying existing backends
  PM2: managing all processes

BYTEPLUS API (shared, same key as Boost):
  Base URL: https://ark.ap-southeast.bytepluses.com/api/v3
  API Key: same as /root/workspace/boost-app/backend/.env BYTEPLUS_API_KEY
  Region: ap-southeast-1

---

## WHAT WE ARE BUILDING

App name: Anom-AI-SaaS
Purpose: AI-powered image/3D generation studio
         Users upload photos → AI generates styled variants
Target: Web-first (designers, brands, e-commerce sellers)

Three generation modes in one app:
1. Interior/Exterior Design → room or building photo → style variants
2. Product on Model → product photo → model wearing/using it
3. Hyper3D → product photo → 3D model render

---

## TECH STACK

Backend:
  Python 3.11 (explicit, never bare python3)
  FastAPI 0.111.0
  No database needed for MVP (stateless API)
  No Redis needed for MVP (no quota system yet)
  BytePlus ModelArk API (Seedream + Hyper3D)
  Port: 8006
  Install dir: /root/workspace/studio-app

Frontend:
  React 18 + Vite
  TailwindCSS
  Host: Vercel (free tier) OR serve as static from VPS
  Calls backend API directly
  No auth needed for MVP

---

## BACKEND CONSTRAINTS (from previous app lessons)

CRITICAL — apply these to every file:
- Python 3.11 explicit EVERYWHERE in setup.sh
  Use: python3.11 -m pip (never bare pip)
  Use: python3.11 main.py (never python3)
- Every HTTPException returns SPECIFIC detail string
  Never: raise HTTPException(status_code=500, detail="Error")
  Always: raise HTTPException(status_code=503, detail="Seedream image generation failed. Please retry.")
- All BytePlus calls wrapped in try/except with full error logging
  Log: logger.error(f"[BytePlus] HTTP {status}: {body[:500]}")
- setup.sh passwords MUST match .env.example exactly
- ecosystem.config.js cwd uses variable, never hardcoded path

---

## BYTEPLUS API PATTERNS (verified working)

### Image Generation (Seedream 4.5) — SYNC
Endpoint: POST /api/v3/images/generations
Pattern: Submit → get result immediately (sync)

Request format (VERIFIED WORKING):
{
  "model": "seedream-4-5-251128",
  "prompt": "your style prompt here",
  "image": ["data:image/jpeg;base64,{base64_string}"],  ← array of data URIs
  "size": "2K",           ← NOT "1024x1024", must be "2K" or "4K"
  "response_format": "url",
  "watermark": false,
  "stream": false
}

Response format:
{
  "data": [{"url": "https://...jpeg", "size": "2048x2048"}],
  "usage": {"generated_images": 1}
}

IMPORTANT NOTES:
- "image" field is ARRAY of strings (data URIs or URLs)
- "size" is "2K" or "4K" — NOT pixel dimensions
- Accepts: data:image/jpeg;base64,... OR data:image/png;base64,...
- Min image size: 14x14 pixels
- Recommended: 512x512 or larger for best results
- Each call generates 1 image
- For 3 variants: make 3 parallel async calls

### 3D Generation (Hyper3D) — ASYNC TASK
Endpoint: POST /api/v3/3d/generations/tasks  ← check exact path in docs
Pattern: Submit task → poll until done (async, takes 60-180s)

IMPORTANT: Verify exact endpoint and model ID in BytePlus console
before coding. Check if hyper3d model is enabled on account.
Test with direct curl before writing backend code.

Direct curl test (run this first):
curl -s -X POST \
  "https://ark.ap-southeast.bytepluses.com/api/v3/3d/generations/tasks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BYTEPLUS_API_KEY" \
  -d '{
    "model": "hyper3d-rodin-20250412",
    "images": [{"url": "data:image/jpeg;base64,..."}]
  }'

If endpoint is wrong, check:
  https://docs.byteplus.com/en/docs/ModelArk/2279947

Polling pattern (same as video gen in boost-backend):
1. Submit → get task_id
2. GET /api/v3/3d/generations/tasks/{task_id} every 10s
3. Check status: "running" | "succeeded" | "failed"
4. On succeeded: extract 3D model URLs from response

---

## API ENDPOINTS TO BUILD

### POST /studio/generate-images
Generate 3 styled image variants from input image(s)

Request body:
{
  "niche": "interior" | "exterior" | "product_model",
  "style": string,           // from STYLES config below
  "images": [string],        // array of base64 strings (1-2 images)
  "user_prompt": string,     // optional, user customization
  "n_variants": 3            // fixed at 3 for now
}

Logic:
1. Validate niche + style combination
2. Build style-specific prompt from PROMPTS config
3. Append user_prompt if provided
4. For each variant (3 total): call Seedream with different style emphasis
5. Run 3 calls in parallel with asyncio.gather
6. Return all 3 URLs

Response:
{
  "niche": "interior",
  "style": "Modern",
  "variants": [
    {"label": "Variant 1", "url": "https://..."},
    {"label": "Variant 2", "url": "https://..."},
    {"label": "Variant 3", "url": "https://..."}
  ]
}

Error responses (specific messages required):
  400: "Niche must be one of: interior, exterior, product_model"
  400: "Style '{style}' not valid for niche '{niche}'"
  400: "At least one image is required"
  400: "Image {n} is invalid or too small (minimum 14x14 pixels)"
  503: "Image generation failed. Please retry."
  503: "Seedream service unavailable. Please retry shortly."

### POST /studio/generate-3d
Generate 3D model from product image

Request body:
{
  "image": string,           // base64 string
  "user_prompt": string      // optional
}

Logic:
1. Submit Hyper3D task
2. Poll until succeeded or failed (max 180s)
3. Return 3D model URLs

Response:
{
  "task_id": "...",
  "status": "succeeded",
  "model_url": "https://...",      // .glb or .obj file
  "preview_url": "https://..."     // preview image
}

### GET /studio/styles
Returns available styles per niche (so frontend can render options)

Response:
{
  "interior": ["Modern", "Minimalist", "Scandinavian", "Bohemian", "Industrial", "Japandi", "Mediterranean"],
  "exterior": ["Contemporary", "Classic", "Tropical", "Minimalist", "Mediterranean", "Industrial Modern"],
  "product_model": ["Casual Street", "Professional", "Outdoor", "Luxury Editorial", "Fitness", "Beach Summer"]
}

### GET /studio/health
{
  "status": "ok",
  "app": "Anom-AI-SaaS Studio",
  "port": 8006
}

---

## PROMPT TEMPLATES PER NICHE

### INTERIOR
Base: "Interior design visualization. {style} style redesign.
       Photorealistic architectural photography.
       Professional interior design magazine quality.
       Natural lighting, high resolution, 8k."

Style additions:
  Modern: "Clean lines, neutral palette, minimal furniture, open space"
  Minimalist: "Extreme simplicity, monochrome, only essential elements"
  Scandinavian: "Light wood, white walls, cozy textures, hygge atmosphere"
  Bohemian: "Eclectic mix, warm colors, plants, layered textiles, rattan"
  Industrial: "Exposed brick, metal, Edison bulbs, raw materials"
  Japandi: "Japanese-Scandinavian fusion, wabi-sabi, muted earth tones"
  Mediterranean: "Arches, terracotta, blue accents, whitewashed walls"

### EXTERIOR
Base: "Architectural exterior visualization. {style} style facade redesign.
       Photorealistic architectural photography.
       Professional architectural render quality.
       Golden hour lighting, landscaping included, high resolution."

Style additions:
  Contemporary: "Glass, steel, geometric forms, flat or low-pitched roof"
  Classic: "Symmetrical, columns, traditional materials, timeless"
  Tropical: "Natural materials, large overhangs, open air design, lush greenery"
  Minimalist: "Clean facade, minimal ornamentation, monochrome palette"
  Mediterranean: "Stucco walls, terracotta roof, arched windows, warm tones"
  Industrial Modern: "Exposed steel, brick, large factory windows, urban"

### PRODUCT ON MODEL
Base: "Professional fashion/lifestyle product photography.
       {style} aesthetic.
       The product must be clearly visible and accurately represented.
       Commercial photography quality, magazine editorial standard."

Style additions:
  Casual Street: "Urban street style, casual outfit, city background, natural light"
  Professional: "Office/business setting, professional attire, clean background"
  Outdoor: "Natural outdoor setting, adventure/lifestyle context, golden hour"
  Luxury Editorial: "High fashion, dramatic lighting, luxury hotel or venue setting"
  Fitness: "Athletic context, gym or outdoor fitness, activewear aesthetic"
  Beach Summer: "Beach/tropical setting, summer fashion, warm light, sand and water"

---

## VARIANT DIFFERENTIATION

For 3 variants of same niche+style, add these suffixes to vary output:

Variant 1: "angle: wide establishing shot, full room/product view"
Variant 2: "angle: medium shot, detail focus, lifestyle context"
Variant 3: "angle: close detail shot, texture and material emphasis"

This ensures 3 genuinely different images rather than near-duplicates.

---

## FILE STRUCTURE

studio-app/
├── backend/
│   ├── main.py              ← FastAPI app, port 8006
│   ├── config.py            ← settings from .env
│   ├── routes.py            ← all endpoints
│   ├── image_gen.py         ← Seedream calls
│   ├── gen_3d.py            ← Hyper3D async task calls
│   ├── prompts.py           ← all prompt templates + styles config
│   ├── schemas.py           ← Pydantic models
│   ├── requirements.txt
│   ├── .env.example
│   ├── setup.sh
│   └── ecosystem.config.js
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api.js            ← all API calls
        └── components/
            ├── NichePicker.jsx
            ├── StylePicker.jsx
            ├── ImageUploader.jsx
            ├── PromptInput.jsx
            ├── GenerateButton.jsx
            ├── ResultsGrid.jsx
            ├── ImageCard.jsx
            └── ThreeDViewer.jsx

---

## REQUIREMENTS.TXT

fastapi==0.111.0
uvicorn[standard]==0.30.1
httpx==0.27.0
python-dotenv==1.0.1
pydantic[email]==2.7.1
pydantic-settings==2.2.1
python-multipart==0.0.9

Note: No SQLAlchemy, no Redis, no bcrypt needed for MVP.
Stateless API — no database.

---

## .ENV.EXAMPLE

# BytePlus (same account as Boost app)
BYTEPLUS_API_KEY=your_byteplus_api_key_here
BYTEPLUS_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3

# Models
BYTEPLUS_IMAGE_MODEL=seedream-4-5-251128
BYTEPLUS_3D_MODEL=hyper3d-rodin-20250412

# App
APP_NAME=Anom-AI-SaaS
PORT=8006
ENVIRONMENT=development

# CORS — update with Vercel URL after deploy
ALLOWED_ORIGINS=http://localhost:5173,https://your-vercel-app.vercel.app

---

## SETUP.SH REQUIREMENTS

Must do (all lessons from previous apps applied):
1. Check python3.11 exists, install if not
2. Create venv with python3.11 -m venv venv
3. Install with venv/bin/python3.11 -m pip install -r requirements.txt
4. Copy .env.example to .env if not exists
5. NO PostgreSQL setup needed (stateless)
6. NO Redis setup needed (stateless)
7. Write ecosystem.config.js with variable INSTALL_DIR
8. Create logs/ directory

---

## ECOSYSTEM.CONFIG.JS TEMPLATE

module.exports = {
  apps: [{
    name: "studio-backend",
    script: "/root/workspace/studio-app/backend/venv/bin/python3.11",
    args: "main.py",
    cwd: "/root/workspace/studio-app/backend",
    interpreter: "none",
    env: { PYTHONPATH: "/root/workspace/studio-app/backend" },
    error_file: "/root/workspace/studio-app/backend/logs/error.log",
    out_file:   "/root/workspace/studio-app/backend/logs/out.log",
    restart_delay: 5000,
    max_restarts: 10,
  }]
};

---

## FRONTEND REQUIREMENTS

### UI Layout
Left panel (controls):
  1. Niche selector — 3 cards with icons
     "Interior Design" / "Exterior Design" / "Product on Model"
  
  2. Style selector — grid changes based on niche
     Fetch from GET /studio/styles on load
  
  3. Image upload zone
     - Drag and drop or click to upload
     - Accepts JPG/PNG
     - Shows preview thumbnail
     - For product_model niche: allow 2 images
       (product photo + optional style reference)
     - CAMERA CAPTURE: yes, use HTML5 <input type="file" accept="image/*" capture="environment">
       This works on mobile browsers natively
       No special library needed for camera capture
  
  4. Optional prompt field
     Placeholder: "Add specific details... (optional)"
     Max 200 chars
  
  5. Generate button
     Shows spinner + "Generating 3 variants..." when loading

Right panel (results):
  - 3 image cards in a grid
  - Loading skeleton while generating
  - Each card: image preview + Download button
  - Click image: opens full-size in modal
  - Download: triggers browser download of image URL

### 3D Section
Separate tab/section below main interface:
  - Single image upload
  - Optional prompt
  - Generate 3D button
  - Result: 3D model viewer (use model-viewer web component)
    <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js">
  - Download .glb button

### Camera capture on web:
Use standard HTML input — works on all mobile browsers:
<input
  type="file"
  accept="image/*"
  capture="environment"
  onChange={handleFileChange}
/>
No special library or permission handling needed.
Browser handles the camera/gallery choice natively.

### API call pattern:
- Convert uploaded file to base64 in browser before sending
- Use FileReader API:
  const reader = new FileReader()
  reader.readAsDataURL(file)
  reader.onload = () => {
    const base64 = reader.result.split(',')[1]  // strip data:image/jpeg;base64, prefix
    // send base64 to backend
  }

### Design:
- Dark theme (consistent with Boost/Nebula)
- Simple, clean, professional
- Not too many colors — white on dark bg
- Orange/amber accent color for CTAs
- App name "Anom AI" in header

---

## PM2 START COMMAND

After setup:
pm2 start ecosystem.config.js
pm2 save

Verify no port conflicts:
netstat -tlnp | grep -E "8000|8002|8004|8006"
Should show all 4 ports active.

---

## NGINX CONFIG (add to existing nginx, don't replace)

Add this server block to /etc/nginx/sites-available/default
(inside the existing http block, don't touch other blocks):

location /studio/ {
    proxy_pass http://localhost:8006/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 300s;    ← important for 3D gen which takes long
    proxy_send_timeout 300s;
}

---

## TEST CASES — VERIFY BEFORE DONE

TC-001: GET /studio/health → {"status":"ok"}
TC-002: GET /studio/styles → returns all 3 niches with style lists
TC-003: POST /studio/generate-images interior+Modern+image → 3 URLs returned
TC-004: POST /studio/generate-images exterior+Contemporary+image → 3 URLs returned
TC-005: POST /studio/generate-images product_model+Casual+image → 3 URLs returned
TC-006: POST /studio/generate-images with user_prompt → prompt included in generation
TC-007: POST /studio/generate-images missing image → 400 "At least one image is required"
TC-008: POST /studio/generate-images invalid niche → 400 specific error
TC-009: POST /studio/generate-3d with product image → task submitted → polls → returns model URL
TC-010: Frontend loads → niche picker shows 3 options
TC-011: Select niche → style picker updates with correct styles
TC-012: Upload image → preview shows
TC-013: Click Generate → loading state shows → results appear
TC-014: Camera capture button works on mobile browser
TC-015: Download button downloads image

---

## WHAT NOT TO BUILD (out of scope for this session)

- User authentication / accounts
- Payment / subscription
- Usage quota / rate limiting
- Database (stateless MVP only)
- Mobile app (webapp only)
- Trending feature
- Social sharing

These are Phase 2. Build clean stateless MVP only.

---

## DELIVERABLES CHECKLIST

Backend:
  [ ] main.py (FastAPI, port 8006)
  [ ] config.py
  [ ] routes.py (3 endpoints)
  [ ] image_gen.py (Seedream parallel calls)
  [ ] gen_3d.py (Hyper3D async poll)
  [ ] prompts.py (all templates + styles)
  [ ] schemas.py
  [ ] requirements.txt
  [ ] .env.example (matches setup.sh)
  [ ] setup.sh (Python 3.11 explicit)
  [ ] ecosystem.config.js (variable cwd)

Frontend:
  [ ] All components listed above
  [ ] Working API integration
  [ ] Camera capture working
  [ ] Base64 encoding before send
  [ ] Loading states
  [ ] Error display (inline, never alert())
  [ ] 3D viewer with model-viewer

Deployment:
  [ ] Backend running as PM2 process "studio-backend"
  [ ] Port 8006 confirmed active
  [ ] No conflicts with ports 8000/8002/8004
  [ ] All TC-001 to TC-015 pass
