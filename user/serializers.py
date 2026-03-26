from rest_framework import serializers

from user.models import CustomUser, IotData


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['user_id', 'name', 'username', 'is_active', 'created_at']


class IotDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = IotData
        fields = ['user_id', 'metric_1', 'metric_2', 'metric_3', 'timestamp', 'created_at']
