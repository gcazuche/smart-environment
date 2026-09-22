"""Dashboard routes included by the web namespace."""

from django.urls import path

from app.web import dashboard_views as views

urlpatterns = [
    path("dashboard/", views.overview, name="overview"),
    path("cameras/", views.cameras, name="cameras"),
    path("cameras/new/", views.edit_camera, name="camera_new"),
    path("cameras/<uuid:camera_id>/", views.camera_detail, name="camera_detail"),
    path("cameras/<uuid:camera_id>/edit/", views.edit_camera, name="camera_edit"),
    path("environments/", views.environments, name="environments"),
    path("environments/new/", views.edit_environment, name="environment_new"),
    path(
        "environments/<uuid:environment_id>/", views.environment_detail, name="environment_detail"
    ),
    path(
        "environments/<uuid:environment_id>/edit/", views.edit_environment, name="environment_edit"
    ),
    path("indicators/", views.indicators, name="indicators"),
    path("alerts/", views.alerts, name="alerts"),
    path("alerts/<uuid:alert_id>/review/", views.review_alert, name="alert_review"),
    path("history/", views.history, name="history"),
    path("rules/", views.rules, name="rules"),
    path("rules/new/", views.edit_rule, name="rule_new"),
    path("rules/<uuid:rule_id>/edit/", views.edit_rule, name="rule_edit"),
    path("profile/", views.profile, name="profile"),
]
