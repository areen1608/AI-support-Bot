from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserForm
from django.db.models import Min
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from datetime import date, timedelta
from .models import QuestionAnswer
import openai
from dotenv import load_dotenv
import os
import chromadb
from openai import OpenAI
import json
import os
import logging
import asyncio
import uuid
import openai
import PyPDF2
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pymongo import MongoClient
from datetime import datetime, timedelta
from .models import Conversation


# Create your views here.
load_dotenv("key.env")

open_api_key = os.getenv('OPENAI_API_KEY')
openai.api_key = open_api_key
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai.api_key,
)


@login_required(login_url='signin')
def index(request):
    session_id = request.session.session_key
    chat_history = QuestionAnswer.objects.filter(user=request.user, session_id=session_id).order_by('timestamp')
    history_data = [
        {"question": qa.question, "answer": qa.answer}
        for qa in chat_history
    ]
    
    context = {
        'history_data': json.dumps(history_data),  # Serialize history data
        # Add other context data here if needed
    }
    
    return render(request, 'chatapp/index.html', context)



def signup(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = UserForm()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            username = request.POST["username"]
            password = request.POST["password1"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("index")
    context = {"form": form}
    return render(request, "chatapp/signup.html", context)


def signin(request):
    err = None
    if request.user.is_authenticated:
        return redirect("index")
    
    if request.method == 'POST':
        
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        
        else:
            err = "Invalid Credentials"
        
        
    context = {"error": err}
    return render(request, "chatapp/signin.html", context)


def signout(request):
    logout(request)
    return redirect("signin")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

file_paths = [
     r"C:\Users\AREEN\Downloads\Web_app\TheIndianEconomy.pdf"
]

def is_folder_empty(folder_path):
    if not os.path.isdir(folder_path):
        raise ValueError(f"The path '{folder_path}' is not a valid directory.")
    contents = os.listdir(folder_path)
    return len(contents) == 0

folder_path = "Web_app\Vector_Store"

'''
if is_folder_empty(folder_path):
    return x
'''

def fetch_and_parse(file_path):
    with open(file_path, 'rb') as file:
        pdf = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Split text into chunks
def split_text(text, chunk_size=1000, chunk_overlap=200):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - chunk_overlap)]

all_docs = []
for file_path in file_paths:
    text = fetch_and_parse(file_path)
    all_docs.extend(split_text(text))

def get_embeddings(texts):
    response = client.embeddings.create(input=texts, model="text-embedding-ada-002")
    return response

# Get embeddings for document chunks
doc_embeddings = get_embeddings(all_docs)

def vectorStore():
    persist_directory = "Vector_Store"
    chroma_client = chromadb.PersistentClient(path=persist_directory)
    collection_name = "my_collection"
    if collection_name in chroma_client.list_collections():
        collection = chroma_client.get_collection(name=collection_name)
    else:
        collection = chroma_client.create_collection(name=collection_name)
    ids = [f'doc_{i}' for i in range(len(all_docs))]
    collection.add(ids=ids, embeddings=doc_embeddings, documents=all_docs)


# Function to find the most relevant document chunk
def retrieve(query, doc_embeddings, docs):
    query_embedding = get_embeddings([query])[0]
    similarities = cosine_similarity([query_embedding], doc_embeddings)
    most_similar_index = np.argmax(similarities)
    return docs[most_similar_index]


def chat_view(request):
    
    user = request.user

    # Fetch the most recent chat history for this user, sorted by timestamp
    previous_conversations = QuestionAnswer.objects.filter(user=user).order_by('-timestamp')[:5]
    
    session_id = request.session.get('session_id')  # Or generate a new one if not present
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session['session_id'] = session_id

    # Construct a context string from the user's recent chat history, including timestamps
    context = ""
    for conversation in previous_conversations:
        # Format the timestamp for readability (e.g., 'Sep 9, 2024, 14:30')
        formatted_timestamp = format(conversation.timestamp, 'M j, Y, P')
        context += f"Timestamp: {formatted_timestamp}\n"
        context += f"Question: {conversation.question}\n"
        context += f"Answer: {conversation.answer}\n\n"
    
    return context.strip()


def ask_openai(message,context):
    prompt = f"Context: {context}\n\nQuestion: {message}\n\nAnswer:"
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {"role": "system", "content": "You are a support assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0
    )
    return response.choices[0].message.content.strip()



def getValue(request):
    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key
    data = json.loads(request.body)
    message = data["msg"] 
    context = chat_view(request)  
    response = ask_openai(message, context)
    QuestionAnswer.objects.create(user=request.user, session_id=session_id, question=message, answer=response)
    return JsonResponse({"msg": message, "res": response})


#this is a change
def conversation_history(request, session_id):
    history = QuestionAnswer.objects.filter(session_id=session_id).order_by('created')
    return render(request, 'chat/conversation_history.html', {'history': history})


def save_chat_message(request):
    session_id = request.session.get('session_id')  # Or generate a new one if not present
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session['session_id'] = session_id
    
    question = request.POST.get('question')
    answer = getValue().response
    QuestionAnswer.objects.create(
        user=request.user, 
        session_id=session_id, 
        question=question, 
        answer=answer
    )

def chat_history(request):
    all_sessions = (
        QuestionAnswer.objects.filter(user=request.user)
        .order_by('session_id', 'timestamp')
        .values('session_id', 'question', 'answer', 'timestamp')
    )

    # Group chats by session ID
    session_dict = {}
    for chat in all_sessions:
        session_id = chat['session_id']
        if session_id not in session_dict:
            session_dict[session_id] = []
        session_dict[session_id].append(chat)

    # Pass the grouped session data to the template
    context = {
        'session_chats': session_dict,  # Dictionary of session-based chat history
    }
    return render(request, 'chatapp/chat_history.html', context)

def session_conversations(request):
    first_conversations = QuestionAnswer.objects.values('session_id').annotate(first_timestamp=Min('timestamp'))

    # Retrieve the actual QuestionAnswer objects with those timestamps and session_ids
    index = QuestionAnswer.objects.filter(
        timestamp__in=[conv['first_timestamp'] for conv in first_conversations],
        session_id__in=[conv['session_id'] for conv in first_conversations]
    ).order_by('session_id', 'timestamp')
    # Pass them to the 'trial.html' template
    print(index)
    return render(request, 'chatapp/trial.html', {'index': index})


#def trial(request):
#    return render(request, 'chatapp/trial.html')

def question_answer_detail(request, id):
    article = get_object_or_404(QuestionAnswer, id=id)
    return render(request, 'question_answer_detail.html', {'article': article})

'''
def getting_value(request):
    if request.method == 'POST':
            upload = QuestionAnswer(
                user=request.user if request.user.is_authenticated else None,
                input=question,
                output_file_location=output_file_location,
                status='Input PDF uploaded'
            )
            upload.save()
'''