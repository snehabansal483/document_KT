from django.contrib.auth import authenticate, logout
from rest_framework import status,permissions,viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from .serializers import *
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import renderers
import json
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.exceptions import ObjectDoesNotExist


User = get_user_model()

current_site_frontend = 'http://localhost:5173'


def sendanemail(request,user,content,subject,template=None):
    if template:
        html_content = render_to_string(template_name=template,context=content)
    else:
        html_content = render_to_string('verify_email.html',context=content)

    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject, 
        text_content, 
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()




class IsExist(APIView):
    def post(self,request):
        try:
            email = request.data.get("email")
            user = Account.objects.get(email=email)
            return Response({'detail': f'Account Detail : {user.email,user.account_type}'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error':"User Doesn't Exist"})



class PasswordResetAPIView(APIView):
    """API endpoint to handle password reset."""
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get("email")
            user_type = request.data.get("user_type")
            if not email:
                return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Try to get user by email (this will raise DoesNotExist if not found)
                user = Account.objects.get(email=email)
                if user_type and user.account_type != user_type:
                    return Response({"error": "Invalid user type."}, status=status.HTTP_401_UNAUTHORIZED)
                if not user.is_active:
                    return self.handle_inactive_user(request,user)

            except ObjectDoesNotExist:
                return Response({"message": "User doesn't exist"}, status=status.HTTP_401_UNAUTHORIZED)

            user = get_object_or_404(User, email=email)
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"{current_site_frontend}/reset-password/{uid}/{token}/"
            try:
                sendanemail(request,user=user,content={"site":reset_link},subject="Reset Your Password",template='forget_password.html')
            except Exception as e:
                return Response({"error": f"Email server error: {e}"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Password reset link sent."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"User not found: {e}"}, status=status.HTTP_404_NOT_FOUND)
    
    def handle_inactive_user(self, request, user):
        """Handles sending the activation email for inactive users."""
        try:
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            activation_link = f"{current_site_frontend}/email-verify/{uid}/{token}/"
            content = {"site": activation_link}
            
            # Send the activation email
            sendanemail(request, user=user, content=content, subject="Activate Your Account")
            return Response({"error": "Account is not activated. Activation link sent."}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": f"Email Token error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmAPIView(APIView):
    """API endpoint to confirm and set new password."""
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
            except (User.DoesNotExist, ValueError, TypeError):
                return Response({"error": "Invalid token or user."}, status=status.HTTP_400_BAD_REQUEST)

            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            new_password = request.data.get("new_password")
            if not new_password:
                return Response({"error": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ActivateAccountAPIView(APIView):
    """API endpoint to activate account using email link."""
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            try:
                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)
            except (User.DoesNotExist, ValueError, TypeError):
                return Response({"error": "Invalid activation link."}, status=status.HTTP_400_BAD_REQUEST)

            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            user.is_active = True
            user.save()
            return Response({"message": "Account activated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class LoginAccount(APIView):
    """API endpoint for user login."""

    def post(self, request):
        try:
            email = request.data.get("email")
            password = request.data.get("password")
            user_type = request.data.get("user_type")

            if not email or not password:
                return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = Account.objects.get(email=email)
            except ObjectDoesNotExist:
                return Response({"message": "User doesn't exist"}, status=status.HTTP_401_UNAUTHORIZED)

            if user.account_type != user_type:
                return Response({"error": "Invalid user type."}, status=status.HTTP_401_UNAUTHORIZED)

            user = authenticate(request, email=email, password=password)
            if user is None:
                return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

            if not user.is_active:
                return self.handle_inactive_user(request, user)

            token = get_tokens_for_user(user)
            user.online = True
            user.save()

            user_data = UserSerializer(user).data

            dealer_id = None
            customer_id = None
            kt_id = None

            if user.account_type == 'Customer':
                customer_profile = CustomerProfile.objects.filter(auth_id=user).first()
                if customer_profile:
                    kt_id = customer_profile.kt_id
                    customer_id = customer_profile.id

            elif user.account_type == 'Dealer':
                dealer_profile = DealerProfile.objects.filter(auth_id=user).first()
                if dealer_profile:
                    kt_id = dealer_profile.kt_id
                    dealer_id = dealer_profile.id

            # Add dealer_id, customer_id, kt_id inside user
            user_data['dealer_id'] = dealer_id
            user_data['customer_id'] = customer_id
            user_data['kt_id'] = kt_id

            return Response(
                {
                    "token": token,
                    "user": user_data,
                    "message": "You have been logged in."
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SignupAPIView(APIView):
    """API endpoint for user signup."""
    def post(self, request):
        try:
            serializer = AccountSerializer(data=request.data)
            email = request.data.get("email")
            account_type = request.data.get("account_type")
            profile_type = request.data.get("profile_type")
            user = Account.objects.filter(email=email).first()
            if user:
                return Response({"error": f"User already exists as {user.account_type} please login for the same account type"}, status=status.HTTP_400_BAD_REQUEST)
            if serializer.is_valid(raise_exception=True):
                user = serializer.save()
                user.is_active = False
                try:
                    token_generator = PasswordResetTokenGenerator()
                    token = token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    activation_link = f"{current_site_frontend}/email-verify/{uid}/{token}/"
                    content = {"site": activation_link}
                    print(activation_link)
                except Exception as e:
                    return Response({"error": f"Email Token error: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                try:
                    sendanemail(request, user=user, content=content, subject="Activate Your Account")
                except Exception as e:
                    return Response({"error": "Email server error"}, status=status.HTTP_400_BAD_REQUEST)
                
                user.save()
                if account_type == 'Customer':
                    # Ensure no duplicate profiles are created
                    CustomerProfile.objects.get_or_create(auth_id=user, defaults={"profile_type": profile_type})
                else:
                    # Ensure no duplicate profiles are created
                    DealerProfile.objects.get_or_create(auth_id=user, defaults={"profile_type": profile_type})
                return Response({"message": "Registration successful. Activation link sent to your email."}, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class UserRenderer(renderers.JSONRenderer):
    charset = 'utf-8'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = ''
        if 'ErrorDetail' in str(data):
            response = json.dumps({'errors':data})
        else:
            response = json.dumps(data)
        return response

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
       

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = Account.objects.get(email=request.user.email)
            user.online = False
            user.save()
            logout(request)
            return Response({'detail': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)




class CustomerProfileAPIView(APIView):
    """API endpoint for managing customer profiles."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # 👈 add this to support form-data

    def get(self, request, *args, **kwargs):
        try:
            customer_profile = CustomerProfile.objects.get(auth_id=request.user)
            serializer = CustomerProfileSerializer(customer_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomerProfile.DoesNotExist:
            return Response({"error": "Customer profile not found"}, status=status.HTTP_404_NOT_FOUND)

    # def post(self, request, *args, **kwargs):
    #     try:
    #         user_instance = request.user

    #         if CustomerProfile.objects.filter(auth_id=user_instance).exists():
    #             return Response({"error": "Customer profile already exists."}, status=status.HTTP_400_BAD_REQUEST)

    #         serializer = CustomerProfileSerializer(data=request.data, context={'auth_id': user_instance})
    #         if serializer.is_valid(raise_exception=True):
    #             serializer.save()
    #             return Response({"message": "Customer profile created successfully"}, status=status.HTTP_201_CREATED)

    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     except Exception as e:
    #         import traceback
    #         traceback.print_exc()
    #         return Response({"error": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        try:
            customer_profile = CustomerProfile.objects.get(auth_id=request.user)
        except CustomerProfile.DoesNotExist:
            return Response({"error": "Customer profile not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            serializer = CustomerProfileSerializer(
                customer_profile,
                data=request.data,
                partial=True,
                context={'auth_id': request.user}  # ✅ add this
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response({"message": "Customer profile updated successfully"}, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DealerProfileAPIView(APIView):
    """API endpoint for managing dealer profiles."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Retrieve the dealer profile for the authenticated user
            dealer_profile = DealerProfile.objects.get(auth_id=request.user)
            serializer = DealerProfileSerializer(dealer_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DealerProfile.DoesNotExist:
            return Response({"error": "Dealer profile not found"}, status=status.HTTP_404_NOT_FOUND)

    # def post(self, request, *args, **kwargs):
    #     user_instance = request.user  # Get the authenticated user

    #     # Check if a profile already exists for this user
    #     if DealerProfile.objects.filter(auth_id=user_instance).exists():
    #         return Response(
    #             {"error": "Dealer profile already exists."},
    #             status=status.HTTP_400_BAD_REQUEST,
    #         )

    #     # Prepare data for the serializer
    #     data = request.data.copy()

    #     serializer = DealerProfileSerializer(data=data, context={'auth_id': user_instance})

    #     if serializer.is_valid(raise_exception=True):
    #         serializer.save()  # Save the profile
    #         return Response(
    #             {"message": "Dealer profile created successfully"},
    #             status=status.HTTP_201_CREATED,
    #         )

    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            # Retrieve the dealer profile for the authenticated user
            dealer_profile = DealerProfile.objects.get(auth_id=request.user)
        except DealerProfile.DoesNotExist:
            return Response({"error": "Dealer profile not found"}, status=status.HTTP_404_NOT_FOUND)

        # Update the dealer profile with the provided data
        serializer = DealerProfileSerializer(dealer_profile, data=request.data, partial=True, context={'auth_id': request.user})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "Dealer profile updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class AddressAPIView(APIView):
    """API endpoint for managing addresses."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            # Retrieve all addresses for the authenticated user
            addresses = Address.objects.filter(add_user=request.user)
            serializer = AddressSerializer(addresses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Address.DoesNotExist:
            return Response({"error": "No addresses found for the user."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        try:
            user_instance = request.user  # Get the authenticated user

            # Prepare data for the serializer
            data = request.data.copy()

            # Check if the new address is set as default
            is_default = data.get('is_default', False)

            if is_default:
                # Update all other addresses of the user to not be default
                Address.objects.filter(add_user=user_instance, is_default=True).update(is_default=False)

            serializer = AddressSerializer(data=data, context={'add_user': user_instance})

            if serializer.is_valid(raise_exception=True):
                serializer.save()  # Save the address
                return Response(
                    {"message": "Address created successfully."},
                    status=status.HTTP_201_CREATED,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id, *args, **kwargs):
        try:
            # Retrieve the specific address by id for the authenticated user
            user_instance = request.user
            address = Address.objects.get(id=id, add_user=user_instance)
        except Address.DoesNotExist:
            return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the updated address is set as default
        is_default = request.data.get('is_default', False)

        if is_default:
            # Update all other addresses of the user to not be default
            Address.objects.filter(add_user=user_instance, is_default=True).exclude(id=address.id).update(is_default=False)

        serializer = AddressSerializer(address, data=request.data, context={'add_user': user_instance}, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"message": "Address updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, *args, **kwargs):
        try:
            # Retrieve the specific address by id for the authenticated user
            address = Address.objects.get(id=id, add_user=request.user)
            address.delete()
            return Response({"message": "Address deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Address.DoesNotExist:
            return Response({"error": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        


class ChangePasswordAPIView(APIView):
    """
    API View to handle changing user password.
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            # Initialize the serializer with the current user
            serializer = ChangePasswordSerializer(data=request.data, context={'request': request})

            if serializer.is_valid(raise_exception=True):
                user = request.user
                new_password = serializer.validated_data['new_password']

                # Set the new password and save
                user.set_password(new_password)
                user.save()

                return Response({"detail": "Password successfully updated."}, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Something went wrong: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

from PIL import Image
import qrcode
import io
import base64

class MyQRCode(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Attempt to fetch kt_id from the correct profile
            try:
                if user.account_type == "Customer":
                    kt_id = user.customerprofile.kt_id
                elif user.account_type == "Dealer":
                    kt_id = user.dealerprofile.kt_id
                else:
                    return Response({"error": "User type is unknown."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"error": f"Profile not found or incomplete: {e}"}, status=status.HTTP_404_NOT_FOUND)

            # Generate QR code with kt_id
            QRcode1 = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
            QRcode1.add_data(f"KT ID: {kt_id}")
            QRcode1.make()
            QRimg1 = QRcode1.make_image(fill_color='black', back_color='white').convert('RGB')

            # Add logo to QR
            logo_path = f"{settings.MEDIA_ROOT}/cvm_qrcodes/logo.png"
            logo = Image.open(logo_path)
            basewidth = 100
            wpercent = (basewidth / float(logo.size[0]))
            hsize = int((float(logo.size[1]) * float(wpercent)))
            logo = logo.resize((basewidth, hsize), Image.LANCZOS)
            pos = ((QRimg1.size[0] - logo.size[0]) // 2, (QRimg1.size[1] - logo.size[1]) // 2)
            QRimg1.paste(logo, pos)

            # Encode to base64
            buffer = io.BytesIO()
            QRimg1.save(buffer, format="JPEG")
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()

            return Response({
                "kt_id": kt_id,
                "qr_code": qr_code_base64
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
