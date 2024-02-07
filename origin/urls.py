from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserLoginView),
    path('register/', views.UserRegistrationView),
    path('sales_preview/', views.SalesPreView),
    path('sales_preview/product/<int:company_id>/', views.SalesPreView),
    path('sales_add/', views.SalesAddView),
    path('sales_add/product/<int:company_id>/', views.ProductSelectionView, name='sales_product'),
    path('sales_add/detail/<int:company_id>/', views.SalesInfoView, name='sales_detail'),
    path('sales_add/detail/status/<int:company_id>', views.SalesStatus, name='sales_status')

]
