import json
from math import ceil

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from user.jwt_utils import create_jwt_token
from user.models import CustomUser, IotData
from user.serializers import CustomUserSerializer, IotDataSerializer


# Create your views here.

@api_view(['POST'])
def login(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)
    user = CustomUser.objects.filter(username=username).first()
    if not user:
        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.check_password(password):
        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)
    access_token = create_jwt_token(user)
    return Response({"message": "Successfully logged in", "token": access_token}, status=status.HTTP_200_OK)


@api_view(['POST', 'GET'])
def create_user(request):
    if request.method == 'POST':
        data = request.data
        name = data.get('name')
        username = data.get('username')
        password = data.get('password')
        if not username or not name or not password:
            return Response({"error": "Username, Name and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser(username=username, name=name)
        user.set_password(password)
        user.save()
        user.user_id = f"U{user.id:04d}"
        user.save(update_fields=['user_id'])
        serializer = CustomUserSerializer(user)
        return Response({"message": "Successfully registered",
                         "user": serializer.data}, status=status.HTTP_201_CREATED)

    if request.method == 'GET':
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def profile(request):
    user = request.user
    serializer = CustomUserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'GET'])
def get_or_update_user(request, user_id):
    if request.method == 'PUT':
        user = request.user
        data = request.data
        if data.get('username'):
            return Response({"error": "Username will not update."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CustomUserSerializer(user, data=data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        if data.get('password'):
            user = serializer.instance
            user.set_password(data['password'])
            user.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    if request.method == 'GET':
        user = CustomUser.objects.filter(user_id=user_id).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = CustomUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_data(request):
    serializer = IotDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        group_name = f"user_{serializer.data['user_id']}"
        async_to_sync(get_channel_layer().group_send)(
            group_name,
            {
                'type': 'chat.message',
                'message': json.dumps({'event': 'NEW_DATA', 'data': serializer.data})
            }
        )
        return Response({"message": "Data created successfully", "data": serializer.data},
                        status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_latest_data(request, user_id):
    data = IotData.objects.filter(user_id=user_id).order_by('-created_at').first()
    if not data:
        return Response({"error": "No data found for the user"}, status=status.HTTP_404_NOT_FOUND)
    serializer = IotDataSerializer(data)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_historical_data(request, user_id):
    limit = request.query_params.get('limit', 50)
    page_no = request.query_params.get('page', 1)
    data = IotData.objects.filter(user_id=user_id).order_by('-created_at').all()
    total_records = data.count()
    if page_no > ceil(total_records / limit):
        return Response({"error": "No data for this page number"}, status=status.HTTP_400_BAD_REQUEST)

    data = data[(page_no - 1) * limit: min(page_no * limit, total_records)]
    if not data:
        return Response({"error": "No data found for the user"}, status=status.HTTP_404_NOT_FOUND)
    serializer = IotDataSerializer(data, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
