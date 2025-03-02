# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model_ import Model
from openapi_server.models.query_constraint import QueryConstraint
from openapi_server import util

from openapi_server.models.query_constraint import QueryConstraint  # noqa: E501

class QEdge(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, predicates=None, subject=None, object=None, constraints=[], exclude=None, option_group_id=None, knowledge_type=None):  # noqa: E501
        """QEdge - a model defined in OpenAPI

        :param knowledge_type: The knowledge_type of this QEdge.  # noqa: E501
        :type knowledge_type: str
        :param predicates: The predicates of this QEdge.  # noqa: E501
        :type predicates: List[str]
        :param subject: The subject of this QEdge.  # noqa: E501
        :type subject: str
        :param object: The object of this QEdge.  # noqa: E501
        :type object: str
        :param constraints: The constraints of this QEdge.  # noqa: E501
        :type constraints: List[QueryConstraint]
        :param exclude: The exclude of this QEdge.  # noqa: E501
        :type exclude: bool
        :param option_group_id: The option_group_id of this QEdge.  # noqa: E501
        :type option_group_id: str
        """
        self.openapi_types = {
            'knowledge_type': str,
            'predicates': List[str],
            'subject': str,
            'object': str,
            'constraints': List[QueryConstraint],
            'exclude': bool,
            'option_group_id': str
        }

        self.attribute_map = {
            'knowledge_type': 'knowledge_type',
            'predicates': 'predicates',
            'subject': 'subject',
            'object': 'object',
            'constraints': 'constraints',
            'exclude': 'exclude',
            'option_group_id': 'option_group_id'
        }

        self._knowledge_type = knowledge_type
        self._predicates = predicates
        self._subject = subject
        self._object = object
        self._constraints = constraints
        self._exclude = exclude
        self._option_group_id = option_group_id

    @classmethod
    def from_dict(cls, dikt) -> 'QEdge':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The QEdge of this QEdge.  # noqa: E501
        :rtype: QEdge
        """
        return util.deserialize_model(dikt, cls)

    @property
    def knowledge_type(self):
        """Gets the knowledge_type of this QEdge.

        Indicates the type of knowledge that the client wants from the server between the subject and object. If the value is 'lookup', then the client wants direct lookup information from knowledge sources. If the value is 'inferred', then the client wants the server to get creative and connect the subject and object in more speculative and non-direct-lookup ways. If this property is absent or null, it MUST be assumed to mean 'lookup'. This feature is currently experimental and may be further extended in the future.  # noqa: E501

        :return: The knowledge_type of this QEdge.
        :rtype: str
        """
        return self._knowledge_type

    @knowledge_type.setter
    def knowledge_type(self, knowledge_type):
        """Sets the knowledge_type of this QEdge.

        Indicates the type of knowledge that the client wants from the server between the subject and object. If the value is 'lookup', then the client wants direct lookup information from knowledge sources. If the value is 'inferred', then the client wants the server to get creative and connect the subject and object in more speculative and non-direct-lookup ways. If this property is absent or null, it MUST be assumed to mean 'lookup'. This feature is currently experimental and may be further extended in the future.  # noqa: E501

        :param knowledge_type: The knowledge_type of this QEdge.
        :type knowledge_type: str
        """

        self._knowledge_type = knowledge_type

    @property
    def predicates(self):
        """Gets the predicates of this QEdge.


        :return: The predicates of this QEdge.
        :rtype: List[str]
        """
        return self._predicates

    @predicates.setter
    def predicates(self, predicates):
        """Sets the predicates of this QEdge.


        :param predicates: The predicates of this QEdge.
        :type predicates: List[str]
        """
        if predicates is not None and len(predicates) < 1:
            raise ValueError("Invalid value for `predicates`, number of items must be greater than or equal to `1`")  # noqa: E501

        self._predicates = predicates

    @property
    def subject(self):
        """Gets the subject of this QEdge.

        Corresponds to the map key identifier of the subject concept node anchoring the query filter pattern for the query relationship edge.  # noqa: E501

        :return: The subject of this QEdge.
        :rtype: str
        """
        return self._subject

    @subject.setter
    def subject(self, subject):
        """Sets the subject of this QEdge.

        Corresponds to the map key identifier of the subject concept node anchoring the query filter pattern for the query relationship edge.  # noqa: E501

        :param subject: The subject of this QEdge.
        :type subject: str
        """
        if subject is None:
            raise ValueError("Invalid value for `subject`, must not be `None`")  # noqa: E501

        self._subject = subject

    @property
    def object(self):
        """Gets the object of this QEdge.

        Corresponds to the map key identifier of the object concept node anchoring the query filter pattern for the query relationship edge.  # noqa: E501

        :return: The object of this QEdge.
        :rtype: str
        """
        return self._object

    @object.setter
    def object(self, object):
        """Sets the object of this QEdge.

        Corresponds to the map key identifier of the object concept node anchoring the query filter pattern for the query relationship edge.  # noqa: E501

        :param object: The object of this QEdge.
        :type object: str
        """
        if object is None:
            raise ValueError("Invalid value for `object`, must not be `None`")  # noqa: E501

        self._object = object

    @property
    def constraints(self):
        """Gets the constraints of this QEdge.

        A list of contraints applied to a query edge. If there are multiple items, they must all be true (equivalent to AND)  # noqa: E501

        :return: The constraints of this QEdge.
        :rtype: List[QueryConstraint]
        """
        return self._constraints

    @constraints.setter
    def constraints(self, constraints):
        """Sets the constraints of this QEdge.

        A list of contraints applied to a query edge. If there are multiple items, they must all be true (equivalent to AND)  # noqa: E501

        :param constraints: The constraints of this QEdge.
        :type constraints: List[QueryConstraint]
        """

        self._constraints = constraints

    @property
    def exclude(self):
        """Gets the exclude of this QEdge.

        If set to true, then all subgraphs containing this edge are excluded from the final results. (optional)  # noqa: E501

        :return: The exclude of this QEdge.
        :rtype: bool
        """
        return self._exclude

    @exclude.setter
    def exclude(self, exclude):
        """Sets the exclude of this QEdge.

        If set to true, then all subgraphs containing this edge are excluded from the final results. (optional)  # noqa: E501

        :param exclude: The exclude of this QEdge.
        :type exclude: bool
        """

        self._exclude = exclude

    @property
    def option_group_id(self):
        """Gets the option_group_id of this QEdge.

        Optional string acting as a label on a set of nodes and/or edges indicating that they belong to a group that are to be evaluated as a group.   # noqa: E501

        :return: The option_group_id of this QEdge.
        :rtype: str
        """
        return self._option_group_id

    @option_group_id.setter
    def option_group_id(self, option_group_id):
        """Sets the option_group_id of this QEdge.

        Optional string acting as a label on a set of nodes and/or edges indicating that they belong to a group that are to be evaluated as a group.   # noqa: E501

        :param option_group_id: The option_group_id of this QEdge.
        :type option_group_id: str
        """

        self._option_group_id = option_group_id
