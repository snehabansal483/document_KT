from rest_framework import serializers
from .models import *
from postalpin.models import DigiPinAddress 

class LoginSerializer(serializers.ModelSerializer):
    email= serializers.EmailField(max_length=255,required=True)
    class Meta:
        model = Account
        fields = ('email','password')

    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'full_name', 'email', 'phone_number', 'account_type', 'account_role']

class AccountSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    profile_type = serializers.CharField(write_only=True)

    class Meta:
        model = Account
        fields = ['full_name',
                   'email', 
                   'phone_number',
                   'password', 
                   'password2',
                   'account_type',
                   'account_role',
                   'profile_type']
        extra_kwargs = {'password': {'write_only': True},'profile_type': {'write_only': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data.pop('profile_type')
        return Account.objects.create_user(**validated_data)


class AddressSerializer(serializers.ModelSerializer):
    digipin_data = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = [
            'id',
            'add_user',
            'add_line1',
            'add_line2',
            'landmark',
            'city',
            'state',
            'country',
            'zipcode',
            'digipin_data',
        ]
        read_only_fields = ['add_user', 'id']

    def get_digipin_data(self, obj):
        try:
            postal_address = DigiPinAddress.objects.filter(pincode=str(obj.zipcode)).first()
            if postal_address:
                return {
                    "digipin": postal_address.digipin,
                    "latitude": postal_address.latitude,
                    "longitude": postal_address.longitude,
                    "digipin_url": postal_address.digipin_url
                }
        except Exception:
            pass
        return None

    def validate(self, attrs):
        if not self.context.get('add_user'):
            raise serializers.ValidationError("User login required.")
        return attrs

    def create(self, validated_data):
        add_user = self.context.get('add_user')
        if not add_user:
            raise serializers.ValidationError("Authenticated user is required.")
        return Address.objects.create(add_user=add_user, **validated_data)

    def update(self, instance, validated_data):
        for field in ['add_line1', 'add_line2', 'landmark', 'city', 'state', 'country', 'zipcode']:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))
        instance.save()
        return instance
    
class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            'ProfilePic',
        ]   
        read_only_fields = ['qrCode']  # These fields are auto-generated.
    
    def validate(self, attrs):
        """Custom validation to ensure account_type is 'Customer'."""
        user = self.context['auth_id']  # Authenticated user passed via context
        if user.account_type != 'Customer':
            raise serializers.ValidationError("Only users with account_type 'Customer' can create a CustomerProfile.")
        return attrs

    def create(self, validated_data):
        # Retrieve `auth_id` from context
        auth_id = self.context.get('auth_id')
        if not auth_id:
            raise serializers.ValidationError("Authentication user is required.")
        
        # Create the profile with `auth_id`
        return CustomerProfile.objects.create(auth_id=auth_id, **validated_data)

    def update(self, instance, validated_data):
        # Update only allowed fields
        for field in ['ProfilePic']:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))

        instance.save()
        return instance




class DealerProfileSerializer(serializers.ModelSerializer):
    """Serializer for DealerProfile model."""

    class Meta:
        model = DealerProfile
        fields = [
             'id',  
            'ProfilePic',
        ]
        read_only_fields = ['auth_id']  # These fields should not be editable by the user.

    def validate(self, attrs):
        """Custom validation to ensure account_type is 'Dealer'."""
        user = self.context['auth_id']  # Authenticated user passed via context
        if user.account_type != 'Dealer':
            raise serializers.ValidationError("Only users with account_type 'Dealer' can create a DealerProfile.")
        return attrs

    def create(self, validated_data):
        """Create a new DealerProfile with the provided data."""
        # Retrieve the user instance from the context
        auth_id = self.context['auth_id']
        validated_data['auth_id'] = auth_id
        return DealerProfile.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update an existing DealerProfile instance."""
        # Update fields as necessary
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance








class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        old_password = attrs.get('old_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        # Ensure new password and confirm password match
        if new_password != confirm_password:
            raise serializers.ValidationError("New password and confirm password must match.")

        # Check if old password is correct
        user = self.context.get('request').user
        if not user.check_password(old_password):
            raise serializers.ValidationError("Old password is incorrect.")

        return attrs