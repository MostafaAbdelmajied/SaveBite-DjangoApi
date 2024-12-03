from django.db import models


# Create your models here.
class EncodedImage(models.Model):
    image = models.ImageField(upload_to='encoded_images/')
    email = models.EmailField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class KeyPair(models.Model):
    public_key = models.TextField()
    private_key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)