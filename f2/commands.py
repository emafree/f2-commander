# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko


class Command:
    """
    A helper class to define an abstract command that is present in the Command
    Palette, and can optionally be bound to a key.
    """

    def __init__(self, action, name, description, binding_key=None):
        self.action = action
        self.name = name
        self.description = description
        self.binding_key = binding_key
