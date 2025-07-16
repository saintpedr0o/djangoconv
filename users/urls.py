from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from users import views
from .forms import EmailOrUsernameAuthenticationForm

app_name = "users"

urlpatterns = [
    path("register/", views.RegisterUserView.as_view(), name="register"),
    path(
        "login/",
        LoginView.as_view(
            template_name="users/login.html",
            authentication_form=EmailOrUsernameAuthenticationForm,
        ),
        name="login",
    ),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
