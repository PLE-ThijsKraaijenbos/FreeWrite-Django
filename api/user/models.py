import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'user'


class AvatarItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    param_key = models.CharField(max_length=50)
    param_value = models.CharField(max_length=100)
    price = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.param_key}={self.param_value}"

    class Meta:
        db_table = 'avatar_item'
        unique_together = [('param_key', 'param_value')]


class UserAvatarItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='avatar_items')
    item = models.ForeignKey(AvatarItem, on_delete=models.CASCADE, related_name='user_items')
    is_equipped = models.BooleanField(default=False)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_avatar_item'
        unique_together = [('user', 'item')]


class Userprofile(models.Model):
    class Substance(models.TextChoices):
        COCAINE = "COCAINE", "Cocaine"
        CATHINONES = "CATHINONES", "3mmc / 4mmc"
        AMPHETAMINE = "AMPHETAMINE", "Amphetamine / speed"
        MDMA = "MDMA", "MDMA / Ecstacy"
    class Duration(models.TextChoices):
        LESS_THAN_SIX_MONTHS = "<6M", "Less than 6 months"
        SIX_TO_TWELVE_MONTHS = "6-12M", "6 to 12 months"
        ONE_TO_TWO_YEARS = "1-2Y", "1 to 2 years"
        GREATER_THAN_TWO_YEARS = ">2Y", "2+ years"
        NOT_SURE = "NOT_SURE", "I'm not sure"
    class Goal(models.TextChoices):
        USE_LESS = "USE_LESS", "I want to use less"
        QUIT = "QUIT", "I want to quit completely"
        NOT_SURE = "NOT_SURE", "I'm not sure yet"

    class Times(models.TextChoices):
        AT_A_PARTY = "AT_A_PARTY", "When i'm at a party"
        WHEN_BORED = "WHEN_BORED", "When i'm bored"
        WHEN_STRESSED = "WHEN_STRESSED", "When i'm stressed or anxious"
        WHEN_DOWN = "WHEN_DOWN", "When i'm feeling down"

    class Frequency(models.TextChoices):
        RARELY = "RARELY", "Rarely"
        MONTHLY = "MONTHLY", "At least once a month"
        WEEKLY = "WEEKLY", "At least once a week"
        DAILY = "DAILY", "Every day"

    class PreviousAttempts(models.TextChoices):
        WENT_WELL = "WENT_WELL", "Yes, and it went better than I expected."
        ONCE_HARD = "ONCE_HARD", "Yes, once. But it was hard to keep up"
        MULTIPLE_RELAPSED = "MULTIPLE_RELAPSED", "Yes, multiple times. But I keep falling back."
        THOUGHT_ABOUT_IT = "THOUGHT_ABOUT_IT", "I've thought about it but haven't tried yet"
        NEVER = "NEVER", "No, this is the first time"


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.TextField(blank=True)
    substance = models.CharField(max_length=20, choices=Substance.choices, blank=True)
    usage_duration = models.CharField(max_length=20, choices=Duration.choices, blank=True)
    goal = models.CharField(max_length=20, choices=Goal.choices, blank=True)
    usage_times = models.CharField(max_length=20, choices=Times.choices, blank=True)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, blank=True)
    previous_attempts = models.CharField(max_length=20, choices=PreviousAttempts.choices, blank=True)
    coins = models.IntegerField(default=100)

    class Meta:
        db_table = 'userprofile'
