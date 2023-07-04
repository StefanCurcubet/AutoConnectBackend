import math

from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Post(models.Model):
    title = models.TextField(null=True, blank=True)
    imageUrl = models.TextField(null=True, blank=True)
    brand = models.TextField(null=True, blank=True)
    modelYear = models.IntegerField()
    mileage = models.IntegerField()
    price = models.IntegerField()
    current_rating = models.IntegerField(default=0)
    author = models.TextField(null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True)

    def calculate_current_rating(self):
        total_rating = 0
        nr_ratings = 0
        try:
            ratings = self.ratings.all()
            for rating in ratings:
                total_rating += rating.rating
                nr_ratings += 1
            self.current_rating = math.ceil(total_rating / nr_ratings)
        except ValueError:
            return

    def save(self, *args, **kwargs):
        self.calculate_current_rating()
        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class Rating(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField()
    rated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rated_posts')

    def __str__(self):
        return f'{self.post} by {self.rated_by}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.TextField(null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment on {self.post.title} by {self.author}'


class UserExtra(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    favourited_posts = models.CharField(max_length=1000, null=True, blank=True)
    current_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    nr_ratings = models.IntegerField(default=0)
    email_confirmed = models.BooleanField(default=False)
    notify_by_mail_message = models.BooleanField(default=False)
    notify_by_mail_comment = models.BooleanField(default=False)

    def toggle_favourite(self, post_id):
        if str(post_id) not in self.favourited_posts.split(','):
            self.favourited_posts += ',' + str(post_id)
            self.save()

        elif str(post_id) in self.favourited_posts.split(','):
            favourites = self.favourited_posts.split(',')
            favourites.remove(str(post_id))
            self.favourited_posts = ','.join(favourites)
            self.save()

    def calculate_current_rating(self):
        total_rating = 0
        nr_ratings = 0
        try:
            ratings = self.ratings.all()
            for rating in ratings:
                total_rating += rating.rating
                nr_ratings += 1

            if nr_ratings != 0:
                self.current_rating = total_rating / nr_ratings
                self.nr_ratings = nr_ratings
        except ValueError:
            return

    def save(self, *args, **kwargs):
        self.calculate_current_rating()
        super(UserExtra, self).save(*args, **kwargs)


class SellerRating(models.Model):
    seller = models.ForeignKey(UserExtra, on_delete=models.CASCADE, related_name='ratings')
    rating = models.FloatField(default=0)
    rated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rated_sellers')


class Conversation(models.Model):
    users = models.ManyToManyField(User, related_name='conversations')
    update_from = models.TextField()

    def __str__(self):
        user_list = list(self.users.all())
        return f"Conversation between {user_list}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(null=True, blank=True, max_length=25)
    content = models.TextField(blank=True)
    added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender} : {self.content}'


class Pin(models.Model):
    user = models.ForeignKey(UserExtra, on_delete=models.CASCADE, related_name='pins')
    code = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.user.username


class PasswordReset(models.Model):
    user = models.CharField(null=True, blank=True, max_length=25)
    code = models.CharField(null=True, blank=True, max_length=25)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user

