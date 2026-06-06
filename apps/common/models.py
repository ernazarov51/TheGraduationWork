import uuid

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    """Abstract base model inherited by all non-auth models.

    Provides UUID primary key, audit timestamps, soft delete, and
    automatic created_by / updated_by population via thread-local storage
    (requires CurrentUserMiddleware to be active).

    NOTE: apps.users.User intentionally does NOT extend BaseModel because
    AbstractBaseUser already defines its own id field and auth-system hooks.
    User instead carries its own created_at / updated_at fields directly.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Avoid circular import — middleware has no model dependency.
        from apps.common.middleware import get_current_user

        user = get_current_user()
        if user and user.is_authenticated:
            if not self.pk:
                self.created_by = user
            self.updated_by = user

            # When update_fields is provided, append updated_by so it persists.
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = list(set(update_fields) | {"updated_by"})

        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Soft delete: set is_active=False instead of removing the row."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the row from the database."""
        super().delete(using=using, keep_parents=keep_parents)


class ActivityLog(models.Model):
    """Records every create / update / delete action performed via the API."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACTION_CHOICES = [
        (CREATE, "Create"),
        (UPDATE, "Update"),
        (DELETE, "Delete"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text='Format: {"field": {"old": "...", "new": "..."}}',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.model_name}({self.object_id}) by {self.user}"
