from rest_framework.test import APIClient

from users.tests.parent import ParentTestCase
from users.models import User, UserStatus, UserRole
from notifications.models import ActivationCode


class AuthTestCase(ParentTestCase):

    def setUp(self):
        super().setUp()

    def test_login_phone(self):
        self.phone_user = APIClient()

        response = self.phone_user.post('/api/users/login_phone', {
            'phone': '79312972206'
        }, format='json')
        self.assertEqual(response.status_code, 401)

        response = self.phone_user.post('/api/users/unauthorized')
        self.assertEqual(response.status_code, 200)
        access_token = response.data['access_token']
        user_id = response.data['user_id']
        unauth_user = User.objects.get(id=user_id)
        self.assertEqual(unauth_user.role, UserRole.UNAUTHORIZED_USER)
        self.phone_user.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.phone_user.post('/api/users/login_phone', {
            'phone': '79312972206'
        }, format='json')
        self.assertEqual(response.status_code, 200)

        code = ActivationCode.objects.filter(
            code_type=1,
            user=unauth_user
        ).first().code
        response = self.phone_user.post('/api/users/confirm_phone', {
            'phone': '79312972206',
            'code': code
        }, format='json')
        self.assertEqual(response.status_code, 200)
        phone_user_id = response.data['user_id']
        self.assertEqual(user_id, phone_user_id)
        phone_user = User.objects.get(id=phone_user_id)
        self.assertEqual(phone_user.role, UserRole.LOGIN_USER)
        self.assertEqual(phone_user.phone, '79312972206')
        self.assertEqual(phone_user.phone_confirmed, True)

    def test_login_password(self):
        self.client = APIClient()
        self.login_user = APIClient()
        self.login_user_2 = APIClient()

        response = self.login_user.post('/api/users/register', {
             'login': 'ivan',
             'email': 'ivanperovsky@gmail.com',
             'password': '1234'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        access_token = response.data['access_token']
        first_user_id = response.data['user_id']
        first_user = User.objects.get(id=first_user_id)
        self.assertEqual(first_user.role, UserRole.LOGIN_USER)
        self.assertEqual(first_user.email, 'ivanperovsky@gmail.com',)
        self.assertEqual(first_user.login, 'ivan')
        self.login_user.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.login_user_2.post('/api/users/unauthorized')
        self.assertEqual(response.status_code, 200)
        access_token = response.data['access_token']
        second_user_id = response.data['user_id']
        second_user = User.objects.get(id=second_user_id)
        self.assertEqual(second_user.role, UserRole.UNAUTHORIZED_USER)
        self.login_user_2.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

        response = self.login_user_2.post('/api/users/register', {
            'email': 'ivan@marga.app',
            'password': '12345'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        access_token = response.data['access_token']
        new_second_user_id = response.data['user_id']
        self.assertEqual(new_second_user_id, second_user_id)
        second_user.refresh_from_db()
        self.assertEqual(second_user.role, UserRole.LOGIN_USER)
        self.assertEqual(second_user.email, 'ivan@marga.app')
        self.assertEqual(second_user.login, 'ivan@marga.app')

        response = self.client.post('/api/users/login_password', {
             'login': 'test@gmail.com',
             'password': '1234'
        }, format='json')
        self.assertEqual(response.status_code, 401)

        response = self.login_user.post('/api/users/login_password', {
             'login': 'test2@gmail.com',
             'password': '1234'
        }, format='json')
        self.assertEqual(response.status_code, 401)

        response = self.client.post('/api/users/login_password', {
             'login': 'ivan',
             'password': '1234'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        current_user_id = response.data['user_id']
        self.assertEqual(current_user_id, first_user_id)

        response = self.client.post('/api/users/send-password', {
            'email': 'ivan@marga.app',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        code = ActivationCode.objects.filter(user_id=new_second_user_id).latest('timestamp').code

        response = self.client.post('/api/users/restore-password', {
            'new_password': 'BlaBla',
            'code': code,
            'user_id': new_second_user_id
        }, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/api/users/login_password', {
             'login': 'ivan@marga.app',
             'password': '12345'
        }, format='json')
        self.assertEqual(response.status_code, 401)

        response = self.client.post('/api/users/login_password', {
             'login': 'ivan@marga.app',
             'password': 'BlaBla'
        }, format='json')
        self.assertEqual(response.status_code, 200)
