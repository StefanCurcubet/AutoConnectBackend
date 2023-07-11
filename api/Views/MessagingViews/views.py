from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.contrib.auth.models import User

from api.models import Conversation, Message
from api.serializers import ConversationSerializer, MessageSerializer


# Create your views here.


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
