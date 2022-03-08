from rest_framework_simplejwt import authentication


class JWTAuthentication(authentication.JWTAuthentication):
    def get_user(self, validated_token):
        try:
            return super().get_user(validated_token)
        except Exception:
            return None
