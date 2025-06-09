from django.urls import path

from . import views


app_name = 'shortlink'

urlpatterns = [
    path('s/<str:url_hash>/', views.load_url, name='load_url'),
]