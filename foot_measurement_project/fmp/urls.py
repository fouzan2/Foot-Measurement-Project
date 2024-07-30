from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_page, name='upload_page'),
    path('measure_foot/', views.measure_foot, name='measure_foot'),
    path('results/', views.results, name='results'),
]