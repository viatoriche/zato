# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from string import whitespace
import itertools

# asteval
from asteval import Interpreter

# Bunch
from bunch import Bunch, bunchify

# ConfigObj
from configobj import ConfigObj

# parse
from parse import compile as parse_compile

# sortedcontainers
from sortedcontainers import SortedDict

# YAML
import yaml

# Zato
from zato.process import step, OrderedDict

def tuple_representer(dumper, data):
    return dumper.represent_list(data)

def ordered_dict_representer(dumper, data):
    return dumper.represent_dict(data)

def sorted_dict_representer(dumper, data):
    return dumper.represent_dict(data)

def unicode_representer(dumper, data):
    return dumper.represent_str(data.encode('utf-8'))

yaml.add_representer(tuple, tuple_representer)
yaml.add_representer(OrderedDict, ordered_dict_representer)
yaml.add_representer(SortedDict, sorted_dict_representer)
yaml.add_representer(unicode, unicode_representer)

# ################################################################################################################################

class Config(object):
    def __init__(self):
        self.start = step.Start()
        self.service_map = {}

    def handle_start(self, data):
        self.start.path = data['path']
        self.start.service = data['service']

    def handle_service_map(self, data):
        self.service_map[data['label']] = data['service']

class Pipeline(object):
    def __init__(self):
        self.config = {}
        self.data = {}

        # Same format for all languages supported
        self.entry_pattern = None

class Path(object):
    def __init__(self):
        self.name = ''
        self.nodes = []

Handler = Path

class NodeItem(object):
    def __init__(self):
        self.node_name = ''
        self.data = {}
        self.node = None

    def __cmp__(self, other):
        return self.node_name == other.node_name and sorted(self.data) == sorted(other.data)

    def create_node(self):
        self.node = step.node_names[self.node_name](**self.data)

# ################################################################################################################################

class ProcessDefinition(object):
    """ A definition of a process out of which new process instances are created.
    """
    def __init__(self):
        self.id = ''
        self.name = ''
        self.version = 0
        self.ext_version = ''
        self.lang_code = ''
        self.lang_name = '' 
        self.vocab_text = ''
        self.text = ''
        self.text_split = []
        self.eval_ = Interpreter()
        self.config = Config()
        self.pipeline = Pipeline()
        self.paths = {}
        self.handlers = {}

        self.vocab = Bunch()
        self.vocab.top_level = []
        self.vocab.config = {}
        self.vocab.pipeline = {}
        self.vocab.path = OrderedDict()
        self.vocab.handler = OrderedDict()

# ################################################################################################################################

    def get_block(self, start_idx):
        block = []

        for line in self.text_split[start_idx+1:]:
            line = line.strip()
            if line:
                if list(itertools.ifilter(line.startswith, self.vocab_top_level)):
                    break
                else:
                    block.append(line)

        return block

    def yield_node_info(self, start_idx, vocab_item):
        for line in self.get_block(start_idx):
            for node_name, v in self.vocab[vocab_item].items():
                result = v.parse(line)
                if result:
                    yield node_name, result.named
                    break

# ################################################################################################################################

    def parse_config(self, start_idx):
        for name, data in self.yield_node_info(start_idx, 'config'):
            getattr(self.config, 'handle_{}'.format(name))(data)

# ################################################################################################################################

    def parse_path_handler(self, start_idx, class_, node_name, target):
        elem = class_()
        elem.name = self.vocab[node_name]['name'].parse(self.text_split[start_idx]).named[node_name]

        for name, data in self.yield_node_info(start_idx, node_name):
            path_item = NodeItem()
            path_item.node_name = name
            path_item.data = data
            path_item.create_node()
            elem.nodes.append(path_item)

        target[elem.name] = elem

    def parse_path(self, start_idx):
        self.parse_path_handler(start_idx, Path, 'path', self.paths)

    def parse_handler(self, start_idx):
        self.parse_path_handler(start_idx, Handler, 'handler', self.handlers)

# ################################################################################################################################

    def parse_pipeline(self, start_idx):
        for item in self.get_block(start_idx):
            named = self.pipeline.entry_pattern.parse(item).named
            self.pipeline.config[named['name']] = self.eval_(named['data_type'])

# ################################################################################################################################

    def read_vocab(self):
        conf = ConfigObj(self.vocab_text.splitlines())
        conf_bunch = bunchify(conf)

        self.lang_name = conf_bunch.main.name
        self.vocab_top_level = conf_bunch.main.top_level
        self.pipeline.entry_pattern = parse_compile(conf_bunch.pipeline.pattern)

        self.vocab['path'] = OrderedDict()

        self.vocab.path['name'] = parse_compile(conf_bunch.path.path)
        self.vocab.handler['name'] = parse_compile(conf_bunch.handler.handler)

        for name in ['config', 'path', 'handler']:
            for k, v in conf[name].iteritems():
                if k != name:
                    self.vocab[name][k] = parse_compile(v)

    def parse(self):
        self.read_vocab()
        self.text_split[:] = self.text.splitlines()

        for idx, line in enumerate(self.text_split):
            if line.strip() and line[0] not in whitespace:
                split = line.split()
                block_name = split[0].replace(':', '')
                getattr(self, 'parse_{}'.format(block_name.lower()))(idx)

# ################################################################################################################################

    def add_path_handler_to_canonical(self, out, name, source):
        for elem_name, data in source.items():
            elem = []
            for node in data.nodes:
                elem.append({'node_name':node.node_name, 'data':node.data})
            out[name][elem_name] = elem

    def to_canonical(self):
        """ Returns a canonical form of the process, i.e. a sorted dictionary
        of lists and dictionaries that can be serialized to formats such as YAML.
        """
        out = OrderedDict()
        out['config'] = OrderedDict()
        out['pipeline'] = SortedDict()
        out['path'] = SortedDict()
        out['handler'] = OrderedDict()
        out['_meta'] = OrderedDict()

        out['config']['start'] = self.config.start.to_canonical()
        out['config']['service_map'] = SortedDict(self.config.service_map.iteritems())

        out['pipeline'].update((key, value().__class__.__name__) for key, value in self.pipeline.config.items())

        self.add_path_handler_to_canonical(out, 'path', self.paths)
        self.add_path_handler_to_canonical(out, 'handler', self.handlers)

        out['_meta']['lang_code'] = self.lang_code
        out['_meta']['lang_name'] = self.lang_name
        out['_meta']['text'] = self.text

        return out

    def to_yaml(self, width=60):
        """ Serializes the canonical form of the definition to YAML.
        """
        return yaml.dump(self.to_canonical(), width=width)

    def extract_path_handler(self, name, source, target, class_):

        for item_name, item_data in source[name].items():

            path = target.setdefault(item_name, class_())
            path.name = item_name

            for step_data in item_data:
                path_item = NodeItem()
                path_item.node_name = step_data.node_name
                path_item.data = step_data.data.toDict()
                path_item.create_node()
                path.nodes.append(path_item)

    @staticmethod
    def from_yaml(y):
        data = bunchify(yaml.load(y))

        pd = ProcessDefinition()

        # Meta stuff
        pd.lang_code = data._meta.lang_code
        pd.lang_name = data._meta.lang_name
        pd.text = data._meta.text

        # Config
        pd.config.start.path = data.config.start.path
        pd.config.start.service = data.config.start.service
        pd.config.service_map.update(data.config.service_map.items())

        # Pipeline
        for k, v in data.pipeline.items():
            pd.pipeline.config[k] = pd.eval_(v)

        # Path and Handler
        pd.extract_path_handler('path', data, pd.paths, Path)
        pd.extract_path_handler('handler', data, pd.handlers, Handler)

        return pd

# ################################################################################################################################

if __name__ == '__main__':

    from zato.process.vocab import en_uk

    text = open('./proc.txt').read()

    pd1 = ProcessDefinition()
    pd1.text = text.strip()
    pd1.lang_code = 'en_uk'
    pd1.vocab_text = en_uk
    pd1.parse()

    y = pd1.to_yaml()

    pd2 = ProcessDefinition.from_yaml(y)
    print(pd2.to_yaml())