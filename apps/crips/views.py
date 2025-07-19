import logging
import zoneinfo
from typing import Dict, Any, Optional, List
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db.models import QuerySet
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from dateutil.parser import parse
from decimal import Decimal

from .models import Crips
from utils.util_functions import admin_required, conv_timezone, filter_items, format_number

# Configure logging
logger = logging.getLogger(__name__)


# =============================================
# CRIPS MANAGEMENT SERVICES
# =============================================

class CripsManagementService:
    """Service class for handling crips management operations"""
    
    @staticmethod
    def create_crip(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new crip with the provided data
        
        Args:
            post_data: Form data for crip creation
            
        Returns:
            Dict containing success status and message
        """
        try:
            crips_comment = post_data.get('comment', '').strip()
            
            Crips.objects.create(
                name=post_data.get('name', '').strip(),
                qty=Decimal(post_data.get('qty', 0)),
                price=Decimal(post_data.get('price', 0)),
                comment=None if crips_comment == "" else crips_comment
            )
            
            logger.info("New crip created successfully")
            return {'success': True, 'sms': 'Operation completed successfully!'}
            
        except Exception as e:
            logger.error(f"Error creating crip: {str(e)}")
            return {'success': False, 'sms': 'Unknown error, reload & try again'}
    
    @staticmethod
    def update_crip(post_data: Dict[str, Any], crip_id: int) -> Dict[str, Any]:
        """
        Update an existing crip with the provided data
        
        Args:
            post_data: Form data for crip update
            crip_id: ID of the crip to update
            
        Returns:
            Dict containing success status and message
        """
        try:
            crip = CripsManagementService._get_crip(crip_id)
            if not crip:
                return {'success': False, 'sms': 'Crip not found.'}
            
            crips_comment = post_data.get('comment', '').strip()
            
            crip.name = post_data.get('name', '').strip()
            crip.qty = Decimal(post_data.get('qty', 0))
            crip.price = Decimal(post_data.get('price', 0))
            crip.comment = None if crips_comment in ('N/A', "") else crips_comment
            crip.save()
            
            logger.info(f"Crip {crip_id} updated successfully")
            return {
                'success': True, 
                'update_success': True, 
                'sms': 'Info updated successfully.'
            }
            
        except Exception as e:
            logger.error(f"Error updating crip {crip_id}: {str(e)}")
            return {'success': False, 'sms': 'Unknown error, reload & try again'}
    
    @staticmethod
    def delete_crip(crip_id: int) -> Dict[str, Any]:
        """
        Delete a crip
        
        Args:
            crip_id: ID of the crip to delete
            
        Returns:
            Dict containing success status and redirect URL
        """
        try:
            crip = CripsManagementService._get_crip(crip_id)
            if not crip:
                return {'success': False, 'sms': 'Failed to delete crip.'}
            
            crip.delete()
            
            logger.info(f"Crip {crip_id} deleted successfully")
            return {'success': True, 'url': reverse('crips_page')}
            
        except Exception as e:
            logger.error(f"Error deleting crip {crip_id}: {str(e)}")
            return {'success': False, 'sms': 'Unknown error, reload & try again'}
    
    @staticmethod
    def get_crip_details(crip_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a crip
        
        Args:
            crip_id: ID of the crip to get details for
            
        Returns:
            Dict containing crip details or None if not found
        """
        try:
            crip = CripsManagementService._get_crip(crip_id)
            if not crip:
                return None
            
            return {
                'id': crip.id,
                'regdate': conv_timezone(crip.created_at, '%d-%b-%Y %H:%M:%S'),
                'updated': conv_timezone(crip.updated_at, '%d-%b-%Y %H:%M:%S'),
                'name': crip.name,
                'price': crip.price,
                'qty': crip.qty,
                'price_txt': format_number(crip.price),
                'qty_txt': format_number(crip.qty),
                'comment': crip.comment or 'N/A',
                'types': ['Ndizi', 'Viazi', 'Tambi']
            }
            
        except Exception as e:
            logger.error(f"Error getting crip details {crip_id}: {str(e)}")
            return None
    
    @staticmethod
    def _get_crip(crip_id: int) -> Optional[Crips]:
        """Get a crip by ID"""
        try:
            return Crips.objects.get(id=crip_id)
        except Crips.DoesNotExist:
            return None


# =============================================
# DATATABLES UTILITIES
# =============================================

class CripsDataTablesService:
    """Service class for handling Crips DataTables functionality"""
    
    # Column mapping for crips DataTable
    CRIPS_COLUMN_MAPPING = {
        0: 'id',
        1: 'regdate',
        2: 'name',
        3: 'qty',
        4: 'price',
        5: 'amount',
    }
    
    # Filter types for specific columns
    COLUMN_FILTER_TYPES = {
        'qty': 'numeric',
        'price': 'numeric',
        'amount': 'numeric',
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
    def prepare_crips_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Convert crips queryset to list of dicts for DataTables
        
        Args:
            queryset: Crips queryset
            
        Returns:
            List of crips data dicts
        """
        return [
            {
                'id': item.id,
                'regdate': item.created_at,
                'name': item.name,
                'qty': item.qty,
                'price': item.price,
                'amount': item.price * item.qty,
                'info': reverse('crips_details', kwargs={'crip_id': int(item.id)})
            }
            for item in queryset
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
        order_column_name = CripsDataTablesService.CRIPS_COLUMN_MAPPING.get(order_column_index, 'regdate')
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
        
        for i in range(len(CripsDataTablesService.CRIPS_COLUMN_MAPPING)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = CripsDataTablesService.CRIPS_COLUMN_MAPPING.get(i)
                if column_field:
                    filter_type = CripsDataTablesService.COLUMN_FILTER_TYPES.get(column_field, 'contains')
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
                'name': item.get('name'),
                'qty': format_number(item.get('qty')),
                'price': format_number(item.get('price')) + " TZS",
                'amount': format_number(item.get('amount')) + " TZS",
                'info': item.get('info'),
            }
            for i, item in enumerate(data)
        ]
    
    @staticmethod
    def calculate_grand_total(data: List[Dict]) -> str:
        """
        Calculate grand total amount from data
        
        Args:
            data: List of data dicts
            
        Returns:
            Formatted grand total string
        """
        grand_total_amount = sum(item['amount'] for item in data)
        return format_number(grand_total_amount) + " TZS"


# =============================================
# VIEW FUNCTIONS
# =============================================

@never_cache
@login_required
@require_POST
@admin_required()
def crips_actions(request: HttpRequest) -> JsonResponse:
    """
    Handle various crips management requests via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with operation result
    """
    try:
        post_data = request.POST
        
        # Determine the operation type
        crip_edit = post_data.get('edit_crips')
        crip_delete = post_data.get('delete_crips')
        
        # Route to appropriate service method
        if crip_edit:
            result = CripsManagementService.update_crip(post_data, crip_edit)
        elif crip_delete:
            result = CripsManagementService.delete_crip(crip_delete)
        else:
            # Default to creating new crip
            result = CripsManagementService.create_crip(post_data)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in crips_actions: {str(e)}")
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})


@never_cache
@login_required
@admin_required()
def crips_page(request: HttpRequest) -> HttpResponse:
    """
    Handle crips page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        try:
            # Parse DataTables request parameters
            params = CripsDataTablesService.parse_datatables_request(request)
            
            # Base queryset
            queryset = Crips.objects.all()
            
            # Apply date filtering
            queryset = CripsDataTablesService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            # Prepare base data
            base_data = CripsDataTablesService.prepare_crips_data(queryset)
            total_records = len(base_data)
            
            # Apply sorting
            base_data = CripsDataTablesService.apply_sorting(
                base_data, params['order_column_index'], params['order_dir']
            )
            
            # Apply column filtering
            base_data = CripsDataTablesService.apply_column_filtering(base_data, request)
            
            # Apply global search
            base_data = CripsDataTablesService.apply_global_search(base_data, params['search_value'])
            
            # Calculate filtered record count and grand total
            records_filtered = len(base_data)
            grand_total = CripsDataTablesService.calculate_grand_total(base_data)
            
            # Apply pagination
            paginated_data = CripsDataTablesService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            # Format final data
            final_data = CripsDataTablesService.format_final_data(
                paginated_data, params['start'], params['length']
            )
            
            # Prepare AJAX response
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
                'grand_total': grand_total
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in crips_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    # GET request - render the page
    return render(request, 'crips/crips.html')


@never_cache
@login_required
@admin_required()
def crips_details(request: HttpRequest, crip_id: int) -> HttpResponse:
    """
    Display detailed crip information page
    
    Args:
        request: HTTP request object
        crip_id: ID of the crip to display
        
    Returns:
        Rendered template or redirect
    """
    try:
        # Get crip details from service
        crip_data = CripsManagementService.get_crip_details(crip_id)
        if not crip_data:
            return redirect('crips_page')
        
        return render(request, 'crips/crips.html', {
            'crips_info': True, 
            'info': crip_data
        })
        
    except Exception as e:
        logger.error(f"Error in crips_details for crip {crip_id}: {str(e)}")
        return redirect('crips_page')