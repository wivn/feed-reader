from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
	site = models.URLField(null=True,unique=True)