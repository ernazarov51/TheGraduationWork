from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """Common base for all project serializers.

    - Formats created_at as "YYYY-MM-DD HH:MM:SS" string.
    - Hides internal audit fields (is_active, created_by, updated_by)
      from API responses so clients don't see them by default.

    Usage:
        class ProductSerializer(BaseSerializer):
            class Meta:
                model = Product
                fields = ("id", "name", "price", "created_at")
    """

    created_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S",
        read_only=True,
        required=False,
    )

    # Stripped from responses ONLY when the subclass did not explicitly
    # include them in Meta.fields (i.e. fields='__all__' or omitted).
    # If a serializer lists one of these in Meta.fields, it is intentional
    # and we leave it untouched.
    _hidden_fields = frozenset({"is_active", "created_by", "updated_by"})

    def to_representation(self, instance):
        data = super().to_representation(instance)
        meta_fields = getattr(getattr(self, "Meta", None), "fields", None)
        # Only auto-hide when fields='__all__' (no explicit list given).
        # When the subclass provides an explicit list it already controls
        # what is exposed, so we must not second-guess it.
        if meta_fields == "__all__":
            for field_name in self._hidden_fields:
                data.pop(field_name, None)
        return data
