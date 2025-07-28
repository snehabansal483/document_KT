from django.urls import path
#from .views import Customer_RegisterView, Customer_VerifyEmail, Customer_LoginAPIView, Customer_UpdateProfilePic ,Customer_RegenerateVerificationEmail, Customer_PasswordTokenCheckAPI, Customer_RequestPasswordResetEmail, Customer_SetNewPassAPIView, Customer_LogoutAPIView, Customer_Database_CheckerAPIView, Dealer_RegisterView, Dealer_RegenerateVerificationEmail, Dealer_VerifyEmail, Dealer_LoginAPIView, Dealer_UpdateProfilePic, Dealer_PasswordTokenCheckAPI, Dealer_RequestPasswordResetEmail, Dealer_SetNewPassAPIView, Dealer_LogoutAPIView, Dealer_Database_CheckerAPIView#, DealerRegistrationView
from .views import *
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)

urlpatterns = [
    path('iam-exist/',IsExist.as_view(),name='i-am-exist'),
    path('myqr/',MyQRCode.as_view(),name='my-qr'),
    path('register/', SignupAPIView.as_view(), name = "registration"),
    path('login/',LoginAccount.as_view(),name='login_account'),
    path('logout/',LogoutAPIView.as_view(),name='logout_account'),
    path('change-pass/',ChangePasswordAPIView.as_view(),name='change-password'),
    path('password-reset/', PasswordResetAPIView.as_view(), name='password_reset'),
    path('reset-password/<str:uidb64>/<str:token>/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountAPIView.as_view(), name='activate_account'),
    path('address/', AddressAPIView.as_view(), name='address'),
    path('address/<int:id>/', AddressAPIView.as_view(), name='address'),

   
    #####-----------------CUSTOMER------------------######
    
    path('customer-profile/', CustomerProfileAPIView.as_view(), name='customer-profile'),

    

    # #####-----------------DEALER------------------######
    path('dealer-profile/',DealerProfileAPIView.as_view(),name='dealer_profile'),
    



    # #####-----------------EXTRAS------------------######
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name="token_refresh"),
    # path('dealers/register/', DealerRegistrationView.as_view(), name='dregister'),
]
