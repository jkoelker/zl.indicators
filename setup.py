#!/usr/bin/env python

# Copyright 2013 Jason Koelker
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import setuptools

classifiers = ['Development Status :: 4 - Beta',
               'License :: OSI Approved :: Apache Software License']

requires = ['zipline']

setuptools.setup(name='zl.indicators',
                 version='0.1',
                 url='https://github.com/jkoelker/zl.indicators',
                 license='Apache Software License',
                 description='Collection of Zipline Indicators',
                 classifiers=classifiers,
                 author='Jason Koelker',
                 author_email='jason@koelker.net',
                 install_requires=requires,
                 packages=['zl', 'zl.indicators'],
                 namespace_packages=['zl'])
