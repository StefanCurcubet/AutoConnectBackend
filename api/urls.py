from django.urls import path
from . import views
from .views import MyTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenRefreshView
)


urlpatterns = [
    # Get all listings
    path('getAllPosts/<str:order>', views.getAllPosts),
    # Create a new listing
    path('newListing/', views.createPost),
    # Delete a listing
    path('deleteListing/<int:pk>', views.deletePost),
    # View a listing
    path('getListing/<int:pk>', views.viewPost),
    # Rate a listing
    path('rateListing/<int:pk>/<int:rating>', views.ratePost),
    # Get comments for a listing
    path('getComments/<int:pk>', views.getComments),
    # Post comment to listing
    path('addComment/<int:pk>', views.addComment),

    # Create a new user
    path('newUser/', views.createUser),
    # Delete an existing user
    path('deleteUser/', views.deleteUser),
    # Toggle a listing in a users favourites list
    path('toggleFavourite/<int:pk>', views.toggle_favourite),
    # Get a users favourited posts
    path('getFavourites/', views.get_favourites),
    # Get settings for logged user
    path('getSettings', views.getUserSettings),
    # Modify settings for logged user
    path('updateSettings', views.updateUserSettings),

    # JWT token urls for issuing and refreshing a token
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Start a conversation with another user
    path('newConversation/<str:pk>', views.createConversation),
    # Get all conversations for the logged user
    path('getConversations/', views.getConversations),
    # Get messages for the selected conversation
    path('getMessages/<int:pk>', views.getMessages),
    # Post a new message to the selected conversation
    path('addMessage/<int:pk>', views.addMessage),

    # View a sellers info
    path('getSeller/<str:pk>', views.getSeller),
    # Rate the seller
    path('rateSeller/<str:pk>/<int:rating>', views.rateSeller),
    # Get the current rating for all sellers
    path('getAllSellerRatings/', views.getAllSellerRatings),
    # GEt the current rating for a selected seller
    path('getSellerRating/<str:pk>', views.getSellerRating),

    # Create verification PIN
    path('createPin/', views.createPin),
    # Verify PIN received in email
    path('verifyPin/<int:pk>', views.verifyPin),

    # Create password reset Mail
    path('createReset/', views.createReset),
    path('checkReset/<str:reset_code>', views.checkReset),
    path('resetPassword/<str:reset_code>', views.resetPassword),
]






