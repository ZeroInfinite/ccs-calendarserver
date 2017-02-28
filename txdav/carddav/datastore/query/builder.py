##
# Copyright (c) 2006-2017 Apple Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

from txdav.common.datastore.query import expression
from txdav.carddav.datastore.query.filter import TextMatch

"""
SQL statement generator from query expressions.
"""

__all__ = [
    "buildExpression",
]


# SQL Index column (field) names

def buildExpression(filter, fields):
    """
    Convert the supplied addressbook-query into an expression tree.

    @param filter: the L{Filter} for the addressbook-query to convert.
    @return: a L{baseExpression} for the expression tree.
    """
    # Lets assume we have a valid filter from the outset.

    # Top-level filter contains zero or more prop-filter element
    if len(filter.children) > 0:
        return propfilterListExpression(filter.children, fields)
    else:
        return expression.allExpression()


def propfilterListExpression(propfilters, fields):
    """
    Create an expression for a list of prop-filter elements.

    @param propfilters: the C{list} of L{ComponentFilter} elements.
    @return: a L{baseExpression} for the expression tree.
    """

    if len(propfilters) == 1:
        return propfilterExpression(propfilters[0], fields)
    else:
        return expression.orExpression([propfilterExpression(c, fields) for c in propfilters])


def propfilterExpression(propfilter, fields):
    """
    Create an expression for a single prop-filter element.

    @param propfilter: the L{PropertyFilter} element.
    @return: a L{baseExpression} for the expression tree.
    """

    # Only handle UID right now
    if propfilter.filter_name != "UID":
        raise ValueError

    # Handle is-not-defined case
    if not propfilter.defined:
        # Test for <<field>> != "*"
        return expression.isExpression(fields["UID"], "", True)

    # Handle embedded parameters/text-match
    params = []
    for filter in propfilter.filters:
        if isinstance(filter, TextMatch):
            if filter.match_type == "equals":
                tm = expression.isnotExpression if filter.negate else expression.isExpression
            elif filter.match_type == "contains":
                tm = expression.notcontainsExpression if filter.negate else expression.containsExpression
            elif filter.match_type == "starts-with":
                tm = expression.notstartswithExpression if filter.negate else expression.startswithExpression
            elif filter.match_type == "ends-with":
                tm = expression.notendswithExpression if filter.negate else expression.endswithExpression
            params.append(tm(fields[propfilter.filter_name], str(filter.text), True))
        else:
            # No embedded parameters - not right now as our Index does not handle them
            raise ValueError

    # Now build return expression
    if len(params) > 1:
        if propfilter.propfilter_test == "anyof":
            return expression.orExpression(params)
        else:
            return expression.andExpression(params)
    elif len(params) == 1:
        return params[0]
    else:
        return None
