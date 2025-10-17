# AI Support Bot

An end‑to‑end **AI customer support assistant** built with **Django** that ingests documents (PDFs), creates embeddings, stores them in **ChromaDB**, and answers user queries using the **OpenAI API** with context retrieval. Includes a simple chat UI and optional **MongoDB** persistence for conversations/analytics.

---

## ✨ Features

* **Chat UI** (Django views & templates) for asking questions.
* **RAG pipeline**: PDF → text → chunks → embeddings → **ChromaDB** → relevant context.
* **LLM answers** via **OpenAI** (Chat Completions / Responses API).
* **Cosine similarity** using `scikit-learn` (or native Chroma search).
* **MongoDB** (via `pymongo`) for storing chats and metadata (optional).
* **.env configuration** with `python-dotenv`.
* Ready-to-use management commands & scripts for ingestion.

---

## 🧱 Tech Stack

* **Backend**: Django (Python 3.11+ / 3.12)
* **Vector DB**: ChromaDB
* **LLM**: OpenAI API
* **Parsing**: PyPDF2
* **ML utils**: scikit-learn, numpy
* **DB (optional)**: MongoDB via `pymongo`

> Confirmed project imports seen in codebase: `django`, `python-dotenv`, `openai`, `chromadb`, `PyPDF2`, `scikit-learn`, `numpy`, `pymongo`.

---

## 📂 Project Structure (illustrative)

```
AI-support-Bot/
├─ chatgpt/                 # Django project folder
│  ├─ settings.py
│  ├─ urls.py               # includes chatapp.urls
│  └─ ...
├─ chatapp/                 # Main app
│  ├─ views.py              # chat endpoint, ingestion helpers
│  ├─ urls.py
│  ├─ templates/
│  │  └─ chat.html
│  └─ ...
├─ manage.py
├─ requirements.txt
├─ docs/                    # PDFs or knowledge base (recommended)
│  └─ TheIndianEconomy.pdf  # example source document
└─ .env.example
```

---

## 🚀 Quick Start

### 1) Clone & enter the project

```bash
git clone https://github.com/<your-username>/AI-support-Bot.git
cd AI-support-Bot
```

### 2) Create & activate a virtual environment

```bash
# Windows (PowerShell)
python -m venv .venv
. .venv/Scripts/Activate.ps1

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
# or, if you need a one‑liner
pip install django python-dotenv openai chromadb PyPDF2 scikit-learn numpy pymongo
```

### 4) Environment variables

Create a file named **`.env`** in the project root:

```dotenv
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# ChromaDB (defaults to local .chromadb/)
CHROMA_PERSIST_DIR=.chromadb

# MongoDB (optional)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=ai_support

# Django
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=change-me
ALLOWED_HOSTS=127.0.0.1,localhost
```

> Tip (Windows paths): in Python strings, use raw strings `r"C:\\path"` or forward slashes `C:/path` to avoid `unicodeescape` errors.

### 5) Database setup (Django)

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6) Run the dev server

```bash
python manage.py runserver
```

Visit: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 📥 Ingesting Documents (PDF → ChromaDB)

Add your PDFs to `docs/` (or any folder you prefer) and update the path in your ingestion code. Typical flow:

```python
from PyPDF2 import PdfReader
from chromadb import PersistentClient
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# 1) Read PDF
reader = PdfReader("docs/TheIndianEconomy.pdf")
pages = [p.extract_text() or "" for p in reader.pages]

# 2) Chunk text (simple example)
CHUNK_SIZE = 800
chunks = []
for i, page in enumerate(pages):
    txt = page.strip()
    for j in range(0, len(txt), CHUNK_SIZE):
        chunk = txt[j:j+CHUNK_SIZE]
        if chunk:
            chunks.append({"id": f"p{i}_c{j}", "text": chunk})

# 3) Create embeddings (via OpenAI or other)
# Pseudocode – replace with actual embeddings call
# embeddings = openai_embed([c["text"] for c in chunks])

# 4) Store in ChromaDB
client = PersistentClient(path=".chromadb")
collection = client.get_or_create_collection("kb")
# collection.add(ids=[c["id"] for c in chunks], documents=[c["text"] for c in chunks], embeddings=embeddings)
```

During query time, retrieve top‑k documents via Chroma’s similarity search and pass them as context to the LLM.

---

## 💬 Chat Endpoint (high‑level)

* **POST** text → retrieve top‑k contexts from Chroma → call OpenAI → return answer.
* Store Q/A pairs & metadata in MongoDB (optional) for analytics.

Example view skeleton:

```python
# chatapp/views.py (illustrative)
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def chat(request):
    if request.method == "POST":
        user_q = request.POST.get("question", "").strip()
        # 1) search chroma for context
        # 2) call openai with system+user+context
        # 3) persist to mongo (optional)
        # 4) return answer
    return render(request, "chat.html", {})
```

---

## 🧪 Local Testing

```bash
# Run Django checks & tests (if tests available)
python manage.py check
python manage.py test
```

---

## 🐳 Optional: Docker

```dockerfile
# Dockerfile (example)
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

```bash
# Build & run
docker build -t ai-support-bot .
docker run -p 8000:8000 --env-file .env ai-support-bot
```

---

## 🔐 Security Notes

* Never commit actual secrets. Use `.env` and keep it out of git via `.gitignore`.
* Validate/limit file uploads if you expose ingestion from the UI.
* Consider rate limiting and auth for production.

---

## 🧭 Git & Branch Protection Tips

If you see *“push declined due to repository rule violations”*:

* Push to a feature branch and open a PR:

  ```bash
  git checkout -b initial-upload
  git push -u origin initial-upload
  ```
* If **signed commits** are required, enable SSH/GPG signing and amend: `git commit --amend -S --no-edit`.
* If **linear history** is required, use `git pull --rebase` before pushing.

---

## 🛠️ Troubleshooting

**Unicode path error on Windows**

```
SyntaxError: (unicode error) 'unicodeescape' codec can't decode bytes ...
```

Use raw strings `r"C:\\..."` or forward slashes `C:/...`.

**OpenAI: 401 Unauthorized**

* Check `OPENAI_API_KEY` is present and valid.

**ChromaDB not persisting**

* Ensure `CHROMA_PERSIST_DIR` is a writable path and you reuse the same collection name.

**MongoDB connection fails**

* Verify `MONGODB_URI` and Mongo service is running: `mongod` / Docker.

---

## 🤝 Contributing

1. Fork the repo & create a feature branch: `git checkout -b feat/<name>`
2. Write tests (if applicable) and keep commits signed if rules require it.
3. Open a PR to `main`. Ensure checks pass.

---

## 📄 License

Specify a license (e.g., MIT) in `LICENSE`.

---

## 🙌 Acknowledgements

* Django, ChromaDB, OpenAI, PyPDF2, scikit‑learn.

---

## 📧 Contact

For questions or support, open an issue or reach out to the maintainer.
