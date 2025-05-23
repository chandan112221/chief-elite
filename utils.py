from datetime import datetime, timedelta
from functools import wraps
from flask import abort
from flask_login import current_user
from models import WebsiteSetting, FundRequest

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Check if user has active funds
def is_fund_active(user_id):
    # Check if user has any approved fund request in the last 3 days
    three_days_ago = datetime.utcnow() - timedelta(days=3)
    
    recent_request = FundRequest.query.filter(
        FundRequest.user_id == user_id,
        FundRequest.status == 'approved',
        FundRequest.processed_date >= three_days_ago
    ).first()
    
    return recent_request is not None

# Get website settings
def get_website_settings():
    settings = WebsiteSetting.query.first()
    if not settings:
        settings = WebsiteSetting()
    return settings

# Generate invoice HTML
def generate_invoice(user, transactions, start_date, end_date):
    # Calculate totals
    total_added = sum(t.amount for t in transactions if t.transaction_type == 'add')
    total_deducted = sum(t.amount for t in transactions if t.transaction_type == 'deduct')
    
    # Format dates
    start_date_str = start_date.isoformat().split('T')[0] if start_date else 'All time'
    end_date_str = end_date.isoformat().split('T')[0] if end_date else 'Present'
    
    # Get website settings
    settings = get_website_settings()
    
    # Generate HTML
    html = f"""
    <div class="invoice">
        <div class="invoice-header">
            <div class="row">
                <div class="col-6">
                    <h2>{settings.site_name}</h2>
                    <p>Contact: {settings.contact_phone}</p>
                    <p>Email: {settings.contact_email}</p>
                </div>
                <div class="col-6 text-end">
                    <h3>INVOICE</h3>
                    <p>Date: {datetime.utcnow().isoformat().split('T')[0]}</p>
                    <p>Invoice #: INV-{user.id}-{datetime.utcnow().isoformat().replace('-', '').replace('T', '').replace(':', '')[:12]}</p>
                </div>
            </div>
        </div>
        
        <div class="invoice-customer mt-4">
            <div class="row">
                <div class="col-6">
                    <h5>Bill To:</h5>
                    <p><strong>{user.full_name or user.username}</strong></p>
                    <p>Email: {user.email}</p>
                    <p>Phone: {user.phone_number or 'N/A'}</p>
                    <p>Address: {user.address or 'N/A'}</p>
                </div>
                <div class="col-6 text-end">
                    <h5>Invoice Period:</h5>
                    <p>From: {start_date_str}</p>
                    <p>To: {end_date_str}</p>
                </div>
            </div>
        </div>
        
        <div class="invoice-items mt-4">
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Type</th>
                        <th class="text-end">Amount (BDT)</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for t in transactions:
        html += f"""
                    <tr>
                        <td>{t.created_at.isoformat().replace('T', ' ').split('.')[0]}</td>
                        <td>{t.description or ('Fund Added' if t.transaction_type == 'add' else 'Purchase')}</td>
                        <td>{'Credit' if t.transaction_type == 'add' else 'Debit'}</td>
                        <td class="text-end">{t.amount:.2f}</td>
                    </tr>
        """
    
    html += f"""
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="3" class="text-end"><strong>Total Added:</strong></td>
                        <td class="text-end">{total_added:.2f}</td>
                    </tr>
                    <tr>
                        <td colspan="3" class="text-end"><strong>Total Deducted:</strong></td>
                        <td class="text-end">{total_deducted:.2f}</td>
                    </tr>
                    <tr>
                        <td colspan="3" class="text-end"><strong>Balance:</strong></td>
                        <td class="text-end">{(total_added - total_deducted):.2f}</td>
                    </tr>
                </tfoot>
            </table>
        </div>
        
        <div class="invoice-footer mt-4">
            <div class="row">
                <div class="col-12 text-center">
                    <p>Thank you for your business!</p>
                    <p><small>This is a computer-generated invoice and does not require a signature.</small></p>
                </div>
            </div>
        </div>
    </div>
    """
    
    return html

# Generate simplified service-based invoice
def generate_service_invoice(user, checked_items):
    from models import OtherOrder, OtherOrderType
    from app import db
    
    # Get website settings
    settings = get_website_settings()
    
    # Calculate totals by service
    service_totals = {}
    total_amount = 0
    
    # Group by service and calculate totals
    for checked_item, stock_item, service in checked_items:
        service_name = service.name
        if service_name not in service_totals:
            service_totals[service_name] = {
                'count': 0,
                'rate': stock_item.rate,
                'total': 0,
                'service_id': service.id
            }
        service_totals[service_name]['count'] += 1
        service_totals[service_name]['total'] += stock_item.rate
        total_amount += stock_item.rate
    
    # Get user's other orders
    other_orders = db.session.query(OtherOrder, OtherOrderType).join(
        OtherOrderType, OtherOrder.order_type_id == OtherOrderType.id
    ).filter(
        OtherOrder.user_id == user.id,
        OtherOrder.status.in_(['completed', 'processing'])
    ).all()
    
    # Add other orders to service totals
    for order, order_type in other_orders:
        service_name = f"{order_type.name} (Other)"
        if service_name not in service_totals:
            service_totals[service_name] = {
                'count': 0,
                'rate': order_type.rate,
                'total': 0,
                'service_id': f'other_{order_type.id}'
            }
        service_totals[service_name]['count'] += 1
        service_totals[service_name]['total'] += order_type.rate
        total_amount += order_type.rate
    
    # Generate HTML with improved styling for printing
    invoice_date = datetime.utcnow().strftime('%Y-%m-%d')
    invoice_number = f"SRV-{user.id}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
    
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
            .customer-details {{ display: flex; justify-content: space-between; }}
            .customer-left, .customer-right {{ flex: 1; }}
            .customer-right {{ text-align: right; }}
            .invoice-table {{ width: 100%; border-collapse: collapse; margin: 30px 0; }}
            .invoice-table th {{ background: #333; color: white; padding: 12px; text-align: left; font-weight: bold; }}
            .invoice-table td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
            .invoice-table tr:nth-child(even) {{ background: #f8f9fa; }}
            .text-center {{ text-align: center; }}
            .text-right {{ text-align: right; }}
            .total-row {{ background: #333 !important; color: white !important; font-weight: bold; }}
            .total-row td {{ border: none !important; }}
            .invoice-footer {{ margin-top: 40px; text-align: center; padding-top: 20px; border-top: 2px solid #ddd; color: #666; }}
        </style>
        
        <div class="invoice-header">
            <div class="company-info">
                <div class="company-logo">Chief Elite BD</div>
                <div class="company-details">
                    Phone: 01856659780<br>
                    Address: Khulna<br>
                    Email: info@chiefelitebd.com
                </div>
            </div>
            <div class="invoice-info">
                <div class="invoice-title">INVOICE</div>
                <div style="font-size: 14px; color: #666;">
                    Date: {invoice_date}<br>
                    Invoice #: {invoice_number}
                </div>
            </div>
        </div>
        
        <div class="invoice-meta">
            <div class="customer-info">
                <div class="customer-header">Bill To:</div>
                <div class="customer-details">
                    <div class="customer-left">
                        <strong>{user.full_name or user.username}</strong><br>
                        Email: {user.email}<br>
                        Phone: {user.phone_number or 'N/A'}<br>
                        Address: {user.address or 'N/A'}
                    </div>
                    <div class="customer-right">
                        <strong>Account Info:</strong><br>
                        Username: {user.username}<br>
                        Current Balance: {user.balance:.2f} BDT
                    </div>
                </div>
            </div>
        </div>
        
        <div class="invoice-items">
            <table class="invoice-table">
                <thead>
                    <tr>
                        <th>Service</th>
                        <th class="text-center">Quantity</th>
                        <th class="text-center">Rate (BDT)</th>
                        <th class="text-right">Total (BDT)</th>
                    </tr>
                </thead>
                <tbody>"""
    
    for service_name, data in service_totals.items():
        html += f"""
                    <tr>
                        <td>{service_name}</td>
                        <td class="text-center">{data['count']}</td>
                        <td class="text-center">{data['rate']:.2f}</td>
                        <td class="text-right">{data['total']:.2f}</td>
                    </tr>"""
    
    html += f"""
                </tbody>
                <tfoot>
                    <tr class="total-row">
                        <td colspan="3"><strong>Total Amount:</strong></td>
                        <td class="text-right"><strong>{total_amount:.2f} BDT</strong></td>
                    </tr>
                </tfoot>
            </table>
        </div>
        
        <div class="invoice-footer">
            <div style="font-size: 16px; font-weight: bold; margin-bottom: 10px;">Thank you for choosing Chief Elite BD!</div>
            <div style="font-size: 14px; color: #666;">This invoice shows your purchased services and their costs.</div>
            <div style="font-size: 12px; color: #999; margin-top: 15px;">Generated on {invoice_date}</div>
        </div>
    </div>"""
    
    return html

# Check if user is allowed to check a specific item
def allowed_to_check(user, service):
    service_name = service.name.lower()
    
    # Return False if user is a mail user and trying to check Facebook or LinkedIn
    if user.is_mail_user() and service_name in ['facebook', 'linkedin']:
        return False
    
    # Return False if user is a pass user and trying to check Gmail or Outlook
    if user.is_pass_user() and service_name in ['gmail', 'outlook']:
        return False
    
    return True
