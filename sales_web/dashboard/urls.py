from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forecast/', views.forecast_view, name='forecast'),
    path('forecast/pdf/', views.forecast_pdf_view, name='forecast_pdf'),
    path('api/forecast/', views.api_forecast, name='api_forecast'),
    path('eda/', views.eda_view, name='eda'),
    path('models/', views.models_view, name='models'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('insights/', views.insights_view, name='insights'),
]
