from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import pyperclip

from botpass.core.vault import Vault
from botpass.core.utils import generate_password_diceware, generate_password_random, check_password_strength, check_hibp

app = Flask(__name__)
# Generate a random secret key for Flask sessions each time
# It's fine since it's local only and restarts mean new sessions anyway
app.secret_key = os.urandom(24)

# Hardcoded paths just like CLI
VAULT_PATH = os.path.expanduser("vault.db")
SALT_PATH = os.path.expanduser("salt.bin")
CONFIG_PATH = os.path.expanduser("config.json")

_vault_instance = Vault(VAULT_PATH, SALT_PATH, CONFIG_PATH)

@app.route('/')
def dashboard():
    # If vault is locked or not initialized
    if not _vault_instance.key:
        return redirect(url_for('login'))
        
    try:
        entries = _vault_instance.list_entries()
    except Exception as e:
        entries = []
        
    return render_template('index.html', entries=entries)

@app.route('/login', methods=['GET', 'POST'])
def login():
    needs_setup = not os.path.exists(VAULT_PATH)
    error = None

    if request.method == 'POST':
        master_pw = request.form.get('master_pw')
        if needs_setup:
            pw2 = request.form.get('master_pw2')
            if master_pw != pw2:
                error = "Passwords do not match."
            else:
                try:
                    _vault_instance.setup(master_pw)
                    return redirect(url_for('dashboard'))
                except Exception as e:
                    error = str(e)
        else:
            if _vault_instance.unlock(master_pw):
                return redirect(url_for('dashboard'))
            else:
                error = "Wrong password. Try again."

    return render_template('login.html', needs_setup=needs_setup, error=error)

@app.route('/api/add', methods=['POST'])
def api_add():
    if not _vault_instance.key:
        return jsonify({"error": "Vault locked"}), 401
        
    data = request.json
    domain = data.get('domain')
    username = data.get('username')
    password = data.get('password')
    notes = data.get('notes', '')
    
    if not domain or not password:
        return jsonify({"error": "Missing domain or password"}), 400
        
    try:
        _vault_instance.add(domain, username, password, notes)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/reveal', methods=['POST'])
def api_reveal():
    if not _vault_instance.key:
        return jsonify({"error": "Vault locked"}), 401
        
    domain = request.json.get('domain')
    data = _vault_instance.get(domain)
    
    if data:
        # Copy to clipboard as a feature
        pyperclip.copy(data.get('password', ''))
        return jsonify({"success": True, "password": data.get('password'), "copied": True})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/delete', methods=['POST'])
def api_delete():
    if not _vault_instance.key:
        return jsonify({"error": "Vault locked"}), 401
        
    domain = request.json.get('domain')
    if _vault_instance.delete(domain):
        return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/update', methods=['POST'])
def api_update():
    if not _vault_instance.key:
        return jsonify({"error": "Vault locked"}), 401
        
    data = request.json
    domain = data.get('domain')
    new_username = data.get('username')
    new_password = data.get('password')
    new_notes = data.get('notes')
    
    try:
        _vault_instance.update_entry(
            domain, 
            new_username=new_username if new_username else None,
            new_password=new_password if new_password else None,
            new_notes=new_notes if new_notes is not None else None
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/generate', methods=['POST'])
def api_generate():
    style = request.json.get('style', 'random')
    if style == 'diceware':
        pw = generate_password_diceware()
    else:
        pw = generate_password_random()
    
    strength = check_password_strength(pw)
    return jsonify({"password": pw, "strength": strength})

@app.route('/api/strength', methods=['POST'])
def api_strength():
    password = request.json.get('password', '')
    strength = check_password_strength(password)
    return jsonify(strength)

@app.route('/api/breach', methods=['POST'])
def api_breach():
    password = request.json.get('password', '')
    count = check_hibp(password)
    return jsonify({"count": count})

@app.route('/api/changepw', methods=['POST'])
def api_changepw():
    if not _vault_instance.key:
        return jsonify({"error": "Vault locked"}), 401
        
    data = request.json
    new_pw = data.get('new_pw')
    new_pw2 = data.get('new_pw2')
    
    if new_pw != new_pw2:
        return jsonify({"error": "Passwords do not match."}), 400
        
    try:
        _vault_instance.change_master_password(new_pw)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/export', methods=['GET'])
def api_export():
    if not _vault_instance.key:
        return jsonify({"error": "Vault locked"}), 401
    
    filepath = os.path.expanduser("vault_backup.botpass")
    try:
        _vault_instance.export_backup(filepath)
        return jsonify({"success": True, "path": os.path.abspath(filepath)})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/import', methods=['POST'])
def api_import():
    if not _vault_instance.key:
        return jsonify({"error": "Vault locked"}), 401
    
    filepath = os.path.expanduser(request.json.get('filepath', ''))
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 400
    
    try:
        result = _vault_instance.import_backup(filepath)
        return jsonify({"success": True, "imported": result['imported'], "skipped": result['skipped']})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/lock', methods=['POST'])
def api_lock():
    _vault_instance.lock()
    return jsonify({"success": True})

if __name__ == '__main__':
    # Local only!
    app.run(host='127.0.0.1', port=5000, debug=True)
