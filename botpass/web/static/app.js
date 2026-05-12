document.addEventListener('DOMContentLoaded', () => {

    const toast = document.getElementById('toast');

    function showToast(msg, duration = 3000) {
        toast.innerText = msg;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), duration);
    }

    // --- Import UI ---
    const importBtn = document.getElementById('import-btn');
    const importSection = document.getElementById('import-section');
    const cancelImport = document.getElementById('cancel-import');
    const importForm = document.getElementById('import-form');
    const importMessage = document.getElementById('import-message');

    if (importBtn && importSection && cancelImport) {
        importBtn.addEventListener('click', () => {
            importSection.style.display = 'block';
        });
        cancelImport.addEventListener('click', () => {
            importSection.style.display = 'none';
        });
    }

    if (importForm) {
        importForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const filepath = document.getElementById('import-path').value;
            if (importMessage) importMessage.innerText = 'Importing...';

            try {
                const res = await fetch('/api/import', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filepath})
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`Imported ${data.imported} entries (${data.skipped} skipped)`);
                    importSection.style.display = 'none';
                    location.reload();
                } else {
                    if (importMessage) {
                        importMessage.innerText = 'Error: ' + data.error;
                        importMessage.style.color = 'var(--danger)';
                    }
                }
            } catch(err) {
                if (importMessage) importMessage.innerText = 'Network error';
            }
        });
    }

    // --- Change Password UI ---
    const showChangePwBtn = document.getElementById('show-change-pw-btn');
    const changePwSection = document.getElementById('change-pw-section');
    const cancelChangePw = document.getElementById('cancel-change-pw');
    
    if (showChangePwBtn && changePwSection && cancelChangePw) {
        showChangePwBtn.addEventListener('click', () => {
            changePwSection.style.display = 'block';
        });
        cancelChangePw.addEventListener('click', () => {
            changePwSection.style.display = 'none';
        });
    }

    const changePwForm = document.getElementById('change-pw-form');
    if (changePwForm) {
        changePwForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const new_pw = document.getElementById('new-pw').value;
            const new_pw2 = document.getElementById('new-pw2').value;

            if (new_pw !== new_pw2) {
                alert("Passwords do not match!");
                return;
            }

            try {
                const res = await fetch('/api/changepw', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({new_pw, new_pw2})
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Master password changed and vault re-encrypted!");
                    changePwSection.style.display = 'none';
                    document.getElementById('new-pw').value = '';
                    document.getElementById('new-pw2').value = '';
                } else {
                    alert("Error: " + data.error);
                }
            } catch (err) {
                alert("Network error");
            }
        });
    }

    // --- Search ---
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.card').forEach(card => {
                const domain = card.getAttribute('data-domain') || '';
                const tags = card.getAttribute('data-tags') || '';
                card.style.display = (domain.includes(term) || tags.includes(term)) ? 'block' : 'none';
            });
        });
    }

    // --- Password Strength Bar (Add Form) ---
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('strength-bar');
    const addMessage = document.getElementById('add-message');
    let strengthTimeout;

    if (passwordInput && strengthBar) {
        passwordInput.addEventListener('input', (e) => {
            clearTimeout(strengthTimeout);
            const pw = e.target.value;
            if (!pw) {
                strengthBar.className = 'strength-bar';
                if (addMessage) addMessage.innerText = '';
                return;
            }
            strengthTimeout = setTimeout(async () => {
                try {
                    const res = await fetch('/api/strength', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({password: pw})
                    });
                    const data = await res.json();
                    strengthBar.className = 'strength-bar strength-' + data.score;
                    if (addMessage) {
                        addMessage.innerText = data.label + ' // ' + data.feedback.join(', ');
                        addMessage.style.color = ['#e74c3c','#e74c3c','#f39c12','#27ae60','#27ae60'][data.score];
                    }
                } catch(err) {}
            }, 300);
        });
    }

    // --- Generate Password (Add Form) ---
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn && passwordInput) {
        generateBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({style: 'random'})
                });
                const data = await res.json();
                passwordInput.type = 'text'; // Show it briefly
                passwordInput.value = data.password;
                passwordInput.dispatchEvent(new Event('input')); // Trigger strength bar
                setTimeout(() => { passwordInput.type = 'password'; }, 3000);
                showToast("SYSTEM: PASSWORD GENERATED. VISIBLE FOR 3S.");
            } catch(err) {
                alert("Failed to generate password");
            }
        });
    }

    // --- Add Form ---
    const addForm = document.getElementById('add-form');
    if (addForm) {
        addForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const domain = document.getElementById('domain').value;
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const notes = document.getElementById('notes') ? document.getElementById('notes').value : '';
            const tags = document.getElementById('tags') ? document.getElementById('tags').value : '';
            const totp_secret = document.getElementById('totp_secret') ? document.getElementById('totp_secret').value : '';

            // Quick breach check before saving
            if (addMessage) addMessage.innerText = 'Checking breaches...';
            try {
                const breachRes = await fetch('/api/breach', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password})
                });
                const breachData = await breachRes.json();
                if (breachData.count > 0) {
                    const proceed = confirm(`SYSTEM ALERT: This password has appeared in ${breachData.count.toLocaleString()} data breaches!\n\nProceed anyway?`);
                    if (!proceed) {
                        if (addMessage) addMessage.innerText = 'Cancelled.';
                        return;
                    }
                }
            } catch(err) {
                // Couldn't reach HIBP, proceed anyway
            }

            try {
                const res = await fetch('/api/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({domain, username, password, notes, tags, totp_secret})
                });
                const data = await res.json();
                if (data.success) {
                    location.reload();
                } else {
                    alert("Error: " + data.error);
                }
            } catch (err) {
                alert("Network error");
            }
        });
    }

    // --- Reveal Buttons ---
    document.querySelectorAll('.reveal-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const domain = e.target.getAttribute('data-domain');
            const originalText = e.target.innerText;
            e.target.innerText = "...";

            try {
                const res = await fetch('/api/reveal', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({domain})
                });
                const data = await res.json();
                if (data.success) {
                    showToast("Password copied to clipboard!");
                    e.target.innerText = "[ COPIED ]";
                    
                    // Show TOTP modal if a code was returned
                    if (data.totp) {
                        const totpModal = document.getElementById('totp-modal');
                        const totpLabel = document.getElementById('totp-domain-label');
                        const totpCode = document.getElementById('totp-code');
                        if (totpModal && totpLabel && totpCode) {
                            totpLabel.innerText = domain;
                            totpCode.innerText = data.totp;
                            totpModal.classList.remove('hidden');
                        }
                    }

                    setTimeout(() => { e.target.innerText = originalText; }, 3000);
                } else {
                    alert("Failed: " + data.error);
                    e.target.innerText = originalText;
                }
            } catch (err) {
                alert("Network error");
                e.target.innerText = originalText;
            }
        });
    });

    // --- TOTP Modal close and copy ---
    const totpModal = document.getElementById('totp-modal');
    const totpCloseBtn = document.getElementById('totp-close-btn');
    const totpCodeDisplay = document.getElementById('totp-code');
    if (totpCloseBtn) {
        totpCloseBtn.addEventListener('click', () => {
            totpModal.classList.add('hidden');
        });
    }
    if (totpCodeDisplay) {
        totpCodeDisplay.addEventListener('click', () => {
            navigator.clipboard.writeText(totpCodeDisplay.innerText).then(() => {
                showToast("SYSTEM: 2FA CODE COPIED");
            });
        });
    }

    // --- Delete Buttons ---
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const domain = e.target.getAttribute('data-domain');
            if (!confirm(`Delete "${domain}"? This cannot be undone.`)) return;

            try {
                const res = await fetch('/api/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({domain})
                });
                const data = await res.json();
                if (data.success) {
                    // Remove the card from DOM
                    e.target.closest('.card').remove();
                    showToast(`Deleted ${domain}`);
                } else {
                    alert("Error: " + data.error);
                }
            } catch(err) {
                alert("Network error");
            }
        });
    });

    // --- Edit Modal ---
    const editModal = document.getElementById('edit-modal');
    const editUsername = document.getElementById('edit-username');
    const editPassword = document.getElementById('edit-password');
    const editDomainLabel = document.getElementById('edit-domain-label');
    const editMessage = document.getElementById('edit-message');
    const editSaveBtn = document.getElementById('edit-save-btn');
    const editCancelBtn = document.getElementById('edit-cancel-btn');
    const editGenerateBtn = document.getElementById('edit-generate-btn');
    const editBreachBtn = document.getElementById('edit-breach-btn');
    let editingDomain = null;

    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            editingDomain = e.target.getAttribute('data-domain');
            const currentUsername = e.target.getAttribute('data-username');
            const currentNotes = e.target.getAttribute('data-notes');
            const currentTags = e.target.getAttribute('data-tags');
            const currentTotp = e.target.getAttribute('data-totp');
            
            editDomainLabel.innerText = `Editing: ${editingDomain}`;
            editUsername.value = currentUsername || '';
            editPassword.value = '';
            
            const editNotesEl = document.getElementById('edit-notes');
            if (editNotesEl) editNotesEl.value = currentNotes || '';
            
            const editTagsEl = document.getElementById('edit-tags');
            if (editTagsEl) editTagsEl.value = currentTags || '';
            
            const editTotpEl = document.getElementById('edit-totp');
            if (editTotpEl) editTotpEl.value = currentTotp || '';
            
            if (editMessage) editMessage.innerText = '';
            editModal.classList.remove('hidden');
        });
    });

    if (editCancelBtn) {
        editCancelBtn.addEventListener('click', () => {
            editModal.classList.add('hidden');
            editingDomain = null;
        });
    }

    if (editGenerateBtn) {
        editGenerateBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({style: 'random'})
                });
                const data = await res.json();
                editPassword.type = 'text';
                editPassword.value = data.password;
                setTimeout(() => { editPassword.type = 'password'; }, 3000);
                if (editMessage) {
                    editMessage.innerText = `[ SYSTEM: GENERATED (${data.strength.label}) ] VISIBLE 3S.`;
                    editMessage.style.color = 'var(--success)';
                }
            } catch(err) {
                alert("Failed to generate");
            }
        });
    }

    if (editBreachBtn) {
        editBreachBtn.addEventListener('click', async () => {
            const pw = editPassword.value;
            if (!pw) {
                if (editMessage) editMessage.innerText = 'Enter a password first.';
                return;
            }
            if (editMessage) editMessage.innerText = 'Checking...';
            try {
                const res = await fetch('/api/breach', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password: pw})
                });
                const data = await res.json();
                if (data.count > 0) {
                    editMessage.innerText = `[ ALERT ] FOUND IN ${data.count.toLocaleString()} BREACHES.`;
                    editMessage.style.color = 'var(--danger)';
                } else if (data.count === 0) {
                    editMessage.innerText = '[ OK ] NOT FOUND IN BREACHES.';
                    editMessage.style.color = 'var(--success)';
                } else {
                    editMessage.innerText = 'Could not reach breach database.';
                    editMessage.style.color = 'var(--warning)';
                }
            } catch(err) {
                editMessage.innerText = 'Network error.';
            }
        });
    }

    if (editSaveBtn) {
        editSaveBtn.addEventListener('click', async () => {
            if (!editingDomain) return;
            const username = editUsername.value;
            const password = editPassword.value;
            const editNotesEl = document.getElementById('edit-notes');
            const notes = editNotesEl ? editNotesEl.value : '';
            const editTagsEl = document.getElementById('edit-tags');
            const tags = editTagsEl ? editTagsEl.value : '';
            const editTotpEl = document.getElementById('edit-totp');
            const totp_secret = editTotpEl ? editTotpEl.value : '';

            try {
                const res = await fetch('/api/update', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({domain: editingDomain, username, password, notes, tags, totp_secret})
                });
                const data = await res.json();
                if (data.success) {
                    showToast(`Updated ${editingDomain}`);
                    editModal.classList.add('hidden');
                    location.reload();
                } else {
                    alert("Error: " + data.error);
                }
            } catch(err) {
                alert("Network error");
            }
        });
    }

    // --- Export ---
    const exportBtn = document.getElementById('export-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/export');
                const data = await res.json();
                if (data.success) {
                    showToast(`Exported to: ${data.path}`);
                } else {
                    alert("Export failed: " + data.error);
                }
            } catch(err) {
                alert("Network error");
            }
        });
    }

    // --- Lock Button ---
    const lockBtn = document.getElementById('lock-btn');
    if (lockBtn) {
        lockBtn.addEventListener('click', async () => {
            await fetch('/api/lock', { method: 'POST' });
            location.href = '/login';
        });
    }

    // --- Auto-lock timer ---
    let idleTime = 0;
    const idleLimit = 5 * 60 * 1000;

    const resetIdle = () => { idleTime = 0; };
    window.addEventListener('mousemove', resetIdle);
    window.addEventListener('keypress', resetIdle);
    window.addEventListener('scroll', resetIdle);

    if (document.body.classList.contains('login-page') === false) {
        setInterval(() => {
            idleTime += 1000;
            if (idleTime >= idleLimit) {
                fetch('/api/lock', { method: 'POST' }).then(() => {
                    location.href = '/login';
                });
            }
        }, 1000);
    }
});
