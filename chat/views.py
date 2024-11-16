from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from itertools import chain
from .models import Profile, Post, LikePost, FollowersCount, Message, Notification
import random
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login
from django.db.models import Count, Q


# Create your views here.


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
             if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('register')
             elif User.objects.filter(username=username).exists():
                 messages.info(request, 'Username already used')
                 return redirect('register')
             else:
                 user = User.objects.create_user(username=username, email=email, password=password)
                 user.save()
                 user_login = auth.authenticate(username=username, password=password)
                 auth.login = (request, user_login)

                 user_model = User.objects.get(username=username)
                 new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                 new_profile.save()
                 return redirect('settings') 

         
            
        else:
            messages.info(request, 'Password not the same')
            return redirect('register')
    else:
        return render(request,'sign-up.html')
                

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)  # Correct login method to use
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')  # Use error message for failed login
            return redirect('login')

    else:
        return render(request, 'sign-in.html')

    return redirect('login')  

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login') 

@login_required(login_url='login')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        # Check if the image is being uploaded
        if request.FILES.get('image') is None:
            # If no image, retain the current profile image and update bio and location
            image = user_profile.profileimg
            bio = request.POST['bio']
            location = request.POST['location']
            
            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        
        if request.FILES.get('image') is not None:
            # If image is being uploaded, update the profile with the new image
            image = request.FILES.get('image')
            bio = request.POST['bio']
            location = request.POST['location']
            
            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        
        # Redirect back to the home page after saving changes
        return redirect('home')

    return render(request, 'setting.html', {'user_profile': user_profile})
@login_required(login_url='login')
def upload(request):



    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()
        return redirect('/home')
    else:
        return redirect('/home')
    return render(request, '<h1>Upload View</h1>')

@login_required(login_url='login')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    try:
        post = Post.objects.get(id=post_id)

        # Check if the user has already liked the post
        like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

        if like_filter is None:
            # Add a like
            LikePost.objects.create(post_id=post_id, username=username)
            post.no_of_likes += 1
            post.save()
            liked = True
        else:
            # Remove a like
            like_filter.delete()
            post.no_of_likes -= 1
            post.save()
            liked = False

        # Return the updated like count and the liked status as JSON
        return JsonResponse({'liked': liked, 'like_count': post.no_of_likes})

    except Post.DoesNotExist:
        return JsonResponse({'error': 'Post not found'}, status=404)



@login_required(login_url='login')
def notifications(request):
    # Assuming you're using a model 'Notification' to store notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')  # Sort by date, newest first
    
    context = {
        'notifications': notifications
    }
    
    return render(request, 'notifications.html', context)




@login_required
def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=request.user)

    username_profile_list = []  # Define a default value here

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []

        for users in username_object:
            username_profile.append(users.id)

        for ids in username_profile:
            profile_lists = Profile.objects.filter(user_id=ids)

            username_profile_list.append(profile_lists)
        
        username_profile_list = list(chain(*username_profile_list))
    
    return render(request, 'search.html', {'user_profile': user_profile, 'username_profile_list': username_profile_list})

    




@login_required(login_url='login')
def home(request):
    user_object = request.user
    
    # Ensure user profile exists
    user_profile, created = Profile.objects.get_or_create(user=user_object)

    # Get user posts and count
    user_posts = Post.objects.filter(user=user_object)
    user_post_length = user_posts.count()  # Use count() instead of len()

    # Get users the current user follows
    user_following = FollowersCount.objects.filter(follower=request.user)
    user_following_list = [user.user for user in user_following]

    # Get all users except the current user and the users they follow
    all_users = User.objects.exclude(username=request.user.username).exclude(username__in=user_following_list)
    if all_users.exists():
        final_suggestions_list = list(all_users)
        random.shuffle(final_suggestions_list)
    else:
        final_suggestions_list = []

    # Fetch profiles for suggestions
    suggestions_username_profile_list = []
    for user in final_suggestions_list[:10]:
        try:
            profile = Profile.objects.get(user=user)
            suggestions_username_profile_list.append(profile)
        except Profile.DoesNotExist:
            continue  # Skip if profile doesn't exist

    # Fetch posts from users the current user follows
    feed_list = Post.objects.filter(user__in=user_following_list)

    # Check if the user is following the profile user
    button_text = 'Unfollow' if FollowersCount.objects.filter(follower=request.user, user=user_object).exists() else 'Follow'

    # User follower and following counts
    user_followers = FollowersCount.objects.filter(user=user_object).count()
    user_following_count = FollowersCount.objects.filter(follower=user_object).count()

    # Context for the template
    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_post_length,
        'posts': feed_list,
        'user_following': user_following_count,
        'user_followers': user_followers,
        'suggestions_username_profile_list': suggestions_username_profile_list,
        'button_text': button_text
    }

    return render(request, 'home.html', context)

@login_required(login_url='login')
def upload_post(request):
    if request.method == 'POST':
        # Handle the form submission
        image = request.FILES.get('image')  # Get the uploaded image
        caption = request.POST.get('caption')  # Get the caption
        
        if image and caption:  # Check if both fields are provided
            # Create a new post instance and assign user, image, and caption
            new_post = Post(user=request.user, image=image, caption=caption)
            new_post.save()  # Save the post to the database
            
            return redirect('/post')
    
    return render(request, 'upload_post.html')  # Render the upload page with the form



@login_required(login_url='login')
def profile(request, username):
    # Get the user object and profile, or return 404 if not found
    user_object = get_object_or_404(User, username=username)
    user_profile = get_object_or_404(Profile, user=user_object)

    # Fetch user-specific posts and optimize queries
    user_posts = Post.objects.filter(user=user_object).select_related('user')  # Using select_related for optimization

    # Check if the logged-in user is following the profile user
    follower = request.user  # Current logged-in user
    is_following = FollowersCount.objects.filter(follower=follower, user=user_object).exists()
    button_text = 'Unfollow' if is_following else 'Follow'

    # Aggregate followers and following counts
    followers_data = FollowersCount.objects.filter(user=user_object).aggregate(
        followers=Count('follower'),  # Count followers for the user
        following=Count('id', filter=Q(follower=user_object))  # Count users the profile follows
    )
    user_followers = followers_data['followers'] or 0  # Handle None values
    user_following = followers_data['following'] or 0

    # Prepare context for the template
    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'user_post_length': user_posts.count(),  # Use .count() on QuerySets instead of len()
        'button_text': button_text,
        'user_followers': user_followers,
        'user_following': user_following,
    }

    # Render the profile page with the context
    return render(request, 'profile.html', context)

@login_required(login_url='login')
def follow(request, username):
    try:
        # Ensure the user to follow/unfollow exists
        user_to_follow = get_object_or_404(User, username=username)
        follower = request.user  # The logged-in user is the follower

        # Toggle follow/unfollow
        follow_relationship = FollowersCount.objects.filter(follower=follower, user=user_to_follow)
        if follow_relationship.exists():
            # Unfollow the user
            follow_relationship.delete()
            messages.success(request, f"You have unfollowed {user_to_follow.username}.")
        else:
            # Follow the user
            FollowersCount.objects.create(follower=follower, user=user_to_follow)
            messages.success(request, f"You are now following {user_to_follow.username}.")

        # Redirect back to the profile page
        return redirect('profile', username=username)

    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}")
        return redirect('profile', username=username)

        




# def send(request):
#     message = request.POST['message']
#     username = request.POST['username']
#     room_id = request.POST['room_id']

#     new_message = Message.objects.create(sender=sender, receiver=receiver, content=message_content)
#     new_message.save()
#     return HttpResponse('Message sent successfully')

def send(request):
    message_content = request.POST['message']
    receiver_username = request.POST['username']
    sender = request.user  # Assuming the sender is the logged-in user

    # Retrieve the receiver user object
    receiver = get_object_or_404(User, username=receiver_username)

    if message_content:
        # Create and save the message
        message = Message.objects.create(sender=sender, receiver=receiver, content=message_content)
        message.save()
        return HttpResponse('Message sent successfully')
    else:
        return HttpResponse('Message content cannot be empty')



def messageroom(request):
    return render(request, 'message-room.html')



def getMessages(request):
    messages = Message.objects.filter(receiver=request.user)

    return render(request, 'message-room.html', {'messages': messages})

def compose_message(request):
    if request.method == 'POST':
        username = request.POST.get('receiver')  # Get the receiver's username from the form
        receiver = get_object_or_404(User, username=username)
        content = request.POST.get('content')

        if content:
            # Create and save the message
            message = Message.objects.create(sender=request.user, receiver=receiver, content=content)
            message.save()
            return redirect('getMessages')  

    return render(request, 'message-room.html')

