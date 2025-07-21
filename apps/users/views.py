import logging
import zoneinfo
from typing import Dict, Any, Optional, List, Tuple
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db.models import Sum, F, QuerySet
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from dateutil.parser import parse

from .forms import LoginForm, UserRegistrationForm, UserUpdateForm
from .models import CustomUser
from apps.shops.models import Shop, Sales, Cart
from utils.util_functions import admin_required, format_phone, conv_timezone, filter_items, format_number

# Configure logging
logger = logging.getLogger(__name__)


# =============================================
# USER MANAGEMENT SERVICES
# =============================================

class UserManagementService:
    """Service class for handling user management operations"""
    
    @staticmethod
    def create_user(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user with the provided data
        
        Args:
            post_data: Form data for user creation
            
        Returns:
            Dict containing success status and message
        """
        try:
            form = UserRegistrationForm(post_data)
            if form.is_valid():
                form.save()
                logger.info("New user created successfully")
                return {'success': True, 'sms': 'New user added successfully.'}
            
            # Extract error message from form
            error_msg = UserManagementService._extract_form_error(form, ['username', 'phone', 'fullname'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return {'success': False, 'sms': 'Failed to create user. Please try again.'}
    
    @staticmethod
    def update_user(post_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        Update an existing user with the provided data
        
        Args:
            post_data: Form data for user update
            user_id: ID of the user to update
            
        Returns:
            Dict containing success status and message
        """
        try:
            user = UserManagementService._get_active_user(user_id)
            if not user:
                return {'success': False, 'sms': 'User not found.'}
            
            form = UserUpdateForm(post_data, instance=user)
            if form.is_valid():
                form.save()
                logger.info(f"User {user_id} updated successfully")
                return {
                    'success': True, 
                    'update_success': True, 
                    'sms': 'User profile updated successfully.'
                }
            
            # Extract error message from form
            error_msg = UserManagementService._extract_form_error(form, ['username', 'phone', 'fullname', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to update user. Please try again.'}
    
    @staticmethod
    def delete_user(user_id: int) -> Dict[str, Any]:
        """
        Soft delete a user and clean up related data
        
        Args:
            user_id: ID of the user to delete
            
        Returns:
            Dict containing success status and redirect URL
        """
        try:
            user = UserManagementService._get_active_user(user_id)
            if not user:
                return {'success': False, 'sms': 'Failed to delete user.'}
            
            # Clean up user's cart items
            Cart.objects.filter(user=user).delete()
            
            # Soft delete the user
            user.deleted = True
            user.save()
            
            logger.info(f"User {user_id} deleted successfully")
            return {'success': True, 'url': reverse('users_page')}
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to delete user.'}
    
    @staticmethod
    def toggle_user_status(user_id: int) -> Dict[str, Any]:
        """
        Toggle user active/inactive status
        
        Args:
            user_id: ID of the user to toggle
            
        Returns:
            Dict containing success status
        """
        try:
            user = UserManagementService._get_active_user(user_id)
            if not user:
                return {'success': False}
            
            user.is_active = not user.is_active
            user.save()
            
            status = "activated" if user.is_active else "deactivated"
            logger.info(f"User {user_id} {status} successfully")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error toggling user status {user_id}: {str(e)}")
            return {'success': False}
    
    @staticmethod
    def reset_user_password(user_id: int) -> Dict[str, Any]:
        """
        Reset user password to default i.e. their username (uppercase)
        
        Args:
            user_id: ID of the user whose password to reset
            
        Returns:
            Dict containing success status and message
        """
        try:
            user = UserManagementService._get_active_user(user_id)
            if not user:
                return {'success': False, 'sms': 'Failed to reset password.'}
            
            # Set password to uppercase username
            new_password = user.username.upper()
            user.set_password(new_password)
            user.save()
            
            logger.info(f"Password reset for user {user_id}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error resetting password for user {user_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to reset password.'}
    
    @staticmethod
    def get_user_details(user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a user including sales data
        
        Args:
            user_id: ID of the user to get details for
            
        Returns:
            Dict containing user details or None if not found
        """
        try:
            user = UserManagementService._get_active_user(user_id)
            if not user:
                return None
            
            # Calculate total sales for the user
            total_sales = Sales.objects.filter(user=user).aggregate(
                total_sales=Sum(F('amount'))
            )
            sales_total = total_sales['total_sales'] or 0
            
            return {
                'id': user.id,
                'regdate': conv_timezone(user.created_at, '%d-%b-%Y %H:%M:%S'),
                'lastlogin': "N/A" if user.last_login is None else conv_timezone(user.last_login, '%d-%b-%Y %H:%M:%S'),
                'fullname': user.fullname,
                'username': user.username,
                'phone': format_phone(user.phone),
                'mobile': user.phone or "+255",
                'status': "Active" if user.is_active else "Blocked",
                'comment': user.comment or 'N/A',
                'shop': user.shop,
                'sales': format_number(sales_total),
            }
            
        except Exception as e:
            logger.error(f"Error getting user details {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def _get_active_user(user_id: int) -> Optional[CustomUser]:
        """Get an active (non-deleted) user by ID"""
        try:
            return CustomUser.objects.get(pk=user_id, deleted=False)
        except CustomUser.DoesNotExist:
            return None
    
    @staticmethod
    def _extract_form_error(form, field_names: List[str]) -> str:
        """Extract the first error message from specified form fields"""
        for field_name in field_names:
            if form.errors.get(field_name):
                return form.errors[field_name][0]
        return "Unknown error, reload & try again"


# =============================================
# AUTHENTICATION SERVICES
# =============================================

class AuthenticationService:
    """Service class for handling authentication operations"""
    
    @staticmethod
    def authenticate_user(request: HttpRequest, post_data: Dict[str, Any]) -> JsonResponse:
        """
        Authenticate user and create session
        
        Args:
            request: HTTP request object
            post_data: Login form data
            
        Returns:
            JsonResponse with authentication result
        """
        try:
            form = LoginForm(post_data)
            
            if form.is_valid():
                user = form.user
                login(request, user)
                
                # Get redirect URL
                next_url = post_data.get('next_url', reverse('dashboard_page'))
                
                # Create response 
                response = JsonResponse({'success': True, 'url': next_url})
                
                logger.info(f"User {user.username} logged in successfully")
                return response
            
            # Extract error message
            error_msg = form.errors['__all__'][0] if '__all__' in form.errors else 'Invalid credentials'
            return JsonResponse({
                'success': False, 
                'sms': error_msg, 
                'error': form.errors
            })
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JsonResponse({
                'success': False, 
                'sms': 'Authentication failed. Please try again.'
            })
    
    @staticmethod
    def update_user_contact(user: CustomUser, new_contact: str) -> Dict[str, Any]:
        """
        Update user's contact information
        
        Args:
            user: User object to update
            new_contact: New contact number
            
        Returns:
            Dict containing success status and message
        """
        try:
            # Check if contact is already used by another user
            if CustomUser.objects.filter(phone=new_contact, deleted=False).exclude(id=user.id).exists():
                return {
                    'success': False, 
                    'sms': 'This phone is linked to another account.'
                }
            
            user.phone = new_contact
            user.save()
            
            logger.info(f"Contact updated for user {user.id}")
            return {'success': True, 'sms': 'Contact updated successfully'}
            
        except Exception as e:
            logger.error(f"Error updating contact for user {user.id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to update contact. Please try again.'}
    
    @staticmethod
    def change_user_password(user: CustomUser, old_password: str, new_password: str, confirm_password: str) -> Dict[str, Any]:
        """
        Change user's password with validation
        
        Args:
            user: User object
            old_password: Current password
            new_password: New password
            confirm_password: Password confirmation
            
        Returns:
            Dict containing success status and message
        """
        try:
            # Validate current password
            if not authenticate(username=user.username, password=old_password):
                return {'success': False, 'sms': 'Incorrect current password!'}
            
            # Validate new password length
            if len(new_password) < 6:
                return {
                    'success': False, 
                    'sms': f'Use 6+ characters (not {len(new_password)})'
                }
            
            # Validate password confirmation
            if new_password != confirm_password:
                return {'success': False, 'sms': "Passwords should match in both fields"}
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            logger.info(f"Password changed for user {user.id}")
            return {'success': True, 'sms': 'Password changed successfully'}
            
        except Exception as e:
            logger.error(f"Error changing password for user {user.id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to change password. Please try again.'}


# =============================================
# DATATABLES UTILITIES
# =============================================

class DataTablesService:
    """Service class for handling DataTables functionality"""
    
    # Column mapping for user DataTable
    USER_COLUMN_MAPPING = {
        0: 'id',
        1: 'fullname', 
        2: 'username',
        3: 'shop',
        4: 'regdate',
        5: 'phone',
        6: 'status',
    }
    
    # Filter types for specific columns
    COLUMN_FILTER_TYPES = {
        'shop': 'exact',
        'status': 'exact'
    }
    
    @staticmethod
    def parse_datatables_request(request: HttpRequest) -> Dict[str, Any]:
        """
        Parse DataTables AJAX request parameters
        
        Args:
            request: HTTP request object
            
        Returns:
            Dict containing parsed parameters
        """
        return {
            'draw': int(request.POST.get('draw', 0)),
            'start': int(request.POST.get('start', 0)),
            'length': int(request.POST.get('length', 10)),
            'search_value': request.POST.get('search[value]', ''),
            'order_column_index': int(request.POST.get('order[0][column]', 0)),
            'order_dir': request.POST.get('order[0][dir]', 'asc'),
            'start_date_str': request.POST.get('startdate'),
            'end_date_str': request.POST.get('enddate'),
        }
    
    @staticmethod
    def apply_date_filtering(queryset: QuerySet, start_date_str: str, end_date_str: str) -> QuerySet:
        """
        Apply date range filtering to queryset
        
        Args:
            queryset: Base queryset to filter
            start_date_str: Start date string
            end_date_str: End date string
            
        Returns:
            Filtered queryset
        """
        try:
            parsed_start_date = None
            parsed_end_date = None
            
            if start_date_str:
                parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
            
            if end_date_str:
                parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))
            
            if parsed_start_date and parsed_end_date:
                return queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
            elif parsed_start_date:
                return queryset.filter(created_at__gte=parsed_start_date)
            elif parsed_end_date:
                return queryset.filter(created_at__lte=parsed_end_date)
                
        except Exception as e:
            logger.warning(f"Date filtering error: {str(e)}")
        
        return queryset
    
    @staticmethod
    def prepare_user_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Convert user queryset to list of dicts for DataTables
        
        Args:
            queryset: User queryset
            
        Returns:
            List of user data dicts
        """
        return [
            {
                'id': user.id,
                'regdate': user.created_at,
                'fullname': user.fullname,
                'username': user.username,
                'shop': user.shop.abbrev,
                'phone': user.phone if user.phone else "N/A",
                'status': "active" if user.is_active else "inactive",
                'info': reverse('user_details', kwargs={'userid': int(user.id)})
            }
            for user in queryset
        ]
    
    @staticmethod
    def apply_sorting(data: List[Dict], order_column_index: int, order_dir: str) -> List[Dict]:
        """
        Apply sorting to data list
        
        Args:
            data: List of data dicts
            order_column_index: Column index to sort by
            order_dir: Sort direction ('asc' or 'desc')
            
        Returns:
            Sorted data list
        """
        order_column_name = DataTablesService.USER_COLUMN_MAPPING.get(order_column_index, 'regdate')
        reverse_order = order_dir != 'asc'
        
        return sorted(data, key=lambda x: x[order_column_name], reverse=reverse_order)
    
    @staticmethod
    def apply_column_filtering(data: List[Dict], request: HttpRequest) -> List[Dict]:
        """
        Apply individual column filtering
        
        Args:
            data: List of data dicts
            request: HTTP request object
            
        Returns:
            Filtered data list
        """
        filtered_data = data
        
        for i in range(len(DataTablesService.USER_COLUMN_MAPPING)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = DataTablesService.USER_COLUMN_MAPPING.get(i)
                if column_field:
                    filter_type = DataTablesService.COLUMN_FILTER_TYPES.get(column_field, 'contains')
                    filtered_data = [
                        item for item in filtered_data 
                        if filter_items(column_field, column_search, item, filter_type)
                    ]
        
        return filtered_data
    
    @staticmethod
    def apply_global_search(data: List[Dict], search_value: str) -> List[Dict]:
        """
        Apply global search filtering
        
        Args:
            data: List of data dicts
            search_value: Search term
            
        Returns:
            Filtered data list
        """
        if not search_value:
            return data
        
        search_lower = search_value.lower()
        return [
            item for item in data 
            if any(str(value).lower().find(search_lower) != -1 for value in item.values())
        ]
    
    @staticmethod
    def paginate_data(data: List[Dict], start: int, length: int) -> List[Dict]:
        """
        Apply pagination to data
        
        Args:
            data: List of data dicts
            start: Start index
            length: Page length
            
        Returns:
            Paginated data list
        """
        if length < 0:
            return data
        return data[start:start + length]
    
    @staticmethod
    def format_final_data(data: List[Dict], start: int, length: int) -> List[Dict]:
        """
        Format data for final DataTables response
        
        Args:
            data: List of data dicts
            start: Start index for pagination
            length: Page length
            
        Returns:
            Formatted data list
        """
        page_number = start // length + 1 if length > 0 else 1
        row_count_start = (page_number - 1) * length + 1
        
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'regdate': conv_timezone(item.get('regdate'), '%d-%b-%Y'),
                'fullname': item.get('fullname'),
                'username': item.get('username'),
                'shop': item.get('shop'),
                'phone': format_phone(item.get('phone')),
                'status': item.get('status'),
                'info': item.get('info'),
            }
            for i, item in enumerate(data)
        ]


# =============================================
# VIEW FUNCTIONS
# =============================================

@require_POST
def authenticate_user(request: HttpRequest) -> JsonResponse:
    """
    Handle user authentication via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with authentication result
    """
    return AuthenticationService.authenticate_user(request, request.POST)


@login_required
def signout_page(request: HttpRequest) -> HttpResponse:
    """
    Handle user logout and redirect
    
    Args:
        request: HTTP request object
        
    Returns:
        Redirect response
    """
    if request.user.is_authenticated:
        logout(request)
        response = redirect(reverse('index_page'))
        return response
    return redirect(reverse('dashboard_page'))


@never_cache
@login_required
@admin_required()
def users_page(request: HttpRequest) -> HttpResponse:
    """
    Handle users page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        try:
            # Parse DataTables request parameters
            params = DataTablesService.parse_datatables_request(request)
            
            # Base queryset - exclude current user and deleted users
            queryset = CustomUser.objects.filter(deleted=False).exclude(id=request.user.id)
            
            # Apply date filtering
            queryset = DataTablesService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            # Prepare base data
            base_data = DataTablesService.prepare_user_data(queryset)
            total_records = len(base_data)
            
            # Apply sorting
            base_data = DataTablesService.apply_sorting(
                base_data, params['order_column_index'], params['order_dir']
            )
            
            # Apply column filtering
            base_data = DataTablesService.apply_column_filtering(base_data, request)
            
            # Apply global search
            base_data = DataTablesService.apply_global_search(base_data, params['search_value'])
            
            # Calculate filtered record count
            records_filtered = len(base_data)
            
            # Apply pagination
            paginated_data = DataTablesService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            # Format final data
            final_data = DataTablesService.format_final_data(
                paginated_data, params['start'], params['length']
            )
            
            # Prepare AJAX response
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in users_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    # GET request - render the page
    shops = Shop.objects.all().order_by('-created_at')
    return render(request, 'users/users.html', {'shops': shops})


@never_cache
@login_required
@require_POST
@admin_required()
def users_requests(request: HttpRequest) -> JsonResponse:
    """
    Handle various user management requests via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with operation result
    """
    try:
        post_data = request.POST
        
        # Determine the operation type
        edit_user = post_data.get('edit_user')
        delete_user = post_data.get('delete_user')
        block_user = post_data.get('block_user')
        reset_password = post_data.get('reset_password')
        
        # Route to appropriate service method
        if delete_user:
            result = UserManagementService.delete_user(delete_user)
        elif block_user:
            result = UserManagementService.toggle_user_status(block_user)
        elif edit_user:
            result = UserManagementService.update_user(post_data, edit_user)
        elif reset_password:
            result = UserManagementService.reset_user_password(reset_password)
        else:
            # Default to creating new user
            result = UserManagementService.create_user(post_data)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in users_requests: {str(e)}")
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})


@never_cache
@login_required
@admin_required()
def user_details(request: HttpRequest, userid: int) -> HttpResponse:
    """
    Display detailed user information page
    
    Args:
        request: HTTP request object
        userid: ID of the user to display
        
    Returns:
        Rendered template or redirect
    """
    # Only allow GET requests and prevent users from viewing their own details
    if request.method != 'GET' or userid == request.user.id:
        return redirect('users_page')
    
    try:
        # Get user details from service
        user_data = UserManagementService.get_user_details(userid)
        if not user_data:
            return redirect('users_page')
        
        # Get shops for the form
        shops = Shop.objects.all().order_by('abbrev')
        
        return render(request, 'users/users.html', {
            'userinfo': userid,
            'info': user_data,
            'shops': shops
        })
        
    except Exception as e:
        logger.error(f"Error in user_details for user {userid}: {str(e)}")
        return redirect('users_page')


@never_cache
@login_required
def user_profile_page(request: HttpRequest) -> HttpResponse:
    """
    Handle user profile page display and updates
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        try:
            user = request.user
            post_data = request.POST
            
            # Determine the operation type
            change_contact = post_data.get('change_contact')
            update_profile = post_data.get('update_profile')
            old_password = post_data.get('old_password')
            new_password = post_data.get('new_password1')
            confirm_password = post_data.get('new_password2')
            
            # Route to appropriate service method
            if change_contact:
                result = AuthenticationService.update_user_contact(user, change_contact)
            elif update_profile:
                result = UserManagementService.update_user(post_data, user.id)
            else:
                # Handle password change
                result = AuthenticationService.change_user_password(
                    user, old_password, new_password, confirm_password
                )
                
                # Re-authenticate user after password change if successful
                if result.get('success'):
                    login(request, user, backend='frank_inventory.password_backend.CaseInsensitiveModelBackend')
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"Error in user_profile_page: {str(e)}")
            return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})
    
    # GET request - render the profile page
    try:
        # Calculate user's total sales
        total_sales = Sales.objects.filter(user=request.user).aggregate(
            total_sales=Sum(F('amount'))
        )
        sales_total = total_sales['total_sales'] or 0
        
        # Prepare profile data
        profile_data = {
            'regdate': conv_timezone(request.user.created_at, '%d-%b-%Y %H:%M:%S'),
            'fullname': request.user.fullname,
            'username': request.user.username,
            'phone': format_phone(request.user.phone),
            'mobile': request.user.phone or "+255",
            'sales': format_number(sales_total),
            'shop': request.user.shop.id,
        }
        
        return render(request, 'users/profile.html', {'profile': profile_data})
        
    except Exception as e:
        logger.error(f"Error loading profile for user {request.user.id}: {str(e)}")
        return render(request, 'users/profile.html', {'profile': {}})