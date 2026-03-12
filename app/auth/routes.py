from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app.auth import auth_bp
from app import supabase

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Eğer kullanıcı zaten giriş yapmışsa, rolüne göre kendi paneline yönlendir
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session.get('role') == 'customer':
            return redirect(url_for('customer.dashboard'))
        elif session.get('role') == 'courier':
            return redirect(url_for('courier.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Kullanıcıyı veritabanında ara
        response = supabase.table('users').select('*').eq('username', username).execute()
        users = response.data

        # Kullanıcı varsa ve şifresi (hashlenmiş haliyle) eşleşiyorsa
        if users and check_password_hash(users[0]['password_hash'], password):
            user = users[0]
            
            # Tarayıcıya güvenli oturum çerezlerini (Session) kaydet
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['reference_id'] = user['reference_id']

            flash(f'Hoş geldiniz, {user["username"]}!', 'success')

            # Role göre uygun portala yönlendir
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user['role'] == 'customer':
                return redirect(url_for('customer.dashboard'))
            elif user['role'] == 'courier':
                return redirect(url_for('courier.dashboard'))
        else:
            flash('Hatalı kullanıcı adı veya şifre.', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear() # Oturumu tamamen temizle
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('auth.login'))