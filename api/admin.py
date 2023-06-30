from django.contrib import admin

# Register your models here.

from .models import Post, UserExtra, Comment, Conversation, Message, Rating, SellerRating, Pin

admin.site.register(Post)
admin.site.register(UserExtra)
admin.site.register(Comment)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Rating)
admin.site.register(SellerRating)
admin.site.register(Pin)
