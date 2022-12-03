from setuptools import setup, find_packages

setup(name='blog',
      version='0.1.0',
      description='A blog developed base on Flask framework',
      long_description='On this blog, you can post anything topic you want.',
      author='Thipro',
      author_email='nnthibk1234@gmail.com',
      maintainer='Thipro',
      maintainer_email='nnthibk1234@gmail.com',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Flask',
          'Natural Language :: Vietnamese',
          'Programming Language :: Python',
          'License :: OSI Approved :: MIT License',
      ],
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'flask',
      ],
      )
