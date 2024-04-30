from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signUp, name='signup'),
    path('login/', views.Login, name='login'),
    path('logout/', views.Logout, name='logout'),
    path('<int:movie_id>/', views.detail, name='detail'),
    path('watch/', views.watch, name='watch'),
    path('recommend/', views.recommend, name='recommend'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('Movies/', views.Movie, name='Movies'),
    path('about/', views.about_view, name='about'),

]