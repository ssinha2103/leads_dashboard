from __future__ import annotations
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
import csv

from .models import Lead, Category, State, City, SavedView


def dashboard(request):
    # Accurate counts via ORM
    total_leads = Lead.objects.count()
    leads_with_email = Lead.objects.exclude(email__isnull=True).exclude(email__exact='').count()
    categories = Category.objects.annotate(n=Count('leads')).order_by('-n')[:10]
    context = {
        'total_leads': total_leads,
        'leads_with_email': leads_with_email,
        'top_categories': categories,
    }
    return render(request, 'dashboard.html', context)


def _filter_queryset(request):
    qs = Lead.objects.select_related('city', 'state', 'category')
    q = request.GET.get('q')
    state = request.GET.get('state')
    city = request.GET.get('city')
    category = request.GET.get('category')
    has_email = request.GET.get('has_email')
    has_website = request.GET.get('has_website')
    sort = request.GET.get('sort', 'business_name')

    if q:
        qs = qs.filter(Q(business_name__icontains=q) | Q(domain__icontains=q) | Q(email__icontains=q))
    if state:
        qs = qs.filter(state_id=state)
    if city:
        qs = qs.filter(city_id=city)
    if category:
        qs = qs.filter(category_id=category)
    if has_email in ('1', 'true', 'True'):
        qs = qs.exclude(email__isnull=True).exclude(email__exact='')
    if has_website in ('1', 'true', 'True'):
        qs = qs.exclude(website__isnull=True).exclude(website__exact='')

    if sort in ['business_name', 'quality_score', 'state__name', 'city__name']:
        qs = qs.order_by(sort)
    else:
        qs = qs.order_by('business_name')

    return qs


def leads_list(request):
    qs = _filter_queryset(request)
    try:
        page_size = int(request.GET.get('page_size', 50))
    except Exception:
        page_size = 50
    page_size = max(10, min(page_size, 200))

    paginator = Paginator(qs, page_size)
    page = paginator.get_page(request.GET.get('page'))

    # Limit cities to selected state to reduce payload
    cities_qs = City.objects.order_by('name')
    if request.GET.get('state'):
        cities_qs = cities_qs.filter(state_id=request.GET.get('state'))
    cities_qs = cities_qs[:1000]

    context = {
        'page': page,
        'categories': Category.objects.order_by('name'),
        'states': State.objects.order_by('name'),
        'cities': cities_qs,
        'params': request.GET,
        'saved_views': SavedView.objects.order_by('-created_at')[:10],
    }
    return render(request, 'leads_list.html', context)


def leads_export(request):
    qs = _filter_queryset(request)[:10000]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Business Name', 'Category', 'State', 'City', 'Website', 'Email', 'Phone', 'Domain', 'Score'])
    for l in qs:
        writer.writerow([
            l.business_name,
            l.category.name if l.category else '',
            l.state.name if l.state else '',
            l.city.name if l.city else '',
            l.website or '',
            l.email or '',
            l.phone or '',
            l.domain or '',
            l.quality_score,
        ])
    return response


def save_view(request):
    if request.method == 'POST':
        name = request.POST.get('name') or 'Saved View'
        # store current GET params
        filters = {k: v for k, v in request.POST.items() if k not in {'csrfmiddlewaretoken', 'name'}}
        SavedView.objects.create(name=name, filters=filters)
    return redirect('leads_list')
