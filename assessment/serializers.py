# assessment/serializers.py

from rest_framework import serializers

class InattentivePredictionSerializer(serializers.Serializer):
    name = serializers.CharField()
    age = serializers.IntegerField()
    gender = serializers.IntegerField()
    family_structure = serializers.IntegerField()
    screen_access = serializers.IntegerField()
    access_level = serializers.IntegerField()
    frequency_level = serializers.IntegerField()
    content_level = serializers.IntegerField()
    interactivity_level = serializers.IntegerField()
