#!/usr/bin/env python3

import yaml
import glob
from jinja2 import Template
from os.path import basename, splitext
from subprocess import check_output
from collections import defaultdict


def convert_markdown_to_tex(markdown):
    return check_output(
        ["pandoc", "--from=markdown", "--to=latex"],
        universal_newlines=True,
        input=markdown
    )


def convert_map_values_to_tex(map):
    if map is not None:
        map.update({k: convert_markdown_to_tex(v) for k, v in map.items()})
        return map


def convert_list_entries_to_tex(list):
    if list is not None:
        return [convert_markdown_to_tex(e) for e in list]


def convert_map_list_to_tex(list_of_maps):
    if list_of_maps is not None:
        return [convert_map_values_to_tex(e) for e in list_of_maps]

##### query cards

with open('templates/query-card-template.tex', 'r') as f:
    query_card_template = Template(f.read())

all_choke_points = set()
all_queries = set()
query_choke_point = defaultdict(list)      # queries -> cps
choke_point_references = defaultdict(list) # cps -> queries

for filename in glob.glob("query-specifications/*.yaml"):
    print("Processing query specification: %s" % filename)
    query_id = splitext(basename(filename))[0]

    with open(filename, 'r') as f:
        doc = yaml.load(f)

    number = doc['number']
    number_string = "%02d" % (number)
    workload = doc['workload']
    description_markdown = doc['description']
    operation = doc['operation']

    query_tuple = (query_id, workload, operation, number)
    all_queries.add(query_tuple)

    choke_points = doc.get('choke_points', [])
    for choke_point in choke_points:
        choke_point_references[choke_point].append(query_tuple)
        all_choke_points.add(choke_point)

    query_choke_point[query_id] = choke_points

    # currently, there are no off-the-shelf solutions for Markdown to TeX conversion in Python 3,
    # so we use Pandoc -- it's hands down the best Markdown to Tex converter you can get anyways
    description_tex = convert_markdown_to_tex(description_markdown)

    query_card_text = query_card_template.render(
        number        = number,
        workload      = workload,
        operation     = operation,
        number_string = number_string,
        query_id      = query_id,
        title         = convert_markdown_to_tex(doc['title']),
        description   = description_tex,
        group         = convert_list_entries_to_tex(doc.get('group')),
        parameters    = convert_map_list_to_tex(doc.get('parameters')),
        result        = convert_map_list_to_tex(doc.get('result')),
        sort          = convert_map_list_to_tex(doc.get('sort')),
        limit         = doc.get('limit'),
        choke_points  = choke_points,
        relevance     = doc.get('relevance'),
    )

    with open("query-cards/%s.tex" % query_id, 'w') as query_card_file:
        query_card_file.write(query_card_text)

##### choke points

with open('templates/choke-point-template.tex', 'r') as f:
    choke_point_template = Template(f.read())

for choke_point in choke_point_references:
    choke_point_filename = str(choke_point).replace('.', '-')

    queries = choke_point_references[choke_point]
    queries_sorted = sorted(queries, key=lambda tup: tup[0])
    choke_point_text = choke_point_template.render(
        queries = queries_sorted,
    )

    with open("query-cards/cp-%s.tex" % choke_point_filename, 'w') as choke_point_file:
        choke_point_file.write(choke_point_text)

##### table for choke points and queries

with open('templates/choke-points-queries.tex', 'r') as f:
    choke_points_queries_template = Template(f.read())

all_queries_sorted = sorted(all_queries, key=lambda tup: tup[0])
all_choke_points_sorted = sorted(all_choke_points)

choke_points_queries_text = choke_points_queries_template.render(
    choke_point_references = choke_point_references,
    query_choke_point = query_choke_point,
    queries = all_queries_sorted,
    choke_points = all_choke_points_sorted,
)

with open("query-cards/choke-points-queries.tex", 'w') as choke_points_queries_template:
    choke_points_queries_template.write(choke_points_queries_text)
