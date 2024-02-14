from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserLoginView, name='login'),
    path('register/', views.UserRegistrationView),
    path('sales_preview/', views.SalesPreView, name='sales_preview'),
    path('sales_preview_closed/', views.SalesPreViewClosed),
    path('sales_preview/product/<int:company_id>/', views.SalesPreView),
    path('sales_add/', views.SalesAddView),
    path('sales_add/product/<int:company_id>/', views.ProductSelectionView, name='sales_product'),
    path('sales_add/detail/<int:company_id>/<str:status>/<int:product_id>', views.SalesInfoView, name='sales_detail'),
    path('sales_add/detail/status/<int:company_id>', views.SalesStatus, name='sales_status'),
    path('sales_preview/status/<int:status_id>', views.SalesStatusUpdate, name='sales_status_update'),
    path('sales_confirmed/', views.Close_View),
    path('interest/', views.ProductInterestRateChart),
    path('salesperformancechart/', views.SalesPerformanceChart)
]
