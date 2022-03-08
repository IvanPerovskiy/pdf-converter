from notifications.api.smsprosto import SMSProsto
import warnings

warnings.simplefilter('ignore', category=RuntimeWarning)

default_app_config = 'notifications.apps.NotificationsConfig'

smsp = SMSProsto()
