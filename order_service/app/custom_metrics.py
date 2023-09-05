from prometheus_client import Counter


total_orders = Counter('total_all_created_orders', 'Total of all created orders', labelnames=('total_orders',))
