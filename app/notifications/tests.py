from users.tests.parent import ParentTestCase
from notifications.tasks import confirm_email, refresh_password


class NotificationTests(ParentTestCase):

    def setUp(self):
        super().setUp()
        self.current_device_user.email = 'ivan@marga.app'
        self.current_device_user.email_confirmed = True
        self.current_device_user.save()

    def test_send_email(self):
        confirm_email('ivan@marga.app', self.current_device_user.id)

    def test_send_restore_password(self):
        refresh_password('ivan@marga.app', self.current_device_user.id)
