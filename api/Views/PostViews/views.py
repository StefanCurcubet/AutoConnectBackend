from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.models import Post, Comment, Rating
from api.serializers import PostSerializer, CommentSerializer


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
