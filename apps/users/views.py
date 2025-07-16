import zoneinfo
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .forms import LoginForm, UserRegistrationForm, UserUpdateForm
from .models import CustomUser
from apps.shops.models import Shop
from dateutil.parser import parse
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from utils.util_functions import admin_required, format_phone, conv_timezone, filter_items



def register_new_user(post_data):
    form = UserRegistrationForm(post_data)
    if form.is_valid():
        form.save()
        return {'success': True, 'sms': 'New user added successfully.'}
    
    errorMsg = (
        form.errors.get('username') or
        form.errors.get('phone') or
        form.errors.get('fullname')
    )
    errorMsg = errorMsg[0] if errorMsg else "Unknown error, reload & try again"
    return {'success': False, 'sms': errorMsg}

def handle_update_user(post_data, user_id):
    try:
        user = CustomUser.objects.get(pk=user_id, deleted=False)
    except CustomUser.DoesNotExist:
        return {'success': False, 'sms': 'User not found.'}
    
    form = UserUpdateForm(post_data, instance=user)
    if form.is_valid():
        form.save()
        return {'success': True, 'update_success': True, 'sms': 'User profile updated successfully.'}
    
    errorMsg = (
        form.errors.get('username') or
        form.errors.get('phone') or
        form.errors.get('fullname') or
        form.errors.get('comment')
    )
    errorMsg = errorMsg[0] if errorMsg else "Unknown error, reload & try again"
    return {'success': False, 'sms': errorMsg}

def handle_delete_user(user_id):
    try:
        user = CustomUser.objects.get(pk=user_id, deleted=False)
    except CustomUser.DoesNotExist:
        return {'success': False, 'sms': 'Failed to delete user.'}
    
    user.deleted = True
    user.save()
    return {'success': True, 'url': reverse('users_page')}

def handle_block_user(user_id):
    try:
        user = CustomUser.objects.get(pk=user_id, deleted=False)
    except CustomUser.DoesNotExist:
        return {'success': False}
    
    user.is_active = not user.is_active
    user.save()
    return {'success': True}

def reset_user_password(user_id):
    try:
        user = CustomUser.objects.get(pk=user_id, deleted=False)
    except CustomUser.DoesNotExist:
        return {'success': False, 'sms': 'Failed to reset password.'}
    
    new_password = user.username.upper()
    user.set_password(new_password)
    user.save()
    return {'success': True}

@require_POST
def authenticate_user(request):
    form = LoginForm(request.POST)

    if form.is_valid():
        user = form.user
        login(request, user)
        next_url = request.POST.get('next_url', reverse('dashboard_page'))
        response = JsonResponse({'success': True, 'url': next_url})
        response.set_cookie('name_text', user.username) 
        return response

    error_msg = form.errors['__all__'][0]
    return JsonResponse({'success': False, 'sms': error_msg, 'error': form.errors})

@login_required
def signout_page(request):
    if request.user.is_authenticated:
        logout(request)
        response = redirect(reverse('index_page'))
        response.delete_cookie('username')
        return response
    return redirect(reverse('dashboard_page'))


@never_cache
@login_required
@admin_required()
def users_page(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        # Base queryset
        queryset = CustomUser.objects.filter(deleted=False).exclude(id=request.user.id)

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
            parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))

        if parsed_start_date and parsed_end_date:
            queryset = queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
        elif parsed_start_date:
            queryset = queryset.filter(created_at__gte=parsed_start_date)
        elif parsed_end_date:
            queryset = queryset.filter(created_at__lte=parsed_end_date)


        # Base data from queryset
        base_data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'regdate': user.created_at,
                'fullname': user.fullname,
                'username': user.username,
                'shop': user.shop.abbrev,
                'phone': user.phone if user.phone else "N/A",
                'status': "active" if user.is_active else "inactive",
                'info': reverse('user_details', kwargs={'userid': int(user.id)})
            }
            base_data.append(user_data)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'fullname',
            2: 'username',
            3: 'shop',
            4: 'regdate',
            5: 'phone',
            6: 'status',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'regdate')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        column_filter_types = {
            'shop': 'exact',
            'status': 'exact'
        }

        # Apply individual column filtering
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    filter_type = column_filter_types.get(column_field, 'contains')
                    base_data = [item for item in base_data if filter_items(column_field, column_search, item, filter_type)]

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
                'fullname': item.get('fullname'),
                'username': item.get('username'),
                'shop': item.get('shop'),
                'phone': format_phone(item.get('phone')),
                'status': item.get('status'),
                'info': item.get('info'),
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
        }
        return JsonResponse(ajax_response)
    
    shops = Shop.objects.all().order_by('-created_at')
    return render(request, 'users/users.html', {'shops': shops})

@never_cache
@login_required
@require_POST
@admin_required()
def users_requests(request):
    try:
        edit_user = request.POST.get('edit_user')
        delete_user = request.POST.get('delete_user')
        block_user = request.POST.get('block_user')
        reset_password = request.POST.get('reset_password')

        if delete_user:
            fdback = handle_delete_user(delete_user)
        elif block_user:
            fdback = handle_block_user(block_user)
        elif edit_user:
            fdback = handle_update_user(request.POST, edit_user)
        elif reset_password:
            fdback = reset_user_password(reset_password)
        else:
            fdback = register_new_user(request.POST)

    except Exception as e:
        fdback = {'success': False, 'sms': 'Unknown error, reload & try again'}
    return JsonResponse(fdback)

@never_cache
@login_required
@admin_required()
def user_details(request, userid):
    if request.method == 'GET' and not userid == request.user.id:
        try:
            userobj = CustomUser.objects.get(id=userid, deleted=False)
        except CustomUser.DoesNotExist:
            return redirect('users_page')

        userdata = {
            'id': userobj.id,
            'regdate': conv_timezone(userobj.created_at,'%d-%b-%Y %H:%M:%S'),
            'lastlogin': "N/A" if userobj.last_login is None else conv_timezone(userobj.last_login,'%d-%b-%Y %H:%M:%S'),
            'fullname': userobj.fullname,
            'username': userobj.username,
            'phone': format_phone(userobj.phone),
            'mobile': userobj.phone or "+255",
            'status': "Active" if userobj.is_active else "Blocked",
            'comment': userobj.comment or 'N/A',
            'shop': userobj.shop,
        }

        shops = Shop.objects.all().order_by('abbrev')
        return render(request, 'users/users.html', {'userinfo': userid, 'info': userdata, 'shops': shops})
    return redirect('users_page')

@never_cache
@login_required
def user_profile_page(request):
    if request.method == 'POST':
        try:
            user = request.user
            change_contact = request.POST.get('change_contact')
            update_profile = request.POST.get('update_profile')
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password1')
            confirm_password = request.POST.get('new_password2')

            if change_contact:
                if CustomUser.objects.filter(phone=change_contact, deleted=False).exclude(id=user.id).exists():
                    return JsonResponse({'success': False, 'sms': 'This phone number is already used by another account.'})
                
                user.phone = change_contact
                user.save()
                return JsonResponse({'success': True, 'sms': 'Contact updated successfully'})

            elif update_profile:
                fdback = handle_update_user(request.POST, user.id)
                return JsonResponse(fdback)

            else:
                if not authenticate(username=user.username, password=old_password):
                    return JsonResponse({'success': False, 'sms': 'Incorrect current password!'})
                if len(new_password) < 6:
                    return JsonResponse({'success': False, 'sms': f'Password should be 6 or more characters long, (not {len(new_password)})'})
                if new_password != confirm_password:
                    return JsonResponse({'success': False, 'sms': "Passwords should match in both fields"})

                user.set_password(new_password)
                user.save()
                login(request, user, backend='frank_inventory.password_backend.CaseInsensitiveModelBackend')
                return JsonResponse({'success': True, 'sms': 'Password changed successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

    data = {
        'regdate': conv_timezone(request.user.created_at,'%d-%b-%Y %H:%M:%S'),
        'fullname': request.user.fullname,
        'username': request.user.username,
        'phone': format_phone(request.user.phone),
        'mobile': request.user.phone or "+255",
    }
    return render(request, 'users/profile.html', {'profile': data})