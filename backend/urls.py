from django.contrib import admin
from django.shortcuts import render
from django.urls import path, include


def home(request):
    """Render the main Smart Task Analyzer UI."""
    return render(request, 'index.html')


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/tasks/', include('tasks.urls')),
]
