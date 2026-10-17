import os
import sys
import json
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Avg, Q
from django.core.paginator import Paginator
from django.conf import settings

# Import ML forecast engine
ML_ENGINE_PATH = os.path.join(settings.BASE_DIR.parent, "ml_engine")
if ML_ENGINE_PATH not in sys.path:
    sys.path.append(ML_ENGINE_PATH)

from .models import Customer, Product, SalesTransaction
from forecast import forecast_future_sales, load_metrics
from .pdf_generator import generate_forecast_pdf

def split_curr(val):
    """Splits numeric currency into formatted integer and decimal parts."""
    formatted = f"{val:,.2f}"
    parts = formatted.split('.')
    return parts[0], f".{parts[1]}"

def format_inr_short(val):
    """Formats figures into Indian Cr / L."""
    if val >= 10000000:
        return f"{val/10000000:.2f} Cr"
    elif val >= 100000:
        return f"{val/100000:.2f} L"
    return f"{val:,.0f}"

def get_kpis():
    """Computes headline KPIs from MySQL database."""
    agg = SalesTransaction.objects.aggregate(
        total_rev=Sum('total_sales_amount'),
        total_prof=Sum('profit'),
        total_tx=Count('sale_id'),
        avg_order=Avg('total_sales_amount')
    )
    total_rev = float(agg['total_rev'] or 0.0)
    total_prof = float(agg['total_prof'] or 0.0)
    total_tx = agg['total_tx'] or 0
    avg_order = float(agg['avg_order'] or 0.0)
    margin = (total_prof / total_rev * 100) if total_rev > 0 else 0.0
    total_cust = Customer.objects.count()

    rev_int, rev_dec = split_curr(total_rev)
    prof_int, prof_dec = split_curr(total_prof)
    aov_int, aov_dec = split_curr(avg_order)
    rev_short = format_inr_short(total_rev)
    prof_short = format_inr_short(total_prof)

    return {
        "total_revenue": total_rev,
        "total_revenue_formatted": f"Rs. {total_rev:,.2f}",
        "revenue_int": rev_int,
        "revenue_dec": rev_dec,
        "revenue_short": rev_short,
        "total_profit": total_prof,
        "total_profit_formatted": f"Rs. {total_prof:,.2f}",
        "profit_int": prof_int,
        "profit_dec": prof_dec,
        "profit_short": prof_short,
        "total_transactions": total_tx,
        "total_transactions_formatted": f"{total_tx:,}",
        "profit_margin": round(margin, 2),
        "avg_order_value": round(avg_order, 2),
        "avg_order_formatted": f"Rs. {avg_order:,.2f}",
        "aov_int": aov_int,
        "aov_dec": aov_dec,
        "total_customers": total_cust,
    }

def login_view(request):
    """Secure Admin Authentication Screen with multi-layer input validation."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error_msg = None
    field_errors = {}
    security_notice = None
    username_val = ""
    
    reason = request.GET.get('reason')
    if reason == 'tab_switch':
        security_notice = "Session Terminated: Active session was automatically logged out because you switched to another browser tab."
    elif reason == 'inactivity':
        security_notice = "Session Expired: You were automatically logged out due to inactivity."
        
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()
        username_val = u
        
        # Comprehensive Field Validations
        if not u:
            field_errors['username'] = "Administrator username is required."
        elif len(u) < 3:
            field_errors['username'] = "Username must be at least 3 characters long."
        elif len(u) > 60:
            field_errors['username'] = "Username cannot exceed 60 characters."
            
        if not p:
            field_errors['password'] = "Security key / password is required."
        elif len(p) < 4:
            field_errors['password'] = "Password must be at least 4 characters long."
            
        if not field_errors:
            user = authenticate(request, username=u, password=p)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next') or 'dashboard'
                return redirect(next_url)
            else:
                error_msg = "Invalid credentials. Please enter authorized username and password."
        else:
            error_msg = "Please resolve the highlighted validation errors below."
            
    return render(request, "dashboard/login.html", {
        "error_msg": error_msg,
        "field_errors": field_errors,
        "security_notice": security_notice,
        "username_val": username_val
    })

@csrf_exempt
def logout_view(request):
    """Logs out current admin user and redirects to login screen with optional security reason."""
    reason = request.GET.get('reason') or request.POST.get('reason')
    logout(request)
    
    # Handle AJAX and Beacon requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'status': 'logged_out', 'reason': reason})
        
    if reason:
        return redirect(f"/login/?reason={reason}")
    return redirect('login')

@login_required(login_url='login')
def dashboard_view(request):
    """Main executive overview dashboard."""
    kpis = get_kpis()
    
    # Category sales breakdown
    cat_qs = SalesTransaction.objects.values('product_category').annotate(
        cat_sales=Sum('total_sales_amount'),
        cat_count=Count('sale_id'),
        cat_profit=Sum('profit')
    ).order_by('-cat_sales')
    
    category_labels = [c['product_category'] for c in cat_qs]
    category_values = [round(float(c['cat_sales']), 2) for c in cat_qs]
    
    # Payment method breakdown
    pay_qs = SalesTransaction.objects.values('payment_method').annotate(
        method_count=Count('sale_id'),
        method_sales=Sum('total_sales_amount')
    ).order_by('-method_sales')
    
    payment_labels = [p['payment_method'] for p in pay_qs]
    payment_values = [round(float(p['method_sales']), 2) for p in pay_qs]
    
    # Top 5 products
    top_products = SalesTransaction.objects.values('product_name', 'product_category').annotate(
        prod_revenue=Sum('total_sales_amount'),
        units_sold=Sum('quantity_sold'),
        prod_profit=Sum('profit')
    ).order_by('-prod_revenue')[:5]
    
    # Monthly sales trend (aggregated from transactions across MySQL, PostgreSQL & SQLite)
    from django.db.models.functions import TruncMonth
    monthly_qs = (
        SalesTransaction.objects
        .annotate(ym_date=TruncMonth('sale_date'))
        .values('ym_date')
        .annotate(
            monthly_rev=Sum('total_sales_amount'),
            monthly_profit=Sum('profit')
        )
        .order_by('ym_date')
    )
    monthly_labels = [
        row['ym_date'].strftime('%Y-%m') if hasattr(row['ym_date'], 'strftime') else str(row['ym_date'])[:7]
        for row in monthly_qs
    ]
    monthly_revenue = [round(float(row['monthly_rev'] or 0), 2) for row in monthly_qs]
    monthly_profits = [round(float(row['monthly_profit'] or 0), 2) for row in monthly_qs]
    
    # Recent 6 transactions
    recent_transactions = SalesTransaction.objects.select_related('customer', 'product').order_by('-sale_date')[:6]

    context = {
        "kpis": kpis,
        "category_labels": json.dumps(category_labels),
        "category_values": json.dumps(category_values),
        "payment_labels": json.dumps(payment_labels),
        "payment_values": json.dumps(payment_values),
        "monthly_labels": json.dumps(monthly_labels),
        "monthly_revenue": json.dumps(monthly_revenue),
        "monthly_profits": json.dumps(monthly_profits),
        "top_products": top_products,
        "recent_transactions": recent_transactions,
    }
    return render(request, "dashboard/dashboard.html", context)

ALLOWED_FORECAST_MODELS = {
    'best_model',
    'random_forest_regression',
    'decision_tree_regression',
    'linear_regression'
}

@login_required(login_url='login')
def forecast_view(request):
    """Interactive forecasting page with validated horizon and model parameters."""
    try:
        raw_days = request.GET.get('days', '30')
        days = int(raw_days)
    except (ValueError, TypeError):
        days = 30
        
    # Strictly validate horizon bounds: 1 to 180 days
    if days < 1 or days > 180:
        days = 30
        
    model_choice = request.GET.get('model', 'best_model')
    if model_choice not in ALLOWED_FORECAST_MODELS:
        model_choice = 'best_model'
        
    forecast_data = forecast_future_sales(days_ahead=days, model_choice=model_choice)
    
    chart_dates = [d['date'] for d in forecast_data['daily_breakdown']]
    chart_preds = [d['predicted_sales'] for d in forecast_data['daily_breakdown']]
    chart_lower = [d['lower_bound'] for d in forecast_data['daily_breakdown']]
    chart_upper = [d['upper_bound'] for d in forecast_data['daily_breakdown']]
    
    metrics = load_metrics()
    best_model_name = metrics.get('best_model_name', 'Random Forest Regression')
    
    context = {
        "forecast": forecast_data,
        "selected_days": days,
        "selected_model": model_choice,
        "best_model_name": best_model_name,
        "chart_dates": json.dumps(chart_dates),
        "chart_preds": json.dumps(chart_preds),
        "chart_lower": json.dumps(chart_lower),
        "chart_upper": json.dumps(chart_upper),
    }
    return render(request, "dashboard/forecast.html", context)

@login_required(login_url='login')
def forecast_pdf_view(request):
    """Direct high-fidelity ReportLab executive PDF export with fail-safe direct download."""
    try:
        raw_days = request.GET.get('days', '30')
        days = int(raw_days)
    except (ValueError, TypeError):
        days = 30
        
    if days < 1 or days > 180:
        days = 30
        
    model_choice = request.GET.get('model', 'best_model')
    if model_choice not in ALLOWED_FORECAST_MODELS:
        model_choice = 'best_model'
        
    forecast_data = forecast_future_sales(days_ahead=days, model_choice=model_choice)
    
    model_display_names = {
        'best_model': 'Random Forest Regression (Optimal Benchmark)',
        'random_forest_regression': 'Random Forest Regression',
        'decision_tree_regression': 'Decision Tree Regression',
        'linear_regression': 'Linear Regression'
    }
    model_name = model_display_names.get(model_choice, 'Random Forest Regression (Optimal Benchmark)')
    
    pdf_buffer = generate_forecast_pdf(forecast_data, selected_days=days, selected_model_name=model_name)
    
    is_inline = request.GET.get('inline', '0') == '1'
    disposition = 'inline' if is_inline else 'attachment'
    filename = f"SalesForecast_Demand_Report_{days}Days.pdf"
    
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    return response

@login_required(login_url='login')
def api_forecast(request):
    """REST endpoint for dynamic client-side forecasting with strict parameter validation."""
    try:
        raw_days = request.GET.get('days', '30')
        days = int(raw_days)
    except (ValueError, TypeError):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid horizon parameter. "days" must be a valid integer between 1 and 180.'
        }, status=400)
        
    if days < 1 or days > 180:
        return JsonResponse({
            'status': 'error',
            'message': 'Horizon out of range. "days" must be between 1 and 180.'
        }, status=400)
        
    model_choice = request.GET.get('model', 'best_model')
    if model_choice not in ALLOWED_FORECAST_MODELS:
        model_choice = 'best_model'
        
    forecast_data = forecast_future_sales(days_ahead=days, model_choice=model_choice)
    return JsonResponse(forecast_data)

@login_required(login_url='login')
def eda_view(request):
    """Exploratory Data Analysis visual gallery and insights."""
    kpis = get_kpis()
    plots = [
        {
            "id": "monthly",
            "title": "Monthly Sales Trends (2023 - 2025)",
            "filename": "monthly_sales_trend.png",
            "description": "Displays historical seasonal trends, identifying massive annual peaks during October-December (Diwali festival rush) and mid-year performance."
        },
        {
            "id": "category",
            "title": "Product Category-wise Sales Distribution",
            "filename": "category_sales.png",
            "description": "Comparative bar chart of revenue generated across Electronics, Fashion, Home & Kitchen, Groceries, Beauty, and Sports."
        },
        {
            "id": "products",
            "title": "Top 8 Revenue Generating Products",
            "filename": "top_products.png",
            "description": "High-ticket contributors including 4K Smart TVs, Robotic Vacuum Cleaners, and Induction Cookware driving overall basket value."
        },
        {
            "id": "profit",
            "title": "Revenue vs Net Profit Analysis",
            "filename": "profit_analysis.png",
            "description": "Side-by-side comparison of gross sales versus realized net margins after accounting for unit costs and discount structures."
        },
        {
            "id": "city",
            "title": "Top 10 Cities by Total Sales",
            "filename": "city_sales.png",
            "description": "Geographical demand concentration across tier-1 metropolitan hubs including Mumbai, Bengaluru, Pune, Delhi, and Hyderabad."
        },
        {
            "id": "growth",
            "title": "Month-over-Month (MoM) Growth Analysis",
            "filename": "sales_growth.png",
            "description": "Velocity of sales expansion, highlighting growth accelerations in festival quarters and seasonal re-balancing."
        }
    ]
    context = {"kpis": kpis, "plots": plots}
    return render(request, "dashboard/eda.html", context)

@login_required(login_url='login')
def models_view(request):
    """Machine learning models evaluation and comparison screen."""
    metrics = load_metrics()
    models_eval = metrics.get('models_evaluation', {})
    best_name = metrics.get('best_model_name', 'Random Forest Regression')
    feature_importances = metrics.get('feature_importances', {})
    
    # Format models for template rendering
    models_list = []
    for mname, mdata in models_eval.items():
        models_list.append({
            "name": mname,
            "mae": mdata.get("mae", 0.0),
            "rmse": mdata.get("rmse", 0.0),
            "r2_score": mdata.get("r2_score", 0.0),
            "r2_pct": mdata.get("r2_percentage", "0%"),
            "is_best": (mname == best_name)
        })
    # Sort best first
    models_list.sort(key=lambda x: x["r2_score"], reverse=True)
    
    feat_labels = list(feature_importances.keys())[:10]
    feat_values = list(feature_importances.values())[:10]
    
    context = {
        "models_list": models_list,
        "best_name": best_name,
        "metrics": metrics,
        "feat_labels": json.dumps(feat_labels),
        "feat_values": json.dumps(feat_values),
    }
    return render(request, "dashboard/models.html", context)

@login_required(login_url='login')
def transactions_view(request):
    """Searchable, filterable transactional ledger with rigorous sanitization and bounds checking."""
    raw_query = request.GET.get('q', '').strip()
    # Bound query length to 100 characters and strip non-printable characters
    query = "".join(ch for ch in raw_query[:100] if ch.isprintable())
    
    category = request.GET.get('category', '').strip()
    payment = request.GET.get('payment', '').strip()
    
    categories = sorted([c for c in SalesTransaction.objects.order_by().values_list('product_category', flat=True).distinct() if c])
    payment_methods = sorted([p for p in SalesTransaction.objects.order_by().values_list('payment_method', flat=True).distinct() if p])
    
    # Whitelist validate filters
    if category and category not in categories:
        category = ''
    if payment and payment not in payment_methods:
        payment = ''
        
    tx_qs = SalesTransaction.objects.all().order_by('-sale_date', '-sale_id')
    
    if query:
        tx_qs = tx_qs.filter(
            Q(product_name__icontains=query) |
            Q(customer_city__icontains=query) |
            Q(customer_state__icontains=query) |
            Q(customer__customer_name__icontains=query) |
            Q(product_category__icontains=query) |
            Q(payment_method__icontains=query) |
            Q(sale_id__icontains=query)
        )
    if category:
        tx_qs = tx_qs.filter(product_category=category)
    if payment:
        tx_qs = tx_qs.filter(payment_method=payment)
        
    paginator = Paginator(tx_qs, 12)
    raw_page = request.GET.get('page', 1)
    try:
        page_number = int(raw_page)
    except (ValueError, TypeError):
        page_number = 1
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "query": query,
        "selected_category": category,
        "selected_payment": payment,
        "categories": categories,
        "payment_methods": payment_methods,
        "total_results": paginator.count,
    }
    return render(request, "dashboard/transactions.html", context)

@login_required(login_url='login')
def insights_view(request):
    """Executive insights and automated recommendations."""
    kpis = get_kpis()
    metrics = load_metrics()
    return render(request, "dashboard/insights.html", {"kpis": kpis, "metrics": metrics})
