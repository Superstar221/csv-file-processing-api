from rest_framework import serializers
from .models import DataFile

class DataFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFile
        fields = ['id', 'file', 'uploaded_at', 'processed']