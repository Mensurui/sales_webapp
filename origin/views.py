from django.shortcuts import redirect, render
from django.http import HttpResponse

from origin.models import Company, Product, ProductStatus, SalesProcess
from .forms import DetailRegistrationForm, ProductSelectionForm, UserRegistrationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import CompanyRegistrationForm
# Create your views here.
def UserRegistrationView(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/home')
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
            return redirect('/home/sales_preview')
        else:
            error_message = "Invalid username or password. Please try again."
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')
    
    
@login_required
def SalesPreView(request):
    companies = Company.objects.filter(user=request.user)
    company_ids = [company.id for company in companies]
    print(f"Company IDs: {company_ids}")

    interesting = SalesProcess.objects.filter(company_id__in=company_ids)
    print(f"Interests: {interesting}")

    data = companies  # Use the queryset directly
    interest = interesting

    print(f"Companies: {data}")
    print(f"Interests: {interest}")

    return render(request, 'sales_preview.html', {'data': data, 'interests': interest})
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
    print(f"Company ID: {company_id}")
    return HttpResponse("eheol")