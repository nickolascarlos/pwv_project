from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

app_name = 'app_menu'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('menu/', views.menu, name='menu')
]