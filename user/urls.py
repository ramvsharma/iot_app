from django.urls import path

from user.views import login, create_user, profile, get_or_update_user, create_data, get_latest_data, \
    get_historical_data

urlpatterns = [
    path('auth/login/', login, name='login'),
    path('users/', create_user, name='create_user'),
    path('profile/', profile, name='profile'),
    path('users/<str:user_id>/', get_or_update_user, name='get_or_update_user'),
    path('users/<str:user_id>/iot/latest/', get_latest_data, name='get_or_update_user'),
    path('users/<str:user_id>/iot/history/', get_historical_data, name='get_or_update_user'),
    path('iot/data/', create_data, name='iot_data'),
]
