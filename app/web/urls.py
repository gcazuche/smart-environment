"""Only public, non-operational routes exist during DJ-01."""

from django.urls import include, path

from app.web import dashboard_urls, views

web_patterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("health/", views.health, name="health"),
    path("api/processing/", include("app.web.video_urls")),
] + dashboard_urls.urlpatterns
urlpatterns = [path("", include((web_patterns, "web"), namespace="web"))]
