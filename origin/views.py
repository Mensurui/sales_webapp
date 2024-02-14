from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render
from django.http import HttpResponse

from origin.models import Company, Product, ProductInterest, ProductStatus, SalesPerformance, SalesProcess
from .forms import DetailRegistrationForm, ProductSelectionForm, ProductStatusUpdateForm, UserRegistrationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import CompanyRegistrationForm
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.urls import reverse

# Create your views here.
def UserRegistrationView(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    else: 
        form = UserRegistrationForm()
    return render(request,'register.html', {'form': form})

def UserLoginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/sales_preview')
        else:
            error_message = "Invalid username or password. Please try again."
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')
    
    
@login_required
def SalesPreView(request):
    # Get the companies associated with the logged-in user
    companies = Company.objects.filter(user=request.user)
    pending = ProductStatus.objects.filter(status="pending")
    pending_statuses = ProductStatus.objects.filter(status="pending")

# Assuming you want to retrieve company IDs related to pending statuses
    company_id_pending = [status.company_id for status in pending_statuses]
    companies_all = Company.objects.filter(id__in=company_id_pending)
    user = request.user
    users_list = User.objects.all()
    # print(f"Users list {users_list}")
    if user.is_superuser:  # Corrected usage of is_superuser
        paginator = Paginator(companies_all,8)
        pagenumber = request.GET.get("page")
        page_obj = paginator.get_page(pagenumber)
    else:
        paginator = Paginator(companies_all,8)
        pagenumber = request.GET.get("page")
        page_obj = paginator.get_page(pagenumber)
    # Extract the IDs of the companies
    company_ids = [company.id for company in companies]
    # Print company IDs for debugging
    # print(f"Company IDs: {company_ids}")
    # Retrieve sales processes related to these companies
    interesting = SalesProcess.objects.filter(company_id__in=company_ids)
    interesting_all = SalesProcess.objects.all()
    # Retrieve product statuses related to these companies
    statuses = ProductStatus.objects.filter(company_id__in=company_ids)
    statuses_all = ProductStatus.objects.all
    # Extract the IDs of the statuses
    status_ids = [status.id for status in statuses]
    # Print sales processes, product statuses, and status IDs for debugging
    # print(f"Interests: {interesting}")
    # print(f"Statuses: {statuses}")
    # print(f"Status IDs: {status_ids}")
    # Pass the companies, sales processes, and statuses to the template
    return render(request, 'sales_preview.html', {'data': companies, 'interests': interesting, 'statuses': statuses, 'status_ids': status_ids, 'companies_all': companies_all, 'interesting_all':interesting_all, 'statuses_all':statuses_all, "page_obj": page_obj, 'users':users_list})


@login_required
def SalesPreViewClosed(request):
    user = request.user
    
    # Filter ProductStatus instances with 'closed' status
    closed_statuses = ProductStatus.objects.filter(status="closed")
    
    # Get the company IDs associated with closed statuses
    company_ids = closed_statuses.values_list('company_id', flat=True)
    
    # Filter companies based on user type
    if user.is_superuser:
        companies_list = Company.objects.filter(id__in=company_ids)
    else:
        companies_list = Company.objects.filter(id__in=company_ids, user_id=user.id)
    
    # Pagination
    paginator = Paginator(companies_list, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'sales_preview_closed.html', {'companies_list': companies_list, "page_obj": page_obj})

@login_required
def SalesAddView(request):
    
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            return redirect(reverse('sales_product', kwargs={'company_id': company.id}))
    else:
        form = CompanyRegistrationForm()
    
    return render(request, 'add_company.html', {'form': form})

@login_required
def ProductSelectionView(request, company_id):
    company = Company.objects.get(id=company_id)

    if request.method == 'POST':
        form = ProductSelectionForm(request.POST)
        if form.is_valid():
            product_id = form.cleaned_data['product'].id  # Access the product id from the selected product
            product_name = form.cleaned_data['product'].product_name  # Access the product name from the selected product
            status = form.cleaned_data['status']
            description = form.cleaned_data['description']
            
            # Save the product status for the company
            product_status = ProductStatus.objects.create(product_id=product_id, company=company, status=status, description=description)
            product_status.save()

            # Redirect to the sales detail view
            return redirect(reverse('sales_detail', kwargs={'company_id': company_id, 'status':status, 'product_id': product_id}))
    else:
        form = ProductSelectionForm()
    
    return render(request, 'select_product.html', {'form': form, 'company_id': company_id})


@login_required
def SalesInfoView(request, company_id, status, product_id):
    if request.method == 'POST':
        form = DetailRegistrationForm(request.POST)
        if form.is_valid():
            interest = form.cleaned_data['interest']
            # Create SalesProcess instance
            sales_process = SalesProcess.objects.create(
                company_id=company_id,
                interest=interest
            )
            # Get the current month and year
            today = timezone.now()
            month = today.month
            year = today.year
            # Try to get the SalesPerformance object for the current month and year
            spr = SalesPerformance.objects.filter(user=request.user).first()
            if not spr:
                # If SalesPerformance object doesn't exist for the current month and year, create it
                spr = SalesPerformance.objects.create(
                    user=request.user,
                    month=0,
                    year=0,
                    closed_deals_count=0  # Set initial value for closed_deals_count
                )
            # Update the closed_deals_count
            if status == 'closed':
                spr.closed_deals_count += 1
                user_id = request.user.id
                user = User.objects.get(id=user_id)
                date_joined = user.date_joined
                today = datetime.now(date_joined.tzinfo)
                difference = today - date_joined
                months_difference = difference.days // 30
                # print(f"Date joined: {date_joined}")
                if difference.days == 30:
                    spr.month = 0
                else:
                    spr.month += 1
                    
                if difference.days == 365:
                    spr.year = 0
                else:
                    spr.year += 1
                interest_av = Decimal(interest)
                product = Product.objects.get(pk=product_id)
                product_interest = ProductInterest.objects.get(product_id=product.id)
                if product_interest:
                    product_interest.count += 1
                    product_interest.average_interest = (product_interest.average_interest+interest_av) // product_interest.count
                    print(f"Okay this is working {product_interest.average_interest}, and {interest_av}")
                    product_interest.save()
                else:
                    ProductInterest.objects.update_or_create(
                    product=product,
                    defaults={'average_interest': interest, 'count': 1}
                    )
                spr.save()
            else:
                interest_av = Decimal(interest)
                product = Product.objects.get(pk=product_id)
                product_interest = ProductInterest.objects.get(product_id=product.id)
                if product_interest:
                    product_interest.count += 1
                    product_interest.average_interest = (product_interest.average_interest+interest_av) // product_interest.count
                    print(f"Okay this is working {product_interest.average_interest}, and {interest_av}")
                    product_interest.save()
                else:
                    ProductInterest.objects.update_or_create(
                    product=product,
                    defaults={'average_interest': interest, 'count': 1}
                    )
                spr.save()

            return redirect(reverse('sales_preview'))
    else:
        form = DetailRegistrationForm()
        
    return render(request, 'add_detail.html', {'form': form})
@login_required
def SalesStatus(request, company_id):
    statuses = ProductStatus.objects.filter(company_id=company_id)
    return render(request, 'sales_status.html', {'statuses':statuses})

from django.http import JsonResponse

# @login_required
# def SalesStatusUpdate(request, status_id):
#     statuses = get_list_or_404(ProductStatus, id=status_id)
#     # print(f"Status: {statuses.company_id}")
#     stat = ProductStatus.objects.filter(id= status_id)
#     # print(f"Status Ohoy: {stat}")
#     if request.method == 'POST':
#         form = ProductStatusUpdateForm(request.POST)
#         if form.is_valid():
#             updated_status = form.cleaned_data['updated_status']
#             for status in statuses:
#                 status.status = updated_status
#                 status.save()
#             return redirect('/sales_preview')
#     else:
#         form = ProductStatusUpdateForm()
#     return render(request, 'sales_status.html', {'statuses': statuses, 'form': form})

@login_required
@login_required
def SalesStatusUpdate(request, status_id):
    # Retrieve the ProductStatus instance
    status = get_object_or_404(ProductStatus, id=status_id)
    user = request.user
    if request.method == 'POST':
        form = ProductStatusUpdateForm(request.POST)
        if form.is_valid():
            updated_status = form.cleaned_data['updated_status']
            if status.status == 'pending' and updated_status == 'closed':
                # Increment the closed_deals_count in SalesPerformance
                today = timezone.now()
                month = today.month
                year = today.year
                sales_performance = SalesPerformance.objects.get(user_id=user.id)
                sales_performance.closed_deals_count += 1
                user_id = request.user.id
                user = User.objects.get(id=user_id)
                date_joined = user.date_joined
                today = datetime.now(date_joined.tzinfo)
                difference = today - date_joined
                months_difference = difference.days // 30
                # print(f"Date joined: {date_joined}")
                if difference.days == 30:
                    sales_performance.month = 0
                else:
                    sales_performance.month += 1
                    
                if difference.days == 365:
                    sales_performance.year = 0
                else:
                    sales_performance.year += 1
                sales_performance.save()
                
            # Update the status
            status.status = updated_status
            status.save()
            return redirect('/sales_preview')
    else:
        form = ProductStatusUpdateForm()
    
    # Pass the status as a list to the template
    statuses = [status]
    return render(request, 'sales_status.html', {'statuses': statuses, 'form': form})


def Close_View(request):
    user = request.user
    company_ids = Company.objects.filter(user=user).values_list('id', flat=True)
    product_items = ProductStatus.objects.filter(company_id__in=company_ids)
    return render(request, 'closed_preview.html', {'product_items': product_items})




'''
from datetime import datetime, timedelta

# Assuming date_joined is a datetime object
date_joined = user.date_joined

# Get today's date
today = datetime.now(date_joined.tzinfo)

# Calculate the difference in days
difference = today - date_joined

# Convert difference to months
months_difference = difference.days // 30

# If the difference is exactly 30 days, reset the month count to zero
if difference.days == 30:
    spr.month = 0
# Otherwise, add the number of months difference to the month count
else:
    spr.month += months_difference

# Save the changes to the spr object
spr.save()
'''