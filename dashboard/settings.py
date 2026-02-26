import os

domain_root = os.environ.get('DOMAIN_ROOT', 'rebble.io')
http_protocol = os.environ.get('HTTP_PROTOCOL', 'https')

config = {
    'DOMAIN_ROOT': domain_root,
    'SECRET_KEY': os.environ.get('SECRET_KEY'),
    'HONEYCOMB_KEY': os.environ.get('HONEYCOMB_KEY', None),
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
}
