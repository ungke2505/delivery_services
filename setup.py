from setuptools import setup, find_packages

setup(
    name="delivery_services",
    version="1.0.0",
    description="Delivery Services PWA for ERPNext v15",
    author="Your Company",
    author_email="admin@yourcompany.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[],  # Frappe is a peer dep managed by bench, not pip
)
