import logging
from typing import Dict, Any, List
from datetime import timedelta
from decimal import Decimal
from collections import defaultdict

from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.timezone import localtime

from apps.shops.models import Shop, Product, Sales, Sale_items
from apps.users.models import CustomUser
from utils.util_functions import format_number

# Configure logging
logger = logging.getLogger(__name__)


# =============================================
# DASHBOARD SERVICES
# =============================================

class DashboardMetricsService:
    """Service class for calculating dashboard metrics"""
    
    @staticmethod
    def get_current_and_previous_month() -> Dict[str, int]:
        """Get current and previous month/year values"""
        now = timezone.now()
        current_month = now.month
        current_year = now.year
        last_month = now.month - 1
        last_year = now.year
        
        if now.month == 1:
            last_month = 12
            last_year = now.year - 1
        
        return {
            'current_month': current_month,
            'current_year': current_year,
            'last_month': last_month,
            'last_year': last_year
        }
    
    @staticmethod
    def get_sales_metrics(user, date_info: Dict[str, int]) -> Dict[str, Any]:
        """Calculate sales metrics for current and previous month"""
        try:
            this_month_sales = Sales.objects.filter(
                created_at__month=date_info['current_month'],
                created_at__year=date_info['current_year']
            )
            
            last_month_sales = Sales.objects.filter(
                created_at__month=date_info['last_month'],
                created_at__year=date_info['last_year']
            )
            
            # Apply user-specific filtering
            if not user.is_admin:
                this_month_sales = this_month_sales.filter(shop=user.shop)
                last_month_sales = last_month_sales.filter(shop=user.shop)
            
            # Calculate totals
            this_month_sales_total = this_month_sales.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            last_month_sales_total = last_month_sales.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            this_month_profit = this_month_sales.aggregate(
                total=Sum('profit')
            )['total'] or Decimal('0.00')
            
            last_month_profit = last_month_sales.aggregate(
                total=Sum('profit')
            )['total'] or Decimal('0.00')
            
            return {
                'this_month_sales_total': this_month_sales_total,
                'last_month_sales_total': last_month_sales_total,
                'this_month_profit': this_month_profit,
                'last_month_profit': last_month_profit,
                'sales_percent': DashboardUtilityService.percentage_change(
                    this_month_sales_total, last_month_sales_total
                ),
                'profits_percent': DashboardUtilityService.percentage_change(
                    this_month_profit, last_month_profit
                )
            }
            
        except Exception as e:
            logger.error(f"Error calculating sales metrics: {str(e)}")
            return {
                'this_month_sales_total': Decimal('0.00'),
                'last_month_sales_total': Decimal('0.00'),
                'this_month_profit': Decimal('0.00'),
                'last_month_profit': Decimal('0.00'),
                'sales_percent': "0.0%",
                'profits_percent': "0.0%"
            }
    
    @staticmethod
    def get_user_metrics(user) -> Dict[str, int]:
        """Calculate user activity metrics"""
        try:
            now = timezone.now()
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
            
            active_users = CustomUser.objects.filter(deleted=False, is_active=True).exclude(is_admin=True)
            
            if not user.is_admin:
                active_users = active_users.filter(shop=user.shop)
            
            users_this_week = active_users.filter(last_login__gte=start_of_week, last_login__lte=now)
            
            return {
                'active_users': active_users.count(),
                'weekly_users': users_this_week.count()
            }
            
        except Exception as e:
            logger.error(f"Error calculating user metrics: {str(e)}")
            return {'active_users': 0, 'weekly_users': 0}
    
    @staticmethod
    def get_inventory_metrics(user) -> Dict[str, Any]:
        """Calculate inventory and stock metrics"""
        try:
            now = timezone.now()
            low_stock_count = Product.objects.filter(is_deleted=False, qty__lt=5)
            
            if not user.is_admin:
                low_stock_count = low_stock_count.filter(shop=user.shop)
            
            # Get stock distribution by shop
            shops_list, stock_distribution = [], []
            select_shops = Shop.objects.all()
            
            if not user.is_admin:
                select_shops = select_shops.filter(id=user.shop_id)
            
            for shop in select_shops:
                shops_list.append(shop.abbrev)
                items_count = Product.objects.filter(
                    is_hidden=False, 
                    is_deleted=False, 
                    shop=shop
                ).filter(
                    Q(expiry_date__isnull=True) | Q(expiry_date__gt=now.date())
                )
                stock_distribution.append(items_count.count())
            
            return {
                'low_stock_count': low_stock_count.count(),
                'stock_distribution': stock_distribution,
                'stock_shops': shops_list
            }
            
        except Exception as e:
            logger.error(f"Error calculating inventory metrics: {str(e)}")
            return {
                'low_stock_count': 0,
                'stock_distribution': [],
                'stock_shops': []
            }


class DashboardSalesService:
    """Service class for sales-related dashboard operations"""
    
    @staticmethod
    def get_weekly_shop_sales(user) -> List[Dict[str, Any]]:
        """Get weekly sales data for shops"""
        try:
            today = timezone.now().date()
            sales_data = []
            
            # Precompute the last 7 days (6 days ago, ..., yesterday, today)
            days = [today - timedelta(days=i) for i in reversed(range(7))]
            
            # For optimization: Fetch all sales in the past 7 days
            last_7_days = today - timedelta(days=6)
            sales_qs = Sales.objects.filter(created_at__date__gte=last_7_days)
            shops_qs = Shop.objects.all()
            
            if not user.is_admin:
                sales_qs = sales_qs.filter(shop=user.shop)
                shops_qs = [user.shop]
            
            # Group by shop and by day
            grouped_sales = defaultdict(lambda: [0] * 7)
            
            for sale in sales_qs:
                shop_abbrev = sale.shop.abbrev
                sale_date = sale.created_at.date()
                if sale_date in days:
                    index = days.index(sale_date)
                    grouped_sales[shop_abbrev][index] += float(sale.amount)
            
            # Build final structured list
            for shop in shops_qs:
                sales_data.append({
                    "name": shop.abbrev,
                    "data": grouped_sales[shop.abbrev]
                })
            
            return sales_data
            
        except Exception as e:
            logger.error(f"Error getting weekly shop sales: {str(e)}")
            return []
    
    @staticmethod
    def get_recent_sales(user) -> List[Dict[str, Any]]:
        """Get recent sales transactions"""
        try:
            recent_sales = Sale_items.objects.all()
            
            if not user.is_admin:
                recent_sales = recent_sales.filter(sale__shop=user.shop)
            
            recent_sales = recent_sales.order_by('-sale__created_at')[:9]
            recent_sales_list = []
            count_sales = 1
            
            for sales in recent_sales:
                recent_sales_list.append({
                    'count': count_sales,
                    'product': sales.product.name,
                    'qty': format_number(sales.qty),
                    'amount': format_number(sales.qty * sales.price),
                    'shop': sales.sale.shop.abbrev,
                    'user': 'Admin' if sales.sale.user.is_admin else sales.sale.user.username,
                    'date': DashboardUtilityService.format_sale_date(sales.sale.created_at)
                })
                count_sales += 1
            
            return recent_sales_list
            
        except Exception as e:
            logger.error(f"Error getting recent sales: {str(e)}")
            return []


class DashboardUtilityService:
    """Service class for dashboard utility functions"""
    
    @staticmethod
    def percentage_change(current, previous):
        """Calculate percentage change between two values"""
        try:
            if previous == 0:
                return "+100%" if current > 0 else "0.0%"
            change = ((current - previous) / previous) * 100
            return f"{change:+.1f}%"
        except Exception as e:
            logger.error(f"Error calculating percentage change: {str(e)}")
            return "0.0%"
    
    @staticmethod
    def format_currency_display(amount):
        """Format currency amount for display"""
        try:
            if amount >= 1_000_000:
                formatted = amount / 1_000_000
                return f"{formatted:.2f}M"
            elif amount >= 1_000:
                formatted = amount / 1_000
                return f"{formatted:.2f}k"
            else:
                return f"{amount:.2f}"
        except Exception as e:
            logger.error(f"Error formatting currency: {str(e)}")
            return "0.00"
    
    @staticmethod
    def format_sale_date(dt):
        """Format sale date for display"""
        try:
            dt_local = localtime(dt)
            now_local = localtime(timezone.now())
            
            today = now_local.date()
            yesterday = today - timedelta(days=1)
            
            if dt_local.date() == today:
                return f"Today {dt_local.strftime('%H:%M')}"
            elif dt_local.date() == yesterday:
                return f"Yesterday {dt_local.strftime('%H:%M')}"
            else:
                return dt_local.strftime('%d-%b-%Y %H:%M')
        except Exception as e:
            logger.error(f"Error formatting sale date: {str(e)}")
            return "Unknown"


class DashboardDataService:
    """Service class for aggregating all dashboard data"""
    
    @staticmethod
    def get_dashboard_context(user) -> Dict[str, Any]:
        """Get complete dashboard context data"""
        try:
            # Get date information
            date_info = DashboardMetricsService.get_current_and_previous_month()
            
            # Get various metrics
            sales_metrics = DashboardMetricsService.get_sales_metrics(user, date_info)
            user_metrics = DashboardMetricsService.get_user_metrics(user)
            inventory_metrics = DashboardMetricsService.get_inventory_metrics(user)
            
            # Get sales data
            weekly_sales_data = DashboardSalesService.get_weekly_shop_sales(user)
            recent_sales_data = DashboardSalesService.get_recent_sales(user)
            
            # Build complete context
            context = {
                'total_sales': DashboardUtilityService.format_currency_display(
                    float(sales_metrics['this_month_sales_total'])
                ),
                'sales_percent': sales_metrics['sales_percent'],
                'total_profits': DashboardUtilityService.format_currency_display(
                    float(sales_metrics['this_month_profit'])
                ),
                'profits_percent': sales_metrics['profits_percent'],
                'low_stock_count': inventory_metrics['low_stock_count'],
                'active_users': user_metrics['active_users'],
                'weekly_users': user_metrics['weekly_users'],
                'shops_sales_data': weekly_sales_data,
                'stock_distribution': inventory_metrics['stock_distribution'],
                'stock_shops': inventory_metrics['stock_shops'],
                'recent_sales': recent_sales_data
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting dashboard context: {str(e)}")
            # Return safe default context
            return {
                'total_sales': "0.00",
                'sales_percent': "0.0%",
                'total_profits': "0.00",
                'profits_percent': "0.0%",
                'low_stock_count': 0,
                'active_users': 0,
                'weekly_users': 0,
                'shops_sales_data': [],
                'stock_distribution': [],
                'stock_shops': [],
                'recent_sales': []
            }


# =============================================
# VIEW FUNCTIONS
# =============================================

@login_required
@never_cache
def dashboard_page(request):
    """
    Handle dashboard page display with comprehensive metrics
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered dashboard template
    """
    try:
        # Get complete dashboard context using service
        context = DashboardDataService.get_dashboard_context(request.user)
        
        logger.info(f"Dashboard loaded successfully for user {request.user.username}")
        return render(request, 'dashboard/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading dashboard for user {request.user.id}: {str(e)}")
        
        # Return dashboard with empty/safe default values
        safe_context = {
            'total_sales': "0.00",
            'sales_percent': "0.0%",
            'total_profits': "0.00",
            'profits_percent': "0.0%",
            'low_stock_count': 0,
            'active_users': 0,
            'weekly_users': 0,
            'shops_sales_data': [],
            'stock_distribution': [],
            'stock_shops': [],
            'recent_sales': []
        }
        
        return render(request, 'dashboard/dashboard.html', safe_context)


# =============================================
# LEGACY FUNCTION SUPPORT (for backward compatibility)
# =============================================

def get_weekly_shop_sales(request):
    """
    Legacy function maintained for backward compatibility
    Use DashboardSalesService.get_weekly_shop_sales() instead
    """
    return DashboardSalesService.get_weekly_shop_sales(request.user)


def percentage_change(current, previous):
    """
    Legacy function maintained for backward compatibility
    Use DashboardUtilityService.percentage_change() instead
    """
    return DashboardUtilityService.percentage_change(current, previous)


def format_currency_display(amount):
    """
    Legacy function maintained for backward compatibility
    Use DashboardUtilityService.format_currency_display() instead
    """
    return DashboardUtilityService.format_currency_display(amount)


def format_sale_date(dt):
    """
    Legacy function maintained for backward compatibility
    Use DashboardUtilityService.format_sale_date() instead
    """
    return DashboardUtilityService.format_sale_date(dt)