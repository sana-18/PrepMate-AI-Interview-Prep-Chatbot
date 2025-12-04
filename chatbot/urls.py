from django.urls import path
from . import views

urlpatterns = [
    # added urls
    path('', views.login, name='login'),  # Root URL for the chatbot app
    path('chatbot/', views.chatbot, name='chatbot'),
    path('save_chat/', views.save_chat, name='save_chat'),
    path('load_chat/<int:chat_id>/', views.load_chat, name='load_chat'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    #path('upload_document/', views.upload_document, name='upload_document'),

]