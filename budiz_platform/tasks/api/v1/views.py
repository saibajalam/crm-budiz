from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from common.swagger import workspace_header

from workspaces.utils import get_user_workspace
from tasks.models import Task
from tasks.permissions import TaskAccessPermission, TaskManagePermission
from .serializers import TaskSerializer


class TaskListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, TaskAccessPermission]

    @extend_schema(
        responses={200: TaskSerializer(many=True)},
        description="List all tasks in the workspace",
        tags=["Tasks"],
        auth=[{"jwtAuth": []}],
        parameters=[
            workspace_header,
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
    )
    def get(self, request):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {"detail": "Workspace not found"},
                status=status.HTTP_403_FORBIDDEN,
            )
        tasks = Task.objects.filter(workspace=workspace).order_by("-created_at")
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=TaskSerializer,
        responses={201: TaskSerializer},
        description="Create a new task",
        tags=["Tasks"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def post(self, request):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return Response(
                {"detail": "Workspace not found"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = TaskSerializer(
            data=request.data,
            context={"workspace": workspace, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


class TaskDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, TaskAccessPermission]

    def get_object(self, request, task_id):
        workspace = get_user_workspace(request.user)
        if not workspace:
            return None
        task = get_object_or_404(Task, id=task_id, workspace=workspace)
        self.check_object_permissions(request, task)

        return task

    @extend_schema(
        responses={200: TaskSerializer},
        description="Retrieve a specific task",
        tags=["Tasks"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def get(self, request, task_id):
        task = self.get_object(request, task_id)
        if not task:
            return Response(
                {"detail": "Workspace not found"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(TaskSerializer(task).data)

    @extend_schema(
        request=TaskSerializer,
        responses={200: TaskSerializer},
        description="Partially update a task",
        tags=["Tasks"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def patch(self, request, task_id):
        task = self.get_object(request, task_id)
        if not task:
            return Response(
                {"detail": "Workspace not found"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not TaskManagePermission().has_object_permission(request, self, task):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        return Response(TaskSerializer(task).data)

    @extend_schema(
        responses={204: OpenApiResponse(description="Task deleted")},
        description="Delete a task",
        tags=["Tasks"],
        auth=[{"jwtAuth": []}],
        parameters=[workspace_header],
    )
    def delete(self, request, task_id):
        task = self.get_object(request, task_id)
        if not task:
            return Response(
                {"detail": "Workspace not found"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not TaskManagePermission().has_object_permission(request, self, task):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN,
            )
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
