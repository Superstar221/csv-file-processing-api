from django.db import models

class DataFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"File {self.id}"

# backend/api/serializers.py
from rest_framework import serializers
from .models import DataFile

class DataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFile
        fields = '__all__'