document.addEventListener('DOMContentLoaded', () => {
    
    // Theme Toggling
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        // Check local storage for preference
        if (localStorage.getItem('theme') === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        }

        themeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            if (current === 'dark') {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            }
        });
    }

    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.card').forEach(card => {
                const domain = card.getAttribute('data-domain');
                if (domain.includes(term)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Reveal Buttons
    const toast = document.getElementById('toast');
    document.querySelectorAll('.reveal-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const domain = e.target.getAttribute('data-domain');
            const originalText = e.target.innerText;
            
            e.target.innerText = "Revealing...";
            
            try {
                const res = await fetch('/api/reveal', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({domain})
                });
                
                const data = await res.json();
                if (data.success) {
                    toast.innerText = "Copied to clipboard!";
                    toast.classList.remove('hidden');
                    e.target.innerText = "Copied!";
                    
                    // The password was actually copied server-side by pyperclip
                    // We don't necessarily need to use navigator.clipboard here,
                    // but we could if we wanted the browser to do it.
                    
                    setTimeout(() => {
                        toast.classList.add('hidden');
                        e.target.innerText = originalText;
                    }, 3000);
                } else {
                    alert("Failed to reveal: " + data.error);
                    e.target.innerText = originalText;
                }
            } catch (err) {
                alert("Network error");
                e.target.innerText = originalText;
            }
        });
    });

    // Add Form
    const addForm = document.getElementById('add-form');
    if (addForm) {
        addForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const domain = document.getElementById('domain').value;
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const res = await fetch('/api/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({domain, username, password})
                });
                
                const data = await res.json();
                if (data.success) {
                    location.reload(); // Quick refresh to show new entry
                } else {
                    alert("Error: " + data.error);
                }
            } catch (err) {
                alert("Network error");
            }
        });
    }

    // Lock Button
    const lockBtn = document.getElementById('lock-btn');
    if (lockBtn) {
        lockBtn.addEventListener('click', async () => {
            await fetch('/api/lock', { method: 'POST' });
            location.href = '/login';
        });
    }

    // Auto-lock timer (JavaScript side to sync with Python side)
    // 5 minutes = 300,000 ms
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
                // Time's up, lock it
                fetch('/api/lock', { method: 'POST' }).then(() => {
                    location.href = '/login';
                });
            }
        }, 1000);
    }
});
