#!/bin/env python3
import sys
def eprint(*args, **kwargs): print(*args, file=sys.stderr, **kwargs)

import os
import json
import ast
import re
import numpy as np
import pandas as pd
import math
from ARAX_response import ARAXResponse
from ARAX_messenger import ARAXMessenger
from ARAX_expander import ARAXExpander
from ARAX_resultify import ARAXResultify
from ARAX_decorator import ARAXDecorator
from biolink_helper import BiolinkHelper
import traceback
from collections import Counter
from collections.abc import Hashable
from itertools import combinations
import copy

pathlist = os.path.realpath(__file__).split(os.path.sep)
RTXindex = pathlist.index("RTX")
sys.path.append(os.path.sep.join([*pathlist[:(RTXindex + 1)], 'code', 'UI', 'OpenAPI', 'python-flask-server']))
from openapi_server.models.q_edge import QEdge
from openapi_server.models.q_node import QNode
from openapi_server.models.attribute import Attribute as EdgeAttribute
from openapi_server.models.edge import Edge
from openapi_server.models.node import Node
from openapi_server.models.knowledge_graph import KnowledgeGraph

sys.path.append(os.path.sep.join([*pathlist[:(RTXindex + 1)], 'code', 'ARAX', 'NodeSynonymizer']))
from node_synonymizer import NodeSynonymizer





class InferUtilities:

    #### Constructor
    def __init__(self):
        self.response = None
        self.message = None
        self.parameters = None
        self.report_stats = True
        self.bh = BiolinkHelper()

    def __get_formated_edge_key(self, edge: Edge, kp: str = 'infores:rtx-kg2') -> str:
        return f"{kp}:{edge.subject}-{edge.predicate}-{edge.object}"

    def __none_to_zero(self, val):
        if val is None:
            return 0
        else: 
            return val

    def resultify_and_sort(self, essence_scores):
        message = self.response.envelope.message
        resultifier = ARAXResultify()
        resultify_params = {
            "ignore_edge_direction": "true"
        }
        self.response = resultifier.apply(self.response, resultify_params)
        for result in message.results:
            if result.essence in essence_scores:
                result.score = essence_scores[result.essence]
            else:
                result.score = None
                self.response.warning(
                    f"Error retrieving score for result essence {result.essence}. Setting result score to None.")
        message.results.sort(key=lambda x: self.__none_to_zero(x.score), reverse=True)

    def genrete_treat_subgraphs(self, response: ARAXResponse, top_drugs: pd.DataFrame, top_paths: dict, qedge_id=None, kedge_global_iter: int=0, qedge_global_iter: int=0, qnode_global_iter: int=0, option_global_iter: int=0):
        """
        top_drugs and top_paths returned by Chunyu's createDTD.py code (predict_top_n_drugs and predict_top_m_paths respectively).
        Ammends the response effectively TRAPI-ifying the paths returned by Chunyu's code.
        May not work on partially filled out response (as it assumes fresh QG and KG, i.e. not stuff partially filled out).
        The *_global_iter vars are to keep count of qedge and kedge if this is run multiple times. But see previous line for proviso.
        Returns the response and all the *_global_iters
        """
        self.response = response
        self.kedge_global_iter = 0
        self.qedge_global_iter = 0
        self.qnode_global_iter = 0
        self.option_global_iter = 0
        self.qedge_id = qedge_id
        message = self.response.envelope.message
        # check to make sure that the qedge_id either exists and is in the QG, or else does not exist and the QG is empty
        if qedge_id is not None:
            if not hasattr(message, 'query_graph') or qedge_id not in message.query_graph.edges:
                self.response.error(f"qedge_id {qedge_id} not in QG, QG is {message.query_graph}")
                raise Exception(f"qedge_id {qedge_id} not in QG")
        elif hasattr(message, 'query_graph'):
            if len(message.query_graph.edges) > 0:
                self.response.error("qedge_id is None but QG is not empty")
                raise Exception("qedge_id is None but QG is not empty")

        expander = ARAXExpander()
        messenger = ARAXMessenger()
        synonymizer = NodeSynonymizer()
        decorator = ARAXDecorator()

        kp = 'infores:rtx-kg2'

        # FW: This would be an example of how to get node info from curies instead of names
        #node_curies = set([y for paths in top_paths.values() for x in paths for y in x[0].split("->")[::2] if y != ''])
        #node_info = synonymizer.get_canonical_curies(curies=list(node_curies))
        node_names = set([y for paths in top_paths.values() for x in paths for y in x[0].split("->")[::2] if y != ''])
        node_info = synonymizer.get_canonical_curies(names=list(node_names))
        node_name_to_id = {k: v['preferred_curie'] for k, v in node_info.items() if v is not None}
        # If there are no paths, then just quit
        # FIXME: A more intelligent thing to do would be to then fall back on the traditional DTD database
        #if not top_paths.values():
        #    self.response.error("No paths found in the explainable DTD model", error_code="NoPathsFound")
        #    return self.response, self.kedge_global_iter, self.qedge_global_iter, self.qnode_global_iter, self.option_global_iter
        path_lengths = set([math.floor(len(x[0].split("->"))/2.) for paths in top_paths.values() for x in paths])
        try:
            max_path_len = max(path_lengths)
        except ValueError:
            max_path_len = 0
        # replace this with the value of top_drugs['drug_name'].tolist()[0]
        #disease = list(top_paths.keys())[0][1]
        #disease_curie = disease
        disease_curie = top_drugs['disease_id'].tolist()[0]
        #disease_name = list(top_paths.values())[0][0][0].split("->")[-1]
        disease_name = top_drugs['disease_name'].tolist()[0]
        if not message.knowledge_graph or not hasattr(message, 'knowledge_graph'):  # if the knowledge graph is empty, create it
            message.knowledge_graph = KnowledgeGraph()
            message.knowledge_graph.nodes = {}
            message.knowledge_graph.edges = {}
        if not hasattr(message.knowledge_graph, 'nodes'):
            message.knowledge_graph.nodes = {}
        if not hasattr(message.knowledge_graph, 'edges'):
            message.knowledge_graph.edges = {}
        # shorthand frequently used entities
        knowledge_graph = message.knowledge_graph
        query_graph = message.query_graph

        # Only add these in if the query graph is empty
        if not hasattr(message, 'query_graph') or len(message.query_graph.edges) == 0:
            qedge_id = "probably_treats"
            add_qnode_params = {
                'key': "disease",
                'name': disease_curie,
            }
            self.response = messenger.add_qnode(self.response, add_qnode_params)
            knowledge_graph.nodes[disease_curie] = Node(name=disease_name, categories=['biolink:DiseaseOrPhenotypicFeature'])
            knowledge_graph.nodes[disease_curie].qnode_keys = ['disease']
            node_name_to_id[disease_name] = disease_curie
            add_qnode_params = {
                'key': "drug",
                'categories': ['biolink:Drug']
            }
            self.response = messenger.add_qnode(self.response, add_qnode_params)
            add_qedge_params = {
                'key': qedge_id,
                'subject': "drug",
                'object': "disease",
                'predicates': [f"biolink:{qedge_id}"]
            }
            self.response = messenger.add_qedge(self.response, add_qedge_params)
            message.query_graph.edges[add_qedge_params['key']].filled = True
            drug_qnode_key = 'drug'
            disease_qnode_key = 'disease'
        else:
            # add the disease to the knowledge graph
            # FIXME: is this the best way to be adding the node to the knowledge graph?
            #knowledge_graph.nodes[disease] = Node(name=disease_name, categories=[
            #    'biolink:DiseaseOrPhenotypicFeature', 'biolink:Disease'])
            categories_to_add = set()
            categories_to_add.update(self.bh.get_ancestors('biolink:Disease'))
            categories_to_add.update(list(synonymizer.get_normalizer_results(disease_curie)[disease_curie]['categories'].keys()))
            categories_to_add = list(categories_to_add)
            knowledge_graph.nodes[disease_curie] = Node(name=disease_name, categories=categories_to_add)
            drug_qnode_key = response.envelope.message.query_graph.edges[qedge_id].subject
            disease_qnode_key = response.envelope.message.query_graph.edges[qedge_id].object
            knowledge_graph.nodes[disease_curie].qnode_keys = [disease_qnode_key]
            # Don't add a new edge in for the probably_treats as there is already an edge there with the knowledge type inferred
            # But do say that this edge has been filled
            message.query_graph.edges[qedge_id].filled = True
            # Nuke the drug categories since they vary depending on what the model returns
            message.query_graph.nodes[drug_qnode_key].categories = ['biolink:NamedThing']
            # Just use the drug and disease that are currently in the QG
        # now that KG and QG are populated with stuff, shorthand them
        knodes = knowledge_graph.nodes
        kedges = knowledge_graph.edges
        qnodes = query_graph.nodes
        qedges = query_graph.edges

        # If the max path len is 0, that means there are no paths found, so just insert the drugs with the probability_treats on them
        if max_path_len == 0:
            essence_scores = {}
            node_ids = set(top_drugs['drug_id'])
            node_info = synonymizer.get_canonical_curies(curies=list(node_ids))
            node_id_to_canonical_id = {k: v['preferred_curie'] for k, v in node_info.items() if v is not None}
            node_id_to_score = dict(zip(node_ids, top_drugs['tp_score']))
            # Add the drugs to the knowledge graph
            for node_id in node_ids:
                drug_canonical_id = node_id_to_canonical_id[node_id]
                drug_categories = [node_info[node_id]['preferred_category']]
                drug_categories.append('biolink:NamedThing')
                # add the node to the knowledge graph
                drug_name = node_info[node_id]['preferred_name']
                essence_scores[drug_name] = node_id_to_score[node_id]
                if drug_canonical_id not in knodes:
                    knodes[drug_canonical_id] = Node(name=drug_name, categories=drug_categories)
                    knodes[drug_canonical_id].qnode_keys = [drug_qnode_key]
                else:  # it's already in the KG, just pass
                    pass
                # add the edge to the knowledge graph
                if drug_canonical_id not in kedges:
                    treat_score = node_id_to_score[node_id]
                    edge_attribute_list = [
                        EdgeAttribute(original_attribute_name="provided_by", value="infores:arax",
                                      attribute_type_id="biolink:aggregator_knowledge_source",
                                      attribute_source="infores:arax", value_type_id="biolink:InformationResource"),
                        EdgeAttribute(original_attribute_name=None, value=True,
                                      attribute_type_id="biolink:computed_value",
                                      attribute_source="infores:arax-reasoner-ara", value_type_id="metatype:Boolean",
                                      value_url=None,
                                      description="This edge is a container for a computed value between two nodes that is not directly attachable to other edges."),
                        EdgeAttribute(attribute_type_id="EDAM:data_0951", original_attribute_name="probability_treats",
                                      value=str(treat_score))
                    ]
                    new_edge = Edge(subject=drug_canonical_id, object=disease_curie, predicate='biolink:probably_treats', attributes=edge_attribute_list)
                    new_edge_key = self.__get_formated_edge_key(edge=new_edge, kp=kp)
                    kedges[new_edge_key] = new_edge
                    kedges[new_edge_key].filled = True
                    kedges[new_edge_key].qedge_keys = [qedge_id]
            self.resultify_and_sort(essence_scores)
            return self.response, self.kedge_global_iter, self.qedge_global_iter, self.qnode_global_iter, self.option_global_iter


        # Otherwise we do have paths and we need to handle them
        path_keys = [{} for i in range(max_path_len)]
        for i in range(max_path_len+1):
            if (i+1) in path_lengths:
                path_qnodes = [drug_qnode_key]
                for j in range(i):
                    new_qnode_key = f"creative_DTD_qnode_{self.qnode_global_iter}"
                    path_qnodes.append(new_qnode_key)
                    add_qnode_params = {
                        'key' : new_qnode_key,
                        'option_group_id': f"creative_DTD_option_group_{self.option_global_iter}",
                        "is_set": "true"
                    }
                    self.response = messenger.add_qnode(self.response, add_qnode_params)
                    self.qnode_global_iter += 1
                path_qnodes.append(disease_qnode_key)
                qnode_pairs = list(zip(path_qnodes,path_qnodes[1:]))
                qedge_key_list = []
                for qnode_pair in qnode_pairs:
                    add_qedge_params = {
                        'key': f"creative_DTD_qedge_{self.qedge_global_iter}",
                        'subject': qnode_pair[0],
                        'object': qnode_pair[1],
                        'option_group_id': f"creative_DTD_option_group_{self.option_global_iter}"
                    }
                    qedge_key_list.append(f"creative_DTD_qedge_{self.qedge_global_iter}")
                    self.qedge_global_iter += 1
                    self.response = messenger.add_qedge(self.response, add_qedge_params)
                    qedges[add_qedge_params['key']].filled = True
                path_keys[i]["qnode_pairs"] = qnode_pairs
                path_keys[i]["qedge_keys"] = qedge_key_list
                self.option_global_iter += 1

        # FW: code that will add resulting paths to the query graph and knowledge graph goes here
        essence_scores = {}
        for (drug, disease), paths in top_paths.items():
            path_added = False
            # Splits the paths which are encodes as strings into a list of nodes names and edge predicates
            # The x[0] is here since each element consists of the string path and a score we are currently ignoring the score
            split_paths = [x[0].split("->") for x in paths]
            for path in split_paths:
                drug_name = path[0]
                if any([x not in node_name_to_id for x in path[::2]]):
                    continue
                n_elements = len(path)
                # Creates edge tuples of the form (node name 1, edge predicate, node name 2)
                edge_tuples = [(path[i],path[i+1],path[i+2]) for i in range(0,n_elements-2,2)]
                path_idx = len(edge_tuples)-1
                added_nodes = set()
                for i in range(path_idx+1):
                    subject_qnode_key = path_keys[path_idx]["qnode_pairs"][i][0]
                    subject_name = edge_tuples[i][0]
                    subject_curie = node_name_to_id[subject_name]
                    subject_category = node_info[subject_name]['preferred_category']
                    if subject_curie not in knodes:
                        knodes[subject_curie] = Node(name=subject_name, categories=[subject_category, 'biolink:NamedThing'])
                        knodes[subject_curie].qnode_keys = [subject_qnode_key]
                    elif subject_qnode_key not in knodes[subject_curie].qnode_keys:
                        knodes[subject_curie].qnode_keys.append(subject_qnode_key)
                    object_qnode_key = path_keys[path_idx]["qnode_pairs"][i][1]
                    object_name = edge_tuples[i][2]
                    object_curie = node_name_to_id[object_name]
                    object_category = node_info[object_name]['preferred_category']
                    if object_curie not in knodes:
                        knodes[object_curie] = Node(name=object_name, categories=[object_category, 'biolink:NamedThing'])
                        knodes[object_curie].qnode_keys = [object_qnode_key]
                    elif object_qnode_key not in knodes[object_curie].qnode_keys:
                        knodes[object_curie].qnode_keys.append(object_qnode_key)
                    predicate = edge_tuples[i][1]
                    # Handle the self-loop relation
                    if predicate == "SELF_LOOP_RELATION":
                        self.response.warning(f"Self-loop relation detected: {subject_name} {predicate} {object_name}, replacing with placeholder 'biolink:self_loop_relation'")
                        predicate = "biolink:self_loop_relation"
                    new_edge = Edge(subject=subject_curie, object=object_curie, predicate=predicate, attributes=[])
                    new_edge.attributes.append(EdgeAttribute(attribute_type_id="biolink:aggregator_knowledge_source",
                                         value=kp,
                                         value_type_id="biolink:InformationResource",
                                         attribute_source=kp))
                    new_edge_key = self.__get_formated_edge_key(edge=new_edge, kp=kp)
                    kedges[new_edge_key] = new_edge
                    kedges[new_edge_key].qedge_keys = [path_keys[path_idx]["qedge_keys"][i]]
                path_added = True
            if path_added:
                treat_score = top_drugs.loc[top_drugs['drug_id'] == drug]["tp_score"].iloc[0]
                essence_scores[drug_name] = treat_score
                edge_attribute_list = [
                    # EdgeAttribute(original_attribute_name="defined_datetime", value=defined_datetime, attribute_type_id="metatype:Datetime"),
                    EdgeAttribute(original_attribute_name="provided_by", value="infores:arax", attribute_type_id="biolink:aggregator_knowledge_source", attribute_source="infores:arax", value_type_id="biolink:InformationResource"),
                    EdgeAttribute(original_attribute_name=None, value=True, attribute_type_id="biolink:computed_value", attribute_source="infores:arax-reasoner-ara", value_type_id="metatype:Boolean", value_url=None, description="This edge is a container for a computed value between two nodes that is not directly attachable to other edges."),
                    EdgeAttribute(attribute_type_id="EDAM:data_0951", original_attribute_name="probability_treats", value=str(treat_score))
                ]
                #edge_predicate = qedge_id
                edge_predicate = "biolink:probably_treats"
                if hasattr(qedges[qedge_id], 'predicates') and qedges[qedge_id].predicates:
                    edge_predicate = qedges[qedge_id].predicates[0]  # FIXME: better way to handle multiple predicates?
                fixed_edge = Edge(predicate=edge_predicate, subject=node_name_to_id[drug_name], object=node_name_to_id[disease_name],
                                attributes=edge_attribute_list)
                #fixed_edge.qedge_keys = ["probably_treats"]
                fixed_edge.qedge_keys = [qedge_id]
                kedges[f"creative_DTD_prediction_{self.kedge_global_iter}"] = fixed_edge
                self.kedge_global_iter += 1
            else:
                self.response.warning(f"Something went wrong when adding the subgraph for the drug-disease pair ({drug},{disease}) to the knowledge graph. Skipping this result....")
        self.response = decorator.decorate_nodes(self.response)
        if self.response.status != 'OK':
            return self.response
        self.response = decorator.decorate_edges(self.response)
        if self.response.status != 'OK':
            return self.response

        #FIXME: this might cause a problem since it doesn't add optional groups for 1 and 2 hops
        # This might also cause issues when infer is on an intermediate edge
        self.resultify_and_sort(essence_scores)
        

        return self.response, self.kedge_global_iter, self.qedge_global_iter, self.qnode_global_iter, self.option_global_iter

