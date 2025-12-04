from django.shortcuts import render, redirect
from django.http import JsonResponse

from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat
import os
#import datetime
from datetime import timedelta
from django.utils import timezone
from datetime import timedelta
#from django.conf import settings
#import requests
#import json
from dotenv import load_dotenv
# upload_document
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from groq import Groq

# Load .env file
load_dotenv()
# Get your API key from environment
Groq_api_key = os.getenv("Groq_API_KEY")
def ask_llama(message):
    client = Groq(

       api_key = Groq_api_key,
    )

    system_prompt = (
    "You are PrepMate, an AI Interview Preparation Assistant and intelligent conversational chatbot. "
    "Your purpose is to help users prepare for IT interviews, while also engaging in natural, clear, "
    "and structured conversations. "

    "Your core responsibilities include: "
    "1. Answering IT interview questions (covering programming, data structures, algorithms, databases, "
    "   networking, operating systems, AI/ML, cloud, etc.). "
    "2. Explaining technical concepts in simple and structured terms with examples where useful. "
    "3. Providing interview strategies and best practices (e.g., STAR method, handling behavioral questions). "
    "4. Offering practice problems (coding, system design, conceptual Q&A) and guiding users through solutions. "
    "5. Giving feedback and tips on user responses to mock interview questions. "

    "Guidelines for responses: "
    "- Always format answers in a clear, concise, and professional tone. "
    "- Use bullet points or numbered lists for steps, concepts, or key takeaways. "
    "- Separate major ideas with line breaks for readability. "
    "- Where possible, include practical examples, sample code (Python, Java, or C++), "
    "  and interview-style scenarios. "
    "- Avoid overly generic responses; tailor advice to IT interview contexts. "

    "Your personality: "
    "- Professional but approachable (like a helpful mentor). "
    "- Encouraging, supportive, and focused on boosting the user’s confidence. "
    "- Adaptive: simplify for beginners, deepen explanations for advanced users. "

    "Final Note: Stay focused on IT interview preparation while keeping conversations engaging, "
    "clear, and useful for skill-building."
)


    response = client.chat.completions.create(
    messages=[
        
        {"role": "system", "content": system_prompt },
        {"role": "user", "content": message},
        
    ],
    model="llama-3.3-70b-versatile",
)
    answer = response.choices[0].message.content
    return answer

def chatbot(request):
    if not request.user.is_authenticated:
        return redirect("login")

    # Fetch all chats for the logged-in user, ordered by creation date
    chats = Chat.objects.filter(user=request.user).order_by('-created_at')

    # Get today's date
    today = timezone.now().date() 

    # Filter chats for Today
    today_chats = chats.filter(created_at__date=today)

    # Filter chats for Last 7 Days (excluding today)
    last_7_days = today - timedelta(days=7)
    last_7_days_chats = chats.filter(created_at__date__range=[last_7_days, today - timedelta(days=1)])

    # Filter chats for Last 30 Days (excluding the last 7 days)
    last_30_days = today - timedelta(days=30)
    last_30_days_chats = chats.filter(created_at__date__range=[last_30_days, last_7_days - timedelta(days=1)])

    # checks if the HTTP request method is POST. POST is typically used to submit data 
    if request.method == 'POST':
        # retrieves the value of the 'message' key from the POST data.
        message = request.POST.get('message')
        response = ask_llama(message)

        # Save the chat to the database
        # creates a new instance of the Chat model (presumably a database model for storing chat messages). It populates the fields of the Chat model
        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()

        return JsonResponse({'message': message, 'response': response})

    return render(request, 'chatbot.html', {
        'today_chats': today_chats,
        'last_7_days_chats': last_7_days_chats,
        'last_30_days_chats': last_30_days_chats,
    })


@csrf_exempt
def save_chat(request):
    if request.method == 'POST':
        user_message = request.POST.get('user_message')
        assistant_response = request.POST.get('assistant_response')

        # Save the chat to the database
        chat = Chat(
            user=request.user,
            message=user_message,
            response=assistant_response,
            created_at=timezone.now()
        )
        chat.save()

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


def load_chat(request, chat_id):
    try:
        chat = Chat.objects.get(id=chat_id, user=request.user)
        messages = [
            {'content': chat.message, 'is_user': True},
            {'content': chat.response, 'is_user': False}
        ]
        return JsonResponse({'messages': messages})
    except Chat.DoesNotExist:
        return JsonResponse({'error': 'Chat not found'}, status=404)


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')  
        password = request.POST.get('password')  

        try:
            # Look up the user by email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user and user.check_password(password):  # Check password manually
            auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('chatbot')
        else:
            error_message = 'Invalid email or password'
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')


def register(request):
    error_message = None 
    if request.method == 'POST':
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                username = email.split('@')[0]
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('login')
            except:
                error_message = 'Error creating account'
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = 'Password don\'t match'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')


def logout(request):
    auth.logout(request)
    return redirect('login')


'''
@csrf_exempt
def upload_document(request):
    if request.method == 'POST' and request.FILES.get('document'):
        uploaded_file = request.FILES['document']
        path = default_storage.save(f"uploads/{uploaded_file.name}", ContentFile(uploaded_file.read()))
        full_path = os.path.join(default_storage.location, path)

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as file:
                document_text = file.read()

            if not document_text.strip():
                return JsonResponse({'error': 'Uploaded document is empty or unreadable.'}, status=400)

            # Optional: limit input size for Mistral
            MAX_INPUT_SIZE = 8000
            document_text = document_text[:MAX_INPUT_SIZE]

            message = f""" You are PrepMate, an AI Interview Preparation Assistant specializing in IT careers. 
        Your role is to help users prepare for technical and behavioral interviews, improve their resumes 
        and cover letters, and align their job applications with IT job descriptions.
Here is the content of the user's document:\n\n{document_text}\n\nPlease extract relevant insights, and offer a structured recommendation."""

            response = ask_llama(message)

            return JsonResponse({'response': response})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'No file uploaded'}, status=400)

    '''
