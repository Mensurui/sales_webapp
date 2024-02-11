from django.shortcuts import get_list_or_404, redirect, render
from django.http import HttpResponse

from origin.models import Company, Product, ProductStatus, SalesProcess
from .forms import DetailRegistrationForm, ProductSelectionForm, ProductStatusUpdateForm, UserRegistrationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import CompanyRegistrationForm
from django.core.paginator import Paginator
from django.contrib.auth.models import User
# Create your views here.
def UserRegistrationView(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('')
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
    companies_all = Company.objects.all()
    user = request.user
    users_list = User.objects.all()
    print(f"Users list {users_list}")
    if user.is_superuser:  # Corrected usage of is_superuser
        paginator = Paginator(companies_all, 8)
        pagenumber = request.GET.get("page")
        page_obj = paginator.get_page(pagenumber)
    else:
        paginator = Paginator(companies, 8)
        pagenumber = request.GET.get("page")
        page_obj = paginator.get_page(pagenumber)
    # Extract the IDs of the companies
    company_ids = [company.id for company in companies]
    # Print company IDs for debugging
    print(f"Company IDs: {company_ids}")
    # Retrieve sales processes related to these companies
    interesting = SalesProcess.objects.filter(company_id__in=company_ids)
    interesting_all = SalesProcess.objects.all()
    # Retrieve product statuses related to these companies
    statuses = ProductStatus.objects.filter(company_id__in=company_ids)
    statuses_all = ProductStatus.objects.all
    # Extract the IDs of the statuses
    status_ids = [status.id for status in statuses]
    # Print sales processes, product statuses, and status IDs for debugging
    print(f"Interests: {interesting}")
    print(f"Statuses: {statuses}")
    print(f"Status IDs: {status_ids}")
    # Pass the companies, sales processes, and statuses to the template
    return render(request, 'sales_preview.html', {'data': companies, 'interests': interesting, 'statuses': statuses, 'status_ids': status_ids, 'companies_all': companies_all, 'interesting_all':interesting_all, 'statuses_all':statuses_all, "page_obj": page_obj, 'users':users_list})
from django.urls import reverse

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
            return redirect(reverse('sales_detail', kwargs={'company_id': company_id}))
    else:
        form = ProductSelectionForm()
    
    return render(request, 'select_product.html', {'form': form, 'company_id': company_id})


@login_required
def SalesInfoView(request, company_id):
    if request.method == 'POST':
        form = DetailRegistrationForm(request.POST)
        if form.is_valid():
            detail = form.save(commit=False)
            detail.company_id = company_id 
            detail.save()
            return redirect(reverse('sales_status', kwargs={'company_id': detail.company_id}))
    else:
        form = DetailRegistrationForm()
        
    return render(request, 'add_detail.html', {'form': form})

@login_required
def SalesStatus(request, company_id):
    statuses = ProductStatus.objects.filter(company_id=company_id)
    return render(request, 'sales_status.html', {'statuses':statuses})

from django.http import JsonResponse

@login_required
def SalesStatusUpdate(request, status_id):
    statuses = get_list_or_404(ProductStatus, id=status_id)
    # print(f"Status: {statuses.company_id}")
    stat = ProductStatus.objects.filter(id= status_id)
    print(f"Status: {stat}")
    if request.method == 'POST':
        form = ProductStatusUpdateForm(request.POST)
        if form.is_valid():
            updated_status = form.cleaned_data['updated_status']
            for status in statuses:
                status.status = updated_status
                status.save()
            return redirect('/sales_preview')
    else:
        form = ProductStatusUpdateForm()
    return render(request, 'sales_status.html', {'statuses': statuses, 'form': form})