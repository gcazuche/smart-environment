"""Same-origin endpoints. All mutations also pass Django CSRF middleware."""

from django.urls import path

from app.web import video

app_name = "video"
urlpatterns = [
    path("cameras/", video.cameras, name="cameras"),
    path("health/", video.health, name="health"),
    path("local-cameras/", video.local_cameras, name="local-cameras"),
    path("cameras/<uuid:camera_id>/whep/", video.connect, name="connect"),
    path("cameras/<uuid:camera_id>/whep/<uuid:session_id>/", video.disconnect, name="disconnect"),
    path(
        "cameras/<uuid:camera_id>/whep/<uuid:session_id>/keepalive/",
        video.keepalive,
        name="keepalive",
    ),
    path("cameras/<uuid:camera_id>/local-frame/", video.local_frame, name="local-frame"),
]
