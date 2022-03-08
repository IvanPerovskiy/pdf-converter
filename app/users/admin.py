from django.contrib import admin

from users.models import *


class UserAdmin(admin.ModelAdmin):
    model = User
    list_display = (
        'login', 'status', 'role'
    )


class DeviceAdmin(admin.ModelAdmin):
    model = Device
    list_display = (
        'number', 'created'
    )


class ProfileAdmin(admin.ModelAdmin):
    model = Profile
    list_display = (
        'name',
    )


admin.site.register(User, UserAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Profile, ProfileAdmin)
