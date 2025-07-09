from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from .forms import ShopForm, ShopUpdateForm
from utils.util_functions import conv_timezone
from .models import Shop
from apps.users.models import CustomUser
import zoneinfo
from dateutil.parser import parse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from utils.util_functions import admin_required


def register_shop(post_data):
    form = ShopForm(post_data)
    if form.is_valid():
        form.save()
        return {'success': True, 'sms': 'New shop added successfully.'}
    
    errorMsg = (
        form.errors.get('names') or
        form.errors.get('abbrev') or
        form.errors.get('comment')
    )
    errorMsg = errorMsg[0] if errorMsg else "Unknown error, reload & try again"
    return {'success': False, 'sms': errorMsg}

def update_shop(post_data, shop_id):
    try:
        shop = Shop.objects.get(pk=shop_id)
    except Shop.DoesNotExist:
        return {'success': False, 'sms': 'Shop not found.'}
    
    form = ShopUpdateForm(post_data, instance=shop)
    if form.is_valid():
        form.save()
        return {'success': True, 'update_success': True, 'sms': 'Shop info updated successfully.'}
    
    errorMsg = (
        form.errors.get('names') or
        form.errors.get('abbrev') or
        form.errors.get('comment')
    )
    errorMsg = errorMsg[0] if errorMsg else "Unknown error, reload & try again"
    return {'success': False, 'sms': errorMsg}


@never_cache
@login_required
@require_POST
@admin_required()
def shops_requests(request):
    try:
        edit_shop = request.POST.get('edit_shop')
        delete_shop = request.POST.get('delete_shop')

        if edit_shop:
            fdback = update_shop(request.POST, edit_shop)
        elif delete_shop:
            shop_id = int(delete_shop)
            try:
                shop_obj = Shop.objects.get(id=shop_id)
                if shop_obj.id == 1:
                    return JsonResponse({'success': False, 'sms': 'Cannot delete the main shop.'})
                
                CustomUser.objects.filter(shop=shop_obj).delete()
                shop_obj.delete()
                fdback = {'success': True, 'url': reverse('shops_page')}
            except Shop.DoesNotExist:
                fdback = {'success': False, 'sms': 'Operation failed.'}
        else:
            fdback = register_shop(request.POST)

    except Exception as e:
        fdback = {'success': False, 'sms': 'Unknown error, reload & try again'}
        
    return JsonResponse(fdback)


@never_cache
@login_required
@admin_required()
def shops_page(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        # Base queryset
        queryset = Shop.objects.all()

        # Date range filtering
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')
        parsed_start_date = None
        parsed_end_date = None

        # Parse start date if provided
        if start_date_str:
            parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))

        # Parse end date if provided
        if end_date_str:
            print(f"End date string: {end_date_str}")
            parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))

        if parsed_start_date and parsed_end_date:
            queryset = queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
        elif parsed_start_date:
            queryset = queryset.filter(created_at__gte=parsed_start_date)
        elif parsed_end_date:
            queryset = queryset.filter(created_at__lte=parsed_end_date)


        # Base data from queryset
        base_data = []
        for shop in queryset:
            shop_data = {
                'id': shop.id,
                'regdate': shop.created_at,
                'names': shop.names,
                'abbrev': shop.abbrev,
                'info': reverse('shop_details', kwargs={'shopid': int(shop.id)})
            }
            base_data.append(shop_data)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'names',
            2: 'abbrev',
            3: 'regdate',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'regdate')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    filtered_base_data = []
                    for item in base_data:
                        column_value = str(item.get(column_field, '')).lower()
                        if column_search.lower() in column_value:
                            filtered_base_data.append(item)

                    base_data = filtered_base_data

        # Apply global search
        if search_value:
            base_data = [item for item in base_data if any(str(value).lower().find(search_value.lower()) != -1 for value in item.values())]

        # Calculate the total number of records after filtering
        records_filtered = len(base_data)

        # Apply pagination
        if length < 0:
            length = len(base_data)
        base_data = base_data[start:start + length]

        # Calculate row_count based on current page and length
        page_number = start // length + 1
        row_count_start = (page_number - 1) * length + 1


        # Final data to be returned to ajax call
        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'regdate': conv_timezone(item.get('regdate'),'%d-%b-%Y'),
                'names': item.get('names'),
                'abbrev': item.get('abbrev'),
                'info': item.get('info'),
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
        }
        return JsonResponse(ajax_response)
    return render(request, 'shops/shops.html')


@never_cache
@login_required
@admin_required()
@require_GET
def shop_details(request, shopid):
    try:
        shop_obj = Shop.objects.get(id=shopid)
    except Shop.DoesNotExist:
        return redirect('shops_page')

    shopdata = {
        'id': shop_obj.id,
        'regdate': conv_timezone(shop_obj.created_at,'%d-%b-%Y %H:%M:%S'),
        'names': shop_obj.names,
        'abbrev': shop_obj.abbrev,
        'comment': shop_obj.comment or 'N/A',
        'users_count': CustomUser.objects.filter(shop=shop_obj).count(),
        # 'users_list': CustomUser.objects.filter(shop=shop_obj).values('id', 'username', 'fullname', 'phone'),
        'items_count': 0,  # Placeholder for items count
        'networth': 0,  # Placeholder for net worth
    }
    
    delete_info = False if shop_obj.id == 1 else True
    return render(request, 'shops/shops.html', {'shopinfo': shopid, 'info': shopdata, 'delete_info': delete_info})
