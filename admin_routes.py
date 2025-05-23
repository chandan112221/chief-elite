import json
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, abort, session
from flask_login import login_required, current_user, logout_user, login_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import (User, Role, ServiceCategory, Service, StockItem, CheckedItem,
                   FundRequest, FundTransaction, Post, PostComment, PostLike,
                   WebsiteSetting, OtherOrderType, OtherOrder, ChatMessage, 
                   InvoiceServiceSetting, PriceList)
from forms import (UserForm, ServiceForm, StockItemForm, PostForm, 
                  FundProcessForm, WebsiteSettingForm, OtherOrderTypeForm)
from utils import admin_required, generate_invoice, generate_service_invoice

# Admin dashboard
@app.route('/admin/price-list', methods=['GET'])
@login_required
@admin_required
def admin_price_list():
    """Admin price list management page"""
    # Get all price items
    prices = PriceList.query.order_by(PriceList.service, PriceList.type).all()
    return render_template('admin/price_list.html', prices=prices)

@app.route('/admin/price-list/add', methods=['POST'])
@login_required
@admin_required
def admin_price_add():
    """Add a new price item"""
    service = request.form.get('service')
    item_type = request.form.get('type')
    rate = request.form.get('rate')
    
    if not service or not item_type or not rate:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_price_list'))
    
    try:
        rate = float(rate)
        # Check if price item already exists for this service and type
        existing = PriceList.query.filter_by(service=service, type=item_type).first()
        if existing:
            flash(f'A price item for {service} ({item_type}) already exists. Edit it instead.', 'warning')
            return redirect(url_for('admin_price_list'))
        
        # Create new price item
        price_item = PriceList(service=service, type=item_type, rate=rate)
        db.session.add(price_item)
        
        # Check if the service exists in Service model, if not create it
        service_obj = Service.query.filter_by(name=service).first()
        if not service_obj:
            # Get or create a default category (you can change this as needed)
            default_category = ServiceCategory.query.first()
            if not default_category:
                default_category = ServiceCategory(name='General', description='General services')
                db.session.add(default_category)
                db.session.flush()  # Get the ID
            
            service_obj = Service(
                name=service,
                description=f'{service} service',
                rate=rate,
                validity='Lifetime',
                category_id=default_category.id
            )
            db.session.add(service_obj)
            db.session.flush()  # Get the service ID
        
        # Update existing stock items with the new rate for this service and type
        stock_items = StockItem.query.filter_by(service_id=service_obj.id).all()
        updated_count = 0
        for stock_item in stock_items:
            # Check if the stock item type matches the price item type
            if (item_type.lower() == 'old' and stock_item.is_old) or \
               (item_type.lower() == 'new' and not stock_item.is_old):
                stock_item.rate = rate
                updated_count += 1
        
        db.session.commit()
        
        success_msg = f'Price for {service} ({item_type}) added successfully'
        if updated_count > 0:
            success_msg += f' and updated {updated_count} stock items'
        flash(success_msg, 'success')
        
    except ValueError:
        flash('Invalid rate value. Please enter a valid number.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding price item: {str(e)}', 'danger')
    
    return redirect(url_for('admin_price_list'))

@app.route('/admin/price-list/edit', methods=['POST'])
@login_required
@admin_required
def admin_price_edit():
    """Edit an existing price item"""
    price_id = request.form.get('price_id')
    service = request.form.get('service')
    item_type = request.form.get('type')
    rate = request.form.get('rate')
    
    if not price_id or not service or not item_type or not rate:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_price_list'))
    
    try:
        rate = float(rate)
        price_item = PriceList.query.get(price_id)
        if not price_item:
            flash('Price item not found', 'danger')
            return redirect(url_for('admin_price_list'))
        
        # Update price item
        price_item.service = service
        price_item.type = item_type
        price_item.rate = rate
        
        # Find the corresponding service and update stock items
        service_obj = Service.query.filter_by(name=service).first()
        updated_count = 0
        
        if service_obj:
            # Update existing stock items with the new rate for this service and type
            stock_items = StockItem.query.filter_by(service_id=service_obj.id).all()
            for stock_item in stock_items:
                # Check if the stock item type matches the price item type
                if (item_type.lower() == 'old' and stock_item.is_old) or \
                   (item_type.lower() == 'new' and not stock_item.is_old):
                    stock_item.rate = rate
                    updated_count += 1
        
        db.session.commit()
        
        success_msg = f'Price for {service} ({item_type}) updated successfully'
        if updated_count > 0:
            success_msg += f' and updated {updated_count} stock items'
        flash(success_msg, 'success')
        
    except ValueError:
        flash('Invalid rate value. Please enter a valid number.', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating price item: {str(e)}', 'danger')
    
    return redirect(url_for('admin_price_list'))

@app.route('/admin/price-list/delete', methods=['POST'])
@login_required
@admin_required
def admin_price_delete():
    """Delete a price item"""
    price_id = request.form.get('price_id')
    
    if not price_id:
        flash('Price ID is required', 'danger')
        return redirect(url_for('admin_price_list'))
    
    try:
        price_item = PriceList.query.get(price_id)
        if not price_item:
            flash('Price item not found', 'danger')
            return redirect(url_for('admin_price_list'))
        
        service = price_item.service
        item_type = price_item.type
        
        # Delete price item
        db.session.delete(price_item)
        db.session.commit()
        flash(f'Price for {service} ({item_type}) deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting price item: {str(e)}', 'danger')
    
    return redirect(url_for('admin_price_list'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Summary data
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_stock = StockItem.query.count()
    checked_stock = StockItem.query.join(CheckedItem).count()
    
    # Recent transactions
    recent_transactions = FundTransaction.query.order_by(FundTransaction.created_at.desc()).limit(10).all()
    
    # Recent fund requests
    pending_requests = FundRequest.query.filter_by(status='pending').count()
    
    # Today's sales
    today = datetime.now().date()
    today_sales = db.session.query(db.func.sum(FundTransaction.amount)).filter(
        FundTransaction.transaction_type == 'deduct',
        db.func.date(FundTransaction.created_at) == today
    ).scalar() or 0
    
    # Monthly sales
    monthly_sales = db.session.query(
        db.func.strftime('%Y-%m', FundTransaction.created_at).label('month'),
        db.func.sum(FundTransaction.amount).label('amount')
    ).filter(
        FundTransaction.transaction_type == 'deduct'
    ).group_by('month').order_by('month').all()
    
    # Service-wise stock
    service_stock = db.session.query(
        Service.name,
        db.func.count(StockItem.id).label('total'),
        db.func.count(CheckedItem.id).label('checked')
    ).outerjoin(
        StockItem, Service.id == StockItem.service_id
    ).outerjoin(
        CheckedItem, StockItem.id == CheckedItem.stock_item_id
    ).group_by(Service.id).all()
    
    return render_template('admin/dashboard.html',
                          title='Admin Dashboard',
                          total_users=total_users,
                          active_users=active_users,
                          total_stock=total_stock,
                          checked_stock=checked_stock,
                          pending_requests=pending_requests,
                          today_sales=today_sales,
                          monthly_sales=monthly_sales,
                          service_stock=service_stock,
                          recent_transactions=recent_transactions)

# User management
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/users.html',
                          title='User Management',
                          users=users,
                          roles=roles)

# Quick login as user (for admin testing/support)
@app.route('/admin/login-as-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_login_as_user(user_id):
    # Store the admin's original user ID in the session
    if 'admin_user_id' not in session:
        session['admin_user_id'] = current_user.id
    
    # Get the target user
    user = User.query.get_or_404(user_id)
    
    # Logout the current user (admin)
    logout_user()
    
    # Log in as the target user
    login_user(user)
    
    flash(f'আপনি এখন {user.username} হিসাবে লগইন করেছেন। ড্যাশবোর্ড দেখা হচ্ছে।', 'info')
    
    # Redirect to the user's dashboard
    return redirect(url_for('dashboard'))

# Add/edit user
@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@app.route('/admin/user/new', methods=['GET', 'POST'], defaults={'user_id': None})
@login_required
@admin_required
def admin_user_edit(user_id):
    if user_id:
        user = User.query.get_or_404(user_id)
        form = UserForm(obj=user)
    else:
        user = None
        form = UserForm()
    
    # Populate role choices
    roles = Role.query.all()
    if not roles:
        # Create default roles if they don't exist
        admin_role = Role(id=1, name='admin', description='Administrator role')
        user_role = Role(id=2, name='user', description='Regular user role')
        db.session.add(admin_role)
        db.session.add(user_role)
        db.session.commit()
        roles = [admin_role, user_role]
    
    form.role_id.choices = [(role.id, role.name.title()) for role in roles]
    
    # Set default role if creating new user
    if not user and not form.role_id.data:
        form.role_id.data = 2  # Default to regular user role
    
    if form.validate_on_submit():
        if not user:
            user = User(username=form.username.data)
        
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.phone_number = form.phone_number.data
        user.address = form.address.data
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        user.is_admin = form.is_admin.data
        user.balance = form.balance.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        if not user_id:  # New user
            db.session.add(user)
        
        db.session.commit()
        flash(f'User {"added" if not user_id else "updated"} successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/user_edit.html',
                          title='Add User' if not user_id else 'Edit User',
                          form=form,
                          user=user)

# Delete user
@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting self
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_users'))

# Fund requests management
@app.route('/admin/fund-requests')
@login_required
@admin_required
def admin_fund_requests():
    requests = db.session.query(FundRequest, User).join(
        User, FundRequest.user_id == User.id
    ).order_by(FundRequest.request_date.desc()).all()
    
    return render_template('admin/fund_requests.html',
                          title='Fund Requests',
                          requests=requests)

# Process fund request
@app.route('/admin/fund-request/<int:request_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_process_fund(request_id):
    fund_request = FundRequest.query.get_or_404(request_id)
    user = User.query.get(fund_request.user_id)
    form = FundProcessForm(obj=fund_request)
    
    if form.validate_on_submit():
        fund_request.status = form.status.data
        fund_request.is_received = form.is_received.data
        fund_request.admin_notes = form.admin_notes.data
        fund_request.processed_date = datetime.utcnow()
        
        # Store the previous status before updating
        previous_status = fund_request.status
        
        # If status changed to approved and wasn't approved before, add funds
        if form.status.data == 'approved' and previous_status != 'approved':
            user.balance += fund_request.amount
            
            # Create transaction record
            transaction = FundTransaction(
                user_id=user.id,
                amount=fund_request.amount,
                transaction_type='add',
                description=f'Fund request approved. Payment: {fund_request.payment_method}, TrxID: {fund_request.transaction_id}'
            )
            db.session.add(transaction)
        
        db.session.commit()
        flash('Fund request processed successfully!', 'success')
        return redirect(url_for('admin_fund_requests'))
    
    return render_template('admin/process_fund.html',
                          title='Process Fund Request',
                          form=form,
                          request=fund_request,
                          user=user)

# Quick approve fund request
@app.route('/admin/fund-request/<int:request_id>/quick-approve', methods=['POST'])
@login_required
@admin_required
def admin_quick_approve_fund(request_id):
    fund_request = FundRequest.query.get_or_404(request_id)
    user = User.query.get(fund_request.user_id)
    
    # Make sure the request is pending
    if fund_request.status != 'pending':
        flash('This fund request is not in pending status!', 'warning')
        return redirect(url_for('admin_fund_requests'))
    
    # Approve the request
    fund_request.status = 'approved'
    fund_request.processed_date = datetime.utcnow()
    
    # Add funds to user's balance
    user.balance += fund_request.amount
    
    # Create transaction record
    transaction = FundTransaction(
        user_id=user.id,
        amount=fund_request.amount,
        transaction_type='add',
        description=f'Fund request approved. Payment: {fund_request.payment_method}, TrxID: {fund_request.transaction_id}'
    )
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Fund request #{fund_request.id} approved successfully! {fund_request.amount} BDT added to {user.username}\'s balance.', 'success')
    return redirect(url_for('admin_fund_requests'))

# Quick reject fund request
@app.route('/admin/fund-request/<int:request_id>/quick-reject', methods=['POST'])
@login_required
@admin_required
def admin_quick_reject_fund(request_id):
    fund_request = FundRequest.query.get_or_404(request_id)
    
    # Make sure the request is pending
    if fund_request.status != 'pending':
        flash('This fund request is not in pending status!', 'warning')
        return redirect(url_for('admin_fund_requests'))
    
    # Reject the request
    fund_request.status = 'rejected'
    fund_request.processed_date = datetime.utcnow()
    db.session.commit()
    
    flash(f'Fund request #{fund_request.id} has been rejected.', 'warning')
    return redirect(url_for('admin_fund_requests'))

# Mark fund as received
@app.route('/admin/fund-request/<int:request_id>/received', methods=['POST'])
@login_required
@admin_required
def admin_mark_fund_received(request_id):
    fund_request = FundRequest.query.get_or_404(request_id)
    fund_request.is_received = True
    db.session.commit()
    flash('Fund marked as received!', 'success')
    return redirect(url_for('admin_fund_requests'))

# Stock management
@app.route('/admin/stock')
@login_required
@admin_required
def admin_stock():
    categories = ServiceCategory.query.all()
    services = Service.query.all()
    
    return render_template('admin/stock.html',
                          title='Stock Management',
                          categories=categories,
                          services=services)

# Get stock items (admin view)
@app.route('/admin/stock/<service_name>/<item_type>')
@login_required
@admin_required
def admin_get_stock_items(service_name, item_type):
    service = Service.query.filter_by(name=service_name).first_or_404()
    
    # Query items based on type (new/old/one time)
    is_old = item_type.lower() == 'old'
    items = StockItem.query.filter_by(service_id=service.id, is_old=is_old).all()
    
    # Format items for JSON response
    result = []
    for idx, item in enumerate(items):
        # Check who has checked this item
        checked_by = None
        checked_at = None
        checked_item = db.session.query(CheckedItem, User).join(
            User, CheckedItem.user_id == User.id
        ).filter(
            CheckedItem.stock_item_id == item.id
        ).first()
        
        if checked_item:
            checked_by = checked_item[1].username
            checked_at = checked_item[0].checked_at.isoformat().split('T')[0]
        
        item_data = {
            'sl': idx + 1,
            'id': item.id,
            'name': item.name,
            'mail': item.mail,
            'pass': item.password,
            'profile_link': item.profile_link,
            'recovery_mail': item.recovery_mail,
            'two_factor': item.two_factor,
            'rate': item.rate,
            'created_date': item.created_date.isoformat().split('T')[0] if item.created_date else None,
            'is_checked': checked_by is not None,
            'checked_by': checked_by,
            'checked_at': checked_at
        }
        
        result.append(item_data)
    
    return jsonify({'items': result, 'service': service_name, 'type': item_type})

# Add/edit service category
@app.route('/admin/service-category/<int:category_id>', methods=['GET', 'POST'])
@app.route('/admin/service-category/new', methods=['GET', 'POST'], defaults={'category_id': None})
@login_required
@admin_required
def admin_category_edit(category_id):
    if category_id:
        category = ServiceCategory.query.get_or_404(category_id)
        # Use a simple form here for category name and description
    else:
        category = None
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Category name is required!', 'danger')
            return redirect(request.referrer)
        
        if not category:
            category = ServiceCategory(name=name, description=description)
            db.session.add(category)
        else:
            category.name = name
            category.description = description
        
        db.session.commit()
        flash(f'Category {"added" if not category_id else "updated"} successfully!', 'success')
        return redirect(url_for('admin_stock'))
    
    return render_template('admin/category_edit.html',
                          title='Add Category' if not category_id else 'Edit Category',
                          category=category)

# Add/edit service
@app.route('/admin/service/<int:service_id>', methods=['GET', 'POST'])
@app.route('/admin/service/new', methods=['GET', 'POST'], defaults={'service_id': None})
@login_required
@admin_required
def admin_service_edit(service_id):
    if service_id:
        service = Service.query.get_or_404(service_id)
        form = ServiceForm(obj=service)
    else:
        service = None
        form = ServiceForm()
    
    # Populate category choices
    categories = ServiceCategory.query.all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        if not service:
            service = Service(name=form.name.data)
        
        service.description = form.description.data
        service.rate = form.rate.data
        service.validity = form.validity.data
        service.category_id = form.category_id.data
        
        if not service_id:  # New service
            db.session.add(service)
        
        db.session.commit()
        flash(f'Service {"added" if not service_id else "updated"} successfully!', 'success')
        return redirect(url_for('admin_stock'))
    
    return render_template('admin/service_edit.html',
                          title='Add Service' if not service_id else 'Edit Service',
                          form=form,
                          service=service)

# Add/edit stock item
@app.route('/admin/stock-item/<int:item_id>', methods=['GET', 'POST'])
@app.route('/admin/stock-item/new', methods=['GET', 'POST'], defaults={'item_id': None})
@login_required
@admin_required
def admin_stock_item_edit(item_id):
    if item_id:
        item = StockItem.query.get_or_404(item_id)
        form = StockItemForm(obj=item)
    else:
        item = None
        form = StockItemForm()
    
    # Populate service choices
    services = Service.query.all()
    form.service_id.choices = [(s.id, s.name) for s in services]
    
    if form.validate_on_submit():
        if not item:
            item = StockItem()
        
        item.service_id = form.service_id.data
        item.name = form.name.data
        item.mail = form.mail.data
        item.password = form.password.data
        item.profile_link = form.profile_link.data
        item.recovery_mail = form.recovery_mail.data
        item.two_factor = form.two_factor.data
        item.rate = form.rate.data
        item.is_old = form.is_old.data
        
        if not item_id:  # New item
            item.created_date = datetime.utcnow()
            item.is_checked = False  # Ensure new items are available for users
            db.session.add(item)
        
        db.session.commit()
        flash(f'Stock item {"added" if not item_id else "updated"} successfully!', 'success')
        return redirect(url_for('admin_stock'))
    
    return render_template('admin/stock_item_edit.html',
                          title='Add Stock Item' if not item_id else 'Edit Stock Item',
                          form=form,
                          item=item)

# Delete stock item
@app.route('/admin/stock-item/<int:item_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_stock_item_delete(item_id):
    item = StockItem.query.get_or_404(item_id)
    
    # Check if item is already checked by someone
    check = CheckedItem.query.filter_by(stock_item_id=item_id).first()
    if check:
        flash('Cannot delete item that has been checked by a user!', 'danger')
        return redirect(url_for('admin_stock'))
    
    db.session.delete(item)
    db.session.commit()
    flash('Stock item deleted successfully!', 'success')
    return redirect(url_for('admin_stock'))

# Bulk import stock items
@app.route('/admin/stock/import', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_import_stock():
    services = Service.query.all()
    
    if request.method == 'POST':
        service_id = request.form.get('service_id', type=int)
        is_old = request.form.get('is_old') == 'true'
        items_text = request.form.get('items_text')
        
        if not service_id or not items_text:
            flash('Service and items data are required!', 'danger')
            return redirect(url_for('admin_import_stock'))
        
        # Process item text (assumed format based on service type)
        service = Service.query.get_or_404(service_id)
        lines = items_text.strip().split('\n')
        items_added = 0
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = [part.strip() for part in line.split(',')]
            
            # Basic validation
            if len(parts) < 2:
                continue
            
            try:
                # Create item based on service type
                item = StockItem(service_id=service_id, is_old=is_old)
                
                if service.name.lower() in ['facebook', 'linkedin']:
                    # Format: name, mail, pass, profile_link, [2fa]
                    if len(parts) >= 3:
                        item.name = parts[0]
                        item.mail = parts[1]
                        item.password = parts[2]
                        
                        if len(parts) >= 4:
                            item.profile_link = parts[3]
                        
                        if len(parts) >= 5:
                            item.two_factor = parts[4]
                
                elif service.name.lower() in ['gmail', 'outlook']:
                    # Format: mail, pass, recovery_mail
                    if len(parts) >= 2:
                        item.mail = parts[0]
                        item.password = parts[1]
                        
                        if len(parts) >= 3:
                            item.recovery_mail = parts[2]
                
                elif service.name.lower() in ['webmail', 'edu mail']:
                    # Format: mail, pass
                    if len(parts) >= 2:
                        item.mail = parts[0]
                        item.password = parts[1]
                
                # Set rate, date and default values
                item.rate = float(request.form.get('rate', 0))
                item.created_date = datetime.utcnow()
                item.is_checked = False  # Ensure new items are not marked as checked
                
                db.session.add(item)
                items_added += 1
                
            except Exception as e:
                flash(f'Error adding item: {str(e)}', 'danger')
                continue
        
        db.session.commit()
        flash(f'Successfully imported {items_added} items!', 'success')
        return redirect(url_for('admin_stock'))
    
    return render_template('admin/import_stock.html',
                          title='Import Stock Items',
                          services=services)

# Post management
@app.route('/admin/posts')
@login_required
@admin_required
def admin_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html',
                          title='Post Management',
                          posts=posts)

# Create new post (dedicated page)
@app.route('/admin/create-post', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_post():
    import os
    from werkzeug.utils import secure_filename
    from flask import request
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not title or not content:
            flash('Title and content are required!', 'danger')
            return render_template('admin/create_post.html')
        
        post = Post(admin_id=current_user.id)
        post.title = title
        post.content = content
        
        # Handle photo - either URL or file upload
        photo_file = request.files.get('photo_file')
        photo_url = request.form.get('photo_url')
        
        if photo_file and photo_file.filename:
            # Process uploaded photo file
            photo_filename = secure_filename(photo_file.filename)
            
            # Create upload directory if it doesn't exist
            uploads_dir = os.path.join('static', 'uploads', 'posts')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save the file
            photo_path = os.path.join(uploads_dir, photo_filename)
            photo_file.save(photo_path)
            
            # Set the URL to the uploaded file path
            post.photo_url = '/' + photo_path
        elif photo_url:
            # Use the provided URL
            post.photo_url = photo_url
        
        # Handle video - either URL or file upload
        video_file = request.files.get('video_file')
        video_url = request.form.get('video_url')
        
        if video_file and video_file.filename:
            # Process uploaded video file
            video_filename = secure_filename(video_file.filename)
            
            # Create upload directory if it doesn't exist
            uploads_dir = os.path.join('static', 'uploads', 'posts')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save the file
            video_path = os.path.join(uploads_dir, video_filename)
            video_file.save(video_path)
            
            # Set the URL to the uploaded file path
            post.video_url = '/' + video_path
        elif video_url:
            # Use the provided URL
            post.video_url = video_url
        
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin_posts'))
    
    return render_template('admin/create_post.html')

# Add/edit post
@app.route('/admin/post/<int:post_id>', methods=['GET', 'POST'])
@app.route('/admin/post/new', methods=['GET', 'POST'], defaults={'post_id': None})
@login_required
@admin_required
def admin_post_edit(post_id):
    import os
    from werkzeug.utils import secure_filename
    
    if post_id:
        post = Post.query.get_or_404(post_id)
        form = PostForm(obj=post)
    else:
        post = None
        form = PostForm()
    
    if form.validate_on_submit():
        if not post:
            post = Post(admin_id=current_user.id)
        
        post.title = form.title.data
        post.content = form.content.data
        
        # Handle photo - either URL or file upload
        if form.photo_file.data:
            # Process uploaded photo file
            photo_file = form.photo_file.data
            photo_filename = secure_filename(photo_file.filename)
            
            # Create upload directory if it doesn't exist
            uploads_dir = os.path.join('static', 'uploads', 'posts')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save the file
            photo_path = os.path.join(uploads_dir, photo_filename)
            photo_file.save(photo_path)
            
            # Set the URL to the uploaded file path
            post.photo_url = '/' + photo_path
        elif form.photo_url.data:
            # Use the provided URL
            post.photo_url = form.photo_url.data
        
        # Handle video - either URL or file upload
        if form.video_file.data:
            # Process uploaded video file
            video_file = form.video_file.data
            video_filename = secure_filename(video_file.filename)
            
            # Create upload directory if it doesn't exist
            uploads_dir = os.path.join('static', 'uploads', 'posts')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save the file
            video_path = os.path.join(uploads_dir, video_filename)
            video_file.save(video_path)
            
            # Set the URL to the uploaded file path
            post.video_url = '/' + video_path
        elif form.video_url.data:
            # Use the provided URL
            post.video_url = form.video_url.data
        
        if not post_id:  # New post
            db.session.add(post)
        
        db.session.commit()
        flash(f'Post {"created" if not post_id else "updated"} successfully!', 'success')
        return redirect(url_for('admin_posts'))
    
    return render_template('admin/post_edit.html',
                          title='Add Post' if not post_id else 'Edit Post',
                          form=form,
                          post=post)

# Delete post
@app.route('/admin/post/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin_posts'))

# Other Order Type management
@app.route('/admin/other-order-types')
@login_required
@admin_required
def admin_other_order_types():
    order_types = OtherOrderType.query.all()
    return render_template('admin/other_order_types.html',
                          title='Other Order Types',
                          order_types=order_types)

# Delete other order type
@app.route('/admin/other-order-type/<int:type_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_other_order_type_delete(type_id):
    order_type = OtherOrderType.query.get_or_404(type_id)
    
    # Check if there are any orders using this type
    orders = OtherOrder.query.filter_by(order_type_id=type_id).count()
    if orders > 0:
        flash(f'Cannot delete type that has {orders} orders associated with it!', 'danger')
        return redirect(url_for('admin_other_order_types'))
    
    db.session.delete(order_type)
    db.session.commit()
    flash('Order type deleted successfully!', 'success')
    return redirect(url_for('admin_other_order_types'))

# Add/edit other order type
@app.route('/admin/other-order-type/<int:type_id>', methods=['GET', 'POST'])
@app.route('/admin/other-order-type/new', methods=['GET', 'POST'], defaults={'type_id': None})
@login_required
@admin_required
def admin_other_order_type_edit(type_id):
    if type_id:
        order_type = OtherOrderType.query.get_or_404(type_id)
        form = OtherOrderTypeForm(obj=order_type)
    else:
        order_type = None
        form = OtherOrderTypeForm()
    
    if form.validate_on_submit():
        if not order_type:
            order_type = OtherOrderType()
        
        order_type.name = form.name.data
        order_type.rate = form.rate.data
        order_type.validity = form.validity.data
        order_type.description = form.description.data
        order_type.required_fields = form.required_fields.data
        order_type.is_active = form.is_active.data
        
        if not type_id:  # New order type
            db.session.add(order_type)
        
        db.session.commit()
        flash(f'Order type {"added" if not type_id else "updated"} successfully!', 'success')
        return redirect(url_for('admin_other_order_types'))
    
    return render_template('admin/other_order_type_edit.html',
                          title='Add Order Type' if not type_id else 'Edit Order Type',
                          form=form,
                          order_type=order_type)

# Other orders management
@app.route('/admin/other-orders')
@login_required
@admin_required
def admin_other_orders():
    # Get status filter from query params
    status_filter = request.args.get('status', 'all')
    
    # Base query
    query = db.session.query(OtherOrder, User, OtherOrderType).join(
        User, OtherOrder.user_id == User.id
    ).join(
        OtherOrderType, OtherOrder.order_type_id == OtherOrderType.id
    )
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter(OtherOrder.status == status_filter)
    
    orders = query.order_by(OtherOrder.created_at.desc()).all()
    
    # Get order counts by status
    status_counts = db.session.query(
        OtherOrder.status,
        db.func.count(OtherOrder.id).label('count')
    ).group_by(OtherOrder.status).all()
    
    counts_dict = {status: count for status, count in status_counts}
    total_orders = sum(counts_dict.values())
    
    return render_template('admin/other_orders.html',
                          title='Other Orders Management',
                          orders=orders,
                          status_filter=status_filter,
                          status_counts=counts_dict,
                          total_orders=total_orders)

# Update order status
@app.route('/admin/other-order/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def admin_update_order_status(order_id):
    order = OtherOrder.query.get_or_404(order_id)
    status = request.form.get('status')
    
    if status not in ['pending', 'approved', 'processing', 'completed', 'rejected', 'cancelled']:
        flash('Invalid status!', 'danger')
        return redirect(url_for('admin_other_orders'))
    
    order.status = status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Send flash message based on status
    status_messages = {
        'pending': 'Order set to pending!',
        'processing': 'Order approved and processing!',
        'completed': 'Order completed successfully!',
        'rejected': 'Order rejected!'
    }
    
    flash(status_messages.get(status, 'Order status updated!'), 'success')
    return redirect(url_for('admin_other_orders'))

# Bulk update order statuses
@app.route('/admin/other-orders/bulk-update', methods=['POST'])
@login_required
@admin_required
def admin_bulk_update_orders():
    data = request.json
    order_ids = data.get('order_ids', [])
    status = data.get('status')
    
    if not order_ids or status not in ['pending', 'processing', 'completed', 'rejected']:
        return jsonify({
            'success': False,
            'error': 'Invalid input data'
        })
    
    # Update all selected orders
    updated_count = 0
    for order_id in order_ids:
        order = OtherOrder.query.get(order_id)
        if order:
            order.status = status
            order.updated_at = datetime.utcnow()
            updated_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Updated {updated_count} orders to status: {status}',
        'updated_count': updated_count
    })

# Other Orders Status Management - Separate dedicated page
@app.route('/admin/other-orders-status')
@login_required
@admin_required
def admin_other_orders_status():
    # Get status filter from query params
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    # Base query
    query = db.session.query(OtherOrder, User, OtherOrderType).join(
        User, OtherOrder.user_id == User.id
    ).join(
        OtherOrderType, OtherOrder.order_type_id == OtherOrderType.id
    )
    
    # Apply status filter
    if status_filter != 'all':
        query = query.filter(OtherOrder.status == status_filter)
    
    # Paginate results
    orders = query.order_by(OtherOrder.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get order counts by status
    status_counts = db.session.query(
        OtherOrder.status,
        db.func.count(OtherOrder.id).label('count')
    ).group_by(OtherOrder.status).all()
    
    counts_dict = {status: count for status, count in status_counts}
    total_orders = sum(counts_dict.values())
    
    return render_template('admin/other_orders_status.html',
                          title='Other Orders Status Management',
                          orders=orders,
                          status_filter=status_filter,
                          status_counts=counts_dict,
                          total_orders=total_orders)

# Quick status update for other orders from status page
@app.route('/admin/other-order/<int:order_id>/quick-status', methods=['POST'])
@login_required
@admin_required
def admin_quick_update_order_status(order_id):
    order = OtherOrder.query.get_or_404(order_id)
    status = request.form.get('status')
    
    if status not in ['pending', 'approved', 'processing', 'completed', 'rejected', 'cancelled']:
        flash('Invalid status!', 'danger')
        return redirect(url_for('admin_other_orders_status'))
    
    old_status = order.status
    order.status = status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Order #{order.id} status updated from {old_status} to {status}!', 'success')
    return redirect(url_for('admin_other_orders_status'))

# Website settings
@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    settings = WebsiteSetting.query.first()
    if not settings:
        settings = WebsiteSetting()
        db.session.add(settings)
        db.session.commit()
    
    form = WebsiteSettingForm(obj=settings)
    
    if form.validate_on_submit():
        settings.site_name = form.site_name.data
        settings.logo_url = form.logo_url.data
        settings.primary_color = form.primary_color.data
        settings.secondary_color = form.secondary_color.data
        settings.contact_phone = form.contact_phone.data
        settings.contact_email = form.contact_email.data
        settings.admin_notice = form.admin_notice.data
        settings.minimum_fund = form.minimum_fund.data
        
        db.session.commit()
        flash('Website settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html',
                          title='Website Settings',
                          form=form,
                          settings=settings)

# Support chat dashboard
@app.route('/admin/support')
@login_required
@admin_required
def admin_support():
    # Get unique users with chat history
    users_with_chats = db.session.query(User).join(
        ChatMessage, User.id == ChatMessage.user_id
    ).distinct().all()
    
    # Get unread message counts
    unread_counts = db.session.query(
        ChatMessage.user_id,
        db.func.count(ChatMessage.id).label('count')
    ).filter(
        ChatMessage.is_admin_message == False,
        ChatMessage.is_read == False
    ).group_by(ChatMessage.user_id).all()
    
    # Convert to dict for easy lookup
    unread_dict = {user_id: count for user_id, count in unread_counts}
    
    return render_template('admin/support.html',
                          title='Support Chat',
                          users=users_with_chats,
                          unread_counts=unread_dict)

# Chat with specific user
@app.route('/admin/support/<int:user_id>')
@login_required
@admin_required
def admin_chat_with_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get chat history
    messages = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.created_at).all()
    
    # Mark messages as read
    for message in messages:
        if not message.is_admin_message and not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    return render_template('admin/chat_with_user.html',
                          title=f'Chat with {user.username}',
                          user=user,
                          messages=messages)

# Send message to user
@app.route('/admin/support/<int:user_id>/send', methods=['POST'])
@login_required
@admin_required
def admin_send_message(user_id):
    user = User.query.get_or_404(user_id)
    content = request.json.get('message')
    
    if not content:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    message = ChatMessage(
        user_id=user_id,
        is_admin_message=True,
        content=content,
        is_read=False
    )
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'is_admin': message.is_admin_message,
            'timestamp': message.created_at.isoformat().replace('T', ' ').split('.')[0]
        }
    })

# Reports
@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    # Report types
    report_type = request.args.get('type', 'total_sales')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Convert date strings to datetime objects if present
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        # Include the entire end day
        end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
    
    # Base query for transactions
    query = db.session.query(FundTransaction)
    
    # Apply date filters if present
    if start_date:
        query = query.filter(FundTransaction.created_at >= start_date)
    if end_date:
        query = query.filter(FundTransaction.created_at <= end_date)
    
    # Run different queries based on report type
    if report_type == 'total_sales':
        # Total deductions (sales)
        sales_data = query.filter(FundTransaction.transaction_type == 'deduct').all()
        total_sales = sum(t.amount for t in sales_data)
        
        # Group by date
        daily_sales = db.session.query(
            db.func.date(FundTransaction.created_at).label('date'),
            db.func.sum(FundTransaction.amount).label('amount')
        ).filter(
            FundTransaction.transaction_type == 'deduct'
        )
        
        if start_date:
            daily_sales = daily_sales.filter(FundTransaction.created_at >= start_date)
        if end_date:
            daily_sales = daily_sales.filter(FundTransaction.created_at <= end_date)
            
        daily_sales = daily_sales.group_by('date').order_by('date').all()
        
        return render_template('admin/reports/total_sales.html',
                              title='Total Sales Report',
                              total_sales=total_sales,
                              daily_sales=daily_sales,
                              start_date=start_date,
                              end_date=end_date)
    
    elif report_type == 'monthly_sales':
        # Monthly sales
        monthly_sales = db.session.query(
            db.func.strftime('%Y-%m', FundTransaction.created_at).label('month'),
            db.func.sum(FundTransaction.amount).label('amount')
        ).filter(
            FundTransaction.transaction_type == 'deduct'
        )
        
        if start_date:
            monthly_sales = monthly_sales.filter(FundTransaction.created_at >= start_date)
        if end_date:
            monthly_sales = monthly_sales.filter(FundTransaction.created_at <= end_date)
            
        monthly_sales = monthly_sales.group_by('month').order_by('month').all()
        
        return render_template('admin/reports/monthly_sales.html',
                              title='Monthly Sales Report',
                              monthly_sales=monthly_sales,
                              start_date=start_date,
                              end_date=end_date)
    
    elif report_type == 'revenue':
        # Total revenue (funds added)
        revenue_data = query.filter(FundTransaction.transaction_type == 'add').all()
        total_revenue = sum(t.amount for t in revenue_data)
        
        # Group by date
        daily_revenue = db.session.query(
            db.func.date(FundTransaction.created_at).label('date'),
            db.func.sum(FundTransaction.amount).label('amount')
        ).filter(
            FundTransaction.transaction_type == 'add'
        )
        
        if start_date:
            daily_revenue = daily_revenue.filter(FundTransaction.created_at >= start_date)
        if end_date:
            daily_revenue = daily_revenue.filter(FundTransaction.created_at <= end_date)
            
        daily_revenue = daily_revenue.group_by('date').order_by('date').all()
        
        return render_template('admin/reports/revenue.html',
                              title='Revenue Report',
                              total_revenue=total_revenue,
                              daily_revenue=daily_revenue,
                              start_date=start_date,
                              end_date=end_date)
    
    elif report_type == 'fund_received':
        # Funds received
        received_requests = db.session.query(
            FundRequest
        ).filter(
            FundRequest.status == 'approved',
            FundRequest.is_received == True
        )
        
        if start_date:
            received_requests = received_requests.filter(FundRequest.processed_date >= start_date)
        if end_date:
            received_requests = received_requests.filter(FundRequest.processed_date <= end_date)
            
        received_requests = received_requests.all()
        total_received = sum(r.amount for r in received_requests)
        
        # Group by payment method
        payment_methods = db.session.query(
            FundRequest.payment_method,
            db.func.sum(FundRequest.amount).label('amount')
        ).filter(
            FundRequest.status == 'approved',
            FundRequest.is_received == True
        )
        
        if start_date:
            payment_methods = payment_methods.filter(FundRequest.processed_date >= start_date)
        if end_date:
            payment_methods = payment_methods.filter(FundRequest.processed_date <= end_date)
            
        payment_methods = payment_methods.group_by(FundRequest.payment_method).all()
        
        return render_template('admin/reports/fund_received.html',
                              title='Funds Received Report',
                              total_received=total_received,
                              payment_methods=payment_methods,
                              received_requests=received_requests,
                              start_date=start_date,
                              end_date=end_date)
    
    elif report_type == 'stock_sales':
        # Service-wise sales vs current stock
        service_data = db.session.query(
            Service.name.label('service_name'),
            db.func.count(StockItem.id).label('total_stock'),
            db.func.sum(db.case([(CheckedItem.id != None, 1)], else_=0)).label('sold')
        ).join(
            StockItem, Service.id == StockItem.service_id
        ).outerjoin(
            CheckedItem, StockItem.id == CheckedItem.stock_item_id
        ).group_by(Service.name).all()
        
        return render_template('admin/reports/stock_sales.html',
                              title='Stock Sales Report',
                              service_data=service_data,
                              start_date=start_date,
                              end_date=end_date)
    
    elif report_type == 'user_transactions':
        # Select user
        user_id = request.args.get('user_id', type=int)
        users = User.query.all()
        
        if user_id:
            user = User.query.get_or_404(user_id)
            
            # Get user's fund transactions
            transactions = FundTransaction.query.filter_by(user_id=user_id)
            
            if start_date:
                transactions = transactions.filter(FundTransaction.created_at >= start_date)
            if end_date:
                transactions = transactions.filter(FundTransaction.created_at <= end_date)
                
            transactions = transactions.order_by(FundTransaction.created_at.desc()).all()
            
            # Summarize transactions
            total_added = sum(t.amount for t in transactions if t.transaction_type == 'add')
            total_deducted = sum(t.amount for t in transactions if t.transaction_type == 'deduct')
            
            return render_template('admin/reports/user_transactions.html',
                                  title='User Transactions Report',
                                  user=user,
                                  users=users,
                                  transactions=transactions,
                                  total_added=total_added,
                                  total_deducted=total_deducted,
                                  start_date=start_date,
                                  end_date=end_date)
        else:
            return render_template('admin/reports/user_transactions.html',
                                  title='User Transactions Report',
                                  users=users,
                                  start_date=start_date,
                                  end_date=end_date)
    
    # Default report view
    return render_template('admin/reports.html',
                          title='Reports',
                          start_date=start_date,
                          end_date=end_date)





# Custom invoice generation
@app.route('/admin/invoice/create')
@login_required
@admin_required
def admin_create_invoice():
    users = User.query.all()
    return render_template('admin/create_invoice.html',
                          title='Create Invoice',
                          users=users)

# Get user info for invoice
@app.route('/admin/user/info/<int:user_id>')
@login_required
@admin_required
def admin_get_user_info(user_id):
    user = User.query.get_or_404(user_id)
    
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'phone_number': user.phone_number,
        'address': user.address,
        'balance': float(user.balance) if user.balance is not None else 0.0,
        'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else None
    }
    
    return jsonify({
        'success': True,
        'user': user_data
    })

# Get user's active services
@app.route('/admin/user/services/<int:user_id>')
@login_required
@admin_required
def admin_get_user_services(user_id):
    # Get user's checked items with service info
    checked_service_data = db.session.query(
        Service.id.label('service_id'),
        Service.name.label('service_name'),
        db.func.count(CheckedItem.id).label('count'),
        db.func.sum(StockItem.rate).label('total'),
        db.func.avg(StockItem.rate).label('rate')
    ).join(
        StockItem, Service.id == StockItem.service_id
    ).join(
        CheckedItem, StockItem.id == CheckedItem.stock_item_id
    ).filter(
        CheckedItem.user_id == user_id
    ).group_by(
        Service.id
    ).all()
    
    services = []
    for service in checked_service_data:
        services.append({
            'service_id': service.service_id,
            'service_name': service.service_name,
            'count': service.count,
            'rate': float(service.rate) if service.rate is not None else 0.0,
            'total': float(service.total) if service.total is not None else 0.0
        })
    
    return jsonify({
        'success': True,
        'services': services
    })

# Get user's orders
@app.route('/admin/user/orders/<int:user_id>')
@login_required
@admin_required
def admin_get_user_orders(user_id):
    # Get user's other orders
    orders_data = db.session.query(
        OtherOrder.id,
        OtherOrder.status,
        OtherOrder.created_at,
        OtherOrderType.id.label('type_id'),
        OtherOrderType.name.label('type_name'),
        OtherOrderType.rate
    ).join(
        OtherOrderType, OtherOrder.order_type_id == OtherOrderType.id
    ).filter(
        OtherOrder.user_id == user_id,
        OtherOrder.status.in_(['completed', 'processing'])
    ).all()
    
    orders = []
    for order in orders_data:
        orders.append({
            'id': order.id,
            'type_id': order.type_id,
            'type_name': order.type_name,
            'rate': float(order.rate) if order.rate is not None else 0.0,
            'status': order.status,
            'created_at': order.created_at.strftime('%Y-%m-%d') if order.created_at else None
        })
    
    return jsonify({
        'success': True,
        'orders': orders
    })

# Generate custom invoice
@app.route('/admin/invoice/generate-custom', methods=['POST'])
@login_required
@admin_required
def admin_generate_custom_invoice():
    data = request.json
    
    if not data or 'user_id' not in data:
        return jsonify({
            'success': False,
            'error': 'User ID is required'
        })
    
    # Get user
    user = User.query.get_or_404(data['user_id'])
    
    # Custom company info
    company_name = data.get('company_name') or 'Chief Elite Bd'
    company_phone = data.get('company_phone') or '01856659780'
    company_address = data.get('company_address') or 'Khulna'
    
    # Get selected services
    selected_services = data.get('selected_services', [])
    
    # Get selected orders
    selected_orders = data.get('selected_orders', [])
    
    # Calculate totals
    total_amount = 0
    service_items = []
    
    # Add service items
    for service in selected_services:
        service_items.append({
            'name': service['name'],
            'count': service['count'],
            'rate': service['rate'],
            'total': service['total']
        })
        total_amount += float(service['total'])
    
    # Add order items
    for order in selected_orders:
        service_items.append({
            'name': f"{order['name']} (Order)",
            'count': 1,
            'rate': order['rate'],
            'total': float(order['rate'])
        })
        total_amount += float(order['rate'])
    
    # Generate HTML with improved styling for printing
    invoice_date = datetime.utcnow().strftime('%Y-%m-%d')
    invoice_number = f"SRV-{user.id}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    
    # Create invoice HTML
    html = f"""
    <div class="invoice-container" style="width: 800px; background: white; padding: 40px; font-family: Arial, sans-serif; color: #333; line-height: 1.4;">
        <style>
            * {{ box-sizing: border-box; }}
            .invoice-container {{ background: white !important; }}
            .invoice-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #333; }}
            .company-info {{ flex: 1; }}
            .invoice-info {{ text-align: right; }}
            .company-logo {{ font-size: 28px; font-weight: bold; color: #333; margin-bottom: 10px; }}
            .company-details {{ font-size: 14px; color: #666; line-height: 1.6; }}
            .invoice-title {{ font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px; }}
            .invoice-meta {{ margin: 30px 0; }}
            .customer-info {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
            .customer-header {{ font-size: 16px; font-weight: bold; margin-bottom: 15px; color: #333; }}
            .customer-details {{ display: flex; flex-wrap: wrap; row-gap: 8px; }}
            .customer-row {{ width: 100%; display: flex; }}
            .customer-label {{ width: 120px; font-weight: 600; color: #666; }}
            .customer-value {{ flex: 1; }}
            .invoice-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; }}
            .invoice-table th {{ background: #f8f9fa; padding: 12px 15px; text-align: left; font-weight: bold; color: #333; border-bottom: 2px solid #ddd; }}
            .invoice-table td {{ padding: 12px 15px; border-bottom: 1px solid #ddd; }}
            .invoice-table tr:last-child td {{ border-bottom: none; }}
            .text-right {{ text-align: right; }}
            .total-section {{ margin-top: 20px; padding-top: 20px; border-top: 2px solid #333; text-align: right; }}
            .total-row {{ display: flex; justify-content: flex-end; margin-bottom: 8px; }}
            .total-label {{ width: 120px; font-weight: 600; }}
            .total-value {{ width: 120px; text-align: right; }}
            .grand-total {{ font-size: 18px; font-weight: bold; color: #333; margin-top: 15px; }}
            .footer {{ margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 14px; color: #666; text-align: center; }}
            @media print {{
                body {{ margin: 0; padding: 0; background: white; }}
                .invoice-container {{ border: none !important; box-shadow: none !important; padding: 20px !important; max-width: 100% !important; }}
            }}
        </style>
        
        <div class="invoice-header">
            <div class="company-info">
                <div class="company-logo">{company_name}</div>
                <div class="company-details">
                    <div>Phone: {company_phone}</div>
                    <div>Address: {company_address}</div>
                </div>
            </div>
            <div class="invoice-info">
                <div class="invoice-title">INVOICE</div>
                <div class="invoice-meta">
                    <div>Invoice #: {invoice_number}</div>
                    <div>Date: {invoice_date}</div>
                </div>
            </div>
        </div>
        
        <div class="customer-info">
            <div class="customer-header">Customer Information</div>
            <div class="customer-details">
                <div class="customer-row">
                    <div class="customer-label">Username:</div>
                    <div class="customer-value">{user.username}</div>
                </div>
    """
    
    if user.full_name:
        html += f"""
                <div class="customer-row">
                    <div class="customer-label">Name:</div>
                    <div class="customer-value">{user.full_name}</div>
                </div>
        """
    
    if user.email:
        html += f"""
                <div class="customer-row">
                    <div class="customer-label">Email:</div>
                    <div class="customer-value">{user.email}</div>
                </div>
        """
    
    if user.phone_number:
        html += f"""
                <div class="customer-row">
                    <div class="customer-label">Phone:</div>
                    <div class="customer-value">{user.phone_number}</div>
                </div>
        """
    
    if user.address:
        html += f"""
                <div class="customer-row">
                    <div class="customer-label">Address:</div>
                    <div class="customer-value">{user.address}</div>
                </div>
        """
    
    html += """
            </div>
        </div>
        
        <table class="invoice-table">
            <thead>
                <tr>
                    <th>Service</th>
                    <th>Quantity</th>
                    <th>Rate (BDT)</th>
                    <th class="text-right">Amount (BDT)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in service_items:
        html += f"""
                <tr>
                    <td>{item['name']}</td>
                    <td>{item['count']}</td>
                    <td>{item['rate']}</td>
                    <td class="text-right">{item['total']}</td>
                </tr>
        """
    
    # Calculate grand total
    html += f"""
            </tbody>
        </table>
        
        <div class="total-section">
            <div class="total-row grand-total">
                <div class="total-label">Total Amount:</div>
                <div class="total-value">{total_amount:.2f} BDT</div>
            </div>
        </div>
        
        <div class="footer">
            <p>Thank you for your business! If you have any questions, please contact us.</p>
        </div>
    </div>
    """
    
    return jsonify({
        'success': True,
        'invoice_html': html
    })


