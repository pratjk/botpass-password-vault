import os
import hashlib
import random
import string
import urllib.request

# I spent 3 hours on this regex and still don't fully trust it
# ...just kidding, there's no regex here. But the vibe stands.

# --- Password Generator ---

# Diceware-ish wordlist (a small one, good enough for a student project)
# In a real app you'd load from a file, but this works
WORDLIST = [
    "correct", "horse", "battery", "staple", "dragon", "monkey",
    "shadow", "master", "freedom", "thunder", "pepper", "orange",
    "castle", "rocket", "wizard", "galaxy", "anchor", "breeze",
    "crystal", "falcon", "harbor", "jungle", "knight", "legend",
    "meadow", "nebula", "oracle", "palace", "quartz", "riddle",
    "sierra", "temple", "utopia", "velvet", "walrus", "zenith",
    "alpine", "blaze", "canyon", "drift", "ember", "frost",
    "golden", "haven", "ivory", "jasper", "karma", "lotus",
    "marble", "noble", "oasis", "prism", "quest", "raven",
    "solar", "tidal", "urban", "vigor", "wheat", "yield",
]

def generate_password_diceware(num_words=4):
    """Generate a diceware-style passphrase like 'correct-horse-battery-staple'."""
    words = random.sample(WORDLIST, num_words)
    return "-".join(words)

def generate_password_random(length=16):
    """Generate a random strong password with mixed characters."""
    if length < 8:
        length = 8
    
    # Make sure we always include at least one of each type
    chars = []
    chars.append(random.choice(string.ascii_uppercase))
    chars.append(random.choice(string.ascii_lowercase))
    chars.append(random.choice(string.digits))
    chars.append(random.choice("!@#$%^&*()-_=+"))
    
    remaining = length - len(chars)
    pool = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    for _ in range(remaining):
        chars.append(random.choice(pool))
    
    random.shuffle(chars)
    return "".join(chars)

# --- Password Strength ---

def check_password_strength(password):
    """
    Simple password strength checker. Returns a dict with score and feedback.
    Score: 0 (terrible) to 4 (strong).
    Not as good as zxcvbn but doesn't need an external dependency.
    """
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Too short (minimum 8 characters)")
        
    if len(password) >= 12:
        score += 1
    
    if any(c.isdigit() for c in password):
        score += 0.5
    else:
        feedback.append("Add some numbers")
        
    if any(not c.isalnum() for c in password):
        score += 0.5
    else:
        feedback.append("Add a special character (!@#$%)")
        
    if any(c.isupper() for c in password) and any(c.islower() for c in password):
        score += 0.5
    else:
        feedback.append("Mix upper and lowercase letters")
    
    # Check for common patterns
    common = ["password", "123456", "qwerty", "admin", "letmein", "welcome"]
    if password.lower() in common:
        score = 0
        feedback = ["This is one of the most common passwords. Please don't."]
    
    # Diceware passphrases get a bonus
    if "-" in password and len(password.split("-")) >= 3:
        score += 0.5
    
    score = min(int(score), 4)
    
    labels = ["Terrible", "Weak", "Fair", "Good", "Strong"]
    
    if not feedback:
        feedback.append("Looks good!")
    
    return {
        "score": score,
        "label": labels[score],
        "feedback": feedback
    }

# --- Have I Been Pwned ---

def check_hibp(password):
    """
    Check if a password has been seen in data breaches using the 
    Have I Been Pwned API with k-anonymity (only first 5 chars of hash sent).
    Returns the number of times it was found, or 0 if clean.
    """
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1[:5]
    suffix = sha1[5:]
    
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'botpass-vault')
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode('utf-8')
            
        # Each line is like: SUFFIX:COUNT
        for line in body.splitlines():
            parts = line.strip().split(":")
            if len(parts) == 2 and parts[0] == suffix:
                return int(parts[1])
                
        return 0
    except Exception:
        # Network error, timeout, etc. Don't block the user.
        return -1  # -1 means "couldn't check"
