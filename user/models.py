from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


# Create your models here.

class CustomUser(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)


def validate_user_id_for_iot_data(value):
    user = CustomUser.objects.filter(user_id=value).first()
    if not user:
        raise ValidationError("Invalid User ID!")


class IotData(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=16, validators=[validate_user_id_for_iot_data])
    metric_1 = models.FloatField(null=False, validators=[MinValueValidator(0), MaxValueValidator(100)])
    metric_2 = models.FloatField(null=False, validators=[MinValueValidator(0), MaxValueValidator(200)])
    metric_3 = models.FloatField(null=True)
    timestamp = models.DateTimeField(null=False, validators=[MaxValueValidator(limit_value=timezone.now())])
    created_at = models.DateTimeField(auto_now_add=True)
