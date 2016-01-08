from django.contrib.auth.models import User


class SimpleBackend:
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate(self, username=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        return user
