#! python3

"""A tool to visualize standard data structures in Python"""

import ast
import collections
import json
import re
import uuid
import pydot_ng as pydot
from IPython.display import Image, display
from _ast import AST


# ~~~~~~~~~~~~~~~~~~ PARSING AST OBJ TO JSON ~~~~~~~~~~~~~~~~~~

def ast_parse(method):
    """Check args is dtype str, parse AST, return json obj"""
    def wrapper(*args, **kwargs):
        obj = args[0]
        if not isinstance(obj, str):
            raise TypeError("arg must be of type str")
        ast_obj = ast.parse(obj)
        json_obj = method(ast_obj, **kwargs)
        json_parsed = json.loads(json_obj)

        return json_parsed

    return wrapper


@ast_parse
def json_ast(node):
    """Parse an AST object into JSON."""
    def _format(_node):
        if isinstance(_node, AST):
            fields = [('_PyType', _format(_node.__class__.__name__))]
            fields += [(a, _format(b)) for a, b in iter_fields(_node)]
            return '{ %s }' % ', '.join(('"%s": %s' % field for field in fields))
        if isinstance(_node, list):
            return '[ %s ]' % ', '.join([_format(x) for x in _node])
        if isinstance(_node, bytes):
            return json.dumps(_node.decode("utf-8"))

        return json.dumps(_node)

    return _format(node)


def iter_fields(node):
    """Get attributes of a node."""
    try:
        for field in node._fields:
            yield field, getattr(node, field)
    except AttributeError:
        yield


# ~~~~~~~~~~~~~~~~~~~~~~~~ DRAWING STD DATATYPES ~~~~~~~~~~~~~~~~~~~~~~~~~


def parse_PyType(node):
    if node in ('Expr', 'Module', 'Attribute'):
        return
    if not isinstance(node, dict):
        return node
    if node.get('_PyType') not in ('Tuple', 'Dict', 'List', 'Set',
                                   'Expr', 'Num', 'Str', 'Name'):
        return
    if node.get('_PyType') == 'Dict':
        keys = node.get('keys')
        values = node.get('values')
        del node['keys']
        del node['values']
        zip_kv = zip(keys, values)

        dict_kv = collections.defaultdict(dict)
        for index, i in enumerate(zip_kv):
            dict_kv[f'{index}_key'] = i[0]
            dict_kv[f'{index}_key']['value'] = i[1]
        node = {**node, **dict_kv}
        print(node)
        return node

    return node

def screen_PyType(key, node):
    if key != '_PyType':
        return
    elif node not in ('Tuple', 'Dict', 'List', 'Set',
                      'Num', 'Str', 'Name'):
        return

    return node


def _grapher(graph, ast_nodes, parent_node='', node_hash='__init__'):
    """Recursively parse JSON-AST object into a tree."""
    if isinstance(ast_nodes, dict):
        for key, node in ast_nodes.items():
            # TODO: make conditional below into a func.
            if isinstance(node, list):
                [_grapher(graph, item, parent_node=parent_node, node_hash=node_hash) for item in node]
            node = parse_PyType(node)
            if node:
                if not parent_node and isinstance(node, str):
                    parent_node = node
                    continue
                # parse recursively
                if isinstance(node, dict):
                    _grapher(graph, node, parent_node=parent_node, node_hash=node_hash)
                if isinstance(node, str):
                    if node.islower():  # hacky way to check for filler nodes (i.e. 's', 'n', etc from dict parse)
                        continue
                    node = graph_detail(node, ast_nodes)  # get node detail for graph
                    node_hash = draw(parent_node, node, graph=graph, parent_hash=node_hash)
                    parent_node = node  # once a child now parent



def graph_detail(value, ast_scope):
    """Retrieve node details."""
    detail_keys = ('module', 'n', 's', 'id', 'name', 'attr', 'arg')
    for key in detail_keys:
        if not isinstance(dict.get(ast_scope, key), type(None)):
            value = f"{key}: {ast_scope[key]}"

    return value


def clean_node(method):
    """Decorator to eliminate illegal characters, check type, and\n
    shorten lengthy child and parent nodes."""
    def wrapper(*args, **kwargs):
        parent_name, child_name = tuple('_node' if node == 'node' else node for node in args)
        illegal_char = re.compile(r'[,\\/]$')
        illegal_char.sub('*', child_name)
        if not child_name:
            return
        if len(child_name) > 2500:
            child_name = '~~~DOCS: too long to fit on graph~~~'
        args = (parent_name, child_name)

        return method(*args, **kwargs)

    return wrapper


@clean_node
def draw(parent_name, child_name, graph, parent_hash):
    """Draw parent and child nodes. Create and return new hash\n
    key declared to a child node."""
    parent_node = pydot.Node(parent_hash, label=parent_name, shape='box')
    child_hash = str(uuid.uuid4())  # create hash key
    child_node = pydot.Node(child_hash, label=child_name, shape='box')

    graph.add_node(parent_node)
    graph.add_node(child_node)
    graph.add_edge(pydot.Edge(parent_node, child_node))

    return child_hash


def set_default(obj):
    if isinstance(obj, set):
        pass


# current return of ast_json works.
if __name__ == '__main__':
    from pprint import pprint
    graph = pydot.Dot(graph_type='graph', strict=True, constraint=True,
                      concentrate=True, splines='polyline')
    gen = (i for i in range(10))
    dtest = {'b': 3, 'a': [1, 2, 3], 'c': [10], 5: {'z': 1, 'xz': 2}, 6: {'a'}, 7: gen}
    ltest = [1, 2, 3, ["a!", "b", "c"], (_grapher, 2, 3)]
    stest = {1, 2, 3, _grapher}
    ttest = (1, 2, 3)
    l2test = """[1, 2, 3, ["a!", "b", "c"], (_grapher, 2, 3)]"""
    x = {
      "message":{'a'},
      "data":[{
        "desc":"Inspect For Fluid Leaks",
        "due_mileage":52500,
        "is_oem":True,
        "repair":{
          "repair_difficulty":2,
          "repair_hours":0.0,
          "labor_rate_per_hour":106.38,
          "part_cost":6.15,
          "labor_cost":0.0,
          "misc_cost":0.0,
          "total_cost":6.15
        },
        "parts":[{
          "desc":"Engine Oil",
          "manufacturer":"",
          "price":"6.15",
          "qty":"1"
        }]
      },
      {'a'}]
    }
    test_list = ['ira', 'nanna', 'ghost', [1, 2, 3], {'a', 'b', 'c'}, ('do', 're', 'mi')]
    user_input = str(test_list)
    # print(user_input, l2test)
    # print(gen.__name__)
    pprint(json_ast(user_input))
    _grapher(graph, json_ast(user_input))
    if graph.write_png('dtree.png'):
        print("Graph made successfully.")




