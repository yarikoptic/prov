"""Graphical visualisation support for prov.model.

This module produces graphical visualisation for provenanve graphs.
Requires pydot module and Graphviz.

References:

* pydot Homepage: http://code.google.com/p/pydot/
* Graphviz:       http://www.graphviz.org/
* DOT Language:   http://www.graphviz.org/doc/info/lang.html

.. moduleauthor:: Trung Dong Huynh <trungdong@donggiang.com>
"""
import cgi
import pydot

from prov.model import (
    ProvBundle, PROV_ACTIVITY, PROV_AGENT, PROV_ALTERNATE, PROV_ASSOCIATION, PROV_ATTRIBUTION, PROV_BUNDLE,
    PROV_COMMUNICATION, PROV_DERIVATION, PROV_DELEGATION, PROV_ENTITY, PROV_GENERATION, PROV_INFLUENCE,
    PROV_INVALIDATION, PROV_END, PROV_MEMBERSHIP, PROV_MENTION, PROV_SPECIALIZATION, PROV_START, PROV_USAGE,
    Identifier, PROV_ATTRIBUTE_QNAMES
)


# Visual styles for various elements (nodes) and relations (edges)
# see http://graphviz.org/content/attrs
DOT_PROV_STYLE = {
    # Generic node
    0: {'shape': 'oval', 'style': 'filled', 'fillcolor': 'lightgray', 'color': 'dimgray'},
    # Elements
    PROV_ENTITY: {'shape': 'oval', 'style': 'filled', 'fillcolor': '#FFFC87', 'color': '#808080'},
    PROV_ACTIVITY: {'shape': 'box', 'style': 'filled', 'fillcolor': '#9FB1FC', 'color': '#0000FF'},
    PROV_AGENT: {'shape': 'house', 'style': 'filled', 'fillcolor': '#FED37F'},
    #    PROV_COLLECTION: {'label': 'wasGeneratedBy', 'fontsize': 10.0},
    PROV_BUNDLE: {'shape': 'folder', 'style': 'filled', 'fillcolor': 'aliceblue'},
    # Relations
    PROV_GENERATION: {'label': 'wasGeneratedBy', 'fontsize': '10.0', 'color': 'darkgreen', 'fontcolor': 'darkgreen'},
    PROV_USAGE: {'label': 'used', 'fontsize': '10.0', 'color': 'red4', 'fontcolor': 'red'},
    PROV_COMMUNICATION: {'label': 'wasInformedBy', 'fontsize': '10.0'},
    PROV_START: {'label': 'wasStartedBy', 'fontsize': '10.0'},
    PROV_END: {'label': 'wasEndedBy', 'fontsize': '10.0'},
    PROV_INVALIDATION: {'label': 'wasInvalidatedBy', 'fontsize': '10.0'},
    PROV_DERIVATION: {'label': 'wasDerivedFrom', 'fontsize': '10.0'},
    PROV_ATTRIBUTION: {'label': 'wasAttributedTo', 'fontsize': '10.0', 'color': '#FED37F'},
    PROV_ASSOCIATION: {'label': 'wasAssociatedWith', 'fontsize': '10.0', 'color': '#FED37F'},
    PROV_DELEGATION: {'label': 'actedOnBehalfOf', 'fontsize': '10.0', 'color': '#FED37F'},
    PROV_INFLUENCE: {'label': 'wasInfluencedBy', 'fontsize': '10.0', 'color': 'grey'},
    PROV_ALTERNATE: {'label': 'alternateOf', 'fontsize': '10.0'},
    PROV_SPECIALIZATION: {'label': 'specializationOf', 'fontsize': '10.0'},
    PROV_MENTION: {'label': 'mentionOf', 'fontsize': '10.0'},
    PROV_MEMBERSHIP: {'label': 'hadMember', 'fontsize': '10.0'},
    }

ANNOTATION_STYLE = {'shape': 'note', 'color': 'gray', 'fontcolor': 'black', 'fontsize': '10'}
ANNOTATION_LINK_STYLE = {'arrowhead': 'none', 'style': 'dashed', 'color': 'gray'}
ANNOTATION_START_ROW = '<<TABLE cellpadding=\"0\" border=\"0\">'
ANNOTATION_ROW_TEMPLATE = """    <TR>
        <TD align=\"left\" href=\"%s\">%s</TD>
        <TD align=\"left\"%s>%s</TD>
    </TR>"""
ANNOTATION_END_ROW = '    </TABLE>>'


def htlm_link_if_uri(value):
    try:
        uri = value.uri
        return '<a href="%s">%s</a>' % (uri, unicode(value))
    except AttributeError:
        return unicode(value)


def prov_to_dot(bundle, show_nary=True, use_labels=False, show_element_attributes=True, show_relation_attributes=True):
    """
    Convert a provenance bundle/document into a DOT graphical representation.

    :param bundle: The provenance bundle/document to be converted.
    :type name: :class:`ProvBundle`
    :param show_nary: shows all elements in n-ary relations.
    :type show_nary: bool
    :param use_labels: uses the prov:label property of an element as its name (instead of its identifier).
    :type use_labels: bool
    :param show_element_attributes: shows attributes of elements.
    :type show_element_attributes: bool
    :param show_relation_attributes: shows attributes of relations.
    :type show_relation_attributes: bool
    :returns:  :class:`pydot.Dot` -- the Dot object.
    """
    maindot = pydot.Dot(graph_type='digraph', rankdir='BT')

    node_map = {}
    count = [0, 0, 0, 0]  # counters for node ids

    def _bundle_to_dot(dot, bundle):

        def _attach_attribute_annotation(node, record):
            # Adding a node to show all attributes
            attributes = list(
                (attr_name, value) for attr_name, value in record.attributes
                if attr_name not in PROV_ATTRIBUTE_QNAMES
            )

            if not attributes:
                return  # No attribute to display

            ann_rows = [ANNOTATION_START_ROW]
            ann_rows.extend(
                ANNOTATION_ROW_TEMPLATE % (
                    attr.uri, cgi.escape(unicode(attr)),
                    ' href=\"%s\"' % value.uri if isinstance(value, Identifier) else '',
                    cgi.escape(unicode(value)))
                for attr, value in attributes
            )
            ann_rows.append(ANNOTATION_END_ROW)
            count[3] += 1
            annotations = pydot.Node('ann%d' % count[3], label='\n'.join(ann_rows), **ANNOTATION_STYLE)
            dot.add_node(annotations)
            dot.add_edge(pydot.Edge(annotations, node, **ANNOTATION_LINK_STYLE))

        def _add_node(record):
            if isinstance(record, ProvBundle):
                count[2] += 1
                subdot = pydot.Cluster(graph_name='c%d' % count[2], URL='"%s"' % record.identifier.uri)
                if use_labels:
                    subdot.set_label('"%s"' % unicode(record.label))
                else:
                    subdot.set_label('"%s"' % unicode(record.identifier))
                _bundle_to_dot(subdot, record)
                dot.add_subgraph(subdot)
                return subdot
            else:
                count[0] += 1
                node_id = 'n%d' % count[0]
                if use_labels:
                    node_label = '"%s"' % unicode(record.label)
                else:
                    node_label = '"%s"' % unicode(record.identifier)

                uri = record.identifier.uri
                style = DOT_PROV_STYLE[record.get_type()]
                node = pydot.Node(node_id, label=node_label, URL='"%s"' % uri, **style)
                node_map[uri] = node
                dot.add_node(node)

                if show_element_attributes:
                    _attach_attribute_annotation(node, rec)
                return node

        def _add_generic_node(qname):
            count[0] += 1
            node_id = 'n%d' % count[0]
            node_label = '"%s"' % unicode(qname)

            uri = qname.uri
            style = DOT_PROV_STYLE[0]
            node = pydot.Node(node_id, label=node_label, URL='"%s"' % uri, **style)
            node_map[uri] = node
            dot.add_node(node)
            return node

        def _get_bnode():
            count[1] += 1
            bnode_id = 'b%d' % count[1]
            bnode = pydot.Node(bnode_id, label='""', shape='point', color='gray')
            dot.add_node(bnode)
            return bnode

        def _get_node(qname):
            if qname is None:
                return _get_bnode()
            uri = qname.uri
            if uri not in node_map:
                _add_generic_node(qname)
            return node_map[uri]

        records = bundle.get_records()
        relations = []
        for rec in records:
            if rec.is_element():
                _add_node(rec)
            else:
                # Saving the relations for later processing
                relations.append(rec)

        for rec in relations:
            args = rec.args
            # skipping empty records
            if not args:
                continue
            # picking element nodes
            nodes = [value for attr_name, value in rec.formal_attributes if attr_name in PROV_ATTRIBUTE_QNAMES]
            other_attributes = [
                (attr_name, value) for attr_name, value in rec.attributes if attr_name not in PROV_ATTRIBUTE_QNAMES
            ]
            add_attribute_annotation = show_relation_attributes and other_attributes
            add_nary_elements = len(nodes) > 2 and show_nary
            style = DOT_PROV_STYLE[rec.get_type()]
            if len(nodes) < 2:  # too few elements for a relation?
                continue  # cannot draw this

            if add_nary_elements or add_attribute_annotation:
                # need a blank node for n-ary relations or the attribute annotation
                # add a blank node
                bnode = _get_bnode()

                dot.add_edge(pydot.Edge(_get_node(nodes[0]), bnode, arrowhead='none', **style))  # the first segment
                style = dict(style)  # copy the style
                del style['label']  # not showing label in the second segment
                dot.add_edge(pydot.Edge(bnode, _get_node(nodes[1]), **style))  # the second segment
                if add_nary_elements:
                    style['color'] = 'gray'  # all remaining segment to be gray
                    for node in nodes[2:]:
                        if node is not None:
                            dot.add_edge(pydot.Edge(bnode, _get_node(node), **style))
                if add_attribute_annotation:
                    _attach_attribute_annotation(bnode, rec)
            else:
                # show a simple binary relations with no annotation
                dot.add_edge(pydot.Edge(_get_node(nodes[0]), _get_node(nodes[1]), **style))

    unified = bundle.unified()
    _bundle_to_dot(maindot, unified)
    return maindot