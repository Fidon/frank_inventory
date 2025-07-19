import logging
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, QuerySet
from datetime import date
from dateutil.parser import parse
import zoneinfo
from decimal import Decimal
from typing import Dict, Any, List, Optional
from .forms import ShopForm, ShopUpdateForm, ProductForm, ProductUpdateForm
from .models import Shop, Product, Cart, Sales, Sale_items
from apps.users.models import CustomUser
from utils.util_functions import admin_required, conv_timezone, filter_items, format_number

# Configure logging
logger = logging.getLogger(__name__)

# =============================================
# SHOP MANAGEMENT SERVICES
# =============================================

class ShopManagementService:
    """Service class for handling shop management operations"""

    @staticmethod
    def create_shop(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new shop with the provided data
        
        Args:
            post_data: Form data for shop creation
            
        Returns:
            Dict containing success status and message
        """
        try:
            form = ShopForm(post_data)
            if form.is_valid():
                form.save()
                logger.info("New shop created successfully")
                return {'success': True, 'sms': 'New shop added successfully.'}
            
            error_msg = ShopManagementService._extract_form_error(form, ['names', 'abbrev', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error creating shop: {str(e)}")
            return {'success': False, 'sms': 'Failed to create shop. Please try again.'}

    @staticmethod
    def update_shop(post_data: Dict[str, Any], shop_id: int) -> Dict[str, Any]:
        """
        Update an existing shop with the provided data
        
        Args:
            post_data: Form data for shop update
            shop_id: ID of the shop to update
            
        Returns:
            Dict containing success status and message
        """
        try:
            shop = ShopManagementService._get_shop(shop_id)
            if not shop:
                return {'success': False, 'sms': 'Shop not found.'}
            
            form = ShopUpdateForm(post_data, instance=shop)
            if form.is_valid():
                form.save()
                logger.info(f"Shop {shop_id} updated successfully")
                return {
                    'success': True,
                    'update_success': True,
                    'sms': 'Shop info updated successfully.'
                }
            
            error_msg = ShopManagementService._extract_form_error(form, ['names', 'abbrev', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error updating shop {shop_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to update shop. Please try again.'}

    @staticmethod
    def delete_shop(shop_id: int) -> Dict[str, Any]:
        """
        Delete a shop
        
        Args:
            shop_id: ID of the shop to delete
            
        Returns:
            Dict containing success status and redirect URL
        """
        try:
            if shop_id == 1:
                return {'success': False, 'sms': 'Cannot delete the main shop.'}
            
            shop = ShopManagementService._get_shop(shop_id)
            if not shop:
                return {'success': False, 'sms': 'Operation failed.'}
            
            shop.delete()
            logger.info(f"Shop {shop_id} deleted successfully")
            return {'success': True, 'url': reverse('shops_page')}
            
        except Exception as e:
            logger.error(f"Error deleting shop {shop_id}: {str(e)}")
            return {'success': False, 'sms': 'Operation failed.'}

    @staticmethod
    def get_shop_details(shop_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a shop
        
        Args:
            shop_id: ID of the shop to get details for
            
        Returns:
            Dict containing shop details or None if not found
        """
        try:
            shop = ShopManagementService._get_shop(shop_id)
            if not shop:
                return None
            
            net_worth_aggregation = Product.objects.filter(shop=shop, is_deleted=False).aggregate(
                total_value=Sum(F('qty') * F('price'))
            )
            net_worth = net_worth_aggregation['total_value'] or 0
            
            return {
                'id': shop.id,
                'regdate': conv_timezone(shop.created_at, '%d-%b-%Y %H:%M:%S'),
                'names': shop.names,
                'abbrev': shop.abbrev,
                'comment': shop.comment or 'N/A',
                'users_count': format_number(CustomUser.objects.filter(shop=shop, deleted=False).count()),
                'items_count': format_number(Product.objects.filter(shop=shop, is_deleted=False).count()),
                'networth': format_number(net_worth),
                'delete_info': False if shop.id == 1 else True
            }
            
        except Exception as e:
            logger.error(f"Error getting shop details {shop_id}: {str(e)}")
            return None

    @staticmethod
    def _get_shop(shop_id: int) -> Optional[Shop]:
        """Get a shop by ID"""
        try:
            return Shop.objects.get(pk=shop_id)
        except Shop.DoesNotExist:
            return None

    @staticmethod
    def _extract_form_error(form, field_names: List[str]) -> str:
        """Extract the first error message from specified form fields"""
        for field_name in field_names:
            if form.errors.get(field_name):
                return form.errors[field_name][0]
        return "Unknown error, reload & try again"

# =============================================
# PRODUCT MANAGEMENT SERVICES
# =============================================

class ProductManagementService:
    """Service class for handling product management operations"""

    @staticmethod
    def create_product(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product with the provided data
        
        Args:
            post_data: Form data for product creation
            
        Returns:
            Dict containing success status and message
        """
        try:
            form = ProductForm(post_data)
            if form.is_valid():
                form.save()
                logger.info("New product created successfully")
                return {'success': True, 'sms': 'New item added successfully.'}
            
            error_msg = ProductManagementService._extract_form_error(
                form, ['name', 'qty', 'cost', 'price', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            return {'success': False, 'sms': 'Failed to create product. Please try again.'}

    @staticmethod
    def update_product(post_data: Dict[str, Any], product_id: int) -> Dict[str, Any]:
        """
        Update an existing product with the provided data
        
        Args:
            post_data: Form data for product update
            product_id: ID of the product to update
            
        Returns:
            Dict containing success status and message
        """
        try:
            product = ProductManagementService._get_active_product(product_id)
            if not product:
                return {'success': False, 'sms': 'Item not found.'}
            
            form = ProductUpdateForm(post_data, instance=product)
            if form.is_valid():
                form.save()
                logger.info(f"Product {product_id} updated successfully")
                return {
                    'success': True,
                    'update_success': True,
                    'sms': 'Item info updated successfully.'
                }
            
            error_msg = ProductManagementService._extract_form_error(
                form, ['name', 'qty', 'cost', 'price', 'comment'])
            return {'success': False, 'sms': error_msg}
            
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to update product. Please try again.'}

    @staticmethod
    def delete_product(product_id: int) -> Dict[str, Any]:
        """
        Soft delete a product
        
        Args:
            product_id: ID of the product to delete
            
        Returns:
            Dict containing success status and redirect URL
        """
        try:
            product = ProductManagementService._get_active_product(product_id)
            if not product:
                return {'success': False, 'sms': 'Failed to delete product.'}
            
            product.is_deleted = True
            product.name = f"{product.name} (deleted)"
            product.save()
            logger.info(f"Product {product_id} deleted successfully")
            return {'success': True, 'url': reverse('products_page')}
            
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to delete product.'}

    @staticmethod
    def toggle_product_status(product_id: int) -> Dict[str, Any]:
        """
        Toggle product hidden/visible status
        
        Args:
            product_id: ID of the product to toggle
            
        Returns:
            Dict containing success status
        """
        try:
            product = ProductManagementService._get_active_product(product_id)
            if not product:
                return {'success': False, 'sms': 'Failed to block/unblock product.'}
            
            product.is_hidden = not product.is_hidden
            product.save()
            status = "blocked" if product.is_hidden else "unblocked"
            logger.info(f"Product {product_id} {status} successfully")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error toggling product status {product_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to block/unblock product.'}

    @staticmethod
    def update_product_quantity(product_id: int, new_qty: str) -> Dict[str, Any]:
        """
        Update product quantity
        
        Args:
            product_id: ID of the product to update
            new_qty: New quantity value
            
        Returns:
            Dict containing success status and message
        """
        try:
            qty_value = Decimal(new_qty)
            if qty_value < 1:
                return {'success': False, 'sms': 'Quantity must be at least 1.'}
            
            product = ProductManagementService._get_active_product(product_id)
            if not product:
                return {'success': False, 'sms': 'Failed to update quantity.'}
            
            product.qty += qty_value
            product.save()
            logger.info(f"Quantity updated for product {product_id}")
            return {'success': True, 'sms': 'Item stock updated.'}
            
        except Exception as e:
            logger.error(f"Error updating quantity for product {product_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to update quantity.'}

    @staticmethod
    def get_product_details(product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a product
        
        Args:
            product_id: ID of the product to get details for
            
        Returns:
            Dict containing product details or None if not found
        """
        try:
            product = ProductManagementService._get_active_product(product_id)
            if not product:
                return None
            
            grand_total = Sale_items.objects.filter(product=product).aggregate(
                total_sales=Sum(F('price') * F('qty'))
            )
            sales_total = grand_total['total_sales'] or 0
            
            product_status = "Sold Out" if product.qty == 0 else (
                "Blocked" if product.is_hidden else
                "Expired" if product.expiry_date and product.expiry_date <= date.today() else
                "Available"
            )
            
            return {
                'id': product.id,
                'regdate': conv_timezone(product.created_at, '%d-%b-%Y %H:%M:%S'),
                'lastupdated': conv_timezone(product.updated_at, '%d-%b-%Y %H:%M:%S'),
                'shop': product.shop,
                'name': product.name,
                'cost': product.cost,
                'price': product.price,
                'qty': product.qty,
                'cost_txt': format_number(product.cost),
                'price_txt': format_number(product.price),
                'qty_txt': format_number(product.qty),
                'status': product_status,
                'active': 'no' if product.is_hidden else 'yes',
                'expiry': product.expiry_date,
                'expiry_date': product.expiry_date.strftime('%d-%b-%Y') if product.expiry_date else "N/A",
                'comment': product.comment or 'N/A',
                'sales': format_number(sales_total),
                'shops_list': Shop.objects.all().order_by('abbrev')
            }
            
        except Exception as e:
            logger.error(f"Error getting product details {product_id}: {str(e)}")
            return None

    @staticmethod
    def _get_active_product(product_id: int) -> Optional[Product]:
        """Get an active (non-deleted) product by ID"""
        try:
            return Product.objects.get(pk=product_id, is_deleted=False)
        except Product.DoesNotExist:
            return None

    @staticmethod
    def _extract_form_error(form, field_names: List[str]) -> str:
        """Extract the first error message from specified form fields"""
        for field_name in field_names:
            if form.errors.get(field_name):
                return form.errors[field_name][0]
        return "Unknown error, reload & try again"

# =============================================
# SALES MANAGEMENT SERVICES
# =============================================

class SalesManagementService:
    """Service class for handling sales operations"""

    @staticmethod
    def add_to_cart(request: HttpRequest, product_id: str, qty: str) -> Dict[str, Any]:
        """
        Add product to user's cart
        
        Args:
            request: HTTP request object
            product_id: ID of the product to add
            qty: Quantity to add
            
        Returns:
            Dict containing success status and message
        """
        try:
            product_qty = Decimal(qty)
            product = ProductManagementService._get_active_product(int(product_id))
            
            if not product:
                return {'success': False, 'sms': 'Product not found.'}
            
            if product_qty > product.qty:
                return {'success': False, 'sms': f'Qty exceeded available stock ({product.qty}).'}
            
            cart_item, created = Cart.objects.get_or_create(
                product=product,
                user=request.user,
                defaults={'qty': product_qty}
            )
            
            cart_count = Cart.objects.filter(user=request.user).count()
            cart_count_display = str(cart_count) if cart_count < 10 else '9+'
            
            logger.info(f"Added {product_qty} items to cart for user {request.user.id}")
            return {
                'success': True,
                'sms': f'{format_number(product_qty)} items added to cart.',
                'cart': cart_count_display
            }
            
        except Exception as e:
            logger.error(f"Error adding to cart for user {request.user.id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to add to cart.'}

    @staticmethod
    def delete_cart_item(cart_id: int, user: CustomUser) -> Dict[str, Any]:
        """
        Delete a cart item
        
        Args:
            cart_id: ID of the cart item to delete
            user: User object
            
        Returns:
            Dict containing success status and cart information
        """
        try:
            cart_item = Cart.objects.get(id=cart_id, user=user)
            cart_item.delete()
            
            items_remaining = Cart.objects.filter(user=user)
            cart_count = items_remaining.count()
            cart_count_display = str(cart_count) if cart_count < 10 else '9+'
            grand_total = sum(item.product.price * item.qty for item in items_remaining)
            
            logger.info(f"Cart item {cart_id} deleted for user {user.id}")
            return {
                'success': True,
                'cart': cart_count_display,
                'grand_total': f"TZS. {format_number(grand_total)}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting cart item {cart_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to delete cart item.'}

    @staticmethod
    def clear_cart(user: CustomUser) -> Dict[str, Any]:
        """
        Clear all cart items for a user
        
        Args:
            user: User object
            
        Returns:
            Dict containing success status
        """
        try:
            Cart.objects.filter(user=user).delete()
            logger.info(f"Cart cleared for user {user.id}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error clearing cart for user {user.id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to clear cart.'}

    @staticmethod
    def checkout(request: HttpRequest, customer: str, comment: str) -> Dict[str, Any]:
        """
        Process cart checkout
        
        Args:
            request: HTTP request object
            customer: Customer name
            comment: Sale comment
            
        Returns:
            Dict containing success status and message
        """
        try:
            full_cart = Cart.objects.filter(user=request.user)
            if not full_cart:
                return {'success': False, 'sms': 'Cart is empty.'}
            
            grand_amount, qty_status, qty_products = 0, True, []
            cart_shops = set()
            
            for item in full_cart:
                grand_amount += item.product.price * item.qty
                cart_shops.add(item.product.shop)
                if item.qty > item.product.qty:
                    qty_status = False
                    qty_products.append(item.product.name)
            
            if len(cart_shops) > 1:
                return {'success': False, 'sms': 'All products must be from the same shop to checkout.'}
            
            if not qty_status:
                return {'success': False, 'sms': f'Not enough stock for: {", ".join(qty_products)}'}
            
            sale_transaction = Sales.objects.create(
                user=request.user,
                amount=grand_amount,
                customer='n/a' if not customer.strip() else customer.strip(),
                comment=None if not comment.strip() else comment.strip(),
                shop=list(cart_shops)[0]
            )
            
            for item in full_cart:
                Sale_items.objects.create(
                    sale=sale_transaction,
                    product=item.product,
                    price=item.product.price,
                    qty=item.qty
                )
                item.product.qty -= item.qty
                item.product.save()
                item.delete()
            
            logger.info(f"Checkout completed for user {request.user.id}")
            return {'success': True, 'sms': 'Checkout completed successfully!'}
            
        except Exception as e:
            logger.error(f"Error during checkout for user {request.user.id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to complete checkout.'}

    @staticmethod
    def remove_sale_item(item_id: int) -> Dict[str, Any]:
        """
        Remove an item from a sale and update related records
        
        Args:
            item_id: ID of the sale item to remove
            
        Returns:
            Dict containing success status and message
        """
        try:
            item = Sale_items.objects.get(id=item_id)
            sale = item.sale
            product = item.product
            
            product.qty += item.qty
            sale.amount -= (item.price * item.qty)
            sale.save()
            product.save()
            item.delete()
            
            if not Sale_items.objects.filter(sale=sale).exists():
                sale.delete()
                logger.info(f"Sale {sale.id} deleted as no items remain")
                return {'success': True, 'sales_page': reverse('sales_report'), 'items': 0}
            
            logger.info(f"Sale item {item_id} removed successfully")
            return {'success': True, 'sms': 'Item removed successfully.', 'items': 1}
            
        except Exception as e:
            logger.error(f"Error removing sale item {item_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to remove sale item.'}

    @staticmethod
    def delete_sale(sale_id: int) -> Dict[str, Any]:
        """
        Delete a sale and restore product quantities
        
        Args:
            sale_id: ID of the sale to delete
            
        Returns:
            Dict containing success status and redirect URL
        """
        try:
            sale = Sales.objects.get(id=sale_id)
            sale_items = Sale_items.objects.filter(sale=sale)
            
            for item in sale_items:
                product = item.product
                product.qty += item.qty
                product.save()
                item.delete()
            
            sale.delete()
            logger.info(f"Sale {sale_id} deleted successfully")
            return {'success': True, 'sales_page': reverse('sales_page')}
            
        except Exception as e:
            logger.error(f"Error deleting sale {sale_id}: {str(e)}")
            return {'success': False, 'sms': 'Failed to delete sale.'}

# =============================================
# DATATABLES UTILITIES
# =============================================

class ShopDataTablesService:
    """Service class for handling shop DataTables functionality"""

    COLUMN_MAPPING = {
        0: 'id',
        1: 'names',
        2: 'abbrev',
        3: 'regdate',
        4: 'users_count',
        5: 'items_count',
        6: 'networth'
    }

    COLUMN_FILTER_TYPES = {
        'users_count': 'numeric',
        'items_count': 'numeric',
        'networth': 'numeric'
    }

    @staticmethod
    def prepare_shop_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Convert shop queryset to list of dicts for DataTables
        
        Args:
            queryset: Shop queryset
            
        Returns:
            List of shop data dicts
        """
        return [
            {
                'id': shop.id,
                'regdate': shop.created_at,
                'names': shop.names,
                'abbrev': shop.abbrev,
                'users_count': CustomUser.objects.filter(shop=shop, deleted=False).count(),
                'items_count': Product.objects.filter(shop=shop, is_deleted=False).count(),
                'networth': Product.objects.filter(shop=shop, is_deleted=False).aggregate(
                    total_value=Sum(F('qty') * F('price'))
                )['total_value'] or 0,
                'info': reverse('shop_details', kwargs={'shopid': shop.id})
            }
            for shop in queryset
        ]

    @staticmethod
    def format_final_data(data: List[Dict], start: int, length: int) -> List[Dict]:
        """
        Format shop data for final DataTables response
        
        Args:
            data: List of shop data dicts
            start: Start index for pagination
            length: Page length
            
        Returns:
            Formatted shop data list
        """
        page_number = start // length + 1 if length > 0 else 1
        row_count_start = (page_number - 1) * length + 1
        
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'regdate': conv_timezone(item.get('regdate'), '%d-%b-%Y'),
                'names': item.get('names'),
                'abbrev': item.get('abbrev'),
                'users_count': format_number(item.get('users_count')),
                'items_count': format_number(item.get('items_count', 0)),
                'networth': format_number(item.get('networth', 0)) + " TZS",
                'info': item.get('info')
            }
            for i, item in enumerate(data)
        ]

class ProductDataTablesService:
    """Service class for handling product DataTables functionality"""

    COLUMN_MAPPING = {
        0: 'id',
        1: 'name',
        2: 'shop',
        3: 'qty',
        4: 'cost',
        5: 'price',
        6: 'status'
    }

    COLUMN_FILTER_TYPES = {
        'shop': 'exact',
        'qty': 'numeric',
        'cost': 'numeric',
        'price': 'numeric',
        'status': 'exact'
    }

    @staticmethod
    def prepare_product_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Convert product queryset to list of dicts for DataTables
        
        Args:
            queryset: Product queryset
            
        Returns:
            List of product data dicts
        """
        return [
            {
                'id': item.id,
                'name': item.name,
                'shop': item.shop.abbrev,
                'qty': item.qty,
                'cost': item.cost,
                'price': item.price,
                'status': ProductDataTablesService._get_product_status(item),
                'info': reverse('product_details', kwargs={'itemid': item.id})
            }
            for item in queryset
        ]

    @staticmethod
    def _get_product_status(item: Product) -> str:
        """Determine product status based on quantity, visibility, and expiry"""
        if item.qty == 0:
            return "SoldOut"
        if item.is_hidden:
            return "Blocked"
        if item.expiry_date and item.expiry_date <= date.today():
            return "Expired"
        return "Active"

    @staticmethod
    def format_final_data(data: List[Dict], start: int, length: int) -> List[Dict]:
        """
        Format product data for final DataTables response
        
        Args:
            data: List of product data dicts
            start: Start index for pagination
            length: Page length
            
        Returns:
            Formatted product data list
        """
        page_number = start // length + 1 if length > 0 else 1
        row_count_start = (page_number - 1) * length + 1
        
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'name': item.get('name'),
                'shop': item.get('shop'),
                'qty': format_number(item.get('qty')),
                'cost': format_number(item.get('cost')) + " TZS",
                'price': format_number(item.get('price')) + " TZS",
                'status': item.get('status'),
                'info': item.get('info')
            }
            for i, item in enumerate(data)
        ]

class SalesDataTablesService:
    """Service class for handling sales DataTables functionality"""

    COLUMN_MAPPING = {
        0: 'id',
        1: 'name',
        2: 'qty',
        3: 'price'
    }

    COLUMN_FILTER_TYPES = {
        'qty': 'numeric',
        'price': 'numeric'
    }

    @staticmethod
    def prepare_sales_data(queryset: QuerySet, user: CustomUser) -> List[Dict[str, Any]]:
        """
        Convert product queryset to list of dicts for sales DataTables
        
        Args:
            queryset: Product queryset
            user: Current user
            
        Returns:
            List of sales data dicts
        """
        return [
            {
                'id': product.id,
                'name': product.name,
                'qty': product.qty,
                'price': product.price,
                'cart': Cart.objects.filter(user=user, product=product).first().qty
                if Cart.objects.filter(user=user, product=product).exists() else 0
            }
            for product in queryset
            if product.expiry_date is None or product.expiry_date > date.today()
        ]

    @staticmethod
    def format_final_data(data: List[Dict], start: int, length: int) -> List[Dict]:
        """
        Format sales data for final DataTables response
        
        Args:
            data: List of sales data dicts
            start: Start index for pagination
            length: Page length
            
        Returns:
            Formatted sales data list
        """
        page_number = start // length + 1 if length > 0 else 1
        row_count_start = (page_number - 1) * length + 1
        
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'name': item.get('name'),
                'qty': format_number(item.get('qty')),
                'price': format_number(item.get('price')) + " TZS",
                'sell_qty': format_number(item.get('qty')),
                'cart': format_number(item.get('cart')),
                'action': ''
            }
            for i, item in enumerate(data)
        ]

class SalesReportDataTablesService:
    """Service class for handling sales report DataTables functionality"""

    COLUMN_MAPPING = {
        0: 'sale_items',
        1: 'id',
        2: 'saledate',
        3: 'shop',
        4: 'amount',
        5: 'customer',
        6: 'user'
    }

    COLUMN_FILTER_TYPES = {
        'shop': 'exact',
        'amount': 'numeric'
    }

    @staticmethod
    def prepare_sales_report_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Convert sales queryset to list of dicts for DataTables
        
        Args:
            queryset: Sales queryset
            
        Returns:
            List of sales report data dicts
        """
        return [
            {
                'id': sale.id,
                'saledate': sale.created_at,
                'shop': sale.shop.abbrev,
                'user': sale.user.username if not sale.user.deleted else f"{sale.user.username} (deleted)",
                'customer': sale.customer,
                'amount': sale.amount,
                'sale_items': [
                    {
                        'count': idx + 1,
                        'names': item.product.name,
                        'price': format_number(item.price) + " TZS",
                        'qty': format_number(item.qty),
                        'total': format_number(item.price * item.qty) + " TZS"
                    }
                    for idx, item in enumerate(Sale_items.objects.filter(sale=sale))
                ]
            }
            for sale in queryset
        ]

    @staticmethod
    def format_final_data(data: List[Dict], start: int, length: int) -> List[Dict]:
        """
        Format sales report data for final DataTables response
        
        Args:
            data: List of sales report data dicts
            start: Start index for pagination
            length: Page length
            
        Returns:
            Formatted sales report data list
        """
        page_number = start // length + 1 if length > 0 else 1
        row_count_start = (page_number - 1) * length + 1
        
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'saledate': conv_timezone(item.get('saledate'), '%d-%b-%Y %H:%M:%S'),
                'shop': item.get('shop'),
                'user': item.get('user'),
                'customer': item.get('customer'),
                'amount': format_number(item.get('amount')) + " TZS",
                'items': item.get('sale_items')
            }
            for i, item in enumerate(data)
        ]

class SalesItemsReportDataTablesService:
    """Service class for handling sales items report DataTables functionality"""

    COLUMN_MAPPING = {
        0: 'id',
        1: 'saledate',
        2: 'shop',
        3: 'product',
        4: 'price',
        5: 'qty',
        6: 'amount',
        7: 'user'
    }

    COLUMN_FILTER_TYPES = {
        'shop': 'exact',
        'amount': 'numeric',
        'price': 'numeric',
        'qty': 'numeric'
    }

    @staticmethod
    def prepare_sales_items_data(queryset: QuerySet) -> List[Dict[str, Any]]:
        """
        Convert sale items queryset to list of dicts for DataTables
        
        Args:
            queryset: Sale items queryset
            
        Returns:
            List of sale items data dicts
        """
        return [
            {
                'id': item.id,
                'saledate': item.sale.created_at,
                'shop': item.sale.shop.abbrev,
                'product': item.product.name,
                'price': item.price,
                'qty': item.qty,
                'amount': item.price * item.qty,
                'user': item.sale.user.username if not item.sale.user.deleted else f"{item.sale.user.username} (deleted)"
            }
            for item in queryset
        ]

    @staticmethod
    def format_final_data(data: List[Dict], start: int, length: int) -> List[Dict]:
        """
        Format sale items data for final DataTables response
        
        Args:
            data: List of sale items data dicts
            start: Start index for pagination
            length: Page length
            
        Returns:
            Formatted sale items data list
        """
        page_number = start // length + 1 if length > 0 else 1
        row_count_start = (page_number - 1) * length + 1
        
        return [
            {
                'count': row_count_start + i,
                'id': item.get('id'),
                'saledate': conv_timezone(item.get('saledate'), '%d-%b-%Y %H:%M:%S'),
                'shop': item.get('shop'),
                'product': item.get('product'),
                'price': format_number(item.get('price')) + " TZS",
                'qty': format_number(item.get('qty')),
                'amount': format_number(item.get('amount')) + " TZS",
                'user': item.get('user')
            }
            for i, item in enumerate(data)
        ]

class DataTablesBaseService:
    """Base service class for common DataTables functionality"""

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
            'end_date_str': request.POST.get('enddate')
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
    def apply_sorting(data: List[Dict], order_column_index: int, order_dir: str, column_mapping: Dict) -> List[Dict]:
        """
        Apply sorting to data list
        
        Args:
            data: List of data dicts
            order_column_index: Column index to sort by
            order_dir: Sort direction ('asc' or 'desc')
            column_mapping: Mapping of column indices to field names
            
        Returns:
            Sorted data list
        """
        order_column_name = column_mapping.get(order_column_index, list(column_mapping.values())[0])
        reverse_order = order_dir != 'asc'
        
        def none_safe_sort(item):
            value = item.get(order_column_name)
            return (value is None, value)
        
        return sorted(data, key=none_safe_sort, reverse=reverse_order)

    @staticmethod
    def apply_column_filtering(data: List[Dict], request: HttpRequest, column_mapping: Dict, column_filter_types: Dict) -> List[Dict]:
        """
        Apply individual column filtering
        
        Args:
            data: List of data dicts
            request: HTTP request object
            column_mapping: Mapping of column indices to field names
            column_filter_types: Mapping of field names to filter types
            
        Returns:
            Filtered data list
        """
        filtered_data = data
        
        for i in range(len(column_mapping)):
            column_search = request.POST.get(f'columns[{i}][search][value]', '')
            if column_search:
                column_field = column_mapping.get(i)
                if column_field:
                    filter_type = column_filter_types.get(column_field, 'contains')
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

# =============================================
# VIEW FUNCTIONS
# =============================================

@never_cache
@login_required
@require_POST
@admin_required()
def shops_requests(request: HttpRequest) -> JsonResponse:
    """
    Handle various shop management requests via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with operation result
    """
    try:
        post_data = request.POST
        edit_shop = post_data.get('edit_shop')
        delete_shop = post_data.get('delete_shop')
        
        if delete_shop:
            result = ShopManagementService.delete_shop(int(delete_shop))
        elif edit_shop:
            result = ShopManagementService.update_shop(post_data, int(edit_shop))
        else:
            result = ShopManagementService.create_shop(post_data)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in shops_requests: {str(e)}")
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

@never_cache
@login_required
@admin_required()
def shops_page(request: HttpRequest) -> HttpResponse:
    """
    Handle shops page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        try:
            params = DataTablesBaseService.parse_datatables_request(request)
            queryset = Shop.objects.all()
            
            queryset = DataTablesBaseService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            base_data = ShopDataTablesService.prepare_shop_data(queryset)
            total_records = len(base_data)
            
            base_data = DataTablesBaseService.apply_sorting(
                base_data, params['order_column_index'], params['order_dir'],
                ShopDataTablesService.COLUMN_MAPPING
            )
            
            base_data = DataTablesBaseService.apply_column_filtering(
                base_data, request, ShopDataTablesService.COLUMN_MAPPING,
                ShopDataTablesService.COLUMN_FILTER_TYPES
            )
            
            base_data = DataTablesBaseService.apply_global_search(base_data, params['search_value'])
            records_filtered = len(base_data)
            
            paginated_data = DataTablesBaseService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            final_data = ShopDataTablesService.format_final_data(
                paginated_data, params['start'], params['length']
            )
            
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in shops_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    return render(request, 'shops/shops.html', {'shops': Shop.objects.all().order_by('-created_at')})

@never_cache
@login_required
@admin_required()
@require_GET
def shop_details(request: HttpRequest, shopid: int) -> HttpResponse:
    """
    Display detailed shop information page
    
    Args:
        request: HTTP request object
        shopid: ID of the shop to display
        
    Returns:
        Rendered template or redirect
    """
    try:
        shop_data = ShopManagementService.get_shop_details(shopid)
        if not shop_data:
            return redirect('shops_page')
        
        return render(request, 'shops/shops.html', {
            'shopinfo': shopid,
            'info': shop_data,
            'delete_info': shop_data['delete_info']
        })
        
    except Exception as e:
        logger.error(f"Error in shop_details for shop {shopid}: {str(e)}")
        return redirect('shops_page')

@never_cache
@login_required
@admin_required()
def products_page(request: HttpRequest) -> HttpResponse:
    """
    Handle products page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        try:
            params = DataTablesBaseService.parse_datatables_request(request)
            queryset = Product.objects.filter(is_deleted=False)
            
            base_data = ProductDataTablesService.prepare_product_data(queryset)
            total_records = len(base_data)
            
            base_data = DataTablesBaseService.apply_sorting(
                base_data, params['order_column_index'], params['order_dir'],
                ProductDataTablesService.COLUMN_MAPPING
            )
            
            base_data = DataTablesBaseService.apply_column_filtering(
                base_data, request, ProductDataTablesService.COLUMN_MAPPING,
                ProductDataTablesService.COLUMN_FILTER_TYPES
            )
            
            base_data = DataTablesBaseService.apply_global_search(base_data, params['search_value'])
            records_filtered = len(base_data)
            
            paginated_data = DataTablesBaseService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            final_data = ProductDataTablesService.format_final_data(
                paginated_data, params['start'], params['length']
            )
            
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in products_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    return render(request, 'shops/products.html', {'shops': Shop.objects.all().order_by('-created_at')})

@never_cache
@login_required
@require_POST
@admin_required()
def products_requests(request: HttpRequest) -> JsonResponse:
    """
    Handle various product management requests via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with operation result
    """
    try:
        post_data = request.POST
        edit_product = post_data.get('edit_product')
        delete_product = post_data.get('delete_product')
        block_product = post_data.get('block_product')
        qty_product = post_data.get('qty_product')
        new_qty = post_data.get('qty_new')
        
        if qty_product and new_qty:
            result = ProductManagementService.update_product_quantity(int(qty_product), new_qty)
        elif block_product:
            result = ProductManagementService.toggle_product_status(int(block_product))
        elif delete_product:
            result = ProductManagementService.delete_product(int(delete_product))
        elif edit_product:
            result = ProductManagementService.update_product(post_data, int(edit_product))
        else:
            result = ProductManagementService.create_product(post_data)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in products_requests: {str(e)}")
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

@never_cache
@login_required
@admin_required()
@require_GET
def product_details(request: HttpRequest, itemid: int) -> HttpResponse:
    """
    Display detailed product information page
    
    Args:
        request: HTTP request object
        itemid: ID of the product to display
        
    Returns:
        Rendered template or redirect
    """
    try:
        product_data = ProductManagementService.get_product_details(itemid)
        if not product_data:
            return redirect('products_page')
        
        return render(request, 'shops/products.html', {
            'productinfo': True,
            'info': product_data
        })
        
    except Exception as e:
        logger.error(f"Error in product_details for product {itemid}: {str(e)}")
        return redirect('products_page')

@never_cache
@login_required
def sales_page(request: HttpRequest) -> HttpResponse:
    """
    Handle sales page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        try:
            params = DataTablesBaseService.parse_datatables_request(request)
            queryset = Product.objects.filter(is_deleted=False, is_hidden=False, qty__gt=0)
            if not request.user.is_admin:
                queryset = queryset.filter(shop=request.user.shop)
            
            base_data = SalesDataTablesService.prepare_sales_data(queryset, request.user)
            total_records = len(base_data)
            
            base_data = DataTablesBaseService.apply_sorting(
                base_data, params['order_column_index'], params['order_dir'],
                SalesDataTablesService.COLUMN_MAPPING
            )
            
            base_data = DataTablesBaseService.apply_column_filtering(
                base_data, request, SalesDataTablesService.COLUMN_MAPPING,
                SalesDataTablesService.COLUMN_FILTER_TYPES
            )
            
            base_data = DataTablesBaseService.apply_global_search(base_data, params['search_value'])
            records_filtered = len(base_data)
            
            paginated_data = DataTablesBaseService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            final_data = SalesDataTablesService.format_final_data(
                paginated_data, params['start'], params['length']
            )
            
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in sales_page DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    cart = Cart.objects.filter(user=request.user).order_by('id')
    grand_total = sum(item.product.price * item.qty for item in cart)
    cart_items = [
        {
            'id': item.id,
            'name': item.product.name,
            'price': f"TZS. {format_number(item.product.price)}",
            'qty': format_number(item.qty),
            'max_qty': item.product.qty
        }
        for item in cart
    ]
    
    context = {
        'cart_label': str(cart.count()) if cart.count() < 10 else '9+',
        'cart_count': cart.count(),
        'cart_items': cart_items,
        'total': f"TZS. {format_number(grand_total)}"
    }
    return render(request, 'shops/sales.html', context)

@never_cache
@login_required
@require_POST
def sales_actions(request: HttpRequest) -> JsonResponse:
    """
    Handle various sales-related actions via AJAX
    
    Args:
        request: HTTP request object
        
    Returns:
        JsonResponse with operation result
    """
    try:
        post_data = request.POST
        add_to_cart = post_data.get('cart_add')
        cart_delete = post_data.get('cart_delete')
        clear_cart = post_data.get('clear_cart')
        checkout = post_data.get('checkout')
        item_remove = post_data.get('item_remove')
        sales_delete = post_data.get('sales_delete')
        
        if add_to_cart:
            result = SalesManagementService.add_to_cart(
                request, post_data.get('product'), post_data.get('qty'))
        elif cart_delete:
            result = SalesManagementService.delete_cart_item(int(cart_delete), request.user)
        elif clear_cart:
            result = SalesManagementService.clear_cart(request.user)
        elif checkout:
            result = SalesManagementService.checkout(
                request, post_data.get('customer'), post_data.get('comment'))
        elif item_remove:
            result = SalesManagementService.remove_sale_item(int(item_remove))
        elif sales_delete:
            result = SalesManagementService.delete_sale(int(sales_delete))
        else:
            result = {'success': False, 'sms': 'Invalid action.'}
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error in sales_actions: {str(e)}")
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

@never_cache
@login_required
def sales_report(request: HttpRequest) -> HttpResponse:
    """
    Handle sales report page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        try:
            params = DataTablesBaseService.parse_datatables_request(request)
            queryset = Sales.objects.all() if request.user.is_admin else Sales.objects.filter(shop=request.user.shop)
            
            queryset = DataTablesBaseService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            base_data = SalesReportDataTablesService.prepare_sales_report_data(queryset)
            total_records = len(base_data)
            
            base_data = DataTablesBaseService.apply_sorting(
                base_data, params['order_column_index'], params['order_dir'],
                SalesReportDataTablesService.COLUMN_MAPPING
            )
            
            base_data = DataTablesBaseService.apply_column_filtering(
                base_data, request, SalesReportDataTablesService.COLUMN_MAPPING,
                SalesReportDataTablesService.COLUMN_FILTER_TYPES
            )
            
            base_data = DataTablesBaseService.apply_global_search(base_data, params['search_value'])
            records_filtered = len(base_data)
            
            grand_total_amount = sum(sale['amount'] for sale in base_data)
            
            paginated_data = DataTablesBaseService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            final_data = SalesReportDataTablesService.format_final_data(
                paginated_data, params['start'], params['length']
            )
            
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
                'grand_total': format_number(grand_total_amount) + " TZS"
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in sales_report DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    shops = Shop.objects.all() if request.user.is_admin else Shop.objects.filter(id=request.user.shop_id)
    return render(request, 'shops/sales_report.html', {'shops': shops.order_by('-created_at')})

@never_cache
@login_required
def sales_items_report(request: HttpRequest) -> HttpResponse:
    """
    Handle sales items report page display and DataTables AJAX requests
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or JSON response for AJAX
    """
    if request.method == 'POST':
        try:
            params = DataTablesBaseService.parse_datatables_request(request)
            queryset = Sale_items.objects.all() if request.user.is_admin else Sale_items.objects.filter(sale__shop=request.user.shop)
            
            queryset = DataTablesBaseService.apply_date_filtering(
                queryset, params['start_date_str'], params['end_date_str']
            )
            
            base_data = SalesItemsReportDataTablesService.prepare_sales_items_data(queryset)
            total_records = len(base_data)
            
            base_data = DataTablesBaseService.apply_sorting(
                base_data, params['order_column_index'], params['order_dir'],
                SalesItemsReportDataTablesService.COLUMN_MAPPING
            )
            
            base_data = DataTablesBaseService.apply_column_filtering(
                base_data, request, SalesItemsReportDataTablesService.COLUMN_MAPPING,
                SalesItemsReportDataTablesService.COLUMN_FILTER_TYPES
            )
            
            base_data = DataTablesBaseService.apply_global_search(base_data, params['search_value'])
            records_filtered = len(base_data)
            
            grand_total_amount = sum(item['amount'] for item in base_data)
            
            paginated_data = DataTablesBaseService.paginate_data(
                base_data, params['start'], params['length']
            )
            
            final_data = SalesItemsReportDataTablesService.format_final_data(
                paginated_data, params['start'], params['length']
            )
            
            ajax_response = {
                'draw': params['draw'],
                'recordsTotal': total_records,
                'recordsFiltered': records_filtered,
                'data': final_data,
                'grand_total': format_number(grand_total_amount) + " TZS"
            }
            return JsonResponse(ajax_response)
            
        except Exception as e:
            logger.error(f"Error in sales_items_report DataTables: {str(e)}")
            return JsonResponse({
                'draw': 0,
                'recordsTotal': 0,
                'recordsFiltered': 0,
                'data': [],
                'error': 'Failed to load data'
            })
    
    shops = Shop.objects.all().order_by('-created_at')
    return render(request, 'shops/items_report.html', {'shops': shops})