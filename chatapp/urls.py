from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path("signup", views.signup, name="signup"),
    path("signin", views.signin, name="signin"),
    path("signout", views.signout, name="signout"),
    path("get-value", views.getValue),
    path("",views.session_conversations, name="index"),
    path("trial", views.session_conversations, name="conversations"),
    path('question_answer/<int:id>/', views.question_answer_detail, name='question_answer_detail'),
]