from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_targets, name='predict_targets'),
]
