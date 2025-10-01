from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('add/', views.add_task, name='add_task'),
    path('<int:pk>/edit/', views.edit_task, name='edit_task'),
    path('<int:pk>/delete/', views.delete_task, name='delete_task'),
    path('<int:pk>/toggle/', views.toggle_complete, name='toggle_complete'),
]
