from flask import render_template, request, redirect, url_for, flash, session
from app.admin import admin_bp
from app import supabase
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# GÜVENLİK KALKANI
@admin_bp.before_request
def require_admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('auth.login'))

# --- ANA DASHBOARD ---
@admin_bp.route('/dashboard')
def dashboard():
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    response = supabase.table('deliveries').select(
        'id, status, delivery_date, created_at, items, '
        'customers(id, full_name, address, phone)'
    ).execute()
    
    deliveries = response.data
    
    # YENİ: Toplam Müşteri Sayısını Çekiyoruz
    cust_resp = supabase.table('customers').select('id').execute()
    total_customers = len(cust_resp.data) if cust_resp.data else 0

    today_packages = []
    tomorrow_packages = []
    delayed_packages = []

    for pkg in deliveries:
        pkg_date_str = pkg.get('delivery_date')
        if not pkg_date_str:
            continue
            
        pkg_date = datetime.strptime(pkg_date_str, '%Y-%m-%d').date()
        status = pkg.get('status')

        if status not in ['Teslim Edildi', 'İptal Edildi']:
            if pkg_date == today:
                today_packages.append(pkg)
            elif pkg_date == tomorrow:
                tomorrow_packages.append(pkg)
            elif pkg_date < today:
                delayed_packages.append(pkg)

    return render_template('dashboard.html', 
                           today_packages=today_packages, 
                           tomorrow_packages=tomorrow_packages, 
                           delayed_packages=delayed_packages,
                           total_customers=total_customers)

@admin_bp.route('/update_status/<int:delivery_id>', methods=['POST'])
def update_status(delivery_id):
    new_status = request.form.get('status')
    
    pkg_response = supabase.table('deliveries').select('*').eq('id', delivery_id).execute()
    if not pkg_response.data:
        flash('Paket bulunamadı.', 'error')
        return redirect(url_for('admin.dashboard'))
        
    package = pkg_response.data[0]
    old_status = package.get('status')

    supabase.table('deliveries').update({'status': new_status}).eq('id', delivery_id).execute()

    if old_status != 'Teslim Edildi' and new_status == 'Teslim Edildi':
        items = package.get('items', [])
        for item in items:
            product_id = item.get('product_id')
            qty_to_deduct = item.get('quantity')
            
            stock_resp = supabase.table('inventory').select('stock_count').eq('id', product_id).execute()
            if stock_resp.data:
                current_stock = stock_resp.data[0].get('stock_count')
                new_stock = current_stock - qty_to_deduct
                supabase.table('inventory').update({'stock_count': new_stock}).eq('id', product_id).execute()

    flash(f'Paket #{delivery_id} durumu "{new_status}" olarak güncellendi.', 'success')
    return redirect(url_for('admin.dashboard'))


# --- MÜŞTERİ YÖNETİMİ ---
@admin_bp.route('/customers')
def customers():
    response = supabase.table('customers').select('*').order('id', desc=True).execute()
    all_customers = response.data
    
    today = datetime.now().date()
    for cust in all_customers:
        end_date_str = cust.get('subscription_end_date')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if end_date < today and cust.get('status') != 'Askıda':
                supabase.table('customers').update({'status': 'Askıda'}).eq('id', cust['id']).execute()
                cust['status'] = 'Askıda'

    return render_template('customers.html', customers=all_customers)

@admin_bp.route('/add_customer', methods=['POST'])
def add_customer():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    city = request.form.get('city')
    address = request.form.get('address')
    username = request.form.get('username')
    password = request.form.get('password')

    customer_data = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "address": f"{city} - {address}",
        "status": "Aktif"
    }
    
    try:
        cust_response = supabase.table('customers').insert(customer_data).execute()
        new_customer_id = cust_response.data[0]['id']

        user_data = {
            "username": username,
            "password_hash": generate_password_hash(password),
            "role": "customer",
            "reference_id": new_customer_id
        }
        supabase.table('users').insert(user_data).execute()
        
        flash(f'Müşteri {full_name} sisteme başarıyla eklendi.', 'success')
    except Exception as e:
        flash(f'Müşteri eklenirken hata oluştu (E-posta veya kullanıcı adı kullanılıyor olabilir).', 'danger')

    return redirect(url_for('admin.customers'))

@admin_bp.route('/update_customer/<int:customer_id>', methods=['POST'])
def update_customer(customer_id):
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    subscription_end_date = request.form.get('subscription_end_date')

    update_data = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "address": address,
        "subscription_end_date": subscription_end_date
    }

    today = datetime.now().date()
    end_date_obj = datetime.strptime(subscription_end_date, '%Y-%m-%d').date()
    
    if end_date_obj < today:
        update_data["status"] = "Askıda"
    else:
        update_data["status"] = "Aktif"

    try:
        supabase.table('customers').update(update_data).eq('id', customer_id).execute()
        flash(f'{full_name} isimli müşterinin bilgileri başarıyla güncellendi.', 'success')
    except Exception as e:
        flash('Güncelleme başarısız. Bu E-posta adresi başka bir hesaba ait olabilir.', 'danger')

    return redirect(url_for('admin.customers'))

@admin_bp.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    try:
        supabase.table('customers').delete().eq('id', customer_id).execute()
        flash('Müşteri sistemden tamamen silindi.', 'success')
    except Exception as e:
        flash('Silme işlemi başarısız.', 'danger')
        
    return redirect(url_for('admin.customers'))