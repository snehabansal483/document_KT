from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin

# Create your models here.
class MyAccountManager(BaseUserManager):
    def create_user(self, full_name, email, phone_number=None, account_type=None,account_role=None ,password=None, password2=None):
        if not email:
            raise ValueError('User must have an email')
        if not phone_number and account_type:
            raise ValueError('User must have a phone number for the specified account type')

        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            phone_number=phone_number,
            account_type=account_type,
            account_role=account_role,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, full_name, email, password):
        user = self.create_user(
            email=self.normalize_email(email),
            full_name=full_name,
            password=password,
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


        


class Account(AbstractBaseUser,PermissionsMixin):
    account_type_choice =(
        ('Customer','Customer'),
        ('Dealer','Dealer'),
    )

    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100,unique=True)
    username = models.CharField(max_length = 255,null=True,blank=True,unique=True)
    phone_number = models.CharField(max_length=13,null=True,blank=True)
    account_type = models.CharField(choices=account_type_choice,max_length=30,null=True,blank=True)
    account_role = models.CharField(max_length=50,null=True,blank=True)
    
    # required
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    online = models.BooleanField(default=False)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    objects = MyAccountManager()
    
    
    def __str__(self):
        return self.email
    
    
    def has_perm(self,perm,obj=None):
        return self.is_admin
    
    def has_module_perms(self,add_label):
        return True
    
    



class Address(models.Model):
    """Represents a customer's address."""

    add_user = models.ForeignKey(Account,related_name='user_address',on_delete=models.CASCADE)
    add_line1 = models.CharField(max_length=200, verbose_name="Address Line 1")
    add_line2 = models.CharField(max_length=200, verbose_name="Address Line 2", blank=True)
    landmark = models.CharField(max_length=100, verbose_name="Landmark", blank=True)
    city = models.CharField(max_length=50, verbose_name="City")
    state = models.CharField(max_length=50, verbose_name="State")
    country = models.CharField(max_length=50, verbose_name="Country")
    zipcode = models.IntegerField(verbose_name="Zipcode")
    is_default = models.BooleanField(default=False, verbose_name="Default Address")
    
    def full_address(self):
        """Combine address lines for human-readable display."""
        return f'{self.add_line1}{" " if self.add_line2 else ""}{self.add_line2}'
    
    def save(self, *args, **kwargs):
        """Auto-generate the Customer ID if not provided."""
        super().save(*args, **kwargs)
        

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"


class CustomerProfile(models.Model):
    """Represents a customer profile."""
    profile_type_choice = (
        ('Personal', 'Personal'),
        ('Organization', 'Organization'),
    )
    kt_id = models.CharField(max_length=20, verbose_name="KT ID", editable=False)
    profile_type = models.CharField(max_length=20, choices=profile_type_choice, default='Personal')
    auth_id = models.OneToOneField(Account, on_delete=models.CASCADE, verbose_name="User")
    ProfilePic = models.ImageField(upload_to='media/accounts/Customer/')
    qrCode = models.ImageField(default = 'cvm_qrcodes/4.jpg', upload_to='media/accounts/Customer/QRs')


    def __str__(self):
        return self.kt_id
    
    def save(self, *args, **kwargs):
        """Auto-generate the KTID based on User Type and Account Type."""
            
        if not self.kt_id or self.kt_id == 'KT':
            if self.profile_type == "Personal":
                        prefix = "KTCP"
            else:
                    prefix = "KTCO"
            # Temporarily assign a high ID value to avoid conflicts
            temp_id = CustomerProfile.objects.count() + 1
            self.kt_id = f"{prefix}{100000 + temp_id}"

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Customer Profile"
        verbose_name_plural = "Customer's Profile"


class DealerProfile(models.Model):
    profile_type_choice = (
        ('Kabadi', 'Kabadi'),
        ('Collector', 'Collector'),
        ('Recycler', 'Recycler'),
    )
    kt_id = models.CharField(max_length=20, verbose_name="KT ID", editable=False)
    profile_type = models.CharField(max_length=20, choices=profile_type_choice, default='Kabadi')
    auth_id = models.OneToOneField(Account,on_delete=models.CASCADE,null=True)
    qrCode = models.ImageField(default = 'cvm_qrcodes/4.jpg', upload_to='accounts/Dealer/QRs')
    ProfilePic = models.ImageField(default = 'photos/Profile_Pic.png', upload_to='accounts/Dealer/ProfilePic', null = True, blank = True)

    
    def __str__(self):
        return str(self.kt_id)

    def save(self, *args, **kwargs):
        """Auto-generate the KTID based on User Type and Account Type."""


        if not self.kt_id or self.kt_id == 'KT':
            if self.profile_type == "kabadi":
                    prefix = "KTDK"
            elif self.profile_type == "Collector":
                prefix = "KTDC"    
            else:
                prefix = "KTDR"
            # Temporarily assign a high ID value to avoid conflicts
            temp_id = DealerProfile.objects.count() + 1
            self.kt_id = f"{prefix}{100000 + temp_id}"

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Dealer Profile"
        verbose_name_plural = "Dealer's Profile"
   
        


        
from django.db.models.signals import post_delete,pre_delete
from django.dispatch import receiver

@receiver(post_delete, sender=CustomerProfile)
def delete_customer_related_user(sender,instance, **kwargs):
    try:
        instance.auth_id.delete()
    except:
        pass

@receiver(post_delete, sender=DealerProfile)
def delete_dealer_related_user(sender,instance, **kwargs):
    try:
        instance.auth_id.delete()
    except:
        pass
