from apps.common.models import ActivityLog
from apps.common.utils import get_client_ip


class LoggableMixin:
    """ViewSet / GenericAPIView mixin that writes an ActivityLog entry on every
    create, update, and destroy operation, and keeps created_by / updated_by
    in sync with the current user."""

    def _log(self, action, instance, changes=None):
        ActivityLog.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            changes=changes,
            ip_address=get_client_ip(self.request),
        )

    def _diff(self, instance, validated_data):
        """Return {field: {old: ..., new: ...}} for every changed field."""
        changes = {}
        for field, new_val in validated_data.items():
            old_val = getattr(instance, field, None)
            if old_val != new_val:
                changes[field] = {"old": str(old_val), "new": str(new_val)}
        return changes or None

    # ── DRF hooks ─────────────────────────────────────────────────────────────

    def perform_create(self, serializer):
        # Thread-local middleware already fills created_by / updated_by via
        # BaseModel.save(), but we also set it explicitly as a safety net for
        # models that don't extend BaseModel.
        kwargs = {}
        if hasattr(serializer.Meta.model, "created_by"):
            kwargs["created_by"] = self.request.user
        instance = serializer.save(**kwargs)
        self._log(ActivityLog.CREATE, instance)

    def perform_update(self, serializer):
        instance = serializer.instance
        changes = self._diff(instance, serializer.validated_data)
        kwargs = {}
        if hasattr(instance, "updated_by"):
            kwargs["updated_by"] = self.request.user
        serializer.save(**kwargs)
        self._log(ActivityLog.UPDATE, instance, changes=changes)

    def perform_destroy(self, instance):
        self._log(ActivityLog.DELETE, instance)
        # Calls BaseModel.delete() which does soft delete.
        instance.delete()
