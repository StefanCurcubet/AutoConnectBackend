import random
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone

from api.models import UserExtra, Conversation, Message, Post, SellerRating, Pin, PasswordReset
from api.serializers import UserExtraSerializer, UserSerializer, PostSerializer


# Create your views here.


@api_view(['POST'])
def createUser(request):
    data = request.data
    hashed_password = make_password(data['password'])
    created_user = User.objects.create(
        username=data['username'],
        email=data['email'],
        password=hashed_password
    )
    UserExtra.objects.create(user=created_user, favourited_posts='')

    admin = User.objects.get(username='stefa')
    admin_conversation = Conversation.objects.create()
    admin_conversation.users.set([admin, created_user])
    Message.objects.create(
        conversation=admin_conversation,
        content=f'Welcome to AutoConnect, '
                f'please feel free to message me with any issues or recommendations you have about the site.',
        sender='stefa'
    )
    admin_conversation.update_from = 'stefa'
    admin_conversation.save()
    return Response({'message': 'Account created'})


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def deleteUser(request):
    user = request.user
    user.delete()
    return Response({'message': 'User deleted'})


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def toggle_favourite(request, pk):
    user = UserExtra.objects.get(user=request.user)
    user.toggle_favourite(pk)
    return Response({'message': 'Favourite updated'})


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_favourites(request):
    user = UserExtra.objects.get(user=request.user)
    serializer = UserExtraSerializer(user)
    return Response(serializer.data)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        # ...

        return token


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


@api_view(['GET'])
def getSeller(request, pk):
    selected_user = User.objects.get(username=pk)
    selected_user_extra = UserExtra.objects.get(user=selected_user)
    user_serializer = UserSerializer(selected_user, many=False)
    user_extra_serializer = UserExtraSerializer(selected_user_extra, many=False)
    selected_user_posts = Post.objects.filter(author=pk)
    post_serializer = PostSerializer(selected_user_posts, many=True)
    edited_user = {'date_joined': user_serializer.data['date_joined'], 'username': user_serializer.data['username'],
                   'listings': post_serializer.data, 'current_rating': user_extra_serializer.data['current_rating'],
                   'ratings': user_extra_serializer.data['ratings']}
    return Response(edited_user)


@api_view(['GET'])
def getAllSellerRatings(request):
    all_user_extras = UserExtra.objects.all()
    serializer = UserExtraSerializer(all_user_extras, many=True)
    all_ratings = []
    for seller in serializer.data:
        user = User.objects.get(id=int(seller['user']))
        user_serializer = UserSerializer(user, many=False)
        all_ratings.append({'username': user_serializer.data['username'],
                            'current_rating': seller['current_rating'],
                            'nr_ratings': seller['nr_ratings']})
    return Response(all_ratings)


@api_view(['GET'])
def getSellerRating(request, pk):
    seller = User.objects.get(username=pk)
    seller_extra = UserExtra.objects.get(user=seller)
    serializer = UserExtraSerializer(seller_extra, many=False)
    seller_rating = {'current_rating': serializer.data['current_rating'], 'nr_ratings': serializer.data['nr_ratings']}

    return Response(seller_rating)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def rateSeller(request, pk, rating):
    seller = User.objects.get(username=pk)
    seller_extra = UserExtra.objects.get(user=seller)
    rated_by = request.user
    try:
        prev_seller_rating = SellerRating.objects.filter(seller=seller_extra).filter(rated_by=rated_by).get()
        prev_seller_rating.rating = rating
        prev_seller_rating.save()
    except SellerRating.DoesNotExist:
        SellerRating.objects.create(
            seller=seller_extra,
            rating=rating,
            rated_by=rated_by
        )
    seller_extra.save()
    return Response({'message': 'Seller rated'})


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getUserSettings(request):
    user = request.user
    user_serializer = UserSerializer(user, many=False)
    user_extra = UserExtra.objects.get(user=user)
    user_extra_serializer = UserExtraSerializer(user_extra, many=False)
    return Response({'email': user_serializer.data['email'],
                     'email_confirmed': user_extra_serializer.data['email_confirmed'],
                     'notify_by_mail_message': user_extra_serializer.data['notify_by_mail_message'],
                     'notify_by_mail_comment': user_extra_serializer.data['notify_by_mail_comment']})


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def updateUserSettings(request):
    user = request.user
    user_extra = UserExtra.objects.get(user=user)
    if not user_extra.email_confirmed:
        user_extra.email_confirmed = True
        user_extra.save()
    if user.email != request.data['email']:
        user.email = request.data['email']
        user.save()
    if user_extra.notify_by_mail_message != request.data['notify_by_mail_message']:
        user_extra.notify_by_mail_message = request.data['notify_by_mail_message']
        user_extra.save()
    if user_extra.notify_by_mail_comment != request.data['notify_by_mail_comment']:
        user_extra.notify_by_mail_comment = request.data['notify_by_mail_comment']
        user_extra.save()
    return Response({'message': 'updated settings'})


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createPin(request):
    expired_pins = Pin.objects.filter(created_at__lt=(timezone.now() - timedelta(minutes=5)))
    expired_pins.delete()
    generated_code = 0
    for _ in range(1, 5):
        generated_code = generated_code * 10 + random.randint(1, 9)

    pin = Pin.objects.create(
        user=request.user.userextra,
        code=generated_code
    )
    subject = 'Email Verification PIN'
    message = f'Use this PIN to confirm your email {pin.code}. Expires in 5 minutes.'
    from_email = 'autoconnectmailer@gmail.com'
    recipient = request.user.email
    context = {
        'pin': pin.code
    }
    html_message = render_to_string('email/confirm_email.html', context)
    send_mail(subject, message, from_email, recipient_list=[recipient], html_message=html_message)
    return Response(pin.id)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def verifyPin(request, pk):
    pin = Pin.objects.get(id=pk)
    if pin.code == int(request.data):
        pin.delete()
        return Response(True)
    return Response(False)


@api_view(['POST'])
def createReset(request):
    chars = 'abcdefghijklmnopqrstuvwxyz'
    generated_code = ''
    for _ in range(0, 24):
        if random.randint(0, 1) == 0:
            generated_code += str(random.randint(0, 9))
        else:
            generated_code += chars[random.randint(0, 25)]
    try:
        if '@' in request.data:
            user = User.objects.get(email=request.data)
        else:
            user = User.objects.get(username=request.data)

        new_reset = PasswordReset.objects.create(
            user=user,
            code=generated_code,
        )

        context = {
            'code': new_reset.code
        }
        subject = 'Password Reset'
        message = f'Go to http://localhost:3000/reset/{new_reset.code}'
        from_email = 'autoconnectmailer@gmail.com'
        recipient = user.email
        html_message = render_to_string('email/password_reset_email.html', context)
        send_mail(subject, message, from_email, recipient_list=[recipient], html_message=html_message)

        return Response({'message': 'Success, reset email sent'})
    except User.DoesNotExist:
        return Response({'message': 'Invalid credentials'})


@api_view(['PUT'])
def resetPassword(request, reset_code):
    password_reset = PasswordReset.objects.get(code=reset_code)
    user = User.objects.get(username=password_reset.user)
    hashed_password = make_password(request.data)
    user.password = hashed_password
    user.save()
    password_reset.delete()
    return Response({'message': 'Password Updated'})


@api_view(['GET'])
def checkReset(request, reset_code):
    expired_resets = PasswordReset.objects.filter(created_at__lt=(timezone.now() - timedelta(minutes=5)))
    expired_resets.delete()
    try:
        PasswordReset.objects.get(code=reset_code)
        return Response(True)
    except PasswordReset.DoesNotExist:
        return Response(False)
