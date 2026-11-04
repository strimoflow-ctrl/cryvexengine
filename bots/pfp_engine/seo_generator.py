import random
import re

TITLE_TEMPLATES = [
    "🔥 Aesthetic {subject} PFP | 4K Ultra HD Profile Picture",
    "✨ {subject} Aesthetic Wallpaper & PFP (Free Ultra HD Download)",
    "🖤 Dark Aesthetic {subject} Icon | High Resolution Profile Picture",
    "💎 Cool {subject} Avatar & Wallpaper 4K | Free Download",
    "🌟 Best {subject} PFP for Discord, Telegram & Insta (Ultra HD)",
    "⚡ Cyberpunk & Dark {subject} PFP | 4K Aesthetic Wallpaper",
    "💜 Moody Aesthetic {subject} Profile Picture (Download in 4K)",
    "🎨 Minimalist & Clean {subject} PFP | Ultra HD 4K Quality",
    "🌸 Trendy {subject} Aesthetic Profile Picture & Background 4K",
    "👑 Ultimate {subject} Wallpaper & PFP (Full HD Original)"
]

SUBJECTS = [
    "Boy", "Anime Boy", "Dark Boy", "Cool Boy", 
    "Girl", "Anime Girl", "Aesthetic Girl",
    "Matching Couple", "Anime", "Aesthetic Mood"
]

DESCRIPTION_TEMPLATES = [
    "Looking for the cleanest {subject} PFP in original 4K resolution? Tap visit site to download the full uncompressed HD image directly with zero quality loss! Perfect for Instagram, Discord, and Telegram avatars.",
    "Upgrade your profile picture with this aesthetic {subject} 4K icon! Visit our website to preview and download the ultra high-definition version instantly.",
    "Free Ultra HD {subject} Wallpaper & PFP. Download original uncompressed graphics, high dynamic range, and crisp colors. Click the link to download now!",
    "Best aesthetic {subject} avatar for social media! High contrast, 4K crisp detail. Visit the site for the original file download."
]

TAGS_POOL = [
    "#pfp", "#aestheticpfp", "#boypfp", "#girlpfp", "#animepfp", 
    "#darkaesthetic", "#wallpaper4k", "#discordpfp", "#profilepicture", 
    "#animeaesthetic", "#coolpfp", "#instapfp", "#aestheticwallpaper"
]

def clean_caption(caption: str) -> str:
    if not caption:
        return ""
    caption = re.sub(r"https?://\S+|t\.me/\S+", "", caption)
    caption = re.sub(r"[@_#*]", " ", caption)
    return " ".join(caption.split())

def generate_seo_metadata(caption: str = "", media_type: str = "photo", msg_id: int = 0):
    cleaned = clean_caption(caption)
    subject = "Boy"
    caption_lower = cleaned.lower()
    
    if "girl" in caption_lower:
        subject = "Girl"
    elif "couple" in caption_lower or "matching" in caption_lower:
        subject = "Matching Couple"
    elif "anime" in caption_lower:
        subject = "Anime Boy" if "boy" in caption_lower else "Anime"
    elif "dark" in caption_lower:
        subject = "Dark Boy"
    else:
        rng = random.Random(msg_id)
        subject = rng.choice(SUBJECTS)
        
    rng = random.Random(msg_id)
    title_template = rng.choice(TITLE_TEMPLATES)
    desc_template = rng.choice(DESCRIPTION_TEMPLATES)
    
    title = title_template.format(subject=subject)
    description = desc_template.format(subject=subject)
    
    selected_tags = rng.sample(TAGS_POOL, min(6, len(TAGS_POOL)))
    tags_str = " ".join(selected_tags)
    
    full_description = f"{description}\n\n{tags_str}"
    
    return {
        "title": title[:100],
        "description": full_description[:500],
        "tags": tags_str
    }

