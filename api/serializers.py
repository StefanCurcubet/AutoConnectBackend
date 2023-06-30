from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import Post, UserExtra, Comment, Conversation, Message, Rating, SellerRating
from django.contrib.auth.models import User


class RatingSerializer(ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'


class CommentSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ('author', 'content', 'added', 'id')


class PostSerializer(ModelSerializer):
    ratings = RatingSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = '__all__'


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class SellerRatingSerializer(ModelSerializer):
    class Meta:
        model = SellerRating
        fields = '__all__'


class UserExtraSerializer(ModelSerializer):
    ratings = SellerRatingSerializer(many=True, read_only=True)

    class Meta:
        model = UserExtra
        fields = '__all__'


class ConversationSerializer(ModelSerializer):
    usernames = serializers.SerializerMethodField()

    def get_usernames(self, conversation):
        user_list = list(conversation.users.all())
        usernames = [user.username for user in user_list]
        return usernames

    class Meta:
        model = Conversation
        fields = ('usernames', 'id', 'update_from')


class MessageSerializer(ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'


