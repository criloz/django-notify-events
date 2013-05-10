from setuptools import setup, find_packages

setup(
    name="django-notify-events",
    version= 0.1,
    description="User notification management for the Django web framework",
    packages=find_packages(),
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ],
    include_package_data=True,
    zip_safe=False,
)