from django.urls import path
from .views import TaskListCreateAPIView, TaskDetailAPIView

urlpatterns = [
    path("tasks/", TaskListCreateAPIView.as_view(), name="task_list_create"),
    path("tasks/<int:task_id>/", TaskDetailAPIView.as_view(), name="task_detail"),
]

app_name = "tasks"
