# vim: tabstop=4 shiftwidth=4 softtabstop=4

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


SENTINEL = object()


class cached_property(object):
    def __init__(self, f):
        self.f = f
        self.__name__ = f.__name__
        self.__module__ = f.__module__
        self.__doc__ = f.__doc__

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, SENTINEL)
        if value is SENTINEL:
            value = self.f(obj)
            obj.__dict__[self.__name__] = value
        return value
