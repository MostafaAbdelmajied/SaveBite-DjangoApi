from django.shortcuts import render
from .models import EncodedImage
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from stegano import lsb
from PIL import Image
import io
from cryptography.fernet import Fernet
import base64


class EmbedDataView(APIView):
    def post(self, request):
        # Get data from request
        image_file = request.FILES.get('image')
        email = request.data.get('email')
        password = request.data.get('password')

        if not (image_file and email and password):
            return Response({"error": "Image, email, and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a Fernet key
        fernet_key = Fernet.generate_key()
        cipher = Fernet(fernet_key)

        # Encrypt the email and password
        data = f"{email}:{password}".encode()
        encrypted_data = cipher.encrypt(data)

        # Embed the encrypted data in the image
        image_data = image_file.read()
        img = Image.open(io.BytesIO(image_data))
        encoded_image = lsb.hide(img, base64.b64encode(encrypted_data).decode())

        # Save the encoded image to a bytes buffer
        img_byte_arr = io.BytesIO()
        encoded_image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        content_file = ContentFile(img_byte_arr.read(), name="encrypted_image.png")

        # Save the encoded image in the database
        image = EncodedImage.objects.create(
            image=content_file,
            email=email,
        )

        return Response({
            "image_url": image.image.url,
            "image": base64.b64encode(img_byte_arr.getvalue()).decode(),
            "fernet_key": fernet_key.decode()  # Provide the Fernet key
        }, status=status.HTTP_200_OK)


class ExtractDataView(APIView):
    def post(self, request):
        image_file = request.FILES.get('image')
        fernet_key = request.data.get('fernet_key')

        if not (image_file and fernet_key):
            return Response({"error": "Image and Fernet key are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Load the Fernet cipher
        cipher = Fernet(fernet_key.encode())

        # Extract the encrypted data from the image
        img = Image.open(image_file)
        hidden_message = lsb.reveal(img)

        if not hidden_message:
            return Response({"error": "No hidden data found in the image"}, status=status.HTTP_400_BAD_REQUEST)

        # Decrypt the data
        encrypted_data = base64.b64decode(hidden_message)
        decrypted_data = cipher.decrypt(encrypted_data)

        # Extract email and password
        email, password = decrypted_data.decode().split(":")
        return Response({"email": email, "password": password}, status=status.HTTP_200_OK)

class TestProjectView(APIView):
    def get(self, request):
        return Response({"hello": "world"}, status=status.HTTP_200_OK)