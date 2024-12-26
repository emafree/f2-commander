# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2024 Timur Rubeko

import nox


@nox.session(python=["3.9", "3.10", "3.11", "3.12", "3.13"])
def tests(session):
    session.run("poetry", "install", "--with=dev", external=True)
    session.run("pytest")
