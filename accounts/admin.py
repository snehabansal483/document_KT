from django.contrib import admin
from .models import Account, Address, CustomerProfile, DealerProfile
from django.contrib.auth.admin import UserAdmin


@admin.register(Account)
class AccountAdmin(UserAdmin):
    model = Account
    list_display = ('email', 'full_name', 'account_role','account_type','is_staff', 'is_active','online',)
    list_filter = ('is_staff', 'is_active','email')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'add_user', 'add_line1', 'add_line2', 'city', 'state', 'country', 'zipcode')
    list_filter = ('city', 'state', 'country')
    search_fields = ('add_line1', 'add_line2', 'city', 'state', 'country', 'zipcode')
    ordering = ('id',)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'auth_id','ProfilePic','qrCode')
    list_filter = ('auth_id','profile_type')
    search_fields = ('auth_id__email', 'kt_id', 'auth_id__phone_number')
    ordering = ('id',)


@admin.register(DealerProfile)
class DealerProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'auth_id','ProfilePic','qrCode')
    list_filter = ('profile_type',)
    search_fields = ('auth_id__email',)
    ordering = ('id',)
