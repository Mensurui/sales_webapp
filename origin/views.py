from datetime import date
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import get_list_or_404, get_object_or_404, redirect, render
from django.http import HttpResponse
import pandas as pd

from origin.models import Company, Product, ProductInterest, ProductStatus, SalesPerformance, SalesProcess, UserWithCompanyCount
from .forms import DetailRegistrationForm, ProductSelectionForm, ProductStatusUpdateForm, UserRegistrationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import CompanyRegistrationForm
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.urls import reverse
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
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
                today = timezone.now()
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
                product = Product.objects.get(id=product_id)
                try:
                    product_interest = ProductInterest.objects.get(product_id=product.id)
                    # Update the existing product interest
                    product_interest.count += 1
                    total_interest = product_interest.average_interest * (product_interest.count - 1)  # Calculate total interest so far
                    total_interest += interest_av  # Add the new interest
                    product_interest.average_interest = total_interest / product_interest.count  # Calculate the new average
                    product_interest.save()
                    print(f"Okay this is working {product_interest.average_interest}, and {interest_av}")
                except ProductInterest.DoesNotExist:
                    # Create a new ProductInterest object if it doesn't exist
                    ProductInterest.objects.create(product=product, average_interest=interest, count=1)
            else:
                interest_av = Decimal(interest)
                product = Product.objects.get(id=product_id)
                try:
                    product_interest = ProductInterest.objects.get(product_id=product.id)
                    # Update the existing product interest
                    product_interest.count += 1
                    total_interest = product_interest.average_interest * (product_interest.count - 1)  # Calculate total interest so far
                    total_interest += interest_av  # Add the new interest
                    product_interest.average_interest = total_interest / product_interest.count  # Calculate the new average
                    product_interest.save()
                    print(f"Okay this second is working {product_interest.average_interest}, and {interest_av}")
                except ProductInterest.DoesNotExist:
                    # Create a new ProductInterest object if it doesn't exist
                    ProductInterest.objects.create(product=product, average_interest=interest, count=1)

            spr.save()
            return redirect(reverse('sales_preview'))
    else:
        form = DetailRegistrationForm()
        
    return render(request, 'add_detail.html', {'form': form})

@login_required
def SalesStatus(request, company_id):
    statuses = ProductStatus.objects.filter(company_id=company_id)
    return render(request, 'sales_status.html', {'statuses':statuses})


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
                today = date.now(date_joined.tzinfo)
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


def ProductInterestRateChart(request):
    product_list = ProductInterest.objects.all()
    name_list=[]
    print(f"Product list {product_list}")
    for product in product_list:
        product_name = Product.objects.filter(id=product.id)
        name_list.append(product_name)
    for i in range(len(name_list)):
        print(name_list[i])
    y = [product.average_interest for product in product_list],
    fig = go.Figure(data=[go.Bar(
       x= [product.product.product_name for product in product_list],
       y = [product.average_interest for product in product_list],
       text="Average Interest",
       textposition='auto',
    )])
    
    chart = fig.to_html()
    
    context = {"chart": chart}
    
    return render(request, 'ProductInterestRateChart.html', context)


def SalesPerformanceChart(request):
    superusers = User.objects.filter(is_superuser=False)
    
    # Calculate the total number of leads generated and closed deals for each superuser
    lead_generated_counts = [Company.objects.filter(user=superuser).count() for superuser in superusers]
    closed_deals_counts = [ProductStatus.objects.filter(company__user=superuser, status='closed').count() for superuser in superusers]

    # Create a DataFrame for Plotly Express
    data = {
        "Salesperson": [superuser.username for superuser in superusers],
        "Lead Generated": lead_generated_counts,
        "Closed Deals": closed_deals_counts
    }
    df = pd.DataFrame(data,)

    # Create the bar chart with Plotly Express
    fig = px.bar(df, x="Salesperson", y=["Lead Generated", "Closed Deals"],
                 title="Sales Performance Chart", barmode="group")

    # Customize the layout
    fig.update_layout(
        yaxis=dict(title="Count"),
    )

    # Convert the figure to HTML
    chart = fig.to_html()
    context = {"chart": chart}

    return render(request, "SalesPerformanceChart.html", context)




def SalesTrendsChart(request):
    # Retrieve product status data excluding 'pending' statuses
    product_status = ProductStatus.objects.exclude(status="pending")
    
    # Create a DataFrame to aggregate the data for all products
    total_data = {'date': [], 'status': []}
    product_data = {}

    # Aggregate data for all products and individual products
    for status in product_status:
        total_data['date'].append(status.date_updated)
        total_data['status'].append(status.status)

        # Aggregate data for each product
        if status.product_id not in product_data:
            product_data[status.product_id] = {'date': [], 'status': []}
        product_data[status.product_id]['date'].append(status.date_updated)
        product_data[status.product_id]['status'].append(status.status)

    # Create DataFrame for total data
    df_total = pd.DataFrame(total_data)
    df_total['date'] = pd.to_datetime(df_total['date'])  # Convert date column to datetime
    df_total.set_index('date', inplace=True)  # Set date column as index

    # Ensure the index is a DatetimeIndex
    if not isinstance(df_total.index, pd.DatetimeIndex):
        df_total.index = pd.to_datetime(df_total.index)

    # Group by date and status, count occurrences, and unstack to pivot status to columns for total data
    df_total_counts = df_total.groupby([pd.Grouper(freq='D'), 'status']).size().unstack(fill_value=0)

    # Create traces for each status for total data
    total_traces = []
    for column in df_total_counts.columns:
        total_traces.append(go.Scatter(x=df_total_counts.index, y=df_total_counts[column], mode='lines', name=column.capitalize()))

    # Create the figure for total data
    fig_total = go.Figure(total_traces)
    fig_total.update_layout(title='Total Sales Trends Chart', xaxis_title='Date', yaxis_title='Number of Sales')

    # Create figures for individual product data
    product_charts = []  # Store HTML representations of individual product charts
    for product_id, data in product_data.items():
        df_product = pd.DataFrame(data)
        df_product['date'] = pd.to_datetime(df_product['date'])  # Convert date column to datetime
        df_product.set_index('date', inplace=True)  # Set date column as index

        # Ensure the index is a DatetimeIndex
        if not isinstance(df_product.index, pd.DatetimeIndex):
            df_product.index = pd.to_datetime(df_product.index)

        # Group by date and status, count occurrences, and unstack to pivot status to columns for individual product data
        df_product_counts = df_product.groupby([pd.Grouper(freq='D'), 'status']).size().unstack(fill_value=0)

        # Create traces for each status for individual product data
        product_traces = []
        product_name = Product.objects.get(id=product_id).product_name
        for column in df_product_counts.columns:
            product_traces.append(go.Scatter(x=df_product_counts.index, y=df_product_counts[column], mode='lines', name=column.capitalize()))

        # Create the figure for individual product data
        fig_product = go.Figure(product_traces)
        fig_product.update_layout(title=f'Sales Trends Chart for {product_name}', xaxis_title='Date', yaxis_title='Number of Sales')

        # Convert the figure to HTML
        chart_product = fig_product.to_html()
        product_charts.append(chart_product)  # Append HTML representation to the list

    # Convert total figure to HTML
    chart_total = fig_total.to_html()

    # Pass the HTML representations to the template
    context = {"product_charts": product_charts, "chart_total": chart_total}

    # Return a success message
    return render(request, 'sales_trend_chart.html', context)
