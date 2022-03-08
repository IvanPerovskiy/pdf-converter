from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from common.actions import start_server
from users.models import User, UserRole


@override_settings(
    BROKER_BACKEND='memory',
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_TASK_ALWAYS_EAGER=True,
    MEDIA_ROOT='/media/media_test/'
)
class ParentTestCase(TestCase):
    def setUp(self):
        """
        Создает пользователей с различными ролями.
        Авторизует каждого из них,
        """
        start_server()
        self.device_user = APIClient()
        self.admin_user = APIClient()
        response = self.device_user.post('/api/users/login_device', {
            'device_id': '12345'
        }, format='json')
        assert response.status_code == 200
        access_token = response.data['access_token']
        self.device_user.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)
        self.current_device_user = User.objects.get(id=response.data['user_id'])

        response = self.admin_user.post('/api/users/login_device', {
            'device_id': '54321'
        }, format='json')
        assert response.status_code == 200
        access_token = response.data['access_token']
        self.admin_user.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)
        self.current_admin_user = User.objects.get(id=response.data['user_id'])
        self.current_admin_user.role = UserRole.ADMIN
        self.current_admin_user.save()

