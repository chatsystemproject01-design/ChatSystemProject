import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key = os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")

print(f"URL: {url}")
print(f"Key preview: {key[:15]}...")

try:
    supabase = create_client(url, key)
    buckets = supabase.storage.list_buckets()
    print("Available Buckets:", [b.name for b in buckets])
    
    found = any(b.name == 'media' for b in buckets)
    print(f"Bucket 'media' exists: {found}")
    
    if found:
        print("Attempting test upload...")
        test_content = b"Hello Supabase Storage"
        res = supabase.storage.from_('media').upload(
            path="test_debug.txt",
            file=test_content,
            file_options={"content-type": "text/plain"}
        )
        print("Upload Result:", res)
except Exception as e:
    print(f"Detailed Error: {type(e).__name__} - {e}")
    import traceback
    traceback.print_exc()
