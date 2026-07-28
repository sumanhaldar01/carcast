import os
import time

import chromadb
import requests
from fastapi import FastAPI
from pydantic import BaseModel, Field


OLLAMA = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434",
).rstrip("/")

CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3.5:4b")
EMBED_MODEL = os.getenv(
    "OLLAMA_EMBED_MODEL",
    "nomic-embed-text:latest",
)

PRODUCT_API = os.getenv(
    "PRODUCT_API_URL",
    "http://127.0.0.1:4000/api/products",
)

CHROMA_PATH = os.getenv("CHROMA_PATH", "/data/chroma")
API_KEY = os.getenv("OLLAMA_API_KEY", "")

app = FastAPI(title="CarCast Product RAG")
collection = None


def headers():
    if API_KEY:
        return {"Authorization": f"Bearer {API_KEY}"}
    return {}


def store_price(price_cents):
    """
    Match the exact display used by the CarCast frontend.
    Example: 1699 stored cents becomes INR 17 in the UI.
    """
    return round(price_cents / 100)


def embed(texts):
    """Create vector embeddings with local Ollama."""
    try:
        response = requests.post(
            f"{OLLAMA}/api/embed",
            json={
                "model": EMBED_MODEL,
                "input": texts,
            },
            headers=headers(),
            timeout=60,
        )

        response.raise_for_status()

        embeddings = response.json().get("embeddings")

        if not embeddings:
            raise KeyError("No embeddings were returned")

        return embeddings

    except (requests.RequestException, KeyError, ValueError):
        vectors = []

        for text in texts:
            response = requests.post(
                f"{OLLAMA}/api/embeddings",
                json={
                    "model": EMBED_MODEL,
                    "prompt": text,
                },
                headers=headers(),
                timeout=60,
            )

            response.raise_for_status()

            vector = response.json().get("embedding")

            if not vector:
                raise RuntimeError("No embedding vector was returned")

            vectors.append(vector)

        return vectors


def seed_catalog():
    """Fetch product data, embed it, and persist it inside ChromaDB."""
    global collection

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    collection = client.get_or_create_collection(
        name="carcast_products",
        metadata={"hnsw:space": "cosine"},
    )

    response = requests.get(PRODUCT_API, timeout=20)
    response.raise_for_status()

    products = response.json()

    if not products:
        raise RuntimeError("CarCast product catalog is empty")

    documents = [
        (
            f"Product: {product['name']}. "
            f"Category: {product['category']}. "
            f"Price shown in the CarCast store: INR "
            f"{store_price(product['priceCents'])}. "
            f"Colour: {product['color']}. "
            f"Description: {product['description']}"
        )
        for product in products
    ]

    collection.upsert(
        ids=[str(product["id"]) for product in products],
        documents=documents,
        metadatas=[
            {
                "name": product["name"],
                "name_lower": product["name"].lower(),
                "category": product["category"],
                "price_cents": product["priceCents"],
                "store_price": store_price(product["priceCents"]),
            }
            for product in products
        ],
        embeddings=embed(documents),
    )

    print(f"CarCast RAG indexed {len(products)} products in ChromaDB.")


def is_product_question(question):
    """The chatbot may only discuss products and pricing."""
    allowed_terms = (
        "price",
        "cost",
        "cheap",
        "cheapest",
        "expensive",
        "lowest",
        "rupee",
        "inr",
        "product",
        "car",
        "toy",
        "truck",
        "set",
        "racer",
        "gt",
        "rally",
        "hauler",
        "orbit",
        "crew",
        "beetle",
        "forest",
        "cabriolet",
        "delivery",
        "rover",
        "garage",
        "colour",
        "color",
        "available",
        "collection",
        "die-cast",
    )

    lowered = question.lower()
    return any(term in lowered for term in allowed_terms)


def all_product_metadata():
    """Read every product's metadata from ChromaDB."""
    records = collection.get(include=["metadatas"])
    return records.get("metadatas", [])


def deterministic_price_answer(question):
    """
    Answer exact price and cheapest-product requests locally from RAG metadata.
    This avoids slow LLM calculation and guarantees UI price consistency.
    """
    question_lower = question.lower()
    metadata = all_product_metadata()

    if not metadata:
        return None

    cheapest_words = (
        "cheapest",
        "most cheap",
        "lowest price",
        "lowest cost",
    )

    if any(word in question_lower for word in cheapest_words):
        cheapest = min(metadata, key=lambda item: item["price_cents"])

        return (
            f"The most affordable CarCast product is "
            f"{cheapest['name']} at ₹{cheapest['store_price']}."
        )

    asks_price = any(
        word in question_lower
        for word in ("price", "cost", "inr", "rupee")
    )

    if asks_price:
        for product in metadata:
            if product["name_lower"] in question_lower:
                return (
                    f"The {product['name']} costs "
                    f"₹{product['store_price']}."
                )

    return None


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=400)


@app.on_event("startup")
def startup():
    for _ in range(12):
        try:
            seed_catalog()
            return

        except Exception as error:
            print(
                "Waiting for CarCast backend, ChromaDB, or Ollama:",
                error,
            )
            time.sleep(5)

    print("RAG startup indexing failed; it will retry on the first request.")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "chat_model": CHAT_MODEL,
        "embedding_model": EMBED_MODEL,
    }


@app.post("/chat")
def chat(body: Question):
    question = body.question.strip()

    if not is_product_question(question):
        return {
            "answer": "I don't have information about that."
        }

    global collection

    try:
        if collection is None:
            seed_catalog()

        if collection.count() == 0:
            return {
                "answer": "I don't have information about that."
            }

        # Instant and accurate answers for prices / comparisons.
        direct_answer = deterministic_price_answer(question)

        if direct_answer:
            return {
                "answer": direct_answer
            }

        # RAG semantic retrieval for normal product-information questions.
        result = collection.query(
            query_embeddings=embed([question]),
            n_results=min(3, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents = result.get("documents", [[]])[0]

        if not documents:
            return {
                "answer": "I don't have information about that."
            }

        prompt = f"""You are the CarCast product assistant.

Answer only about CarCast products, categories, colours,
descriptions, and prices using the provided catalogue context.

Never invent information about stock, availability, shipping,
delivery, returns, payment, discounts, or policies.

If the answer is not available in the supplied context,
reply exactly:
I don't have information about that.

Catalogue context:
{chr(10).join(documents)}

Customer question:
{question}

Give a short, friendly answer."""

        response = requests.post(
            f"{OLLAMA}/api/chat",
            json={
                "model": CHAT_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                "stream": False,
                "think": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 100,
                },
            },
            headers=headers(),
            timeout=180,
        )

        response.raise_for_status()

        answer = response.json().get(
            "message",
            {},
        ).get(
            "content",
            "",
        ).strip()

        if not answer:
            return {
                "answer": "I don't have information about that."
            }

        return {
            "answer": answer
        }

    except Exception as error:
        print("RAG query failed:", error)

        return {
            "answer": "I don't have information about that."
            }
