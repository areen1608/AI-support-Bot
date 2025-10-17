from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class QuestionAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="questions")
    #this is a change
    session_id = models.CharField(max_length=100, null=True) 
    question = models.CharField(max_length=1000)
    answer = models.TextField()
    created = models.DateField(auto_now_add=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    subscription_status = models.CharField(max_length=20, default='Free')
    
    def __str__(self):
        return self.question
    
class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    context = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Conversation for {self.user.username} at {self.timestamp}'