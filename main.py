import os
from typing import List, Optional, Any, Dict
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from database import db, create_document, get_documents
from schemas import HerbalProduct, Article, Order

app = FastAPI(title="Herbal E-Commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc: Dict[str, Any]):
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # Convert datetimes to isoformat
    for k, v in list(doc.items()):
        if isinstance(v, (datetime,)):
            doc[k] = v.isoformat()
    return doc


@app.get("/")
def read_root():
    return {"message": "Herbal Store Backend Running"}


@app.get("/schema")
def get_schema():
    # Minimal schema exposure for tooling
    return {
        "collections": ["herbalproduct", "article", "order"],
        "models": {
            "HerbalProduct": HerbalProduct.model_json_schema(),
            "Article": Article.model_json_schema(),
            "Order": Order.model_json_schema(),
        },
    }


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, "name", None)
            try:
                response["collections"] = db.list_collection_names()
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ------------------ Products ------------------
@app.get("/api/products")
def list_products(q: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_dict: Dict[str, Any] = {}
    if q:
        # Simple case-insensitive search across name/description
        filter_dict["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"ingredients": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]
    if category:
        filter_dict["category"] = category

    docs = get_documents("herbalproduct", filter_dict)
    return [serialize_doc(d) for d in docs]


@app.post("/api/products", status_code=201)
def create_product(product: HerbalProduct):
    product_id = create_document("herbalproduct", product)
    return {"id": product_id}


# ------------------ Articles ------------------
@app.get("/api/articles")
def list_articles(tag: Optional[str] = Query(None)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_dict: Dict[str, Any] = {}
    if tag:
        filter_dict["tags"] = {"$in": [tag]}
    docs = get_documents("article", filter_dict)
    return [serialize_doc(d) for d in docs]


@app.post("/api/articles", status_code=201)
def create_article(article: Article):
    article_id = create_document("article", article)
    return {"id": article_id}


# ------------------ Orders ------------------
@app.post("/api/orders", status_code=201)
def create_order(order: Order):
    # Basic verification of total from items
    calc_total = sum(i.price * i.quantity for i in order.items)
    if abs(calc_total - order.total) > 1e-6:
        raise HTTPException(status_code=400, detail="Total does not match sum of items")
    order_id = create_document("order", order)
    return {"id": order_id}


# ------------------ Seed data on first run ------------------
@app.on_event("startup")
def seed_data():
    if db is None:
        return
    try:
        if db["herbalproduct"].count_documents({}) == 0:
            samples = [
                {
                    "name": "Teh Jahe Hangat",
                    "description": "Campuran jahe dan rempah untuk menghangatkan tubuh dan melancarkan pencernaan.",
                    "price": 35000,
                    "category": "Teh",
                    "in_stock": True,
                    "image": "https://images.unsplash.com/photo-1512314889357-e157c22f938d",
                    "ingredients": ["Jahe", "Kayu Manis", "Cengkeh"],
                    "usage": "Seduh 1 sachet dengan 200ml air panas, minum 2x sehari."
                },
                {
                    "name": "Minyak Kayu Putih Alami",
                    "description": "Minyak esensial untuk meredakan pegal, masuk angin, dan memberikan rasa hangat.",
                    "price": 42000,
                    "category": "Minyak",
                    "in_stock": True,
                    "image": "https://images.unsplash.com/photo-1615485737651-6df9d6f5e3c1",
                    "ingredients": ["Kayu Putih"],
                    "usage": "Oleskan secukupnya pada area yang diperlukan."
                },
                {
                    "name": "Kapsul Kunyit Asam",
                    "description": "Suplemen herbal untuk membantu menjaga kesehatan pencernaan dan stamina.",
                    "price": 59000,
                    "category": "Suplemen",
                    "in_stock": True,
                    "image": "https://images.unsplash.com/photo-1615485290353-2e9d6f8897f0",
                    "ingredients": ["Kunyit", "Asam Jawa"],
                    "usage": "2 kapsul setelah makan pagi dan malam."
                },
            ]
            for s in samples:
                create_document("herbalproduct", s)

        if db["article"].count_documents({}) == 0:
            articles = [
                {
                    "title": "Manfaat Jahe untuk Kesehatan",
                    "summary": "Jahe dikenal sebagai rempah serba guna. Berikut manfaat ilmiahnya.",
                    "content": "Jahe mengandung gingerol yang bersifat anti-inflamasi dan antioksidan...",
                    "cover_image": "https://images.unsplash.com/photo-1604908176997-51f2d7f6f8e2",
                    "tags": ["jahe", "pencernaan", "anti-inflamasi"],
                },
                {
                    "title": "Kunyit: Si Kuning yang Menyehatkan",
                    "summary": "Kunyit memiliki kurkumin yang bermanfaat untuk tubuh.",
                    "content": "Kurkumin pada kunyit telah diteliti membantu mengurangi peradangan...",
                    "cover_image": "https://images.unsplash.com/photo-1615485737651-6df9d6f5e3c1",
                    "tags": ["kunyit", "antioksidan"],
                },
            ]
            for a in articles:
                create_document("article", a)
    except Exception:
        # ignore seeding errors in ephemeral environments
        pass


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
