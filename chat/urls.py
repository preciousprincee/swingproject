from django.urls import path
from . import views 
urlpatterns = [
    path ('', views.home, name='home'),
    path ('settings/', views.settings, name='settings'),
    path ('login/', views.login, name='login'),
    path ('logout/', views.logout, name='logout'), 
    path ('upload/', views.upload, name='upload'),
    path ('profile/<str:username>', views.profile, name='profile'),
    path('messageroom', views.messageroom, name='messageroom'),
    path('register/', views.register, name='register'),
    path('follow/<str:username>/', views.follow, name='follow'),
    path('like-post/', views.like_post, name='like_post'),
    path('search/', views.search, name='search'),
    path('send/', views.send, name='send'),
    path('getMessages', views.getMessages, name='getMessages'),
    path('compose_message', views.compose_message, name='compose_message'),
    path('post/', views.upload_post, name='upload_post'),
    path('notifications/', views.notifications, name='notifications'),
    ]