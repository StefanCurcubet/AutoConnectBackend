from django.urls import path
from .Views.MessagingViews import views as messaging_views
from .Views.PostViews import views as post_views
from .Views.UserViews import views as user_views
from .Views.UserViews.views import MyTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenRefreshView
)


urlpatterns = [
    # Get all listings
    path('getAllPosts/<str:order>', post_views.getAllPosts),
    # Create a new listing
    path('newPost/', post_views.createPost),
    # Delete a listing
    path('deletePost/<int:pk>', post_views.deletePost),
    # View a listing
    path('getPost/<int:pk>', post_views.viewPost),
    # Rate a listing
    path('ratePost/<int:pk>/<int:rating>', post_views.ratePost),
    # Get comments for a listing
    path('getComments/<int:pk>', post_views.getComments),
    # Post comment to listing
    path('addComment/<int:pk>', post_views.addComment),

    # Create a new user
    path('newUser/', user_views.createUser),
    # Delete an existing user
    path('deleteUser/', user_views.deleteUser),
    # Toggle a listing in a users favourites list
    path('toggleFavourite/<int:pk>', user_views.toggle_favourite),
    # Get a users favourited posts
    path('getFavourites/', user_views.get_favourites),
    # Get settings for logged user
    path('getSettings', user_views.getUserSettings),
    # Modify settings for logged user
    path('updateSettings', user_views.updateUserSettings),

    # JWT token urls for issuing and refreshing a token
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # View a sellers info
    path('getSeller/<str:pk>', user_views.getSeller),
    # Rate the seller
    path('rateSeller/<str:pk>/<int:rating>', user_views.rateSeller),
    # Get the current rating for all sellers
    path('getAllSellerRatings/', user_views.getAllSellerRatings),
    # GEt the current rating for a selected seller
    path('getSellerRating/<str:pk>', user_views.getSellerRating),

    # Create verification PIN
    path('createPin/', user_views.createPin),
    # Verify PIN received in email
    path('verifyPin/<int:pk>', user_views.verifyPin),

    # Create password reset Mail
    path('createReset/', user_views.createReset),
    path('checkReset/<str:reset_code>', user_views.checkReset),
    path('resetPassword/<str:reset_code>', user_views.resetPassword),

    # Start a conversation with another user
    path('newConversation/<str:pk>', messaging_views.createConversation),
    # Get all conversations for the logged user
    path('getConversations/', messaging_views.getConversations),
    # Get messages for the selected conversation
    path('getMessages/<int:pk>', messaging_views.getMessages),
    # Post a new message to the selected conversation
    path('addMessage/<int:pk>', messaging_views.addMessage),
]






