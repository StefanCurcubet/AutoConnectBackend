import random
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Post, UserExtra, Comment, Conversation, Message, Rating, SellerRating, Pin
from .serializers import PostSerializer, UserExtraSerializer, CommentSerializer, ConversationSerializer, \
    MessageSerializer, UserSerializer, SellerRatingSerializer
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.utils import timezone

# Create your views here.


@api_view(['GET'])
def getAllPosts(request, order):
    posts = Post.objects.all().order_by(order)
    serializer = PostSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createPost(request):
    data = request.data['listingData']
    new_post = Post.objects.create(
        title=data['title'],
        imageUrl=data['imageUrl'],
        brand=data['make'],
        modelYear=data['firstRegistration'],
        mileage=data['mileage'],
        price=data['price'],
        author=request.user
    )
    Comment.objects.create(
        post=new_post,
        author=request.user,
        content=data['description']
    )
    return Response({'message': 'Post Added'})


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def deletePost(request, pk):
    post = Post.objects.get(id=pk)
    if post.author == str(request.user):
        post.delete()

    return Response({'message': 'Listing deleted'})


@api_view(['GET'])
def viewPost(request, pk):
    post = Post.objects.get(id=pk)
    serializer = PostSerializer(post, many=False)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def ratePost(request, pk, rating):
    post = Post.objects.get(id=pk)
    user = request.user

    try:
        prev_rating = Rating.objects.filter(post=post).filter(rated_by=user).get()
        prev_rating.rating = rating
        prev_rating.save()
    except Rating.DoesNotExist:
        Rating.objects.create(
            post=post,
            rating=rating,
            rated_by=user
        )
    post.save()
    return Response({'message': 'Post rated'})


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
def getComments(request, pk):
    post = Post.objects.get(id=pk)
    comments = post.comments.all()
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def addComment(request, pk):
    data = request.data['newComment']
    post = Post.objects.get(id=pk)
    author = User.objects.get(username=post.author)
    Comment.objects.create(
        post=post,
        author=request.user,
        content=data
    )

    context = {
        'post_title': post.title,
        'post_id': pk,
        'comment_from': request.user,
    }
    subject = f'Comment received on {post.title} from {request.user}'
    from_email = 'autoconnectmailer@gmail.com'
    message = f'Follow the link to view post http://localhost:3000/viewListing/{pk}'
    html_message = render_to_string('email/new_comment_email.html', context)
    if author.userextra.notify_by_mail_comment and post.author != request.user.username:
        send_mail(subject, message, from_email, recipient_list=[author.email], html_message=html_message)

    return Response({'message': 'Comment Added'})


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def createConversation(request, pk):
    data = request.data['newMessage']
    sender = User.objects.get(id=request.user.id)
    recipient = User.objects.get(username=pk)
    try:
        conversation = Conversation.objects.filter(users=sender).filter(users=recipient).get()
    except Conversation.DoesNotExist:
        new_conversation = Conversation.objects.create()
        new_conversation.users.set([sender, recipient])
        conversation = new_conversation

    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=data
    )
    conversation.update_from = request.user.username
    conversation.save()

    context = {
        'message_from': sender.username
    }
    subject = f'New conversation started by {sender.username}'
    from_email = 'autoconnectmailer@gmail.com'
    message = 'Go to Messages to view your new conversation.'
    html_message = render_to_string('email/new_message_email.html', context)
    if recipient.userextra.notify_by_mail_message:
        send_mail(subject, from_email, message, recipient_list=[recipient.email], html_message=html_message)

    return Response({'message': 'Conversation started'})



@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getConversations(request):
    user = User.objects.get(username=request.user.username)
    conversations = user.conversations.all()
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def getMessages(request, pk):
    conversation = Conversation.objects.get(id=pk)
    messages = conversation.messages.all()
    serializer = MessageSerializer(messages, many=True)
    if conversation.update_from != request.user.username:
        conversation.update_from = ''
        conversation.save()

    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def addMessage(request, pk):
    data = request.data['reply']
    conversation = Conversation.objects.get(id=pk)
    recipient = ''
    for user in conversation.users.all():
        if user != request.user:
            recipient = User.objects.get(username=user)

    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=data
    )
    conversation.update_from = request.user.username
    conversation.save()
    context = {
        'message_from': request.user.username
    }
    subject = f'Message received from {request.user.username}'
    from_email = 'autoconnectmailer@gmail.com'
    message = 'Go to Messages to view your message'
    html_message = render_to_string('email/new_message_email.html', context)
    if recipient.userextra.notify_by_mail_message:
        send_mail(subject, from_email, message, recipient_list=[recipient.email], html_message=html_message)
    return Response({'message': 'Reply Added'})


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
