from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect
from .forms import *
from django.http import Http404
from .models import Movie, Myrating, MyList
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Case, When
import pandas as pd

# Create your views here.

def index(request):
    movies = Movie.objects.all()
    query = request.GET.get('q')

    if query:
        movies = Movie.objects.filter(Q(title__icontains=query)).distinct()
        return render(request, 'recommend/list.html', {'movies': movies})

    return render(request, 'recommend/list.html', {'movies': movies})


# Show details of the movie
def detail(request, movie_id):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404
    movies = get_object_or_404(Movie, id=movie_id)
    movie = Movie.objects.get(id=movie_id)
    
    temp = list(MyList.objects.all().values().filter(movie_id=movie_id,user=request.user))
    if temp:
        update = temp[0]['watch']
    else:
        update = False
    if request.method == "POST":

        # For my list
        if 'watch' in request.POST:
            watch_flag = request.POST['watch']
            if watch_flag == 'on':
                update = True
            else:
                update = False
            if MyList.objects.all().values().filter(movie_id=movie_id,user=request.user):
                MyList.objects.all().values().filter(movie_id=movie_id,user=request.user).update(watch=update)
            else:
                q=MyList(user=request.user,movie=movie,watch=update)
                q.save()
            if update:
                messages.success(request, "Movie added to your list!")
            else:
                messages.success(request, "Movie removed from your list!")

            
        # For rating
        else:
            rate = request.POST['rating']
            if Myrating.objects.all().values().filter(movie_id=movie_id,user=request.user):
                Myrating.objects.all().values().filter(movie_id=movie_id,user=request.user).update(rating=rate)
            else:
                q=Myrating(user=request.user,movie=movie,rating=rate)
                q.save()

            messages.success(request, "Rating has been submitted!")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    out = list(Myrating.objects.filter(user=request.user.id).values())

    # To display ratings in the movie detail page
    movie_rating = 0
    rate_flag = False
    for each in out:
        if each['movie_id'] == movie_id:
            movie_rating = each['rating']
            rate_flag = True
            break

    context = {'movies': movies,'movie_rating':movie_rating,'rate_flag':rate_flag,'update':update}
    return render(request, 'recommend/detail.html', context)


# MyList functionality
def watch(request):

    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404

    movies = Movie.objects.filter(mylist__watch=True,mylist__user=request.user)
    query = request.GET.get('q')

    if query:
        movies = Movie.objects.filter(Q(title__icontains=query)).distinct()
        return render(request, 'recommend/watch.html', {'movies': movies})

    return render(request, 'recommend/watch.html', {'movies': movies})


# To get similar movies based on user rating
def get_similar(movie_name,rating,corrMatrix):
    similar_ratings = corrMatrix[movie_name]*(rating-2.5)
    similar_ratings = similar_ratings.sort_values(ascending=False)
    return similar_ratings

# Recommendation Algorithm
def recommend(request):

    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404


    movie_rating=pd.DataFrame(list(Myrating.objects.all().values()))

    new_user=movie_rating.user_id.unique().shape[0]
    current_user_id= request.user.id
	# if new user not rated any movie
    if current_user_id>new_user:
        movie=Movie.objects.get(id=19)
        q=Myrating(user=request.user,movie=movie,rating=0)
        q.save()


    userRatings = movie_rating.pivot_table(index=['user_id'],columns=['movie_id'],values='rating')
    userRatings = userRatings.fillna(0,axis=1)
    corrMatrix = userRatings.corr(method='pearson')

    user = pd.DataFrame(list(Myrating.objects.filter(user=request.user).values())).drop(['user_id','id'],axis=1)
    user_filtered = [tuple(x) for x in user.values]
    movie_id_watched = [each[0] for each in user_filtered]

    similar_movies = pd.DataFrame()
    for movie,rating in user_filtered:
        similar_movies = similar_movies.append(get_similar(movie,rating,corrMatrix),ignore_index = True)

    movies_id = list(similar_movies.sum().sort_values(ascending=False).index)
    movies_id_recommend = [each for each in movies_id if each not in movie_id_watched]
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(movies_id_recommend)])
    movie_list=list(Movie.objects.filter(id__in = movies_id_recommend).order_by(preserved)[:10])

    context = {'movie_list': movie_list}
    return render(request, 'recommend/recommend.html', context)


# Register user
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import UserForm

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import UserForm

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import UserForm

def signUp(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            user.set_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                return redirect("login")  # Redirect to the login page after successful registration
    else:
        form = UserForm()

    context = {'form': form}
    return render(request, 'recommend/signUp.html', context)





# Login User
def Login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect("index")
            else:
                return render(request, 'recommend/login.html', {'error_message': 'Your account disable'})
        else:
            return render(request, 'recommend/login.html', {'error_message': 'Invalid Login'})

    return render(request, 'recommend/login.html')


# Logout user
def Logout(request):
    logout(request)
    return redirect("login")

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required  # Use this decorator to ensure the user is authenticated to access the dashboard
def dashboard(request):
    # Your logic for the dashboard view goes here
    # You can retrieve data, perform calculations, etc.
    # Then pass the necessary data to the template and render it
    context = {
        # Add any context data you want to pass to the template here
    }
    return render(request, 'recommend/dashboard.html', context)
from django.shortcuts import render

def feedback_view(request):
    # Your logic for handling feedback goes here
    # For now, let's just render a template named 'feedback.html'
    return render(request, 'recommend/feedback.html')

def about_view(request):

    return render(request, 'recommend/about.html')


from django.shortcuts import render, redirect
from .forms import FeedbackForm

def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('dashboard')  # Redirect to dashboard after successful submission
    else:
        form = FeedbackForm()
    return render(request, 'recommend/feedback.html', {'form': form})

from django.shortcuts import render

# Other views...

def about(request):
    # You can add context data if needed
    context = {
        'team_members': [
            {'name': 'Alice', 'role': 'Project Manager'},
            {'name': 'Bob', 'role': 'Lead Developer'},
            {'name': 'Charlie', 'role': 'UI/UX Designer'},
            # ... other team members ...
        ],
        'testimonials': [
            {'text': 'This recommendation system has changed the way I discover movies. It\'s like having a personal movie curator!', 'author': 'Jane Doe'},
            {'text': 'I\'ve found so many hidden gems thanks to this platform. Highly recommend it to any movie lover!', 'author': 'John Smith'},
            # ... other testimonials ...
        ]
    }
    # Render the "About Us" page with the context data
    return render(request, 'about.html', context)

# Other views...
