from django.urls import path
from .views import KeywordView, ScanView, FlagListView, FlagDetailView

urlpatterns = [
    path('keywords/', KeywordView.as_view()),
    path('scan/', ScanView.as_view()),
    path('flags/', FlagListView.as_view()),
    path('flags/<int:pk>/', FlagDetailView.as_view()),
]
from django.urls import path
from .views import KeywordView, ScanView, FlagListView, FlagDetailView, LoginPageView

urlpatterns = [
    path('keywords/', KeywordView.as_view()),
    path('scan/', ScanView.as_view()),
    path('flags/', FlagListView.as_view()),
    path('flags/<int:pk>/', FlagDetailView.as_view()),
    path('login/', LoginPageView.as_view()),
]