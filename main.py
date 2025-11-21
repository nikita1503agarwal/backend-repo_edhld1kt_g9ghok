import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from database import create_document, get_documents, db
from schemas import Template as TemplateSchema, Guide as GuideSchema

app = FastAPI(title="Design Tutor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Design Tutor Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ----------------------------------------------------------------------------
# Templates: create and list
# ----------------------------------------------------------------------------

@app.post("/api/templates")
def create_template(payload: TemplateSchema):
    try:
        template_id = create_document("template", payload)
        return {"id": template_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates")
def list_templates(limit: int = 20):
    try:
        docs = get_documents("template", {}, limit)
        # convert ObjectId
        for d in docs:
            d["id"] = str(d.pop("_id", ""))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# Guide generation: analyze a design name/url and produce steps per tool
# ----------------------------------------------------------------------------

class GuideRequest(BaseModel):
    source_name: str = Field(..., description="Name or short description of the uploaded design")
    image_url: Optional[str] = Field(None, description="Optional URL to the design image")
    tools: List[str] = Field(default_factory=lambda: ["photoshop", "canva", "illustrator"])  

@app.post("/api/guides")
def generate_guide(req: GuideRequest):
    detected = _detect_design(req.source_name)
    steps_map: Dict[str, List[str]] = {}
    for tool in req.tools:
        steps_map[tool.lower()] = _build_steps(tool.lower(), detected)

    guide_doc = GuideSchema(
        source_name=req.source_name,
        detected=detected,
        steps=steps_map,
    )
    try:
        guide_id = create_document("guide", guide_doc)
    except Exception:
        guide_id = None

    return {
        "id": guide_id,
        "source_name": guide_doc.source_name,
        "detected": guide_doc.detected,
        "steps": guide_doc.steps,
        "image_url": req.image_url,
    }

# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------

def _detect_design(name: str) -> Dict[str, Any]:
    name_l = name.lower()
    layout = "poster"
    if any(k in name_l for k in ["story", "reel", "vertical", "instagram story"]):
        layout = "story"
    elif any(k in name_l for k in ["square", "instagram", "post"]):
        layout = "square"
    elif any(k in name_l for k in ["a4", "flyer", "print"]):
        layout = "a4"

    palette = ["#0B0F1A", "#FF7A00", "#FFFFFF"] if any(k in name_l for k in ["tech", "futur", "robot"]) else ["#111827", "#E5E7EB", "#FF4D4D"]
    fonts = ["Inter", "Manrope"] if "modern" in name_l or "tech" in name_l else ["Poppins", "Montserrat"]

    structure = [
        {"type": "background", "style": "gradient" if "grad" in name_l else "solid"},
        {"type": "image", "position": "center" if layout != "story" else "top"},
        {"type": "headline", "weight": "700", "case": "upper"},
        {"type": "subhead", "weight": "500"},
        {"type": "cta", "variant": "pill"}
    ]

    return {
        "layout": layout,
        "palette": palette,
        "fonts": fonts,
        "structure": structure
    }

def _build_steps(tool: str, d: Dict[str, Any]) -> List[str]:
    size_map = {
        "story": (1080, 1920),
        "square": (1080, 1080),
        "poster": (1080, 1350),
        "a4": (2480, 3508)
    }
    w, h = size_map.get(d.get("layout", "poster"), (1080, 1350))

    common = [
        f"Create a new document sized {w}x{h} px.",
        f"Set background to {'a subtle radial gradient' if d['structure'][0]['style']=='gradient' else d['palette'][0]}.",
        f"Place the main image {'centered' if d['structure'][1]['position']=='center' else 'near the top'} and size it proportionally.",
        f"Add a bold headline using {d['fonts'][0]} and align left.",
        f"Add supporting text with {d['fonts'][-1]} and reduce tracking slightly.",
        f"Create a call-to-action button using {d['palette'][1]} and white text.",
        "Export as high-quality PNG (and save the source file as a reusable template)."
    ]

    if tool == "photoshop":
        prefix = [
            "Open Photoshop.",
            "File > New.",
            "Use Shape layers and Smart Objects for non-destructive editing.",
        ]
        suffix = [
            "Group layers (BG, Image, Text, CTA).",
            "Save as PSD and export PNG.",
        ]
    elif tool == "illustrator":
        prefix = [
            "Open Illustrator.",
            "File > New (RGB).",
            "Use rectangles and Type tool; keep elements on separate layers.",
        ]
        suffix = [
            "Convert shapes to symbols for reusability.",
            "Save as AI and export PNG.",
        ]
    else:  # canva
        prefix = [
            "Open Canva.",
            f"Create a custom size {w}x{h}.",
            "Add a gradient or color rectangle as background.",
        ]
        suffix = [
            "Use Position > Tidy up to align elements.",
            "Download PNG and save the design as a template.",
        ]

    return prefix + common + suffix

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
