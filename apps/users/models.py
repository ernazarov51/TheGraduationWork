from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.common.validators import validate_uzbek_phone
from apps.users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    TEACHER = "teacher"
    STUDENT = "student"
    DIRECTOR = "director"

    ROLE_CHOICES = [
        (TEACHER, "Teacher"),
        (STUDENT, "Student"),
        (DIRECTOR, "Director"),
    ]

    phone = models.CharField(max_length=20, unique=True, validators=[validate_uzbek_phone])
    full_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=STUDENT)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.phone} ({self.role})"

    @property
    def is_teacher(self):
        return self.role == self.TEACHER

    @property
    def is_student(self):
        return self.role == self.STUDENT

    @property
    def is_director(self):
        return self.role == self.DIRECTOR
