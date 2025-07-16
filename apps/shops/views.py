from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from .forms import ShopForm, ShopUpdateForm, ProductForm, ProductUpdateForm
from .models import Shop, Product, Cart, Sales, Sale_items
from apps.users.models import CustomUser
import zoneinfo
from dateutil.parser import parse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from utils.util_functions import admin_required, conv_timezone, filter_items, format_number
from decimal import Decimal
from django.db.models import Sum, F
from datetime import date


# method to add new shop
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


# method to update existing shop's info
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


# method to add new shop item/product
def register_shop_item(post_data):
    form = ProductForm(post_data)
    if form.is_valid():
        form.save()
        return {'success': True, 'sms': 'New item added successfully.'}
    
    errorMsg = (
        form.errors.get('name') or
        form.errors.get('qty') or
        form.errors.get('cost') or
        form.errors.get('price') or
        form.errors.get('comment')
    )
    errorMsg = errorMsg[0] if errorMsg else "Unknown error, reload & try again"
    return {'success': False, 'sms': errorMsg}


# method to update existing shop item
def update_shop_item(post_data, item_id):
    try:
        item = Product.objects.get(pk=item_id, is_deleted=False)
    except Product.DoesNotExist:
        return {'success': False, 'sms': 'Item not found.'}
    
    form = ProductUpdateForm(post_data, instance=item)
    if form.is_valid():
        form.save()
        return {'success': True, 'update_success': True, 'sms': 'Item info updated successfully.'}
    
    errorMsg = (
        form.errors.get('name') or
        form.errors.get('qty') or
        form.errors.get('cost') or
        form.errors.get('price') or
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
            if shop_id == 1:
                return JsonResponse({'success': False, 'sms': 'Cannot delete the main shop.'})
            
            try:
                Shop.objects.get(id=shop_id).delete()
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
            net_worth_aggregation = Product.objects.filter(shop=shop, is_deleted=False).aggregate(total_value=Sum(F('qty') * F('price')))
            net_worth = net_worth_aggregation['total_value'] if net_worth_aggregation['total_value'] is not None else 0
            
            shop_data = {
                'id': shop.id,
                'regdate': shop.created_at,
                'names': shop.names,
                'abbrev': shop.abbrev,
                'users_count': CustomUser.objects.filter(shop=shop, deleted=False).count(),
                'items_count': Product.objects.filter(shop=shop, is_deleted=False).count(),
                'networth': net_worth,
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
            4: 'users_count',
            5: 'items_count',
            6: 'networth',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'regdate')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        column_filter_types = {
            'users_count': 'numeric',
            'items_count': 'numeric',
            'networth': 'numeric'
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
                'names': item.get('names'),
                'abbrev': item.get('abbrev'),
                'users_count': format_number(item.get('users_count')),
                'items_count': format_number(item.get('items_count', 0)),
                'networth': format_number(item.get('networth', 0)) + " TZS",
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

    net_worth_aggregation = Product.objects.filter(shop=shop_obj, is_deleted=False).aggregate(total_value=Sum(F('qty') * F('price')))
    net_worth = net_worth_aggregation['total_value'] if net_worth_aggregation['total_value'] is not None else 0
    user_count = CustomUser.objects.filter(shop=shop_obj, deleted=False).count()
    product_count = Product.objects.filter(shop=shop_obj, is_deleted=False).count()

    shopdata = {
        'id': shop_obj.id,
        'regdate': conv_timezone(shop_obj.created_at,'%d-%b-%Y %H:%M:%S'),
        'names': shop_obj.names,
        'abbrev': shop_obj.abbrev,
        'comment': shop_obj.comment or 'N/A',
        'users_count': format_number(user_count),
        'items_count': format_number(product_count),
        'networth': format_number(net_worth),
    }
    
    delete_info = False if shop_obj.id == 1 else True
    return render(request, 'shops/shops.html', {'shopinfo': shopid, 'info': shopdata, 'delete_info': delete_info})


@never_cache
@login_required
@admin_required()
def products_page(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        # Base queryset
        queryset = Product.objects.filter(is_deleted=False)

        # Base data from queryset
        base_data = []
        for item in queryset:
            product_status = "SoldOut"
            if item.qty > 0:
                if item.is_hidden:
                    product_status = "Blocked"
                elif not item.is_hidden:
                    product_status = "Active"
                elif item.expiry_date is not None and item.expiry_date <= date.today():
                    product_status = "Expired"

            item_data = {
                'id': item.id,
                'name': item.name,
                'shop': item.shop.abbrev,
                'qty': item.qty,
                'cost': item.cost,
                'price': item.price,
                'status': product_status,
                'info': reverse('product_details', kwargs={'itemid': int(item.id)})
            }
            base_data.append(item_data)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'name',
            2: 'shop',
            3: 'qty',
            4: 'cost',
            5: 'price',
            6: 'status',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'name')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        column_filter_types = {
            'shop': 'exact',
            'qty': 'numeric',
            'cost': 'numeric',
            'price': 'numeric',
            'status': 'exact',
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
                'name': item.get('name'),
                'shop': item.get('shop'),
                'qty': format_number(item.get('qty')),
                'cost': format_number(item.get('cost')) + " TZS",
                'price': format_number(item.get('price')) + " TZS",
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
    return render(request, 'shops/products.html', {'shops': shops})


@never_cache
@login_required
@require_POST
@admin_required()
def products_requests(request):
    fdback = {'success': False, 'sms': 'Unknown error, reload & try again'}

    try:
        data = request.POST
        edit_product = data.get('edit_product')
        delete_product = data.get('delete_product')
        block_product = data.get('block_product')
        qty_product = data.get('qty_product')
        new_qty = data.get('qty_new')

        # Register new product (fallback/default action)
        if not any([edit_product, delete_product, block_product, qty_product, new_qty]):
            fdback = register_shop_item(data)

        # Edit existing product
        elif edit_product:
            fdback = update_shop_item(data, edit_product)

        # Update quantity
        elif qty_product and new_qty:
            try:
                qty_value = Decimal(new_qty)
                if qty_value >= 1:
                    item = Product.objects.get(id=qty_product, is_deleted=False)
                    item.qty += qty_value
                    item.save()
                    fdback = {'success': True, 'sms': 'Item stock updated.'}
                else:
                    fdback = {'success': False, 'sms': 'Quantity must be at least 1.'}
            except Exception as e:
                fdback = {'success': False, 'sms': 'Failed to update quantity.'}

        # Block/unblock product
        elif block_product:
            try:
                item = Product.objects.get(id=block_product, is_deleted=False)
                item.is_hidden = not item.is_hidden
                item.save()
                fdback = {'success': True}
            except Product.DoesNotExist:
                fdback = {'success': False, 'sms': 'Failed to block/unblock product.'}

        # Delete product
        elif delete_product:
            try:
                item = Product.objects.get(id=delete_product, is_deleted=False)
                item.is_deleted = True
                item.save()
                fdback = {'success': True, 'url': reverse('products_page')}
            except Product.DoesNotExist:
                fdback = {'success': False, 'sms': 'Failed to delete product.'}

    except Exception as e:
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})

    return JsonResponse(fdback)


@never_cache
@login_required
@admin_required()
@require_GET
def product_details(request, itemid):
    try:
        product = Product.objects.get(id=itemid, is_deleted=False)
    except Product.DoesNotExist:
        return redirect('products_page')
    
    product_status = "Sold Out"
    if product.qty > 0:
        if product.is_hidden:
            product_status = "Blocked"
        elif not product.is_hidden:
            product_status = "Available"
        elif product.expiry_date is not None and product.expiry_date <= date.today():
            product_status = "Expired"

    product_data = {
        'id': product.id,
        'regdate': conv_timezone(product.created_at,'%d-%b-%Y %H:%M:%S'),
        'lastupdated': conv_timezone(product.updated_at,'%d-%b-%Y %H:%M:%S'),
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
        'sales': 0, #Total sales for this item/product
        'shops_list': Shop.objects.all().order_by('abbrev')
    }
    return render(request, 'shops/products.html', {'productinfo': True, 'info': product_data})


@never_cache
@login_required
def sales_page(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        # Base queryset
        queryset = Product.objects.filter(is_deleted=False, is_hidden=False)
        if not request.user.is_admin:
            queryset = queryset.filter(shop=request.user.shop)

        # Base data from queryset
        base_data = []
        for product in queryset:
            if product.expiry_date is None or (product.expiry_date is not None and product.expiry_date > date.today()):
                cart_count = 0
                if Cart.objects.filter(user=request.user, product=product).exists():
                    cart_item = Cart.objects.filter(user=request.user, product=product).first()
                    cart_count = cart_item.qty

                product_object = {
                    'id': product.id,
                    'name': product.name,
                    'qty': product.qty,
                    'price': product.price,
                    'cart': cart_count
                }
                base_data.append(product_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'name',
            2: 'qty',
            3: 'price',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'name')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        column_filter_types = {
            'qty': 'numeric',
            'price': 'numeric',
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
                'name': item.get('name'),
                'qty': format_number(item.get('qty')),
                'price': format_number(item.get('price')) + " TZS",
                'sell_qty': format_number(item.get('qty')),
                'cart': format_number(item.get('cart')),
                'action': '',
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
        }
        return JsonResponse(ajax_response)
    
    cart = Cart.objects.filter(user=request.user).order_by('id')
    grand_total, cart_items = sum(item.product.price * item.qty for item in cart), []

    for item in cart:
        cart_items.append({
            'id': item.id,
            'name': item.product.name,
            'price': f"TZS. {format_number(item.product.price)}",
            'qty': format_number(item.qty),
            'max_qty': item.product.qty
        })

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
def sales_actions(request):
    try:
        add_to_cart = request.POST.get('cart_add')
        cart_delete = request.POST.get('cart_delete')
        clear_cart = request.POST.get('clear_cart')
        checkout = request.POST.get('checkout')
        sales_paid = request.POST.get('sales_paid')
        item_remove = request.POST.get('item_remove')
        sales_delete = request.POST.get('sales_delete')

        if add_to_cart:
            product_id = request.POST.get('product')
            product_qty = Decimal(request.POST.get('qty'))
            product = Product.objects.get(id=product_id)

            if product_qty > product.qty:
                return JsonResponse({'success': False, 'sms': f'Qty exceeded available stock ({product.qty}).'})
            
            cart_item, created = Cart.objects.get_or_create(product=product, user=request.user, defaults={'qty': product_qty})
            
            cart_count = Cart.objects.filter(user=request.user).count()
            cart_count = cart_count if cart_count < 10 else '9+'

            return JsonResponse({'success': True, 'sms': f'{format_number(product_qty)} items added to cart.', 'cart': cart_count})
        
        elif cart_delete:
            Cart.objects.get(id=cart_delete).delete()

            items_remaining = Cart.objects.filter(user=request.user)
            cart_count = items_remaining.count() if items_remaining.count() < 10 else '9+'
            
            grand_total = sum(item.product.price * item.qty for item in items_remaining)

            return JsonResponse({'success': True, 'cart': cart_count, 'grand_total': "TZS. " + format_number(grand_total)})

        elif clear_cart:
            Cart.objects.filter(user=request.user).delete()
            return JsonResponse({'success': True})
        
        elif checkout:
            customer_names = request.POST.get('customer').strip()
            sale_comment = request.POST.get('comment').strip()
            full_cart = Cart.objects.filter(user=request.user)

            grand_amount, qty_status, qty_products = 0, True, []

            cart_shops = set()
            for item in full_cart:
                grand_amount += item.product.price * item.qty
                cart_shops.add(item.product.shop)

                if item.qty > item.product.qty:
                    qty_status = False
                    qty_products.append(item.product.names)

            if len(cart_shops) > 1:
                return JsonResponse({'success': False, 'sms': 'All products must be from the same shop to checkout.'})

            if not qty_status:
                return JsonResponse({'success': False, 'sms': f'Not enough stock for: {", ".join(qty_products)}'})

            # Proceed with checkout
            sale_transaction = Sales.objects.create(
                user=request.user,
                amount=grand_amount,
                customer='n/a' if customer_names == '' else customer_names,
                comment=None if sale_comment == '' else sale_comment,
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

            return JsonResponse({'success': True, 'sms': 'Checkout completed successfully!'})

        elif item_remove:
            item = Sale_items.objects.get(id=item_remove)
            sale_obj = Sales.objects.get(id=item.sale_id)
            product = Product.objects.get(id=item.product_id)
            product.qty = product.qty + item.qty
            sale_obj.amount = sale_obj.amount - (item.price * item.qty)
            sale_obj.save()
            product.save()
            item.delete()
            if not Sale_items.objects.filter(sale=sale_obj).exists():
                sale_obj.delete()
                return JsonResponse({'success': True, 'sales_page': reverse('sales_report'), 'items': 0})
            return JsonResponse({'success': True, 'sms': 'Item removed successfully.', 'items': 1})

        elif sales_delete:
            sale_obj = Sales.objects.get(id=sales_delete)
            get_items = Sale_items.objects.filter(sale=sale_obj)
            for obj in get_items:
                product = Product.objects.get(id=obj.product_id)
                product.qty = product.qty + obj.qty
                product.save()
                obj.delete()
            sale_obj.delete()
            return JsonResponse({'success': True, 'sales_page': reverse('sales_page')})

    except Exception as e:
        return JsonResponse({'success': False, 'sms': 'Unknown error, reload & try again'})


# Sales report page
@never_cache
@login_required
def sales_report(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        queryset = Sales.objects.filter(shop=request.user.shop)
        if request.user.is_admin:
            queryset = Sales.objects.all()

        # Date range filtering
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')
        parsed_start_date = None
        parsed_end_date = None

        if start_date_str:
            parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))

        if end_date_str:
            parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))

        if parsed_start_date and parsed_end_date:
            queryset = queryset.filter(created_at__range=(parsed_start_date, parsed_end_date))
        elif parsed_start_date:
            queryset = queryset.filter(created_at__gte=parsed_start_date)
        elif parsed_end_date:
            queryset = queryset.filter(created_at__lte=parsed_end_date)

        # Base data from queryset
        base_data, grand_total = [], 0
        for sale in queryset:
            grand_total += sale.amount
            sale_items = Sale_items.objects.filter(sale=sale)
            sales_data = [
                {
                    'count': idx + 1,
                    'names': item.product.name,
                    'price': format_number(item.price)+" TZS",
                    'qty': format_number(item.qty),
                    'total': format_number(item.price * item.qty)+" TZS"
                }
                for idx, item in enumerate(sale_items)
            ]

            sale_object = {
                'id': sale.id,
                'saledate': sale.created_at,
                'shop': sale.shop.abbrev,
                'user': sale.user.username,
                'customer': sale.customer,
                'amount': sale.amount,
                'sale_items': sales_data,
            }
            
            base_data.append(sale_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'sale_items',
            1: 'id',
            2: 'saledate',
            3: 'shop',
            4: 'amount',
            5: 'customer',
            6: 'user',
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'created_at')
        def none_safe_sort(item):
            value = item.get(order_column_name)
            return (value is None, value)
        if order_dir == 'asc':
            base_data = sorted(base_data, key=none_safe_sort, reverse=False)
        else:
            base_data = sorted(base_data, key=none_safe_sort, reverse=True)

        column_filter_types = {
            'shop': 'exact',
            'amount': 'numeric',
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


        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'saledate': conv_timezone(item.get('saledate'), '%d-%b-%Y %H:%M:%S'),
                'shop': item.get('shop'),
                'user': item.get('user'),
                'customer': item.get('customer'),
                'amount': format_number(item.get('amount'))+" TZS",
                'items': item.get('sale_items'),
            })

        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_total': format_number(grand_total)+" TZS",
        }
        return JsonResponse(ajax_response)
    shops = Shop.objects.all().order_by('-created_at')
    return render(request, 'shops/sales_report.html', {'shops':shops})


# Sale items report
@never_cache
@login_required
def sales_items_report(request):
    if request.method == 'POST':
        draw = int(request.POST.get('draw', 0))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 10))
        search_value = request.POST.get('search[value]', '')
        order_column_index = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')

        queryset = Sale_items.objects.filter(sale__shop=request.user.shop)
        if request.user.is_admin:
            queryset = Sale_items.objects.all()

        # Date range filtering
        start_date_str = request.POST.get('startdate')
        end_date_str = request.POST.get('enddate')
        parsed_start_date = None
        parsed_end_date = None

        if start_date_str:
            parsed_start_date = parse(start_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))

        if end_date_str:
            parsed_end_date = parse(end_date_str).astimezone(zoneinfo.ZoneInfo("UTC"))

        if parsed_start_date and parsed_end_date:
            queryset = queryset.filter(sale__created_at__range=(parsed_start_date, parsed_end_date))
        elif parsed_start_date:
            queryset = queryset.filter(sale__created_at__gte=parsed_start_date)
        elif parsed_end_date:
            queryset = queryset.filter(sale__created_at__lte=parsed_end_date)

        # Base data from queryset
        base_data, sales_total = [], 0
        for item in queryset:
            sales_total += item.price * item.qty

            sale_object = {
                'id': item.id,
                'saledate': item.sale.created_at,
                'shop': item.sale.shop.abbrev,
                'product': item.product.name,
                'price': item.price,
                'qty': item.qty,
                'amount': item.price * item.qty,
                'user': item.sale.user.username,
            }
            base_data.append(sale_object)

        
        # Total records before filtering
        total_records = len(base_data)

        # Define a mapping from DataTables column index to the corresponding model field
        column_mapping = {
            0: 'id',
            1: 'saledate',
            2: 'shop',
            3: 'product',
            4: 'price',
            5: 'qty',
            6: 'amount',
            7: 'user'
        }

        # Apply sorting
        order_column_name = column_mapping.get(order_column_index, 'sale__created_at')
        if order_dir == 'asc':
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=False)
        else:
            base_data = sorted(base_data, key=lambda x: x[order_column_name], reverse=True)

        column_filter_types = {
            'shop': 'exact',
            'amount': 'numeric',
            'price': 'numeric',
            'qty': 'numeric',
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


        final_data = []
        for i, item in enumerate(base_data):
            final_data.append({
                'count': row_count_start + i,
                'id': item.get('id'),
                'saledate': conv_timezone(item.get('saledate'), '%d-%b-%Y %H:%M:%S'),
                'shop': item.get('shop'),
                'product': item.get('product'),
                'price': format_number(item.get('price'))+" TZS",
                'qty': format_number(item.get('qty')),
                'amount': format_number(item.get('amount'))+" TZS",
                'user': item.get('user'),
            })
            
        ajax_response = {
            'draw': draw,
            'recordsTotal': total_records,
            'recordsFiltered': records_filtered,
            'data': final_data,
            'grand_total': format_number(sales_total)+" TZS",
        }
        return JsonResponse(ajax_response)
    
    shops = Shop.objects.all().order_by('-created_at')
    return render(request, 'shops/items_report.html', {'shops':shops})

