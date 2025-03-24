import re
import nltk
from nltk.corpus import stopwords

def download_nltk_resources():
    """Download required NLTK resources"""
    try:
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
    except Exception as e:
        print(f"Error downloading NLTK resources: {e}")

# Indonesian stopwords
INDONESIAN_STOPWORDS = [
    'yang', 'dan', 'di', 'dengan', 'untuk', 'pada', 'ke', 'dari', 'dalam',
    'ini', 'itu', 'oleh', 'akan', 'tidak', 'juga', 'saya', 'kamu', 'dia',
    'mereka', 'kita', 'kami', 'ada', 'adalah', 'bisa', 'dapat', 'sebagai',
    'jika', 'kalau', 'agar', 'supaya', 'tentang', 'atau', 'tetapi', 'namun',
    'karena', 'ketika', 'maka', 'saat', 'waktu', 'bila', 'meski', 'walaupun',
    'seperti', 'telah', 'sudah', 'belum', 'masih', 'sedang', 'akan', 'harus',
    'bagi', 'serta', 'lagi', 'menjadi', 'tersebut', 'bahwa', 'merupakan', 
    'demikian', 'sejak', 'hingga', 'sampai', 'selama', 'setelah', 'sebelum',
    'sempat', 'selalu', 'sering', 'jarang', 'pernah', 'terlalu', 'sangat',
    'sekali', 'hanya', 'saja', 'para', 'semua', 'lebih', 'kurang', 'paling',
    'ialah', 'yakni', 'yaitu', 'adalah', 'apa', 'siapa', 'kapan', 'mengapa',
    'bagaimana', 'dimana', 'kemana', 'darimana', 'si', 'sang', 'para',
    'dll', 'dst', 'dsb', 'etc', 'dll', 'hal', 'saat', 'nya'
]

def get_stopwords():
    """Get combined stopwords list"""
    download_nltk_resources()
    try:
        stop_words = set(stopwords.words('indonesian'))
    except:
        stop_words = set()
    
    # Combine with custom Indonesian stopwords
    stop_words.update(INDONESIAN_STOPWORDS)
    return stop_words

def clean_text(text):
    """Clean text for wordcloud processing"""
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def prepare_text_for_wordcloud(text_series):
    """Prepare text data for wordcloud"""
    # Combine all text
    all_text = ' '.join(text_series.apply(clean_text).fillna(''))
    
    # Remove stopwords
    stop_words = get_stopwords()
    words = all_text.split()
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    return ' '.join(filtered_words)
