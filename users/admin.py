from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import UserRegisterForm


# class ProfileAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user')


class UserAdmin(UserAdmin):
    list_display = ('id', 'email', 'name', 'is_staff')
    search_fields = ('name', 'email')
    ordering = ('-id',)

    add_form = UserRegisterForm
    add_form_template = 'admin/add_form.html'

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (('Personal info'), {'fields': ('name', )}),
        (('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


# class AboutUsAdmin(admin.ModelAdmin):
#     list_display = [field.name for field in AboutUs._meta.get_fields()]


# admin.site.register(Profile, ProfileAdmin)
admin.site.register(User, UserAdmin)
# admin.site.register(AboutUs, AboutUsAdmin)
