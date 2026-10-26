try:
    import nacl
    print(f"PyNaCl {nacl.__version__} available")
except ImportError as e:
    print(f"PyNaCl NOT available: {e}")
